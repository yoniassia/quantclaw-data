#!/usr/bin/env python3
"""
ABS Australia Enhanced — SDMX 2.1 Module

Full SDMX 2.1 API coverage for Australian Bureau of Statistics macro indicators:
GDP, CPI, labour force, balance of payments, retail trade, building approvals,
and international trade in goods.

Data Source: https://data.api.abs.gov.au/rest
Protocol: SDMX 2.1 REST (SDMX-JSON 2.0)
Auth: Open access (no key required)
Refresh: Quarterly (GDP, CPI, BOP), Monthly (LF, RT, BA, ITGS)
Coverage: Australia

Author: QUANTCLAW DATA Build Agent
Initiative: 0026
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://data.api.abs.gov.au/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "abs_australia_sdmx"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- National Accounts (Quarterly, ANA_AGG) ---
    "GDP": {
        "dataflow": "ANA_AGG",
        "key": "M1.GPM.20.AUS.Q",
        "name": "GDP — Chain Volume Measures (AUD mn)",
        "description": "Gross domestic product, seasonally adjusted chain volume measures",
        "frequency": "quarterly",
        "unit": "AUD mn",
    },
    "GDP_GROWTH": {
        "dataflow": "ANA_AGG",
        "key": "M2.GPM.20.AUS.Q",
        "name": "GDP Growth — Quarterly (% change)",
        "description": "GDP percentage change from previous quarter, chain volume measures",
        "frequency": "quarterly",
        "unit": "%",
    },
    "GDP_PER_CAPITA": {
        "dataflow": "ANA_AGG",
        "key": "M1.GPM_PCA.20.AUS.Q",
        "name": "GDP Per Capita — Chain Volume (AUD)",
        "description": "GDP per capita, seasonally adjusted chain volume measures",
        "frequency": "quarterly",
        "unit": "AUD",
    },
    "TERMS_OF_TRADE": {
        "dataflow": "ANA_AGG",
        "key": "M5.TTR.20.AUS.Q",
        "name": "Terms of Trade — Index",
        "description": "Terms of trade index, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "Index",
    },
    "HOUSEHOLD_SAVING_RATIO": {
        "dataflow": "ANA_AGG",
        "key": "M7.HSR.20.AUS.Q",
        "name": "Household Saving Ratio (%)",
        "description": "Household saving ratio, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Consumer Price Index (Quarterly, CPI) ---
    "CPI_INDEX": {
        "dataflow": "CPI",
        "key": "1.10001.10.50.Q",
        "name": "CPI — All Groups Index",
        "description": "Consumer Price Index, all groups, weighted average of eight capital cities",
        "frequency": "quarterly",
        "unit": "Index",
    },
    "CPI_ANNUAL_CHANGE": {
        "dataflow": "CPI_M",
        "key": "3.10001.10.50.M",
        "name": "CPI — Annual % Change (Monthly Indicator)",
        "description": "Monthly CPI indicator, annual percentage change, all groups, weighted average of eight capital cities",
        "frequency": "monthly",
        "unit": "%",
    },
    "CPI_QUARTERLY_CHANGE": {
        "dataflow": "CPI",
        "key": "2.10001.10.50.Q",
        "name": "CPI — Quarterly % Change",
        "description": "CPI percentage change from previous quarter, all groups",
        "frequency": "quarterly",
        "unit": "%",
    },
    # --- Labour Force (Monthly, LF) ---
    "UNEMPLOYMENT_RATE": {
        "dataflow": "LF",
        "key": "M13.3.1599.20.AUS.M",
        "name": "Unemployment Rate (%)",
        "description": "Unemployment rate, persons, all ages, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
    },
    "EMPLOYMENT": {
        "dataflow": "LF",
        "key": "M3.3.1599.20.AUS.M",
        "name": "Employed Persons ('000)",
        "description": "Total employed persons, all ages, seasonally adjusted",
        "frequency": "monthly",
        "unit": "'000",
    },
    "PARTICIPATION_RATE": {
        "dataflow": "LF",
        "key": "M12.3.1599.20.AUS.M",
        "name": "Labour Force Participation Rate (%)",
        "description": "Participation rate, persons, all ages, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
    },
    "LABOUR_FORCE": {
        "dataflow": "LF",
        "key": "M9.3.1599.20.AUS.M",
        "name": "Labour Force ('000)",
        "description": "Total labour force, persons, all ages, seasonally adjusted",
        "frequency": "monthly",
        "unit": "'000",
    },
    # --- Balance of Payments (Quarterly, BOP) ---
    "CURRENT_ACCOUNT": {
        "dataflow": "BOP",
        "key": "1.100.20.Q",
        "name": "Current Account Balance (AUD mn)",
        "description": "Balance of payments current account, seasonally adjusted, current prices",
        "frequency": "quarterly",
        "unit": "AUD mn",
    },
    "BOP_GOODS_BALANCE": {
        "dataflow": "BOP",
        "key": "1.170.20.Q",
        "name": "Goods Balance (AUD mn)",
        "description": "Balance of payments goods trade balance, seasonally adjusted",
        "frequency": "quarterly",
        "unit": "AUD mn",
    },
    # --- Retail Trade (Monthly, RT) ---
    "RETAIL_TRADE": {
        "dataflow": "RT",
        "key": "M1.20.20.AUS.M",
        "name": "Retail Turnover — Total (AUD mn)",
        "description": "Total retail turnover, seasonally adjusted, current prices",
        "frequency": "monthly",
        "unit": "AUD mn",
    },
    # --- Building Approvals (Monthly, BA_GCCSA) ---
    "BUILDING_APPROVALS": {
        "dataflow": "BA_GCCSA",
        "key": "1.1.9.TOT.100.10.AUS.M",
        "name": "Building Approvals — Total Residential Dwellings",
        "description": "Number of residential dwelling units approved, total sectors, original",
        "frequency": "monthly",
        "unit": "Number",
    },
    # --- International Trade in Goods (Monthly, ITGS) ---
    "TRADE_BALANCE": {
        "dataflow": "ITGS",
        "key": "M1.170.20.AUS.M",
        "name": "Goods Trade Balance (AUD mn)",
        "description": "Balance on goods, seasonally adjusted, current prices",
        "frequency": "monthly",
        "unit": "AUD mn",
    },
    "EXPORTS": {
        "dataflow": "ITGS",
        "key": "M1.1000.20.AUS.M",
        "name": "Total Goods Exports (AUD mn)",
        "description": "Total goods credits (exports), seasonally adjusted",
        "frequency": "monthly",
        "unit": "AUD mn",
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


def _parse_sdmx_json(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from ABS SDMX-JSON 2.0 response."""
    try:
        datasets = raw.get("data", {}).get("dataSets", [])
        structures = raw.get("data", {}).get("structures", [])
        if not datasets or not structures:
            return []

        obs_dims = structures[0].get("dimensions", {}).get("observation", [])
        if not obs_dims:
            return []
        time_values = obs_dims[0].get("values", [])

        results = []
        for series_key, series_data in datasets[0].get("series", {}).items():
            for obs_idx_str, obs_vals in series_data.get("observations", {}).items():
                idx = int(obs_idx_str)
                if idx < len(time_values) and obs_vals and obs_vals[0] is not None:
                    results.append({
                        "time_period": time_values[idx]["id"],
                        "value": float(obs_vals[0]),
                    })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(dataflow: str, key: str, start_period: str = None, end_period: str = None) -> Dict:
    url = f"{BASE_URL}/data/{dataflow}/{key}"
    params = {}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    headers = {"Accept": "application/vnd.sdmx.data+json"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 404:
            return {"success": False, "error": "Series not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def discover_dataflows(search: str = None) -> Dict:
    """Discover available ABS SDMX dataflows, optionally filtering by keyword."""
    url = f"{BASE_URL}/dataflow/ABS"
    headers = {"Accept": "application/vnd.sdmx.structure+json"}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        flows = data.get("data", {}).get("dataflows", [])
        results = []
        for f in flows:
            name = f.get("name", "")
            fid = f.get("id", "")
            if search and search.lower() not in name.lower() and search.lower() not in fid.lower():
                continue
            results.append({"id": fid, "name": name, "version": f.get("version", "")})
        return {"success": True, "count": len(results), "dataflows": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series with optional date range."""
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

    default_start = "2020-01" if cfg["frequency"] == "monthly" else "2020-Q1"
    start = start_date or default_start

    result = _api_request(cfg["dataflow"], cfg["key"], start_period=start, end_period=end_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_sdmx_json(result["data"])
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
        "source": f"{BASE_URL}/data/{cfg['dataflow']}/{cfg['key']}",
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
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "ABS Australia SDMX 2.1",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_macro_dashboard() -> Dict:
    """Get headline macro indicators: GDP, CPI, unemployment, trade."""
    dashboard_keys = ["GDP", "GDP_GROWTH", "CPI_ANNUAL_CHANGE", "UNEMPLOYMENT_RATE",
                      "PARTICIPATION_RATE", "RETAIL_TRADE", "CURRENT_ACCOUNT", "TRADE_BALANCE"]
    results = {}
    for key in dashboard_keys:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "change": data.get("period_change"),
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(results),
        "dashboard": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print(f"""
ABS Australia Enhanced SDMX Module (Initiative 0026)

Usage:
  python abs_australia_sdmx.py                         # Latest values for all indicators
  python abs_australia_sdmx.py <INDICATOR>              # Fetch specific indicator
  python abs_australia_sdmx.py list                     # List available indicators
  python abs_australia_sdmx.py dashboard                # Headline macro dashboard
  python abs_australia_sdmx.py discover [keyword]       # Discover ABS dataflows

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON)
Coverage: Australia
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "dashboard":
            print(json.dumps(get_macro_dashboard(), indent=2, default=str))
        elif cmd == "discover":
            keyword = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(discover_dataflows(keyword), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
