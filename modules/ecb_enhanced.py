#!/usr/bin/env python3
"""
ECB Enhanced Module — Monetary Aggregates, Surveys & Banking Statistics

Broader ECB coverage beyond the base ecb.py: M1/M2/M3 monetary aggregates,
MFI credit to households and corporations, composite cost of borrowing
indicators, HICP inflation, MFI deposit and lending rates.

Data Source: https://data-api.ecb.europa.eu/service/
Protocol: SDMX 2.1 REST (SDMX-JSON)
Auth: None (public access)
Refresh: Monthly (monetary/credit/MIR/HICP)
Coverage: Euro Area (EA20)

Author: QUANTCLAW DATA Build Agent
Initiative: 0036
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://data-api.ecb.europa.eu/service"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "ecb_enhanced"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # === Monetary Aggregates (BSI dataflow) ===
    "M1_OUTSTANDING": {
        "dataflow": "BSI",
        "key": "M.U2.Y.V.M10.X.1.U2.2300.Z01.E",
        "name": "M1 Monetary Aggregate — Euro Area (EUR mn)",
        "description": "Currency in circulation + overnight deposits, seasonally adjusted outstanding amounts",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "monetary_aggregates",
    },
    "M2_OUTSTANDING": {
        "dataflow": "BSI",
        "key": "M.U2.Y.V.M20.X.1.U2.2300.Z01.E",
        "name": "M2 Monetary Aggregate — Euro Area (EUR mn)",
        "description": "M1 + deposits with maturity up to 2yr + redeemable at notice up to 3mo",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "monetary_aggregates",
    },
    "M3_OUTSTANDING": {
        "dataflow": "BSI",
        "key": "M.U2.Y.V.M30.X.1.U2.2300.Z01.E",
        "name": "M3 Monetary Aggregate — Euro Area (EUR mn)",
        "description": "M2 + repos + MMF shares/units + debt securities up to 2yr",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "monetary_aggregates",
    },
    # === MFI Credit / Loans (BSI dataflow) ===
    "LOANS_HH": {
        "dataflow": "BSI",
        "key": "M.U2.Y.U.A20.A.1.U2.2240.Z01.E",
        "name": "MFI Loans to Households — Euro Area (EUR mn)",
        "description": "Outstanding amounts of MFI loans to households and NPISH",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "credit",
    },
    "LOANS_NFC": {
        "dataflow": "BSI",
        "key": "M.U2.Y.U.A20.A.1.U2.2250.Z01.E",
        "name": "MFI Loans to Non-Financial Corporations — Euro Area (EUR mn)",
        "description": "Outstanding amounts of MFI loans to non-financial corporations",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "credit",
    },
    "LOANS_HH_HOUSING": {
        "dataflow": "BSI",
        "key": "M.U2.Y.U.A20.J.1.U2.2240.Z01.E",
        "name": "MFI Housing Loans to Households — Euro Area (EUR mn)",
        "description": "Outstanding amounts of MFI housing loans to households",
        "frequency": "monthly",
        "unit": "EUR mn",
        "category": "credit",
    },
    # === Composite Cost of Borrowing (MIR dataflow) ===
    "CCOB_NFC": {
        "dataflow": "MIR",
        "key": "M.U2.B.A2I.AM.R.A.2240.EUR.N",
        "name": "Composite Cost of Borrowing — NFCs (% p.a.)",
        "description": "Composite indicator of the cost of borrowing for new loans to non-financial corporations",
        "frequency": "monthly",
        "unit": "% p.a.",
        "category": "cost_of_borrowing",
    },
    "CCOB_HH_HOUSING": {
        "dataflow": "MIR",
        "key": "M.U2.B.A2C.P.R.A.2250.EUR.N",
        "name": "Composite Cost of Borrowing — Household Housing (% p.a.)",
        "description": "Composite indicator of the cost of borrowing for new housing loans to households",
        "frequency": "monthly",
        "unit": "% p.a.",
        "category": "cost_of_borrowing",
    },
    # === MFI Interest Rates (MIR dataflow) ===
    "NFC_LOAN_RATE_SHORT": {
        "dataflow": "MIR",
        "key": "M.U2.B.A2A.D.R.1.2240.EUR.N",
        "name": "NFC New Loan Rate — Up to 1yr (% p.a.)",
        "description": "Interest rate on new business loans to NFCs, maturity up to 1 year",
        "frequency": "monthly",
        "unit": "% p.a.",
        "category": "interest_rates",
    },
    "NFC_LOAN_RATE_LONG": {
        "dataflow": "MIR",
        "key": "M.U2.B.A2A.O.R.1.2240.EUR.N",
        "name": "NFC New Loan Rate — Over 5yr (% p.a.)",
        "description": "Interest rate on new business loans to NFCs, maturity over 5 years",
        "frequency": "monthly",
        "unit": "% p.a.",
        "category": "interest_rates",
    },
    "HH_DEPOSIT_RATE": {
        "dataflow": "MIR",
        "key": "M.U2.B.L22.A.R.A.2250.EUR.N",
        "name": "Household Deposit Rate — New Business (% p.a.)",
        "description": "Interest rate on new deposits from households with agreed maturity",
        "frequency": "monthly",
        "unit": "% p.a.",
        "category": "interest_rates",
    },
    # === HICP Inflation (ICP dataflow) ===
    "HICP_HEADLINE": {
        "dataflow": "ICP",
        "key": "M.U2.N.000000.4.ANR",
        "name": "HICP — All Items Annual Rate (%)",
        "description": "Harmonised Index of Consumer Prices, all items, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "inflation",
    },
    "HICP_CORE": {
        "dataflow": "ICP",
        "key": "M.U2.N.XEF000.4.ANR",
        "name": "HICP Core — Excl. Energy & Food Annual Rate (%)",
        "description": "HICP excluding energy and food (unprocessed), annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "inflation",
    },
    "HICP_FOOD": {
        "dataflow": "ICP",
        "key": "M.U2.N.010000.4.ANR",
        "name": "HICP Food & Non-Alcoholic Beverages — Annual Rate (%)",
        "description": "HICP food and non-alcoholic beverages component, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "inflation",
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
    """Extract time-period/value pairs from ECB SDMX-JSON 1.0 response."""
    try:
        datasets = raw.get("dataSets", [])
        structure = raw.get("structure", {})
        if not datasets:
            return []

        obs_dims = structure.get("dimensions", {}).get("observation", [])
        if not obs_dims:
            return []
        time_values = obs_dims[0].get("values", [])

        results = []
        for _series_key, series_data in datasets[0].get("series", {}).items():
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


def _api_request(dataflow: str, key: str, last_n: int = 60) -> Dict:
    url = f"{BASE_URL}/data/{dataflow}/{key}"
    params = {"lastNObservations": last_n}
    headers = {
        "Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd",
        "User-Agent": "QuantClaw-Data/1.0",
    }
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


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
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

    last_n = 60

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
        "category": cfg.get("category", ""),
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
            "category": v.get("category", ""),
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
        "source": "ECB Enhanced (SDMX)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_monetary_aggregates() -> Dict:
    """Get M1/M2/M3 monetary aggregates."""
    agg_keys = ["M1_OUTSTANDING", "M2_OUTSTANDING", "M3_OUTSTANDING"]
    aggregates = {}
    for key in agg_keys:
        data = fetch_data(key)
        if data.get("success"):
            aggregates[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(aggregates),
        "aggregates": aggregates,
        "count": len(aggregates),
        "timestamp": datetime.now().isoformat(),
    }


def get_cost_of_borrowing() -> Dict:
    """Get composite cost of borrowing indicators."""
    cob_keys = ["CCOB_NFC", "CCOB_HH_HOUSING"]
    rates = {}
    for key in cob_keys:
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
ECB Enhanced Module (Initiative 0036)
Monetary Aggregates, Cost of Borrowing, Credit, Inflation

Usage:
  python ecb_enhanced.py                      # Latest values for all indicators
  python ecb_enhanced.py <INDICATOR>           # Fetch specific indicator
  python ecb_enhanced.py list                  # List available indicators
  python ecb_enhanced.py monetary              # M1/M2/M3 aggregates
  python ecb_enhanced.py borrowing             # Composite cost of borrowing

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: SDMX 2.1 REST (JSON)
Coverage: Euro Area (EA20)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "monetary":
            print(json.dumps(get_monetary_aggregates(), indent=2, default=str))
        elif cmd == "borrowing":
            print(json.dumps(get_cost_of_borrowing(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
