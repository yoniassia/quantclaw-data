#!/usr/bin/env python3
"""
TCMB EVDS Module — Central Bank of Turkey Electronic Data Delivery System

Exchange rates (USD/TRY, EUR/TRY), policy interest rate, CPI/PPI inflation,
monetary aggregates (M1/M2), FX reserves, current account balance, interbank
rates, banking credit, gold reserves, and tourism revenue.

Data Source: https://evds2.tcmb.gov.tr/service/evds
Protocol: REST (JSON)
Auth: API key (TCMB_EVDS_API_KEY in .env)
Rate Limit: 100 requests/minute (free tier)
Coverage: Turkey

Author: QUANTCLAW DATA Build Agent
Initiative: 0066
"""

import json
import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://evds2.tcmb.gov.tr/service/evds"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "tcmb_evds"
CACHE_TTL_FX = 1        # hours — FX rates, interbank, policy rate
CACHE_TTL_MONTHLY = 24   # hours — CPI, money supply, reserves, BOP
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.6       # ~100 req/min → 600ms between requests

_ENV_PATH = Path(__file__).parent.parent / ".env"


def _load_api_key() -> Optional[str]:
    key = os.environ.get("TCMB_EVDS_API_KEY")
    if key:
        return key
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TCMB_EVDS_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


INDICATORS = {
    # --- Exchange Rates (daily) ---
    "FX_USD_TRY": {
        "series": "TP.DK.USD.A.YTL",
        "name": "USD/TRY Exchange Rate (Buying)",
        "description": "Official TCMB USD/TRY buying rate, daily",
        "frequency": "daily",
        "unit": "TRY per USD",
        "cache_ttl": CACHE_TTL_FX,
    },
    "FX_EUR_TRY": {
        "series": "TP.DK.EUR.A.YTL",
        "name": "EUR/TRY Exchange Rate (Buying)",
        "description": "Official TCMB EUR/TRY buying rate, daily",
        "frequency": "daily",
        "unit": "TRY per EUR",
        "cache_ttl": CACHE_TTL_FX,
    },
    "FX_GBP_TRY": {
        "series": "TP.DK.GBP.A.YTL",
        "name": "GBP/TRY Exchange Rate (Buying)",
        "description": "Official TCMB GBP/TRY buying rate, daily",
        "frequency": "daily",
        "unit": "TRY per GBP",
        "cache_ttl": CACHE_TTL_FX,
    },
    "FX_JPY_TRY": {
        "series": "TP.DK.JPY.A.YTL",
        "name": "JPY/TRY Exchange Rate (Buying)",
        "description": "Official TCMB JPY/TRY buying rate, daily (per 100 JPY)",
        "frequency": "daily",
        "unit": "TRY per 100 JPY",
        "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CHF_TRY": {
        "series": "TP.DK.CHF.A.YTL",
        "name": "CHF/TRY Exchange Rate (Buying)",
        "description": "Official TCMB CHF/TRY buying rate, daily",
        "frequency": "daily",
        "unit": "TRY per CHF",
        "cache_ttl": CACHE_TTL_FX,
    },
    # --- Policy & Interbank Rates (daily/weekly) ---
    "POLICY_RATE": {
        "series": "TP.YNTBANKAM.POLITIKAFAIZ",
        "name": "TCMB Policy Rate (One-Week Repo)",
        "description": "Central Bank of Turkey one-week repo auction rate",
        "frequency": "daily",
        "unit": "% p.a.",
        "cache_ttl": CACHE_TTL_FX,
    },
    "OVERNIGHT_RATE": {
        "series": "TP.PY.P1",
        "name": "Overnight Interbank Rate (BIST)",
        "description": "BIST interbank overnight lending rate",
        "frequency": "daily",
        "unit": "% p.a.",
        "cache_ttl": CACHE_TTL_FX,
    },
    # --- CPI / PPI Inflation (monthly) ---
    "CPI_INDEX": {
        "series": "TP.FG.J0",
        "name": "CPI General Index",
        "description": "Consumer Price Index, general (2003=100), monthly",
        "frequency": "monthly",
        "unit": "Index (2003=100)",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    "CPI_FOOD": {
        "series": "TP.FG.J1",
        "name": "CPI Food & Non-Alcoholic Beverages",
        "description": "CPI food and non-alcoholic beverages sub-index, monthly",
        "frequency": "monthly",
        "unit": "Index (2003=100)",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    "CPI_ANNUAL": {
        "series": "TP.TUFE1YI.T1",
        "name": "Annual CPI Inflation Rate (%)",
        "description": "Year-over-year CPI change, headline inflation, monthly",
        "frequency": "monthly",
        "unit": "%",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    # --- Monetary Aggregates (monthly) ---
    "M1_MONEY_SUPPLY": {
        "series": "TP.MBPAR.HM1",
        "name": "M1 Money Supply",
        "description": "Narrow money supply (M1), monthly",
        "frequency": "monthly",
        "unit": "TRY mn",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    "M2_MONEY_SUPPLY": {
        "series": "TP.MBPAR.HM2",
        "name": "M2 Money Supply",
        "description": "Broad money supply (M2), monthly",
        "frequency": "monthly",
        "unit": "TRY mn",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    # --- Balance of Payments (monthly) ---
    "CURRENT_ACCOUNT": {
        "series": "TP.AB.B1",
        "name": "Current Account Balance",
        "description": "Monthly current account balance",
        "frequency": "monthly",
        "unit": "USD mn",
        "cache_ttl": CACHE_TTL_MONTHLY,
    },
    # --- Reserves (weekly) ---
    "FX_RESERVES": {
        "series": "TP.PR.ARZ01",
        "name": "Total FX Reserves",
        "description": "Gross foreign exchange reserves",
        "frequency": "weekly",
        "unit": "USD mn",
        "cache_ttl": CACHE_TTL_FX,
    },
}

# Shorthand FX currency map for CLI
_FX_MAP = {
    "USD": "FX_USD_TRY",
    "EUR": "FX_EUR_TRY",
    "GBP": "FX_GBP_TRY",
    "JPY": "FX_JPY_TRY",
    "CHF": "FX_CHF_TRY",
}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(".", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=ttl_hours):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, default=str, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _to_evds_date(iso_date: str) -> str:
    """Convert YYYY-MM-DD or similar to DD-MM-YYYY for EVDS."""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(iso_date, fmt)
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            continue
    return iso_date


def _api_request(series: str, start_date: str = None, end_date: str = None,
                 api_key: str = None, retries: int = 3) -> Dict:
    """Make a request to the EVDS API with exponential backoff."""
    if not api_key:
        return {"success": False, "error": "No API key — set TCMB_EVDS_API_KEY in .env"}

    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%d-%m-%Y")
    else:
        start_date = _to_evds_date(start_date)

    if not end_date:
        end_date = datetime.now().strftime("%d-%m-%Y")
    else:
        end_date = _to_evds_date(end_date)

    params = {
        "series": series,
        "startDate": start_date,
        "endDate": end_date,
        "type": "json",
        "key": api_key,
    }

    for attempt in range(retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = (2 ** attempt) * 2
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "data": data}

        except requests.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.ConnectionError:
            return {"success": False, "error": "Connection failed"}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            if status == 404:
                return {"success": False, "error": f"Series not found (HTTP 404)"}
            return {"success": False, "error": f"HTTP {status}"}
        except (ValueError, json.JSONDecodeError):
            return {"success": False, "error": "Invalid JSON response"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Rate limited — max retries exceeded"}


def _parse_evds_response(data: dict, series_code: str) -> List[Dict]:
    """Extract date/value pairs from EVDS JSON response."""
    items = data.get("items", [])
    if not items:
        totalCount = data.get("totalCount", 0)
        if totalCount == 0:
            return []
        return []

    series_key = series_code.replace(".", "_")

    results = []
    for item in items:
        date_str = item.get("Tarih") or item.get("UNIXTIME")
        if not date_str:
            continue

        value = item.get(series_key)
        if value is None:
            for k, v in item.items():
                if k not in ("Tarih", "UNIXTIME", "YEARWEEK") and v is not None:
                    value = v
                    break

        if value is None:
            continue

        try:
            if isinstance(value, str):
                value = float(value.replace(",", "."))
            else:
                value = float(value)
        except (ValueError, TypeError):
            continue

        if "Tarih" in item:
            try:
                dt = datetime.strptime(item["Tarih"], "%d-%m-%Y")
                iso_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                iso_date = str(item["Tarih"])
        else:
            iso_date = str(date_str)

        results.append({"date": iso_date, "value": value})

    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator by key name."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    api_key = _load_api_key()
    if not api_key:
        return {"success": False, "error": "No API key — set TCMB_EVDS_API_KEY in .env"}

    cfg = INDICATORS[indicator]
    ttl = cfg["cache_ttl"]

    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, ttl)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["series"], start_date, end_date, api_key)
    if not result["success"]:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_evds_response(result["data"], cfg["series"])
    if not observations:
        return {
            "success": False,
            "indicator": indicator,
            "name": cfg["name"],
            "error": "No observations returned",
        }

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
        "series_code": cfg["series"],
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": observations[0]["value"],
        "latest_date": observations[0]["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": "TCMB EVDS (Central Bank of Turkey)",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_series(series_code: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch any arbitrary EVDS series by its code (e.g. TP.AB.B1)."""
    api_key = _load_api_key()
    if not api_key:
        return {"success": False, "error": "No API key — set TCMB_EVDS_API_KEY in .env"}

    cache_params = {"series": series_code, "start": start_date, "end": end_date}
    cp = _cache_path(series_code, _params_hash(cache_params))
    cached = _read_cache(cp, CACHE_TTL_FX)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(series_code, start_date, end_date, api_key)
    if not result["success"]:
        return {"success": False, "series_code": series_code, "error": result["error"]}

    observations = _parse_evds_response(result["data"], series_code)
    if not observations:
        return {"success": False, "series_code": series_code, "error": "No observations returned"}

    response = {
        "success": True,
        "series_code": series_code,
        "latest_value": observations[0]["value"],
        "latest_date": observations[0]["date"],
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": "TCMB EVDS (Central Bank of Turkey)",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_categories(api_key: str = None) -> Dict:
    """List top-level EVDS data categories."""
    api_key = api_key or _load_api_key()
    if not api_key:
        return {"success": False, "error": "No API key — set TCMB_EVDS_API_KEY in .env"}

    url = f"{BASE_URL}/categories"
    try:
        resp = requests.get(url, params={"type": "json", "key": api_key}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "categories": data, "source": "TCMB EVDS"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_datagroups(api_key: str = None) -> Dict:
    """List all available EVDS data groups."""
    api_key = api_key or _load_api_key()
    if not api_key:
        return {"success": False, "error": "No API key — set TCMB_EVDS_API_KEY in .env"}

    url = f"{BASE_URL}/datagroups"
    try:
        resp = requests.get(url, params={"mode": "0", "type": "json", "key": api_key},
                            timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "datagroups": data, "source": "TCMB EVDS"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_available_indicators() -> List[Dict]:
    """Return list of available pre-configured indicators."""
    return [
        {
            "key": k,
            "series_code": v["series"],
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
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
                "date": data["latest_date"],
                "unit": data["unit"],
                "series_code": data["series_code"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "TCMB EVDS (Central Bank of Turkey)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
TCMB EVDS Module — Central Bank of Turkey (Initiative 0066)

Usage:
  python tcmb_evds.py                                         # Latest key indicators summary
  python tcmb_evds.py fx USD                                   # USD/TRY exchange rate
  python tcmb_evds.py fx EUR                                   # EUR/TRY exchange rate
  python tcmb_evds.py policy_rate                              # Current policy interest rate
  python tcmb_evds.py cpi                                      # CPI inflation latest
  python tcmb_evds.py reserves                                 # FX reserves
  python tcmb_evds.py money_supply                             # M1/M2 monetary aggregates
  python tcmb_evds.py series TP.AB.B1 01-01-2024 01-01-2025   # Custom series with date range
  python tcmb_evds.py categories                               # List all data categories
  python tcmb_evds.py datagroups                               # List all data groups
  python tcmb_evds.py list                                     # List pre-configured indicators
  python tcmb_evds.py <INDICATOR>                              # Fetch specific indicator by key

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<22s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth:   TCMB_EVDS_API_KEY in .env
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd in ("--help", "-h", "help"):
            _print_help()

        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str, ensure_ascii=False))

        elif cmd == "fx":
            currency = sys.argv[2].upper() if len(sys.argv) > 2 else "USD"
            ind = _FX_MAP.get(currency)
            if not ind:
                print(json.dumps({"error": f"Unknown currency: {currency}",
                                  "available": list(_FX_MAP.keys())}))
            else:
                print(json.dumps(fetch_data(ind), indent=2, default=str, ensure_ascii=False))

        elif cmd == "policy_rate":
            print(json.dumps(fetch_data("POLICY_RATE"), indent=2, default=str, ensure_ascii=False))

        elif cmd == "cpi":
            results = {}
            for k in ("CPI_INDEX", "CPI_FOOD", "CPI_ANNUAL"):
                results[k] = fetch_data(k)
                time.sleep(REQUEST_DELAY)
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))

        elif cmd == "reserves":
            print(json.dumps(fetch_data("FX_RESERVES"), indent=2, default=str, ensure_ascii=False))

        elif cmd == "money_supply":
            results = {}
            for k in ("M1_MONEY_SUPPLY", "M2_MONEY_SUPPLY"):
                results[k] = fetch_data(k)
                time.sleep(REQUEST_DELAY)
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))

        elif cmd == "series":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: series <code> [start_date] [end_date]"}))
            else:
                code = sys.argv[2]
                sd = sys.argv[3] if len(sys.argv) > 3 else None
                ed = sys.argv[4] if len(sys.argv) > 4 else None
                print(json.dumps(fetch_series(code, sd, ed), indent=2, default=str,
                                 ensure_ascii=False))

        elif cmd == "categories":
            print(json.dumps(fetch_categories(), indent=2, default=str, ensure_ascii=False))

        elif cmd == "datagroups":
            print(json.dumps(fetch_datagroups(), indent=2, default=str, ensure_ascii=False))

        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
