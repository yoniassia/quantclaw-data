#!/usr/bin/env python3
"""
Bank Negara Malaysia (BNM) Open API Module

Malaysia's central bank data: MYR exchange rates (20+ currencies), Overnight Policy
Rate (OPR), KLIBOR interbank rates, Islamic interbank rates, Kijang Emas gold prices,
and bank base/lending rates across the Malaysian banking system.

Data Source: https://api.bnm.gov.my
Protocol: REST (GET), JSON responses
Auth: None (fully open, no key required)
Refresh: Daily (FX, gold, interbank), Per-decision (OPR), Periodic (base rates)
Coverage: Malaysia / MYR

Author: QUANTCLAW DATA Build Agent
Initiative: 0061
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://api.bnm.gov.my/public"
ACCEPT_HEADER = "application/vnd.BNM.API.v1+json"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bnm_malaysia"
CACHE_TTL_FX = 1        # hours — FX rates, interbank, gold
CACHE_TTL_POLICY = 24   # hours — OPR, base rates, structural
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.2

INDICATORS = {
    "EXCHANGE_RATE": {
        "endpoint": "/exchange-rate",
        "name": "MYR Exchange Rates",
        "description": "Daily MYR exchange rates against 20+ currencies (buying/selling/middle)",
        "frequency": "daily",
        "unit": "MYR",
        "cache_hours": CACHE_TTL_FX,
    },
    "OPR": {
        "endpoint": "/opr",
        "name": "Overnight Policy Rate",
        "description": "BNM key policy rate — equivalent to Fed Funds Rate for Malaysia",
        "frequency": "per-decision",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_POLICY,
    },
    "INTERBANK_RATE": {
        "endpoint": "/interest-rate",
        "name": "Interbank Rates (KLIBOR)",
        "description": "KLIBOR term structure: overnight, 1w, 1m, 3m, 6m, 12m",
        "frequency": "daily",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_FX,
    },
    "ISLAMIC_INTERBANK_RATE": {
        "endpoint": "/islamic-interbank-rate",
        "name": "Islamic Interbank Money Market Rate",
        "description": "Islamic interbank rates — unique to Malaysian Shariah-compliant system",
        "frequency": "daily",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_FX,
    },
    "KIJANG_EMAS": {
        "endpoint": "/kijang-emas",
        "name": "Kijang Emas Gold Price",
        "description": "BNM gold coin prices in MYR (1oz, 1/2oz, 1/4oz buy/sell)",
        "frequency": "daily",
        "unit": "MYR",
        "cache_hours": CACHE_TTL_FX,
    },
    "BASE_RATE": {
        "endpoint": "/base-rate",
        "name": "Bank Base & Lending Rates",
        "description": "Base rate, base lending rate, and indicative effective lending rate per bank",
        "frequency": "periodic",
        "unit": "% p.a.",
        "cache_hours": CACHE_TTL_POLICY,
    },
    "CONSUMER_ALERT": {
        "endpoint": "/consumer-alert",
        "name": "Consumer Financial Fraud Alerts",
        "description": "BNM consumer alerts on unauthorized financial entities",
        "frequency": "periodic",
        "unit": "N/A",
        "cache_hours": CACHE_TTL_POLICY,
    },
}


# --- Cache helpers ---

def _cache_path(key: str, params_hash: str) -> Path:
    safe = key.replace("/", "_").replace(" ", "_")
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


# --- API request ---

def _api_get(endpoint: str, params: dict = None) -> Dict:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Accept": ACCEPT_HEADER}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") == 404 or (isinstance(body.get("data"), list) and len(body["data"]) == 0):
            return {"success": False, "error": "No records found"}
        return {"success": True, "data": body.get("data"), "meta": body.get("meta")}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Data parsers ---

def _parse_exchange_rates(data, currency_filter: str = None) -> List[Dict]:
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        code = item.get("currency_code", "")
        if currency_filter and code.upper() != currency_filter.upper():
            continue
        rate = item.get("rate", {})
        results.append({
            "currency_code": code,
            "unit": item.get("unit", 1),
            "date": rate.get("date"),
            "buying_rate": rate.get("buying_rate"),
            "selling_rate": rate.get("selling_rate"),
            "middle_rate": rate.get("middle_rate"),
            "pair": f"MYR/{code}",
        })
    results.sort(key=lambda x: x["currency_code"])
    return results


def _parse_opr(data) -> Dict:
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = [data]
    else:
        return {}
    parsed = []
    for item in entries:
        parsed.append({
            "date": item.get("date"),
            "year": item.get("year"),
            "opr_level": item.get("new_opr_level"),
            "change": item.get("change_in_opr"),
        })
    parsed.sort(key=lambda x: x.get("date", ""), reverse=True)
    return parsed


def _parse_interbank(data) -> List[Dict]:
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        results.append({
            "product": item.get("product"),
            "date": item.get("date"),
            "overnight": item.get("overnight"),
            "1_week": item.get("1_week"),
            "1_month": item.get("1_month"),
            "3_month": item.get("3_month"),
            "6_month": item.get("6_month"),
            "1_year": item.get("1_year"),
        })
    return results


def _parse_islamic_rate(data) -> Dict:
    if not isinstance(data, dict):
        return {}
    return {
        "date": data.get("date"),
        "overnight": data.get("overnight"),
        "1_week": data.get("1_week"),
        "1_month": data.get("1_month"),
        "3_month": data.get("3_month"),
        "6_month": data.get("6_month"),
        "1_year": data.get("1_year"),
    }


def _parse_kijang_emas(data) -> Dict:
    if not isinstance(data, dict):
        return {}
    return {
        "effective_date": data.get("effective_date"),
        "one_oz": data.get("one_oz"),
        "half_oz": data.get("half_oz"),
        "quarter_oz": data.get("quarter_oz"),
    }


def _parse_base_rates(data) -> List[Dict]:
    if not isinstance(data, list):
        return []
    results = []
    for item in data:
        results.append({
            "bank_name": item.get("bank_name"),
            "bank_code": item.get("bank_code", ""),
            "base_rate": item.get("base_rate"),
            "base_lending_rate": item.get("base_lending_rate"),
            "indicative_eff_lending_rate": item.get("indicative_eff_lending_rate"),
        })
    results.sort(key=lambda x: x.get("bank_name", ""))
    return results


# --- Public API ---

def fetch_exchange_rates(currency: str = None, date: str = None) -> Dict:
    """Fetch MYR exchange rates. Optionally filter by currency code (e.g. USD, SGD)."""
    indicator = "EXCHANGE_RATE"
    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator, "currency": currency, "date": date}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {}
    if date:
        params["date"] = date

    result = _api_get(cfg["endpoint"], params)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    rates = _parse_exchange_rates(result["data"], currency)
    if not rates:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": f"No rates found" + (f" for {currency}" if currency else "")}

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "currency_filter": currency,
        "date": rates[0].get("date") if rates else None,
        "rates": rates,
        "count": len(rates),
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    if not currency:
        _write_cache(cp, response)
    return response


def fetch_opr(year: int = None) -> Dict:
    """Fetch Overnight Policy Rate. Optionally by year for historical decisions."""
    indicator = "OPR"
    cfg = INDICATORS[indicator]
    endpoint = cfg["endpoint"]
    if year:
        endpoint = f"{endpoint}/year/{year}"

    cache_key = {"indicator": indicator, "year": year}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(endpoint)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    decisions = _parse_opr(result["data"])
    if not decisions:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No OPR data returned"}

    latest = decisions[0]
    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "current_rate": latest["opr_level"],
        "last_change": latest["change"],
        "last_decision_date": latest["date"],
        "decisions": decisions,
        "total_decisions": len(decisions),
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_interbank_rates() -> Dict:
    """Fetch KLIBOR interbank rate term structure."""
    indicator = "INTERBANK_RATE"
    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(cfg["endpoint"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    rates = _parse_interbank(result["data"])
    if not rates:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No interbank data returned"}

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "date": rates[0].get("date") if rates else None,
        "products": rates,
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_islamic_rate() -> Dict:
    """Fetch Islamic interbank money market rates."""
    indicator = "ISLAMIC_INTERBANK_RATE"
    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(cfg["endpoint"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    parsed = _parse_islamic_rate(result["data"])
    if not parsed:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No Islamic rate data returned"}

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "date": parsed.get("date"),
        "rates": parsed,
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_kijang_emas() -> Dict:
    """Fetch Kijang Emas gold prices in MYR."""
    indicator = "KIJANG_EMAS"
    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(cfg["endpoint"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    parsed = _parse_kijang_emas(result["data"])
    if not parsed:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No gold price data returned"}

    one_oz = parsed.get("one_oz", {})
    spread = None
    if one_oz and one_oz.get("buying") and one_oz.get("selling"):
        spread = round(one_oz["selling"] - one_oz["buying"], 2)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "effective_date": parsed.get("effective_date"),
        "one_oz_buying": one_oz.get("buying"),
        "one_oz_selling": one_oz.get("selling"),
        "one_oz_spread": spread,
        "prices": parsed,
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_base_rates() -> Dict:
    """Fetch base rate and lending rates for all Malaysian banks."""
    indicator = "BASE_RATE"
    cfg = INDICATORS[indicator]
    cache_key = {"indicator": indicator}
    cp = _cache_path(indicator, _params_hash(cache_key))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_get(cfg["endpoint"])
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    banks = _parse_base_rates(result["data"])
    if not banks:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No base rate data returned"}

    base_rates = [b["base_rate"] for b in banks if b.get("base_rate") is not None]
    avg_base = round(sum(base_rates) / len(base_rates), 4) if base_rates else None

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "average_base_rate": avg_base,
        "bank_count": len(banks),
        "banks": banks,
        "source": "Bank Negara Malaysia",
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return response


def fetch_data(indicator: str, **kwargs) -> Dict:
    """Unified fetch — routes to the appropriate endpoint handler."""
    indicator = indicator.upper()
    dispatch = {
        "EXCHANGE_RATE": lambda: fetch_exchange_rates(currency=kwargs.get("currency"), date=kwargs.get("date")),
        "OPR": lambda: fetch_opr(year=kwargs.get("year")),
        "INTERBANK_RATE": fetch_interbank_rates,
        "ISLAMIC_INTERBANK_RATE": fetch_islamic_rate,
        "KIJANG_EMAS": fetch_kijang_emas,
        "BASE_RATE": fetch_base_rates,
    }
    if indicator not in dispatch:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}
    return dispatch[indicator]()


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "endpoint": v["endpoint"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all key indicators (summary view)."""
    if indicator:
        return fetch_data(indicator)

    summary = {}
    errors = []

    fx = fetch_exchange_rates()
    if fx.get("success"):
        usd = next((r for r in fx["rates"] if r["currency_code"] == "USD"), None)
        sgd = next((r for r in fx["rates"] if r["currency_code"] == "SGD"), None)
        summary["MYR_USD"] = {"middle_rate": usd["middle_rate"], "date": usd["date"]} if usd else None
        summary["MYR_SGD"] = {"middle_rate": sgd["middle_rate"], "date": sgd["date"]} if sgd else None
        summary["FX_CURRENCIES"] = fx["count"]
    else:
        errors.append({"indicator": "EXCHANGE_RATE", "error": fx.get("error")})
    time.sleep(REQUEST_DELAY)

    opr = fetch_opr()
    if opr.get("success"):
        summary["OPR"] = {
            "rate": opr["current_rate"],
            "last_change": opr["last_change"],
            "date": opr["last_decision_date"],
            "unit": "% p.a.",
        }
    else:
        errors.append({"indicator": "OPR", "error": opr.get("error")})
    time.sleep(REQUEST_DELAY)

    interbank = fetch_interbank_rates()
    if interbank.get("success"):
        overall = next((p for p in interbank["products"] if p["product"] == "overall"), None)
        if overall:
            summary["KLIBOR_OVERNIGHT"] = overall.get("overnight")
            summary["KLIBOR_3M"] = overall.get("3_month")
    else:
        errors.append({"indicator": "INTERBANK_RATE", "error": interbank.get("error")})
    time.sleep(REQUEST_DELAY)

    islamic = fetch_islamic_rate()
    if islamic.get("success"):
        summary["ISLAMIC_OVERNIGHT"] = islamic["rates"].get("overnight")
    else:
        errors.append({"indicator": "ISLAMIC_INTERBANK_RATE", "error": islamic.get("error")})
    time.sleep(REQUEST_DELAY)

    gold = fetch_kijang_emas()
    if gold.get("success"):
        summary["KIJANG_EMAS_1OZ"] = {
            "buying": gold["one_oz_buying"],
            "selling": gold["one_oz_selling"],
            "spread": gold["one_oz_spread"],
            "unit": "MYR",
        }
    else:
        errors.append({"indicator": "KIJANG_EMAS", "error": gold.get("error")})

    return {
        "success": True,
        "source": "Bank Negara Malaysia",
        "summary": summary,
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Bank Negara Malaysia (BNM) Open API Module

Usage:
  python bnm_malaysia.py                          # Latest key indicators summary
  python bnm_malaysia.py exchange_rate             # All MYR exchange rates
  python bnm_malaysia.py exchange_rate USD         # MYR/USD rate
  python bnm_malaysia.py opr                       # Overnight Policy Rate (current)
  python bnm_malaysia.py opr 2025                  # OPR decisions for 2025
  python bnm_malaysia.py interbank                 # KLIBOR interbank rates
  python bnm_malaysia.py islamic_rate              # Islamic interbank rates
  python bnm_malaysia.py kijang_emas               # Gold prices in MYR
  python bnm_malaysia.py base_rate                 # Bank lending rates
  python bnm_malaysia.py list                      # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Auth: None (open access)
Coverage: Malaysia / MYR
""")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    cmd = args[0].lower()

    if cmd in ("--help", "-h", "help"):
        _print_help()
    elif cmd == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif cmd == "exchange_rate":
        currency = args[1].upper() if len(args) > 1 else None
        print(json.dumps(fetch_exchange_rates(currency=currency), indent=2, default=str))
    elif cmd == "opr":
        year = int(args[1]) if len(args) > 1 else None
        print(json.dumps(fetch_opr(year=year), indent=2, default=str))
    elif cmd == "interbank":
        print(json.dumps(fetch_interbank_rates(), indent=2, default=str))
    elif cmd == "islamic_rate":
        print(json.dumps(fetch_islamic_rate(), indent=2, default=str))
    elif cmd == "kijang_emas":
        print(json.dumps(fetch_kijang_emas(), indent=2, default=str))
    elif cmd == "base_rate":
        print(json.dumps(fetch_base_rates(), indent=2, default=str))
    else:
        result = fetch_data(cmd)
        print(json.dumps(result, indent=2, default=str))
