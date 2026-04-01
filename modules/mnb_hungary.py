#!/usr/bin/env python3
"""
MNB Hungary (Magyar Nemzeti Bank) Module

Hungary's central bank data: policy base rate, official FX rates (HUF crosses),
and derived money-market/banking aggregates.

Data Source: http://www.mnb.hu (SOAP web services)
Protocol: SOAP 1.1 (XML over HTTP — HTTPS returns WAF errors)
Auth: None (open access)
Refresh: Daily (FX rates), Ad-hoc (base rate on policy decisions)
Coverage: Hungary

Endpoints:
  - arfolyamok.asmx  — exchange rates (GetCurrentExchangeRates, GetExchangeRates)
  - alapkamat.asmx    — base rate (GetCurrentCentralBankBaseRate, GetCentralBankBaseRate)

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
from typing import Dict, List, Optional
from pathlib import Path

FX_SOAP_URL = "http://www.mnb.hu/arfolyamok.asmx"
RATE_SOAP_URL = "http://www.mnb.hu/alapkamat.asmx"
SOAP_NS = "http://www.mnb.hu/webservices/"

CACHE_DIR = Path(__file__).parent.parent / "cache" / "mnb_hungary"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- MNB Policy Rate ---
    "MNB_BASE_RATE": {
        "source": "base_rate",
        "name": "MNB Central Bank Base Rate (%)",
        "description": "Magyar Nemzeti Bank policy base rate, set by the Monetary Council",
        "frequency": "ad-hoc",
        "unit": "%",
    },
    # --- Major FX Rates (HUF per unit) ---
    "FX_EUR_HUF": {
        "source": "fx",
        "currency": "EUR",
        "name": "EUR/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per euro",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_USD_HUF": {
        "source": "fx",
        "currency": "USD",
        "name": "USD/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per US dollar",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_GBP_HUF": {
        "source": "fx",
        "currency": "GBP",
        "name": "GBP/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per British pound",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_CHF_HUF": {
        "source": "fx",
        "currency": "CHF",
        "name": "CHF/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Swiss franc",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_JPY_HUF": {
        "source": "fx",
        "currency": "JPY",
        "name": "JPY/HUF Official MNB Rate (per 100 JPY)",
        "description": "Official MNB mid-rate, Hungarian forint per 100 Japanese yen",
        "frequency": "daily",
        "unit": "HUF per 100 JPY",
    },
    "FX_CZK_HUF": {
        "source": "fx",
        "currency": "CZK",
        "name": "CZK/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Czech koruna",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_PLN_HUF": {
        "source": "fx",
        "currency": "PLN",
        "name": "PLN/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Polish zloty",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_RON_HUF": {
        "source": "fx",
        "currency": "RON",
        "name": "RON/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Romanian leu",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_SEK_HUF": {
        "source": "fx",
        "currency": "SEK",
        "name": "SEK/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Swedish krona",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_CNY_HUF": {
        "source": "fx",
        "currency": "CNY",
        "name": "CNY/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Chinese yuan",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_TRY_HUF": {
        "source": "fx",
        "currency": "TRY",
        "name": "TRY/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Turkish lira",
        "frequency": "daily",
        "unit": "HUF",
    },
    "FX_CAD_HUF": {
        "source": "fx",
        "currency": "CAD",
        "name": "CAD/HUF Official MNB Rate",
        "description": "Official MNB mid-rate, Hungarian forint per Canadian dollar",
        "frequency": "daily",
        "unit": "HUF",
    },
    # --- Banking / Money-Market Aggregates (derived) ---
    "FX_CEE_BASKET": {
        "source": "aggregate",
        "currencies": ["CZK", "PLN", "RON"],
        "name": "CEE FX Basket vs HUF (equal-weighted index)",
        "description": "Equal-weighted basket of CZK, PLN, RON rates against HUF — tracks regional CEE currency moves",
        "frequency": "daily",
        "unit": "index",
    },
    "FX_G4_BASKET": {
        "source": "aggregate",
        "currencies": ["EUR", "USD", "GBP", "CHF"],
        "name": "G4 FX Basket vs HUF (equal-weighted index)",
        "description": "Equal-weighted basket of EUR, USD, GBP, CHF rates against HUF — tracks hard-currency exposure",
        "frequency": "daily",
        "unit": "index",
    },
}

ALL_FX_CURRENCIES = sorted({
    cfg["currency"]
    for cfg in INDICATORS.values()
    if cfg["source"] == "fx"
} | {
    c
    for cfg in INDICATORS.values()
    if cfg["source"] == "aggregate"
    for c in cfg.get("currencies", [])
})


# ---------------------------------------------------------------------------
# SOAP helpers
# ---------------------------------------------------------------------------

def _soap_envelope(namespace_action: str, body_xml: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        f'xmlns:web="{SOAP_NS}">'
        f"<soap:Body>{body_xml}</soap:Body>"
        "</soap:Envelope>"
    )


def _soap_request(url: str, action: str, body_xml: str) -> Dict:
    envelope = _soap_envelope(action, body_xml)
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": action,
    }
    try:
        resp = requests.post(url, data=envelope, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        if "text/html" in resp.headers.get("Content-Type", ""):
            return {"success": False, "error": "WAF blocked request (HTML response)"}
        return {"success": True, "raw": resp.text}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _extract_inner_xml(raw: str, result_tag: str) -> Optional[str]:
    """Pull the XML string embedded inside a SOAP *Result element (HTML-escaped)."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    ns = {"s": "http://schemas.xmlsoap.org/soap/envelope/", "w": SOAP_NS}
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local == result_tag and elem.text:
            return unescape(elem.text)
    return None


def _hungarian_float(val: str) -> Optional[float]:
    """Parse Hungarian-locale number (comma as decimal separator)."""
    try:
        return float(val.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def _fetch_current_fx() -> Dict:
    """GetCurrentExchangeRates → {currency: {value, unit, date}}."""
    action = f"{SOAP_NS}MNBArfolyamServiceSoap/GetCurrentExchangeRates"
    result = _soap_request(FX_SOAP_URL, action, "<web:GetCurrentExchangeRates/>")
    if not result["success"]:
        return result

    inner = _extract_inner_xml(result["raw"], "GetCurrentExchangeRatesResult")
    if not inner:
        return {"success": False, "error": "Could not parse SOAP response"}

    try:
        root = ET.fromstring(inner)
    except ET.ParseError:
        return {"success": False, "error": "Malformed inner XML"}

    rates = {}
    for day in root.iter("Day"):
        date_str = day.attrib.get("date", "")
        for rate_el in day.iter("Rate"):
            curr = rate_el.attrib.get("curr", "")
            unit = int(rate_el.attrib.get("unit", "1"))
            val = _hungarian_float(rate_el.text)
            if curr and val is not None:
                rates[curr] = {"value": val, "unit": unit, "date": date_str}

    return {"success": True, "rates": rates}


def _fetch_historical_fx(currencies: List[str], days: int = 90) -> Dict:
    """GetExchangeRates for a date range → list of day dicts."""
    end = datetime.now()
    start = end - timedelta(days=days)
    cur_str = ",".join(currencies)
    body = (
        "<web:GetExchangeRates>"
        f"<web:startDate>{start.strftime('%Y-%m-%d')}</web:startDate>"
        f"<web:endDate>{end.strftime('%Y-%m-%d')}</web:endDate>"
        f"<web:currencyNames>{cur_str}</web:currencyNames>"
        "</web:GetExchangeRates>"
    )
    action = f"{SOAP_NS}MNBArfolyamServiceSoap/GetExchangeRates"
    result = _soap_request(FX_SOAP_URL, action, body)
    if not result["success"]:
        return result

    inner = _extract_inner_xml(result["raw"], "GetExchangeRatesResult")
    if not inner:
        return {"success": False, "error": "Could not parse SOAP response"}

    try:
        root = ET.fromstring(inner)
    except ET.ParseError:
        return {"success": False, "error": "Malformed inner XML"}

    history = []
    for day in root.iter("Day"):
        date_str = day.attrib.get("date", "")
        day_rates = {}
        for rate_el in day.iter("Rate"):
            curr = rate_el.attrib.get("curr", "")
            unit = int(rate_el.attrib.get("unit", "1"))
            val = _hungarian_float(rate_el.text)
            if curr and val is not None:
                day_rates[curr] = {"value": val, "unit": unit}
        if day_rates:
            history.append({"date": date_str, "rates": day_rates})

    history.sort(key=lambda x: x["date"], reverse=True)
    return {"success": True, "history": history}


def _fetch_current_base_rate() -> Dict:
    action = f"{SOAP_NS}MNBAlapkamatServiceSoap/GetCurrentCentralBankBaseRate"
    result = _soap_request(RATE_SOAP_URL, action, "<web:GetCurrentCentralBankBaseRate/>")
    if not result["success"]:
        return result

    inner = _extract_inner_xml(result["raw"], "GetCurrentCentralBankBaseRateResult")
    if not inner:
        return {"success": False, "error": "Could not parse SOAP response"}

    try:
        root = ET.fromstring(inner)
    except ET.ParseError:
        return {"success": False, "error": "Malformed inner XML"}

    for br in root.iter("BaseRate"):
        val = _hungarian_float(br.text)
        date_str = br.attrib.get("publicationDate", "")
        if val is not None:
            return {"success": True, "value": val, "date": date_str}

    return {"success": False, "error": "No base rate in response"}


def _fetch_historical_base_rate(years: int = 5) -> Dict:
    end = datetime.now()
    start = end - timedelta(days=years * 365)
    body = (
        "<web:GetCentralBankBaseRate>"
        f"<web:startDate>{start.strftime('%Y-%m-%d')}</web:startDate>"
        f"<web:endDate>{end.strftime('%Y-%m-%d')}</web:endDate>"
        "</web:GetCentralBankBaseRate>"
    )
    action = f"{SOAP_NS}MNBAlapkamatServiceSoap/GetCentralBankBaseRate"
    result = _soap_request(RATE_SOAP_URL, action, body)
    if not result["success"]:
        return result

    inner = _extract_inner_xml(result["raw"], "GetCentralBankBaseRateResult")
    if not inner:
        return {"success": False, "error": "Could not parse SOAP response"}

    try:
        root = ET.fromstring(inner)
    except ET.ParseError:
        return {"success": False, "error": "Malformed inner XML"}

    history = []
    for br in root.iter("BaseRate"):
        val = _hungarian_float(br.text)
        date_str = br.attrib.get("publicationDate", "")
        if val is not None:
            history.append({"date": date_str, "value": val})

    history.sort(key=lambda x: x["date"], reverse=True)
    return {"success": True, "history": history}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
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

    response = _build_indicator_response(indicator, cfg)
    if response.get("success"):
        _write_cache(cp, response)
    return response


def _build_indicator_response(indicator: str, cfg: Dict) -> Dict:
    source = cfg["source"]

    if source == "base_rate":
        return _build_base_rate_response(indicator, cfg)
    elif source == "fx":
        return _build_fx_response(indicator, cfg)
    elif source == "aggregate":
        return _build_aggregate_response(indicator, cfg)

    return {"success": False, "error": f"Unknown source type: {source}"}


def _build_base_rate_response(indicator: str, cfg: Dict) -> Dict:
    current = _fetch_current_base_rate()
    if not current["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": current["error"]}

    hist = _fetch_historical_base_rate()
    history_points = hist.get("history", []) if hist["success"] else []

    period_change = period_change_pct = None
    if len(history_points) >= 2:
        curr_v = history_points[0]["value"]
        prev_v = history_points[1]["value"]
        period_change = round(curr_v - prev_v, 4)
        if prev_v != 0:
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": current["value"],
        "latest_period": current["date"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": h["date"], "value": h["value"]} for h in history_points[:30]],
        "total_observations": len(history_points),
        "source": f"{RATE_SOAP_URL} (SOAP)",
        "timestamp": datetime.now().isoformat(),
    }


def _build_fx_response(indicator: str, cfg: Dict) -> Dict:
    currency = cfg["currency"]
    hist_result = _fetch_historical_fx([currency], days=90)
    if not hist_result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": hist_result["error"]}

    observations = []
    for day in hist_result["history"]:
        r = day["rates"].get(currency)
        if r:
            observations.append({"period": day["date"], "value": r["value"], "unit": r["unit"]})

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

    latest = observations[0]
    period_change = period_change_pct = None
    if len(observations) >= 2:
        curr_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(curr_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest["value"],
        "latest_period": latest["period"],
        "quote_unit": latest["unit"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{FX_SOAP_URL} (SOAP)",
        "timestamp": datetime.now().isoformat(),
    }


def _build_aggregate_response(indicator: str, cfg: Dict) -> Dict:
    currencies = cfg["currencies"]
    hist_result = _fetch_historical_fx(currencies, days=90)
    if not hist_result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": hist_result["error"]}

    observations = []
    for day in hist_result["history"]:
        values = []
        for c in currencies:
            r = day["rates"].get(c)
            if r:
                values.append(r["value"])
        if len(values) == len(currencies):
            avg = round(sum(values) / len(values), 4)
            observations.append({"period": day["date"], "value": avg})

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Insufficient data for basket"}

    latest = observations[0]
    period_change = period_change_pct = None
    if len(observations) >= 2:
        curr_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(curr_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "basket_currencies": currencies,
        "latest_value": latest["value"],
        "latest_period": latest["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{FX_SOAP_URL} (SOAP, basket)",
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "source": v["source"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
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
        "source": "MNB Hungary (Magyar Nemzeti Bank)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_snapshot() -> Dict:
    """Current MNB official FX rates for all quoted currencies."""
    result = _fetch_current_fx()
    if not result["success"]:
        return result

    rates = result["rates"]
    return {
        "success": True,
        "date": next((v["date"] for v in rates.values()), None),
        "rates": {
            curr: {"value": info["value"], "unit": info["unit"]}
            for curr, info in sorted(rates.items())
        },
        "count": len(rates),
        "source": f"{FX_SOAP_URL} (SOAP)",
        "timestamp": datetime.now().isoformat(),
    }


def get_base_rate_history() -> Dict:
    """Full MNB base rate history (last 5 years)."""
    result = _fetch_historical_base_rate(years=5)
    if not result["success"]:
        return result

    history = result["history"]
    return {
        "success": True,
        "current_rate": history[0]["value"] if history else None,
        "current_since": history[0]["date"] if history else None,
        "history": history,
        "count": len(history),
        "source": f"{RATE_SOAP_URL} (SOAP)",
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
MNB Hungary (Magyar Nemzeti Bank) Module

Usage:
  python mnb_hungary.py                        # Latest values for all indicators
  python mnb_hungary.py <INDICATOR>            # Fetch specific indicator
  python mnb_hungary.py list                   # List available indicators
  python mnb_hungary.py fx-snapshot            # Current FX rates (all currencies)
  python mnb_hungary.py base-rate-history      # Base rate history (5 years)

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<20s} {cfg['name']}")
    print(f"""
Sources:
  FX rates:  {FX_SOAP_URL}
  Base rate: {RATE_SOAP_URL}
Protocol: SOAP 1.1 (HTTP only — HTTPS blocked by WAF)
Coverage: Hungary
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "fx-snapshot":
            print(json.dumps(get_fx_snapshot(), indent=2, default=str))
        elif cmd == "base-rate-history":
            print(json.dumps(get_base_rate_history(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
