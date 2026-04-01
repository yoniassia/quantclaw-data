#!/usr/bin/env python3
"""
BNR Romania FX Rates Module — National Bank of Romania

Daily and 10-day reference exchange rates for RON against 37 currencies,
plus gold (XAU) and IMF SDR (XDR).

Data Source: https://www.bnr.ro/nbrfxrates.xml (daily), nbrfxrates10days.xml
Protocol: XML feeds (open access, stable)
Auth: None
Refresh: Daily (published ~13:00 EET on business days)
Coverage: Romania — RON base currency

Author: QUANTCLAW DATA Build Agent
Initiative: 0031
"""

import json
import sys
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

DAILY_URL = "https://www.bnr.ro/nbrfxrates.xml"
TENDAY_URL = "https://www.bnr.ro/nbrfxrates10days.xml"
XML_NS = {"bnr": "http://www.bnr.ro/xsd"}
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bnr_romania"
CACHE_TTL_HOURS = 1
REQUEST_TIMEOUT = 20

# All currencies published by BNR, keyed as RON_<CCY>
# Multiplier-adjusted currencies note the multiplier in the description.
INDICATORS = {
    "RON_AED": {"currency": "AED", "name": "RON/AED (UAE Dirham)", "description": "BNR reference rate, 1 AED in RON", "unit": "RON"},
    "RON_AUD": {"currency": "AUD", "name": "RON/AUD (Australian Dollar)", "description": "BNR reference rate, 1 AUD in RON", "unit": "RON"},
    "RON_BRL": {"currency": "BRL", "name": "RON/BRL (Brazilian Real)", "description": "BNR reference rate, 1 BRL in RON", "unit": "RON"},
    "RON_CAD": {"currency": "CAD", "name": "RON/CAD (Canadian Dollar)", "description": "BNR reference rate, 1 CAD in RON", "unit": "RON"},
    "RON_CHF": {"currency": "CHF", "name": "RON/CHF (Swiss Franc)", "description": "BNR reference rate, 1 CHF in RON", "unit": "RON"},
    "RON_CNY": {"currency": "CNY", "name": "RON/CNY (Chinese Yuan)", "description": "BNR reference rate, 1 CNY in RON", "unit": "RON"},
    "RON_CZK": {"currency": "CZK", "name": "RON/CZK (Czech Koruna)", "description": "BNR reference rate, 1 CZK in RON", "unit": "RON"},
    "RON_DKK": {"currency": "DKK", "name": "RON/DKK (Danish Krone)", "description": "BNR reference rate, 1 DKK in RON", "unit": "RON"},
    "RON_EGP": {"currency": "EGP", "name": "RON/EGP (Egyptian Pound)", "description": "BNR reference rate, 1 EGP in RON", "unit": "RON"},
    "RON_EUR": {"currency": "EUR", "name": "RON/EUR (Euro)", "description": "BNR reference rate, 1 EUR in RON", "unit": "RON"},
    "RON_GBP": {"currency": "GBP", "name": "RON/GBP (British Pound)", "description": "BNR reference rate, 1 GBP in RON", "unit": "RON"},
    "RON_HKD": {"currency": "HKD", "name": "RON/HKD (Hong Kong Dollar)", "description": "BNR reference rate, 1 HKD in RON", "unit": "RON"},
    "RON_HUF": {"currency": "HUF", "name": "RON/HUF (Hungarian Forint)", "description": "BNR reference rate, 1 HUF in RON (published per 100 HUF, normalized to 1)", "unit": "RON"},
    "RON_IDR": {"currency": "IDR", "name": "RON/IDR (Indonesian Rupiah)", "description": "BNR reference rate, 1 IDR in RON (published per 100 IDR, normalized to 1)", "unit": "RON"},
    "RON_ILS": {"currency": "ILS", "name": "RON/ILS (Israeli Shekel)", "description": "BNR reference rate, 1 ILS in RON", "unit": "RON"},
    "RON_INR": {"currency": "INR", "name": "RON/INR (Indian Rupee)", "description": "BNR reference rate, 1 INR in RON", "unit": "RON"},
    "RON_ISK": {"currency": "ISK", "name": "RON/ISK (Icelandic Króna)", "description": "BNR reference rate, 1 ISK in RON (published per 100 ISK, normalized to 1)", "unit": "RON"},
    "RON_JPY": {"currency": "JPY", "name": "RON/JPY (Japanese Yen)", "description": "BNR reference rate, 1 JPY in RON (published per 100 JPY, normalized to 1)", "unit": "RON"},
    "RON_KRW": {"currency": "KRW", "name": "RON/KRW (South Korean Won)", "description": "BNR reference rate, 1 KRW in RON (published per 100 KRW, normalized to 1)", "unit": "RON"},
    "RON_MDL": {"currency": "MDL", "name": "RON/MDL (Moldovan Leu)", "description": "BNR reference rate, 1 MDL in RON", "unit": "RON"},
    "RON_MXN": {"currency": "MXN", "name": "RON/MXN (Mexican Peso)", "description": "BNR reference rate, 1 MXN in RON", "unit": "RON"},
    "RON_MYR": {"currency": "MYR", "name": "RON/MYR (Malaysian Ringgit)", "description": "BNR reference rate, 1 MYR in RON", "unit": "RON"},
    "RON_NOK": {"currency": "NOK", "name": "RON/NOK (Norwegian Krone)", "description": "BNR reference rate, 1 NOK in RON", "unit": "RON"},
    "RON_NZD": {"currency": "NZD", "name": "RON/NZD (New Zealand Dollar)", "description": "BNR reference rate, 1 NZD in RON", "unit": "RON"},
    "RON_PHP": {"currency": "PHP", "name": "RON/PHP (Philippine Peso)", "description": "BNR reference rate, 1 PHP in RON", "unit": "RON"},
    "RON_PLN": {"currency": "PLN", "name": "RON/PLN (Polish Zloty)", "description": "BNR reference rate, 1 PLN in RON", "unit": "RON"},
    "RON_RSD": {"currency": "RSD", "name": "RON/RSD (Serbian Dinar)", "description": "BNR reference rate, 1 RSD in RON", "unit": "RON"},
    "RON_RUB": {"currency": "RUB", "name": "RON/RUB (Russian Ruble)", "description": "BNR reference rate, 1 RUB in RON", "unit": "RON"},
    "RON_SEK": {"currency": "SEK", "name": "RON/SEK (Swedish Krona)", "description": "BNR reference rate, 1 SEK in RON", "unit": "RON"},
    "RON_SGD": {"currency": "SGD", "name": "RON/SGD (Singapore Dollar)", "description": "BNR reference rate, 1 SGD in RON", "unit": "RON"},
    "RON_THB": {"currency": "THB", "name": "RON/THB (Thai Baht)", "description": "BNR reference rate, 1 THB in RON", "unit": "RON"},
    "RON_TRY": {"currency": "TRY", "name": "RON/TRY (Turkish Lira)", "description": "BNR reference rate, 1 TRY in RON", "unit": "RON"},
    "RON_UAH": {"currency": "UAH", "name": "RON/UAH (Ukrainian Hryvnia)", "description": "BNR reference rate, 1 UAH in RON", "unit": "RON"},
    "RON_USD": {"currency": "USD", "name": "RON/USD (US Dollar)", "description": "BNR reference rate, 1 USD in RON", "unit": "RON"},
    "RON_XAU": {"currency": "XAU", "name": "RON/XAU (Gold, troy oz)", "description": "BNR reference rate, 1 troy oz gold in RON", "unit": "RON"},
    "RON_XDR": {"currency": "XDR", "name": "RON/XDR (IMF SDR)", "description": "BNR reference rate, 1 IMF Special Drawing Right in RON", "unit": "RON"},
    "RON_ZAR": {"currency": "ZAR", "name": "RON/ZAR (South African Rand)", "description": "BNR reference rate, 1 ZAR in RON", "unit": "RON"},
}

_CURRENCY_TO_KEY = {v["currency"]: k for k, v in INDICATORS.items()}


def _cache_path(name: str, params_hash: str) -> Path:
    return CACHE_DIR / f"{name}_{params_hash}.json"


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


def _fetch_xml(url: str) -> Optional[ET.Element]:
    """Fetch and parse a BNR XML feed. Returns root element or None."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except (requests.RequestException, ET.ParseError):
        return None


def _parse_cubes(root: ET.Element) -> List[Dict]:
    """
    Parse all Cube elements from BNR XML into a list of
    {"date": "YYYY-MM-DD", "rates": {"CCY": float_per_unit, ...}}
    Multiplier-adjusted currencies are normalized to per-1-unit.
    """
    cubes = []
    for cube in root.findall(".//bnr:Cube", XML_NS):
        date = cube.get("date")
        if not date:
            continue
        rates = {}
        for rate_el in cube.findall("bnr:Rate", XML_NS):
            ccy = rate_el.get("currency")
            multiplier = int(rate_el.get("multiplier", "1"))
            try:
                raw_value = float(rate_el.text)
                rates[ccy] = raw_value / multiplier
            except (TypeError, ValueError):
                continue
        if rates:
            cubes.append({"date": date, "rates": rates})
    cubes.sort(key=lambda c: c["date"], reverse=True)
    return cubes


def _get_cubes(use_10day: bool = True) -> Optional[List[Dict]]:
    """Fetch and parse cubes, preferring 10-day feed for history."""
    cache_key = "tenday" if use_10day else "daily"
    cp = _cache_path("cubes", _params_hash({"feed": cache_key}))
    cached = _read_cache(cp)
    if cached and "cubes" in cached:
        return cached["cubes"]

    url = TENDAY_URL if use_10day else DAILY_URL
    root = _fetch_xml(url)
    if root is None:
        if use_10day:
            root = _fetch_xml(DAILY_URL)
        if root is None:
            return None

    cubes = _parse_cubes(root)
    if cubes:
        _write_cache(cp, {"cubes": cubes})
    return cubes if cubes else None


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific FX rate indicator with 10-day history."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    ccy = cfg["currency"]

    cubes = _get_cubes(use_10day=True)
    if not cubes:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Failed to fetch BNR XML feed"}

    observations = []
    for cube in cubes:
        date = cube["date"]
        if start_date and date < start_date:
            continue
        if end_date and date > end_date:
            continue
        if ccy in cube["rates"]:
            observations.append({"period": date, "value": round(cube["rates"][ccy], 6)})

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": f"No data for {ccy} in feed"}

    observations.sort(key=lambda o: o["period"], reverse=True)

    period_change = period_change_pct = None
    if len(observations) >= 2:
        latest_v = observations[0]["value"]
        prev_v = observations[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 6)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": "daily",
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": observations,
        "total_observations": len(observations),
        "source": TENDAY_URL,
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "currency": v["currency"],
            "unit": v["unit"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    cubes = _get_cubes(use_10day=False)
    if not cubes:
        return {"success": False, "error": "Failed to fetch BNR daily XML feed"}

    latest_cube = cubes[0]
    results = {}
    for ccy, rate in latest_cube["rates"].items():
        key = _CURRENCY_TO_KEY.get(ccy)
        if key:
            results[key] = {
                "name": INDICATORS[key]["name"],
                "value": round(rate, 6),
                "period": latest_cube["date"],
                "unit": "RON",
            }

    return {
        "success": True,
        "source": "National Bank of Romania",
        "base_currency": "RON",
        "date": latest_cube["date"],
        "indicators": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_all_rates(date: str = None) -> Dict:
    """Get all FX rates for a specific date (or latest)."""
    cubes = _get_cubes(use_10day=True)
    if not cubes:
        return {"success": False, "error": "Failed to fetch BNR XML feed"}

    if date:
        cube = next((c for c in cubes if c["date"] == date), None)
        if not cube:
            available = [c["date"] for c in cubes]
            return {"success": False, "error": f"No data for {date}", "available_dates": available}
    else:
        cube = cubes[0]

    rates = {ccy: round(val, 6) for ccy, val in sorted(cube["rates"].items())}
    return {
        "success": True,
        "source": "National Bank of Romania",
        "base_currency": "RON",
        "date": cube["date"],
        "rates": rates,
        "count": len(rates),
        "timestamp": datetime.now().isoformat(),
    }


def get_history() -> Dict:
    """Get 10-day history for all currencies."""
    cubes = _get_cubes(use_10day=True)
    if not cubes:
        return {"success": False, "error": "Failed to fetch BNR XML feed"}

    history = {}
    for cube in cubes:
        for ccy, rate in cube["rates"].items():
            history.setdefault(ccy, []).append({"date": cube["date"], "value": round(rate, 6)})

    return {
        "success": True,
        "source": "National Bank of Romania",
        "base_currency": "RON",
        "currencies": len(history),
        "days": len(cubes),
        "date_range": {"from": cubes[-1]["date"], "to": cubes[0]["date"]},
        "history": history,
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
BNR Romania FX Rates Module (Initiative 0031)

Usage:
  python bnr_romania.py                     # Latest rates for all currencies
  python bnr_romania.py <INDICATOR>          # Fetch specific indicator (e.g. RON_USD)
  python bnr_romania.py list                 # List available indicators
  python bnr_romania.py rates                # All rates for today
  python bnr_romania.py rates <DATE>         # All rates for specific date
  python bnr_romania.py history              # 10-day history all currencies

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<15s} {cfg['name']}")
    print(f"""
Source: {DAILY_URL}
Protocol: XML feed (open access)
Base Currency: RON (Romanian Leu)
Currencies: {len(INDICATORS)}
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "rates":
            date_arg = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(get_all_rates(date_arg), indent=2, default=str))
        elif cmd == "history":
            print(json.dumps(get_history(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
