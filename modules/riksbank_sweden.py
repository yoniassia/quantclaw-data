#!/usr/bin/env python3
"""
Sveriges Riksbank Module — Phase 1

Sweden's central bank data: policy rates, FX rates (SEK crosses),
government bond yields, Treasury bill rates, mortgage bond rates,
and interbank deposit rates.

Data Source: https://api.riksbank.se/swea/v1
Protocol: REST (JSON)
Auth: Open (IP-based rate limits; portal registration for higher limits)
Refresh: Daily (FX, yields), as-needed (policy rates)
Coverage: Sweden

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

BASE_URL = "https://api.riksbank.se/swea/v1"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "riksbank_sweden"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.5  # Riksbank has strict rate limits for unauthenticated access

INDICATORS = {
    # --- Riksbank Policy Rates ---
    "POLICY_RATE": {
        "series_id": "SECBREPOEFF",
        "name": "Riksbank Policy Rate (%)",
        "description": "The Riksbank's main policy rate (formerly repo rate), 7-day term",
        "frequency": "daily",
        "unit": "%",
        "group": "policy_rates",
    },
    "DEPOSIT_RATE": {
        "series_id": "SECBDEPOEFF",
        "name": "Riksbank Deposit Rate (%)",
        "description": "Overnight deposit rate, floor of the interest rate corridor (policy rate - 0.75pp)",
        "frequency": "daily",
        "unit": "%",
        "group": "policy_rates",
    },
    "LENDING_RATE": {
        "series_id": "SECBLENDEFF",
        "name": "Riksbank Lending Rate (%)",
        "description": "Overnight lending rate, ceiling of the interest rate corridor (policy rate + 0.75pp)",
        "frequency": "daily",
        "unit": "%",
        "group": "policy_rates",
    },
    "REFERENCE_RATE": {
        "series_id": "SECBREFEFF",
        "name": "Riksbank Reference Rate (%)",
        "description": "Half-yearly reference rate derived from the policy rate, used for overdue payments etc.",
        "frequency": "daily",
        "unit": "%",
        "group": "policy_rates",
    },
    # --- FX Rates (SEK mid-rate vs major currencies) ---
    "SEK_EUR": {
        "series_id": "SEKEURPMI",
        "name": "SEK/EUR Exchange Rate",
        "description": "Swedish krona per euro, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per EUR",
        "group": "fx_rates",
    },
    "SEK_USD": {
        "series_id": "SEKUSDPMI",
        "name": "SEK/USD Exchange Rate",
        "description": "Swedish krona per US dollar, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per USD",
        "group": "fx_rates",
    },
    "SEK_GBP": {
        "series_id": "SEKGBPPMI",
        "name": "SEK/GBP Exchange Rate",
        "description": "Swedish krona per British pound, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per GBP",
        "group": "fx_rates",
    },
    "SEK_JPY": {
        "series_id": "SEKJPYPMI",
        "name": "SEK/JPY Exchange Rate",
        "description": "Swedish krona per Japanese yen, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per JPY",
        "group": "fx_rates",
    },
    "SEK_CHF": {
        "series_id": "SEKCHFPMI",
        "name": "SEK/CHF Exchange Rate",
        "description": "Swedish krona per Swiss franc, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per CHF",
        "group": "fx_rates",
    },
    "SEK_NOK": {
        "series_id": "SEKNOKPMI",
        "name": "SEK/NOK Exchange Rate",
        "description": "Swedish krona per Norwegian krone, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per NOK",
        "group": "fx_rates",
    },
    "SEK_DKK": {
        "series_id": "SEKDKKPMI",
        "name": "SEK/DKK Exchange Rate",
        "description": "Swedish krona per Danish krone, daily mid-rate",
        "frequency": "daily",
        "unit": "SEK per DKK",
        "group": "fx_rates",
    },
    "KIX_INDEX": {
        "series_id": "SEKKIX92",
        "name": "KIX Trade-Weighted SEK Index",
        "description": "Riksbank KIX index — trade-weighted nominal effective exchange rate for SEK (1992-11-18 = 100)",
        "frequency": "daily",
        "unit": "index",
        "group": "fx_rates",
    },
    # --- Swedish Government Bond Yields ---
    "GVB_2Y": {
        "series_id": "SEGVB2YC",
        "name": "Swedish Govt Bond Yield 2Y (%)",
        "description": "Swedish government bond benchmark yield, 2-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "govt_bonds",
    },
    "GVB_5Y": {
        "series_id": "SEGVB5YC",
        "name": "Swedish Govt Bond Yield 5Y (%)",
        "description": "Swedish government bond benchmark yield, 5-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "govt_bonds",
    },
    "GVB_7Y": {
        "series_id": "SEGVB7YC",
        "name": "Swedish Govt Bond Yield 7Y (%)",
        "description": "Swedish government bond benchmark yield, 7-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "govt_bonds",
    },
    "GVB_10Y": {
        "series_id": "SEGVB10YC",
        "name": "Swedish Govt Bond Yield 10Y (%)",
        "description": "Swedish government bond benchmark yield, 10-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "govt_bonds",
    },
    # --- Treasury Bills ---
    "TB_1M": {
        "series_id": "SETB1MBENCHC",
        "name": "Swedish T-Bill Rate 1M (%)",
        "description": "Swedish Treasury bill benchmark rate, 1-month maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "treasury_bills",
    },
    "TB_3M": {
        "series_id": "SETB3MBENCH",
        "name": "Swedish T-Bill Rate 3M (%)",
        "description": "Swedish Treasury bill benchmark rate, 3-month maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "treasury_bills",
    },
    "TB_6M": {
        "series_id": "SETB6MBENCH",
        "name": "Swedish T-Bill Rate 6M (%)",
        "description": "Swedish Treasury bill benchmark rate, 6-month maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "treasury_bills",
    },
    # --- Mortgage Bond Yields ---
    "MB_2Y": {
        "series_id": "SEMB2YCACOMB",
        "name": "Swedish Mortgage Bond Yield 2Y (%)",
        "description": "Swedish mortgage bond composite benchmark yield, 2-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "mortgage_bonds",
    },
    "MB_5Y": {
        "series_id": "SEMB5YCACOMB",
        "name": "Swedish Mortgage Bond Yield 5Y (%)",
        "description": "Swedish mortgage bond composite benchmark yield, 5-year maturity",
        "frequency": "daily",
        "unit": "%",
        "group": "mortgage_bonds",
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


def _api_request(series_id: str, from_date: str, to_date: str) -> Dict:
    """Fetch observations for a series between two dates (YYYY-MM-DD)."""
    url = f"{BASE_URL}/Observations/{series_id}/{from_date}/{to_date}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("statusCode") == 429:
            return {"success": False, "error": "Rate limited — retry later"}
        return {"success": True, "data": data}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 404:
            return {"success": False, "error": f"Series not found (HTTP 404)"}
        if status == 429:
            return {"success": False, "error": "Rate limited — retry later"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_observations(raw_data) -> List[Dict]:
    """Parse the Riksbank JSON response into date/value pairs.

    The API returns a flat JSON array: [{"date": "YYYY-MM-DD", "value": <float|null>}, ...]
    """
    if not isinstance(raw_data, list):
        return []
    results = []
    for obs in raw_data:
        if not isinstance(obs, dict):
            continue
        date_str = obs.get("date")
        value = obs.get("value")
        if date_str and value is not None:
            try:
                results.append({"date": date_str, "value": float(value)})
            except (ValueError, TypeError):
                continue
    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["series_id"], start_date, end_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_observations(result["data"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 6)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "group": cfg["group"],
        "latest_value": observations[0]["value"],
        "latest_date": observations[0]["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"date": o["date"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/Observations/{cfg['series_id']}",
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
            "series_id": v["series_id"],
            "group": v["group"],
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
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Sveriges Riksbank",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get current Riksbank policy rates (repo, deposit, lending)."""
    rate_keys = [k for k, v in INDICATORS.items() if v["group"] == "policy_rates"]
    rates = {}
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "date": data["latest_date"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_rates() -> Dict:
    """Get latest SEK exchange rates against major currencies."""
    fx_keys = [k for k, v in INDICATORS.items() if v["group"] == "fx_rates"]
    rates = {}
    for key in fx_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "date": data["latest_date"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "count": len(rates),
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Get Swedish government bond yield curve (2Y, 5Y, 7Y, 10Y)."""
    maturities = ["GVB_2Y", "GVB_5Y", "GVB_7Y", "GVB_10Y"]
    curve = []
    for key in maturities:
        data = fetch_data(key)
        if data.get("success"):
            curve.append({
                "maturity": key.replace("GVB_", ""),
                "yield_pct": data["latest_value"],
                "date": data["latest_date"],
            })
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(curve),
        "curve": curve,
        "count": len(curve),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print(f"""
Sveriges Riksbank Module (Phase 1)

Usage:
  python riksbank_sweden.py                   # Latest values for all indicators
  python riksbank_sweden.py <INDICATOR>        # Fetch specific indicator
  python riksbank_sweden.py list               # List available indicators
  python riksbank_sweden.py policy-rates       # Riksbank policy rates
  python riksbank_sweden.py fx-rates           # SEK exchange rates
  python riksbank_sweden.py yield-curve        # Swedish govt bond yield curve

Indicators:""")
    groups = {}
    for key, cfg in INDICATORS.items():
        groups.setdefault(cfg["group"], []).append((key, cfg))
    for group_name, items in groups.items():
        print(f"\n  [{group_name}]")
        for key, cfg in items:
            print(f"    {key:<20s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON)
Coverage: Sweden
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        elif cmd == "fx-rates":
            print(json.dumps(get_fx_rates(), indent=2, default=str))
        elif cmd == "yield-curve":
            print(json.dumps(get_yield_curve(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
