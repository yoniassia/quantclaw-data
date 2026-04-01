#!/usr/bin/env python3
"""
Deutsche Bundesbank SDMX Module — Phase 1

German central bank statistical data: government bond yields (Svensson curve),
ECB policy rates, MFI bank lending rates, monetary aggregates (M2/M3),
and balance of payments (current account, trade balance).

Data Source: https://api.statistiken.bundesbank.de/rest
Protocol: SDMX 2.1 REST (SDMX-JSON)
Auth: None (open access)
Refresh: Daily (yields), Monthly (rates, monetary, BOP)
Coverage: Germany / Euro Area

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

BASE_URL = "https://api.statistiken.bundesbank.de/rest"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bundesbank_sdmx"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.25

INDICATORS = {
    # --- German Government Bond Yields (Svensson term structure, daily) ---
    "BUND_1Y": {
        "dataflow": "BBSIS",
        "key": "D.I.ZST.ZI.EUR.S1311.B.A604.R01XX.R.A.A._Z._Z.A",
        "name": "German Govt Bond Yield 1Y (%)",
        "description": "Svensson yield curve, listed federal securities, 1-year residual maturity",
        "frequency": "daily",
        "unit": "%",
    },
    "BUND_2Y": {
        "dataflow": "BBSIS",
        "key": "D.I.ZST.ZI.EUR.S1311.B.A604.R02XX.R.A.A._Z._Z.A",
        "name": "German Govt Bond Yield 2Y (%)",
        "description": "Svensson yield curve, listed federal securities, 2-year residual maturity",
        "frequency": "daily",
        "unit": "%",
    },
    "BUND_5Y": {
        "dataflow": "BBSIS",
        "key": "D.I.ZST.ZI.EUR.S1311.B.A604.R05XX.R.A.A._Z._Z.A",
        "name": "German Govt Bond Yield 5Y (%)",
        "description": "Svensson yield curve, listed federal securities, 5-year residual maturity",
        "frequency": "daily",
        "unit": "%",
    },
    "BUND_10Y": {
        "dataflow": "BBSIS",
        "key": "D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A",
        "name": "German Govt Bond Yield 10Y (%)",
        "description": "Svensson yield curve, listed federal securities, 10-year residual maturity",
        "frequency": "daily",
        "unit": "%",
    },
    "BUND_30Y": {
        "dataflow": "BBSIS",
        "key": "D.I.ZST.ZI.EUR.S1311.B.A604.R30XX.R.A.A._Z._Z.A",
        "name": "German Govt Bond Yield 30Y (%)",
        "description": "Svensson yield curve, listed federal securities, 30-year residual maturity",
        "frequency": "daily",
        "unit": "%",
    },
    # --- ECB Policy Rates (monthly, end-of-month) ---
    "ECB_DEPOSIT_RATE": {
        "dataflow": "BBIN1",
        "key": "M.D0.ECB.ECBFAC.EUR.ME",
        "name": "ECB Deposit Facility Rate (% p.a.)",
        "description": "ECB deposit facility interest rate, month-end",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "ECB_REFI_RATE": {
        "dataflow": "BBIN1",
        "key": "M.D0.ECB.ECBMIN.EUR.ME",
        "name": "ECB Main Refinancing Rate (% p.a.)",
        "description": "ECB main refinancing operations rate, month-end",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "ECB_MARGINAL_RATE": {
        "dataflow": "BBIN1",
        "key": "M.D0.ECB.ECBREF.EUR.ME",
        "name": "ECB Marginal Lending Facility Rate (% p.a.)",
        "description": "ECB marginal lending facility rate, month-end",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    # --- Bank Lending Rates (monthly, MFI interest rate statistics) ---
    "LENDING_RATE_NFC": {
        "dataflow": "BBIM1",
        "key": "M.DE.B.A20.F.R.A.2240.EUR.O",
        "name": "Bank Lending Rate to Corporates (%)",
        "description": "Effective interest rate, outstanding loans to non-financial corporations, all maturities",
        "frequency": "monthly",
        "unit": "%",
    },
    "LENDING_RATE_HOUSING": {
        "dataflow": "BBIM1",
        "key": "M.DE.B.A22.J.R.A.2250.EUR.O",
        "name": "Housing Loan Rate to Households (%)",
        "description": "Effective interest rate, outstanding housing loans to households, maturity >5yr",
        "frequency": "monthly",
        "unit": "%",
    },
    "LENDING_RATE_CONSUMER": {
        "dataflow": "BBIM1",
        "key": "M.DE.B.A25.F.R.A.2250.EUR.O",
        "name": "Consumer Credit Rate to Households (%)",
        "description": "Effective interest rate, outstanding consumer credit to households, all maturities",
        "frequency": "monthly",
        "unit": "%",
    },
    # --- Monetary Aggregates (monthly) ---
    "M2_GERMANY": {
        "dataflow": "BBBS2",
        "key": "M.DB.Y.U.M20.X.1.U2.2300.Z01.E",
        "name": "M2 Money Supply — German Contribution (EUR bn)",
        "description": "German contribution to Euro Area M2 monetary aggregate",
        "frequency": "monthly",
        "unit": "EUR bn",
    },
    "M3_EUROAREA": {
        "dataflow": "BBBS2",
        "key": "M.U2.Y.U.M30.X.1.U2.2300.Z01.E",
        "name": "M3 Money Supply — Euro Area (EUR bn)",
        "description": "Euro Area M3 monetary aggregate",
        "frequency": "monthly",
        "unit": "EUR bn",
    },
    # --- Balance of Payments (monthly) ---
    "CURRENT_ACCOUNT": {
        "dataflow": "BBFBOPV",
        "key": "M.N.DE.W1.S1.S1.T.B.CA._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "Current Account Balance (EUR mn)",
        "description": "Germany current account balance, all countries, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
    },
    "TRADE_BALANCE": {
        "dataflow": "BBFBOPV",
        "key": "M.N.DE.W1.S1.S1.T.B.G._Z._Z._Z.EUR._T._X.N.ALL",
        "name": "Trade Balance — Goods (EUR mn)",
        "description": "Germany goods trade balance, all countries, monthly",
        "frequency": "monthly",
        "unit": "EUR mn",
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
    """Extract time-period/value pairs from Bundesbank SDMX-JSON response."""
    try:
        structure = raw["data"]["structure"]
        datasets = raw["data"]["dataSets"]
        if not datasets:
            return []

        obs_dim = structure["dimensions"]["observation"][0]
        time_values = obs_dim["values"]

        series_attrs = structure["attributes"]["series"]
        title_idx = next((i for i, a in enumerate(series_attrs) if a["id"] == "BBK_TITLE"), None)
        unit_idx = next((i for i, a in enumerate(series_attrs) if a["id"] == "BBK_UNIT"), None)

        results = []
        for series_key, series_data in datasets[0].get("series", {}).items():
            meta = {}
            if title_idx is not None:
                attr_val = series_data["attributes"][title_idx]
                if isinstance(attr_val, int) and attr_val < len(series_attrs[title_idx]["values"]):
                    meta["title"] = series_attrs[title_idx]["values"][attr_val]["name"]
            if unit_idx is not None:
                attr_val = series_data["attributes"][unit_idx]
                if isinstance(attr_val, int) and attr_val < len(series_attrs[unit_idx]["values"]):
                    meta["unit"] = series_attrs[unit_idx]["values"][attr_val]["name"]

            for obs_idx, obs_vals in series_data.get("observations", {}).items():
                idx = int(obs_idx)
                if idx < len(time_values) and obs_vals and obs_vals[0] is not None:
                    results.append({
                        "time_period": time_values[idx]["id"],
                        "value": float(obs_vals[0]),
                        **meta,
                    })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(dataflow: str, key: str, last_n: int = 52) -> Dict:
    url = f"{BASE_URL}/data/{dataflow}/{key}"
    params = {"lastNObservations": last_n}
    headers = {"Accept": "application/json"}
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
            return {"success": False, "error": f"Series not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
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

    extra_params = {}
    if start_date:
        extra_params["startPeriod"] = start_date
    if end_date:
        extra_params["endPeriod"] = end_date
    last_n = 260 if cfg["frequency"] == "daily" else 60

    result = _api_request(cfg["dataflow"], cfg["key"], last_n=last_n)
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
        "source": "Deutsche Bundesbank SDMX",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Get current German government bond yield curve."""
    maturities = ["BUND_1Y", "BUND_2Y", "BUND_5Y", "BUND_10Y", "BUND_30Y"]
    curve = []
    for key in maturities:
        data = fetch_data(key)
        if data.get("success"):
            curve.append({
                "maturity": key.replace("BUND_", ""),
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
            })
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(curve),
        "curve": curve,
        "count": len(curve),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get current ECB policy rates from Bundesbank data."""
    rate_keys = ["ECB_DEPOSIT_RATE", "ECB_REFI_RATE", "ECB_MARGINAL_RATE"]
    rates = {}
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Deutsche Bundesbank SDMX Module (Phase 1)

Usage:
  python bundesbank_sdmx.py                         # Latest values for all indicators
  python bundesbank_sdmx.py <INDICATOR>              # Fetch specific indicator
  python bundesbank_sdmx.py list                     # List available indicators
  python bundesbank_sdmx.py yield-curve              # German govt bond yield curve
  python bundesbank_sdmx.py policy-rates             # ECB policy rates

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON)
Coverage: Germany / Euro Area
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "yield-curve":
            print(json.dumps(get_yield_curve(), indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
