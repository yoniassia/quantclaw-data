#!/usr/bin/env python3
"""
NBP Poland Module — National Bank of Poland

Exchange rates (Table A: mid rates, Table B: minor currencies, Table C: buy/sell),
gold prices (PLN per gram), and key currency pairs against the Polish zloty.

Data Source: https://api.nbp.pl/api
Protocol: REST (JSON)
Auth: None (open access)
Refresh: Daily (business days)
Coverage: Poland / PLN

Author: QUANTCLAW DATA Build Agent
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.nbp.pl/api"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "nbp_poland"
CACHE_TTL_FX = 1       # hours — exchange rates
CACHE_TTL_GOLD = 24    # hours — gold prices
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.2

INDICATORS = {
    # --- Table A: Major currency mid rates (PLN) ---
    "FX_USD_PLN": {
        "table": "A", "code": "USD",
        "name": "USD/PLN Mid Rate",
        "description": "US Dollar to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_EUR_PLN": {
        "table": "A", "code": "EUR",
        "name": "EUR/PLN Mid Rate",
        "description": "Euro to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_GBP_PLN": {
        "table": "A", "code": "GBP",
        "name": "GBP/PLN Mid Rate",
        "description": "British Pound to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CHF_PLN": {
        "table": "A", "code": "CHF",
        "name": "CHF/PLN Mid Rate",
        "description": "Swiss Franc to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_JPY_PLN": {
        "table": "A", "code": "JPY",
        "name": "JPY/PLN Mid Rate (per 100 JPY)",
        "description": "Japanese Yen to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CAD_PLN": {
        "table": "A", "code": "CAD",
        "name": "CAD/PLN Mid Rate",
        "description": "Canadian Dollar to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_AUD_PLN": {
        "table": "A", "code": "AUD",
        "name": "AUD/PLN Mid Rate",
        "description": "Australian Dollar to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CNY_PLN": {
        "table": "A", "code": "CNY",
        "name": "CNY/PLN Mid Rate",
        "description": "Chinese Yuan to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_SEK_PLN": {
        "table": "A", "code": "SEK",
        "name": "SEK/PLN Mid Rate",
        "description": "Swedish Krona to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_NOK_PLN": {
        "table": "A", "code": "NOK",
        "name": "NOK/PLN Mid Rate",
        "description": "Norwegian Krone to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CZK_PLN": {
        "table": "A", "code": "CZK",
        "name": "CZK/PLN Mid Rate",
        "description": "Czech Koruna to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_HUF_PLN": {
        "table": "A", "code": "HUF",
        "name": "HUF/PLN Mid Rate (per 100 HUF)",
        "description": "Hungarian Forint to Polish Zloty, NBP Table A mid rate",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    # --- Table B: Minor / exotic currency mid rates (published weekly, Wed) ---
    "FX_TWD_PLN": {
        "table": "B", "code": "TWD",
        "name": "TWD/PLN Mid Rate",
        "description": "Taiwan New Dollar to Polish Zloty, NBP Table B mid rate",
        "frequency": "weekly", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_AED_PLN": {
        "table": "B", "code": "AED",
        "name": "AED/PLN Mid Rate",
        "description": "UAE Dirham to Polish Zloty, NBP Table B mid rate",
        "frequency": "weekly", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_SAR_PLN": {
        "table": "B", "code": "SAR",
        "name": "SAR/PLN Mid Rate",
        "description": "Saudi Riyal to Polish Zloty, NBP Table B mid rate",
        "frequency": "weekly", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_KWD_PLN": {
        "table": "B", "code": "KWD",
        "name": "KWD/PLN Mid Rate",
        "description": "Kuwaiti Dinar to Polish Zloty, NBP Table B mid rate",
        "frequency": "weekly", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    # --- Table C: Buy/Sell spread (dealer rates) ---
    "FX_USD_PLN_BID_ASK": {
        "table": "C", "code": "USD",
        "name": "USD/PLN Bid/Ask Spread",
        "description": "US Dollar to PLN, NBP Table C buy/sell rates",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_EUR_PLN_BID_ASK": {
        "table": "C", "code": "EUR",
        "name": "EUR/PLN Bid/Ask Spread",
        "description": "Euro to PLN, NBP Table C buy/sell rates",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_GBP_PLN_BID_ASK": {
        "table": "C", "code": "GBP",
        "name": "GBP/PLN Bid/Ask Spread",
        "description": "British Pound to PLN, NBP Table C buy/sell rates",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    "FX_CHF_PLN_BID_ASK": {
        "table": "C", "code": "CHF",
        "name": "CHF/PLN Bid/Ask Spread",
        "description": "Swiss Franc to PLN, NBP Table C buy/sell rates",
        "frequency": "daily", "unit": "PLN", "cache_ttl": CACHE_TTL_FX,
    },
    # --- Gold ---
    "GOLD_PLN": {
        "table": "GOLD", "code": None,
        "name": "Gold Price (PLN/gram)",
        "description": "NBP gold price, PLN per gram of 1000 fineness",
        "frequency": "daily", "unit": "PLN/g", "cache_ttl": CACHE_TTL_GOLD,
    },
}


def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_")
    return CACHE_DIR / f"{safe}_{params_hash}.json"


def _params_hash(params: dict) -> str:
    raw = json.dumps(params, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:10]


def _read_cache(path: Path, ttl_hours: int) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
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
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _api_get(url: str) -> Dict:
    """Make a GET request to NBP API, return parsed JSON or error dict."""
    try:
        resp = requests.get(url, params={"format": "json"}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 404:
            return {"success": False, "error": "No data available (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_fx_rate(table: str, code: str, last_n: int = 30) -> Dict:
    url = f"{BASE_URL}/exchangerates/rates/{table}/{code}/last/{last_n}/"
    return _api_get(url)


def _fetch_fx_range(table: str, code: str, start: str, end: str) -> Dict:
    url = f"{BASE_URL}/exchangerates/rates/{table}/{code}/{start}/{end}/"
    return _api_get(url)


def _fetch_gold(last_n: int = 30) -> Dict:
    url = f"{BASE_URL}/cenyzlota/last/{last_n}/"
    return _api_get(url)


def _fetch_gold_range(start: str, end: str) -> Dict:
    url = f"{BASE_URL}/cenyzlota/{start}/{end}/"
    return _api_get(url)


def _fetch_table(table: str) -> Dict:
    url = f"{BASE_URL}/exchangerates/tables/{table}/"
    return _api_get(url)


def _parse_fx_response(raw_data: Dict, table: str) -> List[Dict]:
    """Parse NBP FX rates response into a list of observations."""
    rates = raw_data.get("rates", [])
    results = []
    for r in rates:
        entry = {"date": r["effectiveDate"]}
        if table == "C":
            entry["bid"] = r.get("bid")
            entry["ask"] = r.get("ask")
            if entry["bid"] and entry["ask"]:
                entry["mid"] = round((entry["bid"] + entry["ask"]) / 2, 6)
                entry["spread"] = round(entry["ask"] - entry["bid"], 6)
        else:
            entry["mid"] = r.get("mid")
        results.append(entry)
    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def _parse_gold_response(raw_data: list) -> List[Dict]:
    """Parse NBP gold price response."""
    results = []
    for r in raw_data:
        results.append({"date": r["data"], "price": r["cena"]})
    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def _split_date_range(start_date: str, end_date: str, max_days: int = 93):
    """Split a date range into chunks of max_days (NBP API limit is 93 days)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    chunks = []
    while start <= end:
        chunk_end = min(start + timedelta(days=max_days - 1), end)
        chunks.append((start.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        start = chunk_end + timedelta(days=1)
    return chunks


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, cfg["cache_ttl"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    is_gold = cfg["table"] == "GOLD"

    if start_date and end_date:
        chunks = _split_date_range(start_date, end_date)
        all_obs = []
        for cs, ce in chunks:
            if is_gold:
                result = _fetch_gold_range(cs, ce)
            else:
                result = _fetch_fx_range(cfg["table"], cfg["code"], cs, ce)
            if not result["success"]:
                return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}
            if is_gold:
                all_obs.extend(_parse_gold_response(result["data"]))
            else:
                all_obs.extend(_parse_fx_response(result["data"], cfg["table"]))
            time.sleep(REQUEST_DELAY)
        observations = sorted(all_obs, key=lambda x: x["date"], reverse=True)
    else:
        if is_gold:
            result = _fetch_gold(last_n=60)
        else:
            result = _fetch_fx_rate(cfg["table"], cfg["code"], last_n=60)
        if not result["success"]:
            return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}
        if is_gold:
            observations = _parse_gold_response(result["data"])
        else:
            observations = _parse_fx_response(result["data"], cfg["table"])

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

    value_key = "price" if is_gold else ("mid" if "mid" in observations[0] else "bid")
    latest_val = observations[0].get(value_key)

    period_change = period_change_pct = None
    if len(observations) >= 2:
        prev_val = observations[1].get(value_key)
        if latest_val is not None and prev_val and prev_val != 0:
            period_change = round(latest_val - prev_val, 6)
            period_change_pct = round((period_change / abs(prev_val)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest_val,
        "latest_date": observations[0]["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": BASE_URL,
        "timestamp": datetime.now().isoformat(),
    }

    if cfg["table"] == "C" and not is_gold:
        response["latest_bid"] = observations[0].get("bid")
        response["latest_ask"] = observations[0].get("ask")
        response["latest_spread"] = observations[0].get("spread")

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with metadata."""
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
            entry = {
                "name": data["name"],
                "value": data["latest_value"],
                "date": data["latest_date"],
                "unit": data["unit"],
            }
            if "latest_bid" in data:
                entry["bid"] = data["latest_bid"]
                entry["ask"] = data["latest_ask"]
                entry["spread"] = data["latest_spread"]
            results[key] = entry
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "NBP Poland — National Bank of Poland",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_full_table(table: str) -> Dict:
    """Fetch a full exchange rate table (A, B, or C)."""
    table = table.upper()
    if table not in ("A", "B", "C"):
        return {"success": False, "error": f"Invalid table type: {table}. Use A, B, or C."}

    cp = _cache_path(f"TABLE_{table}", _params_hash({"table": table}))
    cached = _read_cache(cp, CACHE_TTL_FX)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _fetch_table(table)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    tbl = result["data"][0]
    rates = []
    for r in tbl["rates"]:
        entry = {"currency": r["currency"], "code": r["code"]}
        if table == "C":
            entry["bid"] = r.get("bid")
            entry["ask"] = r.get("ask")
            if entry["bid"] and entry["ask"]:
                entry["spread"] = round(entry["ask"] - entry["bid"], 6)
        else:
            entry["mid"] = r.get("mid")
        rates.append(entry)

    response = {
        "success": True,
        "table": table,
        "table_no": tbl.get("no"),
        "effective_date": tbl.get("effectiveDate"),
        "trading_date": tbl.get("tradingDate"),
        "currency_count": len(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


# --- CLI ---

def _print_help():
    print("""
NBP Poland Module — National Bank of Poland

Usage:
  python nbp_poland.py                            # Latest values for all indicators
  python nbp_poland.py <INDICATOR>                 # Fetch specific indicator
  python nbp_poland.py list                        # List available indicators
  python nbp_poland.py table <A|B|C>               # Full exchange rate table
  python nbp_poland.py <INDICATOR> <START> <END>   # Date range query (YYYY-MM-DD)

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Tables:
  A  — Mid rates for 32 major currencies (daily)
  B  — Mid rates for 116 minor/exotic currencies (weekly, Wed)
  C  — Bid/Ask dealer rates for 13 currencies (daily)

Source: {BASE_URL}
Protocol: REST (JSON)
Coverage: Poland / PLN
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
    elif args[0] in ("--help", "-h", "help"):
        _print_help()
    elif args[0] == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif args[0] == "table" and len(args) >= 2:
        print(json.dumps(get_full_table(args[1]), indent=2, default=str))
    elif len(args) == 3:
        result = fetch_data(args[0], start_date=args[1], end_date=args[2])
        print(json.dumps(result, indent=2, default=str))
    else:
        result = fetch_data(args[0])
        print(json.dumps(result, indent=2, default=str))
