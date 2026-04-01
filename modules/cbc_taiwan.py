#!/usr/bin/env python3
"""
CBC Taiwan Module — Central Bank of the Republic of China (Taiwan)

FX rates (TWD/USD), monetary aggregates (M1A, M1B, M2), CBC policy rates
(discount rate, accommodation rates), deposit/lending rates from five major
banks, reserve money, and weighted-average interest rates.

Data Source: https://cpx.cbc.gov.tw/API/DataAPI/Get
Protocol: REST (JSON)
Auth: None (open access)
Refresh: Monthly (rates, monetary), Daily (FX spot)
Coverage: Taiwan

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

BASE_URL = "https://cpx.cbc.gov.tw/API/DataAPI/Get"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "cbc_taiwan"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

INDICATORS = {
    # --- TWD/USD Spot Exchange Rate (daily) ---
    "TWD_USD_CLOSE": {
        "file_code": "EG51D01en",
        "col_idx": 3,
        "name": "TWD/USD Closing Rate",
        "description": "Spot exchange rate of NTD against USD, closing rate",
        "frequency": "daily",
        "unit": "NTD per USD",
    },
    "TWD_USD_BUY": {
        "file_code": "EG51D01en",
        "col_idx": 1,
        "name": "TWD/USD Buying Rate",
        "description": "Spot exchange rate of NTD against USD, bank buying rate",
        "frequency": "daily",
        "unit": "NTD per USD",
    },
    "TWD_USD_SELL": {
        "file_code": "EG51D01en",
        "col_idx": 2,
        "name": "TWD/USD Selling Rate",
        "description": "Spot exchange rate of NTD against USD, bank selling rate",
        "frequency": "daily",
        "unit": "NTD per USD",
    },
    # --- CBC Policy Rates (monthly) ---
    "CBC_DISCOUNT_RATE": {
        "file_code": "EG2AM01en",
        "col_idx": 1,
        "name": "CBC Discount Rate (% p.a.)",
        "description": "Central bank discount rate",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "CBC_SECURED_RATE": {
        "file_code": "EG2AM01en",
        "col_idx": 2,
        "name": "CBC Secured Accommodation Rate (% p.a.)",
        "description": "Rate on accommodations with collateral",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "CBC_UNSECURED_RATE": {
        "file_code": "EG2AM01en",
        "col_idx": 3,
        "name": "CBC Unsecured Accommodation Rate (% p.a.)",
        "description": "Rate on accommodations without collateral",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    # --- Five Major Banks Rates (monthly) ---
    "DEPOSIT_RATE_1Y_FIXED": {
        "file_code": "EG2BM01en",
        "col_idx": 1,
        "name": "1-Year Fixed Deposit Rate (% p.a.)",
        "description": "Average 1-year fixed deposit rate at five major banks",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "SAVINGS_RATE_1Y": {
        "file_code": "EG2BM01en",
        "col_idx": 2,
        "name": "1-Year Savings Deposit Rate (% p.a.)",
        "description": "Average 1-year time savings deposit rate at five major banks",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    "BASE_LENDING_RATE": {
        "file_code": "EG2BM01en",
        "col_idx": 3,
        "name": "Base Lending Rate (% p.a.)",
        "description": "Average base lending rate at five major banks",
        "frequency": "monthly",
        "unit": "% p.a.",
    },
    # --- Monetary Aggregates, Averages of Daily Figures (monthly) ---
    "RESERVE_MONEY": {
        "file_code": "EF15M01en",
        "col_idx": 1,
        "change_col_idx": 2,
        "name": "Reserve Money — Daily Average (M NTD)",
        "description": "Reserve money, averages of daily figures",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    "M1A": {
        "file_code": "EF15M01en",
        "col_idx": 3,
        "change_col_idx": 4,
        "name": "M1A — Daily Average (M NTD)",
        "description": "M1A monetary aggregate (currency + demand deposits), daily average",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    "M1B": {
        "file_code": "EF15M01en",
        "col_idx": 27,
        "change_col_idx": 28,
        "name": "M1B — Daily Average (M NTD)",
        "description": "M1B monetary aggregate (M1A + passbook savings), daily average",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    "M2": {
        "file_code": "EF15M01en",
        "col_idx": 29,
        "change_col_idx": 30,
        "name": "M2 — Daily Average (M NTD)",
        "description": "M2 monetary aggregate, daily average",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    # --- Monetary Aggregates, End of Month (monthly) ---
    "RESERVE_MONEY_EOM": {
        "file_code": "EF17M01en",
        "col_idx": 1,
        "change_col_idx": 2,
        "name": "Reserve Money — End of Month (M NTD)",
        "description": "Reserve money, end-of-month outstanding",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    "M1B_EOM": {
        "file_code": "EF17M01en",
        "col_idx": 27,
        "change_col_idx": 28,
        "name": "M1B — End of Month (M NTD)",
        "description": "M1B monetary aggregate, end-of-month outstanding",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    "M2_EOM": {
        "file_code": "EF17M01en",
        "col_idx": 29,
        "change_col_idx": 30,
        "name": "M2 — End of Month (M NTD)",
        "description": "M2 monetary aggregate, end-of-month outstanding",
        "frequency": "monthly",
        "unit": "Millions NTD",
    },
    # --- Weighted Average Interest Rates (quarterly) ---
    "WEIGHTED_DEPOSIT_RATE": {
        "file_code": "EG39Q01en",
        "col_idx": 1,
        "name": "Weighted Avg Deposit Rate — All Banks (% p.a.)",
        "description": "Weighted average interest rate on deposits, all banks",
        "frequency": "quarterly",
        "unit": "% p.a.",
    },
    "WEIGHTED_LENDING_RATE": {
        "file_code": "EG39Q01en",
        "col_idx": 2,
        "name": "Weighted Avg Lending Rate — All Banks (% p.a.)",
        "description": "Weighted average interest rate on loans, all banks",
        "frequency": "quarterly",
        "unit": "% p.a.",
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


def _api_request(file_code: str) -> Dict:
    """Fetch a full dataset from the CBC Statistical Database."""
    params = {"FileName": file_code}
    try:
        resp = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, list) and len(payload) == 2:
            return {"success": False, "error": f"API returned info message: {payload}"}
        return {"success": True, "data": payload}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _safe_float(val: str) -> Optional[float]:
    if not val or val.strip() in ("-", "…", "...", "N/A", ""):
        return None
    try:
        return float(val.replace(",", ""))
    except (ValueError, TypeError):
        return None


def _extract_series(raw: Dict, col_idx: int, change_col_idx: Optional[int] = None,
                    tail_n: int = 60) -> List[Dict]:
    """Extract a time-series column from a CBC dataset response."""
    payload = raw.get("data", {})
    rows = payload.get("data", {}).get("dataSets", [])
    if not rows:
        return []

    results = []
    for row in rows:
        if not isinstance(row, list) or len(row) <= col_idx:
            continue
        period = row[0]
        value = _safe_float(row[col_idx])
        if value is None:
            continue
        entry = {"period": period, "value": value}
        if change_col_idx is not None and len(row) > change_col_idx:
            yoy = _safe_float(row[change_col_idx])
            if yoy is not None:
                entry["yoy_pct"] = yoy
        results.append(entry)

    results.sort(key=lambda x: x["period"], reverse=True)
    return results[:tail_n]


_dataset_cache: Dict[str, Dict] = {}


def _get_dataset(file_code: str) -> Dict:
    """Fetch dataset with in-memory dedup so shared file_codes aren't fetched twice."""
    if file_code in _dataset_cache:
        return _dataset_cache[file_code]
    result = _api_request(file_code)
    if result["success"]:
        _dataset_cache[file_code] = result
    return result


def fetch_data(indicator: str) -> Dict:
    """Fetch a specific indicator from the CBC Statistical Database."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _get_dataset(cfg["file_code"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": result["error"]}

    observations = _extract_series(
        result, cfg["col_idx"],
        change_col_idx=cfg.get("change_col_idx"),
    )
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations parsed from dataset"}

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
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"{BASE_URL}?FileName={cfg['file_code']}",
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
            "file_code": v["file_code"],
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
        "source": "Central Bank of the Republic of China (Taiwan)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get current CBC policy rates and major bank deposit/lending rates."""
    rate_keys = [
        "CBC_DISCOUNT_RATE", "CBC_SECURED_RATE", "CBC_UNSECURED_RATE",
        "DEPOSIT_RATE_1Y_FIXED", "SAVINGS_RATE_1Y", "BASE_LENDING_RATE",
    ]
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


def get_monetary_aggregates() -> Dict:
    """Get latest monetary aggregates (M1A, M1B, M2) with growth rates."""
    agg_keys = ["RESERVE_MONEY", "M1A", "M1B", "M2"]
    aggregates = {}
    for key in agg_keys:
        data = fetch_data(key)
        if data.get("success"):
            entry = {
                "name": data["name"],
                "value_millions_ntd": data["latest_value"],
                "period": data["latest_period"],
            }
            latest_dp = data["data_points"][0] if data["data_points"] else {}
            if "yoy_pct" in latest_dp:
                entry["yoy_growth_pct"] = latest_dp["yoy_pct"]
            aggregates[key] = entry
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(aggregates),
        "aggregates": aggregates,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
CBC Taiwan Module — Central Bank of the Republic of China (Taiwan)

Usage:
  python cbc_taiwan.py                          # Latest values for all indicators
  python cbc_taiwan.py <INDICATOR>              # Fetch specific indicator
  python cbc_taiwan.py list                     # List available indicators
  python cbc_taiwan.py policy-rates             # CBC policy & bank rates
  python cbc_taiwan.py monetary                 # Monetary aggregates (M1A/M1B/M2)

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON)
Coverage: Taiwan
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
        elif cmd == "monetary":
            print(json.dumps(get_monetary_aggregates(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
