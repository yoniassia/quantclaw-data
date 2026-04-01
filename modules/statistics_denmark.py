#!/usr/bin/env python3
"""
Statistics Denmark (DST) Module — Phase 1

Danish national statistics: GDP, CPI inflation, unemployment, foreign trade,
housing prices, consumer confidence, and industrial production.

Data Source: https://api.statbank.dk/v1
Protocol: REST (POST for data queries, JSONSTAT format)
Auth: None (open access)
Refresh: Quarterly (GDP, housing), Monthly (CPI, unemployment, trade, confidence, IPI)
Coverage: Denmark

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.statbank.dk/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "statistics_denmark"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- GDP / National Accounts (quarterly) ---
    "GDP_NOMINAL": {
        "table": "NKHO2",
        "name": "Gross Domestic Product — Current Prices (DKK mn)",
        "description": "Quarterly GDP at current prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "DKK mn",
        "variables": [
            {"code": "TRANSAKT", "values": ["B1GQD"]},
            {"code": "PRISENHED", "values": ["V"]},
            {"code": "SÆSON", "values": ["Y"]},
        ],
    },
    "GDP_REAL": {
        "table": "NKHO2",
        "name": "Gross Domestic Product — 2020 Chained Prices (DKK mn)",
        "description": "Quarterly GDP at 2020 chained prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "DKK mn (2020 prices)",
        "variables": [
            {"code": "TRANSAKT", "values": ["B1GQD"]},
            {"code": "PRISENHED", "values": ["LKV"]},
            {"code": "SÆSON", "values": ["Y"]},
        ],
    },
    "GVA": {
        "table": "NKHO2",
        "name": "Gross Value Added — Current Prices (DKK mn)",
        "description": "Quarterly gross value added at current prices, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "DKK mn",
        "variables": [
            {"code": "TRANSAKT", "values": ["B1GD"]},
            {"code": "PRISENHED", "values": ["V"]},
            {"code": "SÆSON", "values": ["Y"]},
        ],
    },
    # --- Consumer Prices (monthly) ---
    "CPI_INDEX": {
        "table": "PRIS01",
        "name": "Consumer Price Index (2015=100)",
        "description": "Monthly CPI, all items, index level",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
        "variables": [
            {"code": "VAREGR", "values": ["000000"]},
            {"code": "ENHED", "values": ["100"]},
        ],
    },
    "CPI_YOY": {
        "table": "PRIS01",
        "name": "CPI Inflation — Year-on-Year (%)",
        "description": "Monthly CPI, all items, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "variables": [
            {"code": "VAREGR", "values": ["000000"]},
            {"code": "ENHED", "values": ["300"]},
        ],
    },
    "HICP": {
        "table": "PRIS07",
        "name": "EU-Harmonized CPI (HICP, 2015=100)",
        "description": "Monthly HICP, all items, index level",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
        "variables": [
            {"code": "VAREGR", "values": ["000001"]},
            {"code": "ENHED", "values": ["100"]},
        ],
    },
    # --- Labour Market (monthly) ---
    "UNEMPLOYMENT_RATE": {
        "table": "AUS07",
        "name": "Gross Unemployment Rate — Seasonally Adjusted (%)",
        "description": "Monthly gross unemployment as pct of labour force, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "variables": [
            {"code": "YD", "values": ["TOT"]},
            {"code": "SAESONFAK", "values": ["9"]},
        ],
    },
    "UNEMPLOYMENT_NET_RATE": {
        "table": "AUS07",
        "name": "Net Unemployment Rate — Seasonally Adjusted (%)",
        "description": "Monthly net unemployment as pct of labour force, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "variables": [
            {"code": "YD", "values": ["NET"]},
            {"code": "SAESONFAK", "values": ["9"]},
        ],
    },
    "UNEMPLOYED_PERSONS": {
        "table": "AUS07",
        "name": "Gross Unemployed Persons — Seasonally Adjusted",
        "description": "Monthly gross unemployed persons, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Persons",
        "variables": [
            {"code": "YD", "values": ["TOT"]},
            {"code": "SAESONFAK", "values": ["10"]},
        ],
    },
    # --- Foreign Trade (monthly) ---
    "EXPORTS_GOODS": {
        "table": "UHM",
        "name": "Goods Exports — Rest of World (DKK mn, SA)",
        "description": "Monthly goods exports FOB, all countries, seasonally adjusted",
        "frequency": "monthly",
        "unit": "DKK mn",
        "variables": [
            {"code": "POST", "values": ["1.A.A"]},
            {"code": "INDUD", "values": ["2"]},
            {"code": "LAND", "values": ["W1"]},
            {"code": "ENHED", "values": ["93"]},
            {"code": "SÆSON", "values": ["2"]},
        ],
    },
    "IMPORTS_GOODS": {
        "table": "UHM",
        "name": "Goods Imports — Rest of World (DKK mn, SA)",
        "description": "Monthly goods imports, all countries, seasonally adjusted",
        "frequency": "monthly",
        "unit": "DKK mn",
        "variables": [
            {"code": "POST", "values": ["1.A.A"]},
            {"code": "INDUD", "values": ["1"]},
            {"code": "LAND", "values": ["W1"]},
            {"code": "ENHED", "values": ["93"]},
            {"code": "SÆSON", "values": ["2"]},
        ],
    },
    # --- Housing Prices (quarterly) ---
    "HOUSING_PRICE_INDEX": {
        "table": "EJENEU",
        "name": "House Price Index — All Denmark (2015=100)",
        "description": "Quarterly house price index, purchases of dwellings, all Denmark",
        "frequency": "quarterly",
        "unit": "Index (2015=100)",
        "variables": [
            {"code": "URBANGRAD", "values": ["000"]},
            {"code": "UDGTYP", "values": ["H1"]},
        ],
    },
    # --- Consumer Confidence (monthly) ---
    "CONSUMER_CONFIDENCE": {
        "table": "FORV1",
        "name": "Consumer Confidence Indicator",
        "description": "Monthly composite consumer confidence indicator (net balance)",
        "frequency": "monthly",
        "unit": "Net balance",
        "variables": [
            {"code": "INDIKATOR", "values": ["F1"]},
        ],
    },
    "CONSUMER_PRICE_EXPECT": {
        "table": "FORV1",
        "name": "Consumer Price Expectations — Next 12 Months",
        "description": "Monthly consumer price expectations over the next 12 months",
        "frequency": "monthly",
        "unit": "Net balance",
        "variables": [
            {"code": "INDIKATOR", "values": ["F7"]},
        ],
    },
    # --- Industrial Production (monthly) ---
    "INDUSTRIAL_PRODUCTION": {
        "table": "IPOP21",
        "name": "Industrial Production Index — Manufacturing (SA, 2021=100)",
        "description": "Monthly industrial production index, manufacturing, seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2021=100)",
        "variables": [
            {"code": "BRANCHEDB25UDVALG", "values": ["C"]},
            {"code": "SÆSON", "values": ["SÆSON"]},
        ],
    },
}


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


def _parse_jsonstat(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from DST JSONSTAT response.

    DST returns JSONSTAT v1 where ``id`` and ``size`` live inside the
    ``dimension`` object, not at the dataset root.
    """
    try:
        ds = raw.get("dataset", raw)
        values = ds.get("value", [])
        if not values:
            return []

        dim_obj = ds["dimension"]
        dim_ids = dim_obj["id"]
        dim_sizes = dim_obj["size"]

        tid_dim = dim_obj["Tid"]["category"]
        tid_index = tid_dim["index"]
        tid_label = tid_dim.get("label", {})

        tid_pos = dim_ids.index("Tid")

        stride = 1
        for i in range(tid_pos + 1, len(dim_ids)):
            stride *= dim_sizes[i]

        prefix_stride = stride * dim_sizes[tid_pos]
        leading = 1
        for i in range(tid_pos):
            leading *= dim_sizes[i]

        results = []
        for period_id, period_pos in tid_index.items():
            for block in range(leading):
                flat_idx = block * prefix_stride + period_pos * stride
                if flat_idx < len(values) and values[flat_idx] is not None:
                    period_label = tid_label.get(period_id, period_id)
                    results.append({
                        "time_period": period_label,
                        "value": float(values[flat_idx]),
                    })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(table: str, variables: List[Dict]) -> Dict:
    """POST a data query to the DST StatBank API."""
    url = f"{BASE_URL}/data"
    payload = {
        "table": table,
        "format": "JSONSTAT",
        "lang": "en",
        "variables": variables + [{"code": "Tid", "values": ["*"]}],
    }
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if "errorTypeCode" in data:
            return {"success": False, "error": f"DST API error: {data.get('message', data['errorTypeCode'])}"}
        return {"success": True, "data": data}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def discover_tables(query: str = None, limit: int = 20) -> Dict:
    """Discover available DST tables, optionally filtering by keyword."""
    url = f"{BASE_URL}/tables"
    payload = {"lang": "en"}
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        tables = resp.json()
        if query:
            q = query.lower()
            tables = [t for t in tables if q in t.get("text", "").lower() or q in t.get("id", "").lower()]
        tables = tables[:limit]
        return {
            "success": True,
            "tables": [{"id": t["id"], "text": t.get("text", "")} for t in tables],
            "count": len(tables),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["table"], cfg["variables"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_jsonstat(result["data"])

    if start_date:
        observations = [o for o in observations if o["time_period"] >= start_date]
    if end_date:
        observations = [o for o in observations if o["time_period"] <= end_date]

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

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
        "source": f"{BASE_URL} — table {cfg['table']}",
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
            "table": v["table"],
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
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Statistics Denmark (DST)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_trade_balance() -> Dict:
    """Compute trade balance from exports minus imports."""
    exports = fetch_data("EXPORTS_GOODS")
    time.sleep(REQUEST_DELAY)
    imports = fetch_data("IMPORTS_GOODS")

    if not exports.get("success") or not imports.get("success"):
        return {"success": False, "error": "Failed to fetch trade data"}

    exp_map = {dp["period"]: dp["value"] for dp in exports["data_points"]}
    imp_map = {dp["period"]: dp["value"] for dp in imports["data_points"]}
    common = sorted(set(exp_map) & set(imp_map), reverse=True)

    balance_points = []
    for period in common[:30]:
        balance_points.append({
            "period": period,
            "exports": exp_map[period],
            "imports": imp_map[period],
            "balance": round(exp_map[period] - imp_map[period], 1),
        })

    return {
        "success": True,
        "name": "Denmark Goods Trade Balance (DKK mn, SA)",
        "latest_period": balance_points[0]["period"] if balance_points else None,
        "latest_balance": balance_points[0]["balance"] if balance_points else None,
        "data_points": balance_points,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Statistics Denmark (DST) Module (Phase 1)

Usage:
  python statistics_denmark.py                       # Latest values for all indicators
  python statistics_denmark.py <INDICATOR>            # Fetch specific indicator
  python statistics_denmark.py list                   # List available indicators
  python statistics_denmark.py trade-balance          # Goods trade balance
  python statistics_denmark.py tables [QUERY]         # Discover DST tables

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (POST, JSONSTAT)
Coverage: Denmark
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "trade-balance":
            print(json.dumps(get_trade_balance(), indent=2, default=str))
        elif cmd == "tables":
            query = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(discover_tables(query), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
