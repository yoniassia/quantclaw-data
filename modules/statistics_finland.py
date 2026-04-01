#!/usr/bin/env python3
"""
Statistics Finland (Tilastokeskus) PxWeb Module

Finnish macroeconomic data: GDP growth, CPI inflation, unemployment,
employment, industrial production, foreign trade, and housing prices.

Data Source: https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/
Protocol: PxWeb REST API (POST with JSON query)
Auth: None (open access)
Formats: JSON (PxWeb tabular)
Refresh: Monthly (CPI, labour, industrial), Quarterly (GDP, trade, housing)
Coverage: Finland

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

BASE_URL = "https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "statistics_finland"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- GDP (Quarterly National Accounts, Seasonally Adjusted) ---
    "GDP_QOQ": {
        "table_path": "ntp/statfin_ntp_pxt_132h.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Taloustoimi", "selection": {"filter": "item", "values": ["B1GMH"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["vol_kk_kausitvv2015"]}},
        ],
        "name": "GDP Volume Change QoQ (%, SA)",
        "description": "GDP at market prices, seasonally adjusted volume change from previous quarter",
        "frequency": "quarterly",
        "unit": "%",
        "last_n": 40,
    },
    "GDP_YOY": {
        "table_path": "ntp/statfin_ntp_pxt_132h.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Taloustoimi", "selection": {"filter": "item", "values": ["B1GMH"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["vol_vv_kausitvv2015"]}},
        ],
        "name": "GDP Volume Change YoY (%, SA)",
        "description": "GDP at market prices, seasonally adjusted volume change from previous year",
        "frequency": "quarterly",
        "unit": "%",
        "last_n": 40,
    },
    "GDP_CURRENT_PRICES": {
        "table_path": "ntp/statfin_ntp_pxt_132h.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Taloustoimi", "selection": {"filter": "item", "values": ["B1GMH"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["kausitcp"]}},
        ],
        "name": "GDP at Current Prices (EUR mn, SA)",
        "description": "GDP at market prices, seasonally adjusted, current prices in millions of euro",
        "frequency": "quarterly",
        "unit": "EUR million",
        "last_n": 40,
    },
    # --- Consumer Price Index (Monthly) ---
    "CPI_INDEX": {
        "table_path": "khi/statfin_khi_pxt_11xs.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["ip_0_2015"]}},
        ],
        "name": "CPI Index (2015=100)",
        "description": "Consumer Price Index, overall index, base year 2015",
        "frequency": "monthly",
        "unit": "Index (2015=100)",
        "last_n": 60,
    },
    # --- Labour Market (Monthly, Seasonally Adjusted) ---
    "UNEMPLOYMENT_RATE": {
        "table_path": "tyti/statfin_tyti_pxt_135z.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Tyottaste_kausi"]}},
        ],
        "name": "Unemployment Rate (%, SA)",
        "description": "Unemployment rate, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "UNEMPLOYMENT_RATE_YOUTH": {
        "table_path": "tyti/statfin_tyti_pxt_135z.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Tyottaste_15_24_kausi"]}},
        ],
        "name": "Youth Unemployment Rate 15-24 (%, SA)",
        "description": "Unemployment rate, persons aged 15-24, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "EMPLOYMENT_RATE": {
        "table_path": "tyti/statfin_tyti_pxt_135z.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Tyollaste_15_64_kausi"]}},
        ],
        "name": "Employment Rate 15-64 (%, SA)",
        "description": "Employment rate, persons aged 15-64, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    "EMPLOYED_PERSONS": {
        "table_path": "tyti/statfin_tyti_pxt_135z.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Tyolliset_kausi"]}},
        ],
        "name": "Employed Persons (1000, SA)",
        "description": "Number of employed persons in thousands, seasonally adjusted",
        "frequency": "monthly",
        "unit": "1000 persons",
        "last_n": 60,
    },
    # --- Industrial Production (Monthly) ---
    "INDUSTRIAL_OUTPUT_TOTAL": {
        "table_path": "ttvi/statfin_ttvi_pxt_14mh.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Toimiala (TOL 2008)", "selection": {"filter": "item", "values": ["BTD"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Kausitasoitettu"]}},
        ],
        "name": "Industrial Output Index, Total (2021=100, SA)",
        "description": "Volume index of industrial output, total industries (BCD), seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2021=100)",
        "last_n": 60,
    },
    "INDUSTRIAL_OUTPUT_MFG": {
        "table_path": "ttvi/statfin_ttvi_pxt_14mh.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Toimiala (TOL 2008)", "selection": {"filter": "item", "values": ["C"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["Kausitasoitettu"]}},
        ],
        "name": "Industrial Output Index, Manufacturing (2021=100, SA)",
        "description": "Volume index of industrial output, manufacturing (NACE C), seasonally adjusted",
        "frequency": "monthly",
        "unit": "Index (2021=100)",
        "last_n": 60,
    },
    "INDUSTRIAL_OUTPUT_YOY": {
        "table_path": "ttvi/statfin_ttvi_pxt_14mh.px",
        "time_code": "Kuukausi",
        "query_filters": [
            {"code": "Toimiala (TOL 2008)", "selection": {"filter": "item", "values": ["BTD"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["tpk_muutos"]}},
        ],
        "name": "Industrial Output YoY (%, working-day adj.)",
        "description": "Annual change of the working-day adjusted index, total industries",
        "frequency": "monthly",
        "unit": "%",
        "last_n": 60,
    },
    # --- Foreign Trade (Quarterly) ---
    "EXPORTS": {
        "table_path": "tpulk/statfin_tpulk_pxt_12gq.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Alue", "selection": {"filter": "item", "values": ["ULK"]}},
            {"code": "Palveluer\u00e4", "selection": {"filter": "item", "values": ["GS"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["tpulk_C"]}},
        ],
        "name": "Exports of Goods & Services (EUR mn)",
        "description": "Total exports of goods and services, all countries, quarterly",
        "frequency": "quarterly",
        "unit": "EUR million",
        "last_n": 40,
    },
    "IMPORTS": {
        "table_path": "tpulk/statfin_tpulk_pxt_12gq.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Alue", "selection": {"filter": "item", "values": ["ULK"]}},
            {"code": "Palveluer\u00e4", "selection": {"filter": "item", "values": ["GS"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["tpulk_D"]}},
        ],
        "name": "Imports of Goods & Services (EUR mn)",
        "description": "Total imports of goods and services, all countries, quarterly",
        "frequency": "quarterly",
        "unit": "EUR million",
        "last_n": 40,
    },
    # --- Housing Prices (Quarterly) ---
    "HOUSING_PRICE_INDEX": {
        "table_path": "ashi/statfin_ashi_pxt_13mp.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Alue", "selection": {"filter": "item", "values": ["ksu"]}},
            {"code": "Talotyyppi", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Huoneluku", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["ketj_P_QA_T"]}},
        ],
        "name": "Housing Price Index, Old Dwellings (2020=100)",
        "description": "Price index of old dwellings in housing companies, whole country, all types",
        "frequency": "quarterly",
        "unit": "Index (2020=100)",
        "last_n": 24,
    },
    "HOUSING_PRICE_YOY": {
        "table_path": "ashi/statfin_ashi_pxt_13mp.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Alue", "selection": {"filter": "item", "values": ["ksu"]}},
            {"code": "Talotyyppi", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Huoneluku", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["vmuut_P_QA_T"]}},
        ],
        "name": "Housing Price Annual Change (%)",
        "description": "Annual change of price index, old dwellings, whole country, all types",
        "frequency": "quarterly",
        "unit": "%",
        "last_n": 24,
    },
    "HOUSING_PRICE_SQM": {
        "table_path": "ashi/statfin_ashi_pxt_13mp.px",
        "time_code": "Vuosinelj\u00e4nnes",
        "query_filters": [
            {"code": "Alue", "selection": {"filter": "item", "values": ["ksu"]}},
            {"code": "Talotyyppi", "selection": {"filter": "item", "values": ["0"]}},
            {"code": "Huoneluku", "selection": {"filter": "item", "values": ["00"]}},
            {"code": "Tiedot", "selection": {"filter": "item", "values": ["keskihinta_aritm"]}},
        ],
        "name": "Housing Price per m\u00b2 (EUR)",
        "description": "Average price per square metre of old dwellings, whole country, all types",
        "frequency": "quarterly",
        "unit": "EUR/m\u00b2",
        "last_n": 24,
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


def _parse_pxweb_json(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from PxWeb JSON response."""
    try:
        data_rows = raw.get("data", [])
        if not data_rows:
            return []

        columns = raw.get("columns", [])
        time_col_idx = next((i for i, c in enumerate(columns) if c.get("type") == "t"), None)

        results = []
        for row in data_rows:
            keys = row.get("key", [])
            values = row.get("values", [])
            if not values or values[0] in ("..", "", None):
                continue
            try:
                val = float(values[0])
            except (ValueError, TypeError):
                continue

            period = keys[time_col_idx] if time_col_idx is not None and time_col_idx < len(keys) else keys[-1]
            results.append({"time_period": period, "value": val})

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(table_path: str, query_filters: List[Dict], time_code: str, last_n: int = 60) -> Dict:
    """POST a PxWeb query and return parsed response."""
    url = f"{BASE_URL}/{table_path}"
    body = {
        "query": query_filters + [
            {"code": time_code, "selection": {"filter": "top", "values": [str(last_n)]}}
        ],
        "response": {"format": "json"},
    }
    try:
        resp = requests.post(url, json=body, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body_text = ""
        try:
            body_text = e.response.text[:200]
        except Exception:
            pass
        if status == 404:
            return {"success": False, "error": f"Table not found (HTTP 404)"}
        if status == 429:
            return {"success": False, "error": "Rate limited (HTTP 429), retry later"}
        return {"success": False, "error": f"HTTP {status}: {body_text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def navigate_table(path: str = "") -> Dict:
    """Navigate the PxWeb table hierarchy. Pass empty string for root."""
    url = f"{BASE_URL}/{path}" if path else f"{BASE_URL}/"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "items": resp.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, last_n: int = None) -> Dict:
    """Fetch a specific indicator with optional observation count."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    obs_count = last_n or cfg["last_n"]
    cache_params = {"indicator": indicator, "last_n": obs_count}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["table_path"], cfg["query_filters"], cfg["time_code"], last_n=obs_count)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_pxweb_json(result["data"])
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
        "source": f"{BASE_URL}/{cfg['table_path']}",
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
            "table_path": v["table_path"],
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
        "source": "Statistics Finland (Tilastokeskus) PxWeb API",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Statistics Finland (Tilastokeskus) PxWeb Module

Usage:
  python statistics_finland.py                   # Latest values for all indicators
  python statistics_finland.py <INDICATOR>        # Fetch specific indicator
  python statistics_finland.py list               # List available indicators
  python statistics_finland.py navigate [PATH]    # Browse PxWeb table hierarchy

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: PxWeb REST API (POST with JSON query)
Coverage: Finland
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "navigate":
            path = sys.argv[2] if len(sys.argv) > 2 else ""
            print(json.dumps(navigate_table(path), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
