#!/usr/bin/env python3
"""
Bank of England IADB Enhanced Module

Full coverage of the BoE Interactive Statistical Database (IADB):
yield curve (nominal zero coupon), money supply (M4, M4 lending),
Bank Rate history, mortgage rates, consumer credit, FX rates,
and effective exchange rate indices.

Data Source: https://www.bankofengland.co.uk/boeapps/iadb/
Protocol: XML via URL parameters (GESMES namespace)
Auth: None (open access)
Refresh: Daily (yields, FX, EER), Monthly (M4, mortgage, consumer credit)
Coverage: United Kingdom

Author: QUANTCLAW DATA Build Agent
Initiative: 0044-boe-enhanced
"""

import json
import sys
import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://www.bankofengland.co.uk/boeapps/iadb/FromShowColumns.asp"
XML_NS = "https://www.bankofengland.co.uk/website/agg_series"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "boe_iadb_enhanced"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- UK Gilt Yield Curve: Nominal Zero Coupon (daily) ---
    "GILT_NZC_5Y": {
        "series_code": "IUDSNZC",
        "name": "UK Gilt 5Y Nominal Zero Coupon Yield (%)",
        "description": "Yield from British Government Securities, 5-year Nominal Zero Coupon",
        "frequency": "daily",
        "unit": "%",
        "category": "yield_curve",
    },
    "GILT_NZC_10Y": {
        "series_code": "IUDMNZC",
        "name": "UK Gilt 10Y Nominal Zero Coupon Yield (%)",
        "description": "Yield from British Government Securities, 10-year Nominal Zero Coupon",
        "frequency": "daily",
        "unit": "%",
        "category": "yield_curve",
    },
    "GILT_NZC_20Y": {
        "series_code": "IUDLNZC",
        "name": "UK Gilt 20Y Nominal Zero Coupon Yield (%)",
        "description": "Yield from British Government Securities, 20-year Nominal Zero Coupon",
        "frequency": "daily",
        "unit": "%",
        "category": "yield_curve",
    },
    "GILT_NZC_5Y_MAVG": {
        "series_code": "IUMASNZC",
        "name": "UK Gilt 5Y NZC Yield — Monthly Average (%)",
        "description": "Monthly average yield from British Govt Securities, 5-year Nominal Zero Coupon",
        "frequency": "monthly",
        "unit": "%",
        "category": "yield_curve",
    },
    "GILT_NZC_10Y_MAVG": {
        "series_code": "IUMAMNZC",
        "name": "UK Gilt 10Y NZC Yield — Monthly Average (%)",
        "description": "Monthly average yield from British Govt Securities, 10-year Nominal Zero Coupon",
        "frequency": "monthly",
        "unit": "%",
        "category": "yield_curve",
    },
    "GILT_NZC_20Y_MAVG": {
        "series_code": "IUMALNZC",
        "name": "UK Gilt 20Y NZC Yield — Monthly Average (%)",
        "description": "Monthly average yield from British Govt Securities, 20-year Nominal Zero Coupon",
        "frequency": "monthly",
        "unit": "%",
        "category": "yield_curve",
    },

    # --- Bank Rate ---
    "BANK_RATE": {
        "series_code": "IUDBEDR",
        "name": "Official Bank Rate (%)",
        "description": "Bank of England Official Bank Rate (base rate)",
        "frequency": "daily",
        "unit": "%",
        "category": "policy_rate",
    },

    # --- Money Supply (M4 & M4 Lending) ---
    "M4_OUTSTANDING": {
        "series_code": "LPMAUYN",
        "name": "M4 Money Supply — Outstanding (GBP mn, SA)",
        "description": "M4 amounts outstanding, MFI sterling M4 liabilities to private sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
        "category": "money_supply",
    },
    "M4_LENDING_OUTSTANDING": {
        "series_code": "LPMBC69",
        "name": "M4 Lending — Outstanding (GBP mn, SA)",
        "description": "M4 lending amounts outstanding, MFI sterling net lending to private sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
        "category": "money_supply",
    },
    "M4_LENDING_12M_GROWTH": {
        "series_code": "LPMVWVP",
        "name": "M4 Lending — 12-Month Growth Rate (%, SA)",
        "description": "M4 lending 12-month growth rate, MFI sterling net lending to private sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "money_supply",
    },
    "M4_LENDING_1M_GROWTH": {
        "series_code": "LPMVWVM",
        "name": "M4 Lending — 1-Month Growth Rate (%, SA)",
        "description": "M4 lending 1-month growth rate, MFI sterling net lending to private sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "money_supply",
    },
    "M4_LENDING_3M_GROWTH": {
        "series_code": "LPMVWVN",
        "name": "M4 Lending — 3-Month Annualised Growth Rate (%, SA)",
        "description": "M4 lending 3-month annualised growth rate, MFI sterling net lending to private sector, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "money_supply",
    },

    # --- Mortgage Rates ---
    "MORTGAGE_SVR": {
        "series_code": "IUMTLMV",
        "name": "Standard Variable Rate Mortgage (%)",
        "description": "MFI sterling revert-to-rate (SVR) mortgage to households, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "mortgage",
    },

    # --- Consumer Credit ---
    "CONSUMER_CREDIT_EXCL_CARD": {
        "series_code": "LPMBC54",
        "name": "Consumer Credit excl. Cards — Outstanding (GBP mn, SA)",
        "description": "MFI sterling consumer credit (excl. credit card) excl. securitisations to individuals, seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
        "category": "consumer_credit",
    },
    "CONSUMER_CREDIT_TOTAL_EXCL_CARD": {
        "series_code": "LPMB4TT",
        "name": "Total Consumer Credit excl. Cards — Outstanding (GBP mn)",
        "description": "Total sterling consumer credit (excl. credit card) lending to individuals, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "GBP mn",
        "category": "consumer_credit",
    },
    "CONSUMER_CREDIT_EXCL_CARD_1M_GROWTH": {
        "series_code": "LPMB3UJ",
        "name": "Consumer Credit excl. Cards — 1-Month Growth Rate (%)",
        "description": "MFI sterling consumer credit (excl. credit card) excl. securitisations 1-month growth rate",
        "frequency": "monthly",
        "unit": "%",
        "category": "consumer_credit",
    },

    # --- FX Rates (GBP vs Major Currencies) ---
    "GBP_USD": {
        "series_code": "XUDLUSS",
        "name": "GBP/USD Spot Exchange Rate",
        "description": "Spot exchange rate, US Dollar into Sterling",
        "frequency": "daily",
        "unit": "USD per GBP",
        "category": "fx_rates",
    },
    "GBP_EUR": {
        "series_code": "XUDLERS",
        "name": "GBP/EUR Spot Exchange Rate",
        "description": "Spot exchange rate, Euro into Sterling",
        "frequency": "daily",
        "unit": "EUR per GBP",
        "category": "fx_rates",
    },
    "GBP_JPY": {
        "series_code": "XUDLJYS",
        "name": "GBP/JPY Spot Exchange Rate",
        "description": "Spot exchange rate, Japanese Yen into Sterling",
        "frequency": "daily",
        "unit": "JPY per GBP",
        "category": "fx_rates",
    },
    "GBP_CHF": {
        "series_code": "XUDLSFS",
        "name": "GBP/CHF Spot Exchange Rate",
        "description": "Spot exchange rate, Swiss Franc into Sterling",
        "frequency": "daily",
        "unit": "CHF per GBP",
        "category": "fx_rates",
    },

    # --- Effective Exchange Rates ---
    "STERLING_EER": {
        "series_code": "XUDLBK67",
        "name": "Sterling Effective Exchange Rate Index",
        "description": "Effective exchange rate index, Sterling (Jan 2005 = 100)",
        "frequency": "daily",
        "unit": "Index (Jan 2005=100)",
        "category": "eer",
    },
    "STERLING_BROAD_EER": {
        "series_code": "XUDLBK82",
        "name": "Sterling Broad Effective Exchange Rate Index",
        "description": "Broad effective exchange rate index, Sterling (Jan 2005 = 100)",
        "frequency": "daily",
        "unit": "Index (Jan 2005=100)",
        "category": "eer",
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


def _parse_xml(text: str, target_code: str) -> List[Dict]:
    """Parse BoE IADB XML (GESMES format) into time/value observations."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    observations = []
    current_code = ""
    series_desc = ""

    for elem in root.iter():
        tag = elem.tag.replace(f"{{{XML_NS}}}", "")
        attrib = elem.attrib

        if tag == "Cube" and "SCODE" in attrib:
            current_code = attrib["SCODE"]
            series_desc = attrib.get("DESC", "")
        elif tag == "Cube" and "TIME" in attrib and "OBS_VALUE" in attrib:
            if current_code == target_code:
                try:
                    observations.append({
                        "time_period": attrib["TIME"],
                        "value": float(attrib["OBS_VALUE"]),
                    })
                except (ValueError, TypeError):
                    pass

    observations.sort(key=lambda x: x["time_period"], reverse=True)
    return observations


def _api_request(series_code: str, from_date: str = None, to_date: str = "now") -> Dict:
    """Fetch a single BoE IADB series via the XML endpoint."""
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=730)).strftime("%d/%b/%Y")

    params = {
        "xml.x": "1",
        "xml.y": "1",
        "SeriesCodes": series_code,
        "UsingCodes": "Y",
        "Datefrom": from_date,
        "Dateto": to_date,
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; QuantClaw/1.0)"}

    try:
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "text": resp.text, "series_code": series_code}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
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

    from_date = start_date
    if from_date is None:
        lookback = 730 if cfg["frequency"] == "daily" else 1095
        from_date = (datetime.now() - timedelta(days=lookback)).strftime("%d/%b/%Y")

    to_date = end_date if end_date else "now"

    result = _api_request(cfg["series_code"], from_date, to_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_xml(result["text"], cfg["series_code"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations parsed"}

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
        "category": cfg["category"],
        "series_code": cfg["series_code"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}?SeriesCodes={cfg['series_code']}",
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
            "category": v["category"],
            "series_code": v["series_code"],
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
                "category": data["category"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Bank of England IADB Enhanced",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Get current UK gilt nominal zero coupon yield curve (daily)."""
    curve_keys = ["GILT_NZC_5Y", "GILT_NZC_10Y", "GILT_NZC_20Y"]
    curve = []
    for key in curve_keys:
        data = fetch_data(key)
        if data.get("success"):
            maturity = key.replace("GILT_NZC_", "")
            curve.append({
                "maturity": maturity,
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
            })
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(curve),
        "type": "Nominal Zero Coupon",
        "curve": curve,
        "count": len(curve),
        "timestamp": datetime.now().isoformat(),
    }


def get_money_supply() -> Dict:
    """Get M4 and M4 lending aggregates."""
    keys = ["M4_OUTSTANDING", "M4_LENDING_OUTSTANDING", "M4_LENDING_12M_GROWTH",
            "M4_LENDING_1M_GROWTH", "M4_LENDING_3M_GROWTH"]
    aggregates = {}
    for key in keys:
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
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_rates() -> Dict:
    """Get GBP spot exchange rates vs major currencies."""
    fx_keys = ["GBP_USD", "GBP_EUR", "GBP_JPY", "GBP_CHF"]
    rates = {}
    for key in fx_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print(f"""
Bank of England IADB Enhanced Module (Initiative 0044)

Usage:
  python boe_iadb_enhanced.py                     # Latest values for all indicators
  python boe_iadb_enhanced.py <INDICATOR>          # Fetch specific indicator
  python boe_iadb_enhanced.py list                 # List available indicators
  python boe_iadb_enhanced.py yield-curve          # UK gilt NZC yield curve
  python boe_iadb_enhanced.py money-supply         # M4 & M4 lending aggregates
  python boe_iadb_enhanced.py fx-rates             # GBP vs major currencies
  python boe_iadb_enhanced.py test                 # Quick validation test

Categories: yield_curve, policy_rate, money_supply, mortgage, consumer_credit, fx_rates, eer

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<38s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: XML (GESMES namespace)
Series: {len(INDICATORS)} indicators
Coverage: United Kingdom
""")


def _run_test():
    """Quick validation: fetch one indicator per category."""
    test_keys = [
        "GILT_NZC_10Y", "BANK_RATE", "M4_OUTSTANDING",
        "MORTGAGE_SVR", "CONSUMER_CREDIT_EXCL_CARD",
        "GBP_USD", "STERLING_EER",
    ]
    passed = 0
    failed = 0
    for key in test_keys:
        data = fetch_data(key)
        ok = data.get("success") and data.get("latest_value") is not None
        status = "PASS" if ok else "FAIL"
        val = data.get("latest_value", data.get("error", "?"))
        period = data.get("latest_period", "")
        print(f"  [{status}] {key:<38s} = {val} @ {period}")
        if ok:
            passed += 1
        else:
            failed += 1
        time.sleep(REQUEST_DELAY)

    print(f"\nResults: {passed}/{passed + failed} passed")
    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "yield-curve":
            print(json.dumps(get_yield_curve(), indent=2, default=str))
        elif cmd == "money-supply":
            print(json.dumps(get_money_supply(), indent=2, default=str))
        elif cmd == "fx-rates":
            print(json.dumps(get_fx_rates(), indent=2, default=str))
        elif cmd == "test":
            _run_test()
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
