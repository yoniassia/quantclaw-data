#!/usr/bin/env python3
"""
ISTAT Italy SDMX Module — Phase 1

Italian national statistics: GDP quarterly accounts, CPI inflation (NIC, IPCA/HICP),
unemployment rate, industrial production index, consumer confidence, and business
confidence (IESI economic sentiment).

Data Source: https://esploradati.istat.it/SDMXWS/rest
Protocol: SDMX 2.1 REST (CSV output via content negotiation)
Auth: None (open access, 5 req/min rate limit — exceeding triggers 1-2 day IP ban)
Refresh: Monthly (CPI, IPI, confidence, unemployment), Quarterly (GDP)
Coverage: Italy

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import csv
import io
import json
import sys
import time
import hashlib
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

ENDPOINTS = [
    "http://sdmx.istat.it/SDMXWS/rest",
    "https://esploradati.istat.it/SDMXWS/rest",
]
CACHE_DIR = Path(__file__).parent.parent / "cache" / "istat_italy"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = (10, 90)  # (connect, read) — ISTAT can be extremely slow
ACCEPT_CSV = "application/vnd.sdmx.data+csv;version=1.0.0"

# ISTAT enforces 5 requests per minute per IP; exceeding triggers a 1-2 day block.
RATE_LIMIT = 5
_rate_timestamps: List[float] = []
_rate_lock = threading.Lock()

INDICATORS = {
    # --- GDP (quarterly national accounts) ---
    "GDP_QOQ": {
        "dataflow": "163_184",
        "key": "",
        "name": "GDP & Main Components — Quarterly (SA-WDA)",
        "description": "Prodotto interno lordo e principali componenti, quarterly chain-linked volumes, seasonally and working-day adjusted",
        "frequency": "quarterly",
        "unit": "EUR mn / %",
        "last_n": 20,
    },
    # --- Consumer Prices: NIC (monthly, base 2015) ---
    "CPI_NIC": {
        "dataflow": "167_744",
        "key": "",
        "name": "CPI NIC — Monthly (base 2015=100)",
        "description": "Indice nazionale prezzi al consumo per l'intera collettività (NIC), monthly indices from 2016, base 2015",
        "frequency": "monthly",
        "unit": "index",
        "last_n": 24,
    },
    # --- Consumer Prices: IPCA / HICP (monthly, base 2015) ---
    "CPI_IPCA": {
        "dataflow": "168_760",
        "key": "",
        "name": "HICP/IPCA — Monthly (base 2015=100)",
        "description": "Indice armonizzato dei prezzi al consumo (IPCA/HICP), monthly from 2001, base 2015",
        "frequency": "monthly",
        "unit": "index",
        "last_n": 24,
    },
    # --- Unemployment Rate (monthly) ---
    "UNEMPLOYMENT_RATE": {
        "dataflow": "151_874",
        "key": "",
        "name": "Unemployment Rate — Monthly (%)",
        "description": "Tasso di disoccupazione mensile, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 24,
    },
    # --- Industrial Production Index ---
    "INDUSTRIAL_PRODUCTION": {
        "dataflow": "115_333",
        "key": "",
        "name": "Industrial Production Index — Monthly",
        "description": "Indice della produzione industriale, monthly",
        "frequency": "monthly",
        "unit": "index",
        "last_n": 24,
    },
    # --- Consumer Confidence ---
    "CONSUMER_CONFIDENCE": {
        "dataflow": "30_264",
        "key": "",
        "name": "Consumer Confidence Index (SA)",
        "description": "Fiducia dei consumatori, monthly composite indicator, seasonally adjusted",
        "frequency": "monthly",
        "unit": "index",
        "last_n": 24,
    },
    # --- Business Confidence / Economic Sentiment (IESI) ---
    "BUSINESS_CONFIDENCE": {
        "dataflow": "6_64",
        "key": "",
        "name": "Business Confidence — IESI (SA)",
        "description": "Clima di fiducia delle imprese / Istat Economic Sentiment Indicator, monthly, seasonally adjusted",
        "frequency": "monthly",
        "unit": "index",
        "last_n": 24,
    },
}


def _enforce_rate_limit():
    """Sleep if needed to stay within ISTAT's 5 req/min limit."""
    with _rate_lock:
        now = time.time()
        _rate_timestamps[:] = [t for t in _rate_timestamps if now - t < 60]
        if len(_rate_timestamps) >= RATE_LIMIT:
            sleep_for = 60 - (now - _rate_timestamps[0]) + 0.2
            if sleep_for > 0:
                time.sleep(sleep_for)
        _rate_timestamps.append(time.time())


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _parse_csv(raw_csv: str) -> List[Dict]:
    """Parse ISTAT SDMX CSV response into list of row dicts."""
    try:
        reader = csv.DictReader(io.StringIO(raw_csv))
        rows = []
        for row in reader:
            obs_val = row.get("OBS_VALUE", "")
            if obs_val == "" or obs_val is None:
                continue
            try:
                row["_value"] = float(obs_val)
            except (ValueError, TypeError):
                continue
            rows.append(row)
        return rows
    except Exception:
        return []


def _select_series(rows: List[Dict]) -> List[Dict]:
    """From all CSV rows, pick the best single time-series.

    ISTAT datasets often contain many sub-series (by territory, sex, age, etc.).
    This heuristic selects the series with the most recent observation, preferring
    national-level totals when possible.
    """
    if not rows:
        return []

    skip_cols = {"DATAFLOW", "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME",
                 "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "OBS_QUAL",
                 "OBS_CONF", "_value"}

    dim_cols = [c for c in rows[0].keys() if c not in skip_cols and not c.startswith("_")]

    groups: Dict[str, List[Dict]] = {}
    for row in rows:
        key = "|".join(str(row.get(c, "")) for c in dim_cols)
        groups.setdefault(key, []).append(row)

    if len(groups) == 1:
        series = list(groups.values())[0]
        series.sort(key=lambda r: r.get("TIME_PERIOD", ""), reverse=True)
        return series

    def _score(series_rows):
        """Score a series to pick the best one (higher = better)."""
        score = 0
        sample = series_rows[0] if series_rows else {}
        vals = " ".join(str(v) for v in sample.values()).upper()

        if "IT" in [str(sample.get(c, "")).upper() for c in dim_cols]:
            score += 100
        for tok in ["TOTALE", "TOTAL", "TUTTI", "ALL", "T", "99", "9"]:
            if tok in vals:
                score += 10

        periods = [r.get("TIME_PERIOD", "") for r in series_rows]
        if periods:
            score += len(periods)
            latest = max(periods)
            try:
                year = int(latest[:4])
                score += year - 2000
            except (ValueError, IndexError):
                pass

        return score

    best_key = max(groups, key=lambda k: _score(groups[k]))
    series = groups[best_key]
    series.sort(key=lambda r: r.get("TIME_PERIOD", ""), reverse=True)
    return series


def _api_request(dataflow: str, key: str = "", last_n: int = 24,
                 start_period: str = None, end_period: str = None) -> Dict:
    """Try each ISTAT endpoint in order; return first successful response."""
    key_part = f"/{key}" if key else ""
    path = f"/data/{dataflow}{key_part}"
    params = {}
    if last_n:
        params["lastNObservations"] = last_n
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    headers = {"Accept": ACCEPT_CSV}

    last_error = "All endpoints failed"
    for base_url in ENDPOINTS:
        _enforce_rate_limit()
        url = f"{base_url}{path}"
        try:
            resp = requests.get(url, headers=headers, params=params,
                                timeout=REQUEST_TIMEOUT, verify=False)
            if resp.status_code == 404:
                return {"success": False, "error": f"Dataset not found (HTTP 404)"}
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "html" in content_type.lower():
                last_error = f"Server returned HTML error page ({base_url})"
                continue
            return {"success": True, "data": resp.text, "endpoint": base_url}
        except requests.Timeout:
            last_error = f"Request timed out ({base_url})"
        except requests.ConnectionError:
            last_error = f"Connection failed ({base_url})"
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            last_error = f"HTTP {status} ({base_url})"
        except Exception as e:
            last_error = f"{e} ({base_url})"

    return {"success": False, "error": last_error}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["dataflow"], key=cfg.get("key", ""),
                          last_n=cfg.get("last_n", 24),
                          start_period=start_date, end_period=end_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": result["error"]}

    all_rows = _parse_csv(result["data"])
    if not all_rows:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations in response (empty CSV or parse failure)"}

    series = _select_series(all_rows)
    if not series:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "Could not identify a matching series in the response"}

    observations = [
        {"time_period": r.get("TIME_PERIOD", ""), "value": r["_value"]}
        for r in series
    ]

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    dim_info = {}
    if series:
        sample = series[0]
        skip = {"DATAFLOW", "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME",
                "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "OBS_QUAL",
                "OBS_CONF", "_value"}
        dim_info = {k: v for k, v in sample.items() if k not in skip and not k.startswith("_")}

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "series_dimensions": dim_info,
        "source": f"{ENDPOINTS[0]}/data/{cfg['dataflow']}",
        "endpoint_used": result.get("endpoint", ""),
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "dataflow": v["dataflow"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    results = {}
    errors = []
    for key in INDICATORS:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})

    return {
        "success": True,
        "source": "ISTAT Italy SDMX",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_dataflow(dataflow_id: str, last_n: int = 2) -> Dict:
    """Fetch a small sample from a dataflow and show all available series.

    Useful for exploring dimension structures and calibrating indicator key filters.
    """
    result = _api_request(dataflow_id, last_n=last_n)
    if not result["success"]:
        return result

    rows = _parse_csv(result["data"])
    if not rows:
        return {"success": False, "error": "No data rows returned"}

    skip_cols = {"DATAFLOW", "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME",
                 "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "OBS_QUAL",
                 "OBS_CONF", "_value"}
    dim_cols = [c for c in rows[0].keys() if c not in skip_cols and not c.startswith("_")]

    groups: Dict[str, Dict] = {}
    for row in rows:
        key = "|".join(str(row.get(c, "")) for c in dim_cols)
        if key not in groups:
            groups[key] = {
                "dimensions": {c: row.get(c, "") for c in dim_cols},
                "latest_period": row.get("TIME_PERIOD", ""),
                "latest_value": row.get("_value"),
                "count": 0,
            }
        groups[key]["count"] += 1
        tp = row.get("TIME_PERIOD", "")
        if tp > groups[key]["latest_period"]:
            groups[key]["latest_period"] = tp
            groups[key]["latest_value"] = row.get("_value")

    return {
        "success": True,
        "dataflow": dataflow_id,
        "dimension_columns": dim_cols,
        "total_rows": len(rows),
        "unique_series": len(groups),
        "series": list(groups.values())[:50],
        "endpoint_used": result.get("endpoint", ""),
    }


# --- CLI ---

def _print_help():
    print("""
ISTAT Italy SDMX Module (Phase 1)

Usage:
  python istat_italy.py                              # Latest values for all indicators
  python istat_italy.py <INDICATOR>                   # Fetch specific indicator
  python istat_italy.py list                          # List available indicators
  python istat_italy.py discover <DATAFLOW_ID>        # Explore a dataflow's structure

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {ENDPOINTS[0]}
Fallback: {ENDPOINTS[1]}
Protocol: SDMX 2.1 REST (CSV)
Rate Limit: 5 requests/minute (STRICT — exceeding blocks IP for 1-2 days)
Coverage: Italy
""")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "discover":
            if len(sys.argv) < 3:
                print("Usage: python istat_italy.py discover <DATAFLOW_ID>")
                print("Example: python istat_italy.py discover 163_184")
                sys.exit(1)
            df_id = sys.argv[2]
            last_n = int(sys.argv[3]) if len(sys.argv) > 3 else 2
            print(json.dumps(discover_dataflow(df_id, last_n), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
