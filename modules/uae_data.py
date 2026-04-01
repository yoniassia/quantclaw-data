#!/usr/bin/env python3
"""
UAE Open Data & CBUAE Module — Phase 1

Central Bank of the UAE exchange rates, plus key macroeconomic indicators
(GDP, CPI, money supply, reserves, trade, current account) via World Bank API.

Data Sources:
  - CBUAE FX: https://www.centralbank.ae (Umbraco Surface API, HTML)
  - World Bank: https://api.worldbank.org/v2 (REST JSON)
Auth: None (open access)
Refresh: FX daily, macro annual/quarterly
Coverage: United Arab Emirates

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import sys
import time
import hashlib
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

CBUAE_FX_URL = "https://www.centralbank.ae/umbraco/Surface/Exchange/GetExchangeRateAllCurrency"
CBUAE_FX_HIST_URL = "https://www.centralbank.ae/umbraco/Surface/Exchange/GetExchangeRateAllCurrencyDate"
WB_BASE_URL = "https://api.worldbank.org/v2/country/ARE/indicator"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "uae_data"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.3

ARABIC_TO_ISO = {
    "دولار امريكي": "USD", "بيسو ارجنتيني": "ARS", "دولار استرالي": "AUD",
    "تاكا بنغلاديشية": "BDT", "دينار بحريني": "BHD", "دولار بروناي": "BND",
    "ريال برازيلي": "BRL", "بولا بوتسواني": "BWP", "روبل بلاروسي": "BYN",
    "دولار كندي": "CAD", "فرنك سويسري": "CHF", "بيزو تشيلي": "CLP",
    "يوان صيني - الخارج": "CNH", "يوان صيني": "CNY", "بيزو كولومبي": "COP",
    "كرونة تشيكية": "CZK", "كرون دانماركي": "DKK", "دينار جزائري": "DZD",
    "جينيه مصري": "EGP", "يورو": "EUR", "جنيه استرليني": "GBP",
    "دولار هونج كونج": "HKD", "فورنت هنغاري": "HUF", "روبية اندونيسية": "IDR",
    "روبية هندية": "INR", "كرونة آيسلندية": "ISK", "دينار أردني": "JOD",
    "ين ياباني": "JPY", "شلن كيني": "KES", "ون كوري": "KRW",
    "دينار كويتي": "KWD", "تينغ كازاخستاني": "KZT", "ليرة لبنانية": "LBP",
    "روبية سريلانكي": "LKR", "درهم مغربي": "MAD", "دينار مقدوني": "MKD",
    "بيسو مكسيكي": "MXN", "رينغيت ماليزي": "MYR", "نيرا نيجيري": "NGN",
    "كرون نرويجي": "NOK", "دولار نيوزيلندي": "NZD", "ريال عماني": "OMR",
    "سول بيروفي": "PEN", "بيسو فلبيني": "PHP", "روبية باكستانية": "PKR",
    "زلوتي بولندي": "PLN", "ريال قطري": "QAR", "دينار صربي": "RSD",
    "روبل روسي": "RUB", "ريال سعودي": "SAR", "دينار سوداني": "SDG",
    "كرونة سويدية": "SEK", "دولار سنغافوري": "SGD", "بات تايلندي": "THB",
    "دينار تونسي": "TND", "ليرة تركية": "TRY", "دولار تريندادي": "TTD",
    "دولار تايواني": "TWD", "شلن تنزاني": "TZS", "شلن اوغندي": "UGX",
    "دونغ فيتنامي": "VND", "ريال يمني": "YER", "راند جنوب أفريقي": "ZAR",
    "كواشا زامبي": "ZMW", "مانات أذربيجاني": "AZN", "ليف بلغاري": "BGN",
    "بر إثيوبي": "ETB", "دينار عراقي": "IQD", "شيكل اسرائيلي": "ILS",
    "دينار ليبي": "LYD", "روبي موريشي": "MUR", "ليو روماني": "RON",
    "ليرة سورية": "SYP", "منات تركمانستاني": "TMT", "سوم أوزبكستاني": "UZS",
    "ريال ايراني": "IRR",
}

MAJOR_FX = ["USD", "EUR", "GBP", "JPY", "CHF", "SAR", "KWD", "CNY", "INR", "EGP"]

INDICATORS = {
    # --- CBUAE Exchange Rates (daily, HTML scrape) ---
    "FX_USD": {
        "source": "cbuae_fx", "fx_code": "USD",
        "name": "AED per USD (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 USD (pegged ~3.6725)",
        "frequency": "daily", "unit": "AED",
    },
    "FX_EUR": {
        "source": "cbuae_fx", "fx_code": "EUR",
        "name": "AED per EUR (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 EUR",
        "frequency": "daily", "unit": "AED",
    },
    "FX_GBP": {
        "source": "cbuae_fx", "fx_code": "GBP",
        "name": "AED per GBP (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 GBP",
        "frequency": "daily", "unit": "AED",
    },
    "FX_JPY": {
        "source": "cbuae_fx", "fx_code": "JPY",
        "name": "AED per JPY (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 JPY",
        "frequency": "daily", "unit": "AED",
    },
    "FX_CHF": {
        "source": "cbuae_fx", "fx_code": "CHF",
        "name": "AED per CHF (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 CHF",
        "frequency": "daily", "unit": "AED",
    },
    "FX_SAR": {
        "source": "cbuae_fx", "fx_code": "SAR",
        "name": "AED per SAR (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 Saudi Riyal",
        "frequency": "daily", "unit": "AED",
    },
    "FX_CNY": {
        "source": "cbuae_fx", "fx_code": "CNY",
        "name": "AED per CNY (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 Chinese Yuan",
        "frequency": "daily", "unit": "AED",
    },
    "FX_INR": {
        "source": "cbuae_fx", "fx_code": "INR",
        "name": "AED per INR (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 Indian Rupee",
        "frequency": "daily", "unit": "AED",
    },
    "FX_KWD": {
        "source": "cbuae_fx", "fx_code": "KWD",
        "name": "AED per KWD (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 Kuwaiti Dinar",
        "frequency": "daily", "unit": "AED",
    },
    "FX_EGP": {
        "source": "cbuae_fx", "fx_code": "EGP",
        "name": "AED per EGP (CBUAE Official)",
        "description": "Central Bank of UAE official exchange rate, AED per 1 Egyptian Pound",
        "frequency": "daily", "unit": "AED",
    },
    # --- World Bank Macroeconomic Indicators (annual) ---
    "GDP_CURRENT_USD": {
        "source": "worldbank", "wb_code": "NY.GDP.MKTP.CD",
        "name": "UAE GDP — Current USD",
        "description": "Gross domestic product at purchaser's prices, current US dollars",
        "frequency": "annual", "unit": "USD",
    },
    "GDP_GROWTH": {
        "source": "worldbank", "wb_code": "NY.GDP.MKTP.KD.ZG",
        "name": "UAE GDP Growth Rate (%)",
        "description": "Annual percentage growth rate of GDP at constant prices",
        "frequency": "annual", "unit": "%",
    },
    "CPI_INFLATION": {
        "source": "worldbank", "wb_code": "FP.CPI.TOTL.ZG",
        "name": "UAE CPI Inflation (%)",
        "description": "Annual consumer price inflation, percentage change",
        "frequency": "annual", "unit": "%",
    },
    "CPI_INDEX": {
        "source": "worldbank", "wb_code": "FP.CPI.TOTL",
        "name": "UAE Consumer Price Index (2010=100)",
        "description": "Consumer price index, all items, base year 2010",
        "frequency": "annual", "unit": "index",
    },
    "BROAD_MONEY": {
        "source": "worldbank", "wb_code": "FM.LBL.BMNY.CN",
        "name": "UAE Broad Money — M2 (AED)",
        "description": "Broad money (M2) in local currency units (AED)",
        "frequency": "annual", "unit": "AED",
    },
    "FX_RESERVES": {
        "source": "worldbank", "wb_code": "FI.RES.TOTL.CD",
        "name": "UAE Total Reserves incl. Gold (USD)",
        "description": "Total reserves including gold, current US dollars",
        "frequency": "annual", "unit": "USD",
    },
    "EXPORTS": {
        "source": "worldbank", "wb_code": "NE.EXP.GNFS.CD",
        "name": "UAE Exports of Goods & Services (USD)",
        "description": "Exports of goods and services, current US dollars",
        "frequency": "annual", "unit": "USD",
    },
    "IMPORTS": {
        "source": "worldbank", "wb_code": "NE.IMP.GNFS.CD",
        "name": "UAE Imports of Goods & Services (USD)",
        "description": "Imports of goods and services, current US dollars",
        "frequency": "annual", "unit": "USD",
    },
    "CURRENT_ACCOUNT": {
        "source": "worldbank", "wb_code": "BN.CAB.XOKA.CD",
        "name": "UAE Current Account Balance (USD)",
        "description": "Current account balance, current US dollars",
        "frequency": "annual", "unit": "USD",
    },
    "GDP_PER_CAPITA": {
        "source": "worldbank", "wb_code": "NY.GDP.PCAP.CD",
        "name": "UAE GDP per Capita (USD)",
        "description": "GDP per capita, current US dollars",
        "frequency": "annual", "unit": "USD",
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


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return s


def _parse_cbuae_fx_html(html: str) -> Dict[str, float]:
    """Extract currency→rate pairs from CBUAE FX HTML table."""
    rows = re.findall(
        r'<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*class="[^"]*value[^"]*">([^<]*)</td>',
        html,
    )
    rates = {}
    for name_ar, val_str in rows:
        iso = ARABIC_TO_ISO.get(name_ar.strip())
        if iso:
            try:
                rates[iso] = float(val_str.strip())
            except ValueError:
                pass
    return rates


def _fetch_cbuae_fx_current() -> Dict:
    """Fetch current FX rates from CBUAE."""
    try:
        s = _session()
        s.headers["Accept"] = "text/html,application/xhtml+xml"
        resp = s.get(CBUAE_FX_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        if "cf_chl" in resp.text or "Just a moment" in resp.text:
            return {"success": False, "error": "Cloudflare challenge blocked request"}
        rates = _parse_cbuae_fx_html(resp.text)
        if not rates:
            return {"success": False, "error": "No rates parsed from HTML"}

        updated_match = re.search(
            r'Last updated:\s*[^\n]*?(\d{2}\s[\u0600-\u06FF]+\s\d{4})',
            resp.text,
        )
        update_str = updated_match.group(1) if updated_match else None

        return {"success": True, "rates": rates, "updated": update_str}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def _fetch_cbuae_fx_historical(date_str: str) -> Dict:
    """Fetch FX rates for a specific date (YYYY-MM-DD)."""
    try:
        s = _session()
        s.headers["Accept"] = "text/html,application/xhtml+xml"
        resp = s.get(
            CBUAE_FX_HIST_URL,
            params={"dateTime": date_str},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 500:
            return {"success": False, "error": f"No data for date {date_str} (weekend/holiday)"}
        resp.raise_for_status()
        if "cf_chl" in resp.text:
            return {"success": False, "error": "Cloudflare challenge"}
        rates = _parse_cbuae_fx_html(resp.text)
        if not rates:
            return {"success": False, "error": f"No rates for {date_str}"}
        return {"success": True, "rates": rates, "date": date_str}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def _fetch_worldbank(wb_code: str, years: int = 10) -> Dict:
    """Fetch indicator from World Bank API for UAE."""
    try:
        s = _session()
        end_year = datetime.now().year
        start_year = end_year - years
        url = f"{WB_BASE_URL}/{wb_code}"
        params = {
            "format": "json",
            "per_page": str(years + 2),
            "date": f"{start_year}:{end_year}",
        }
        resp = s.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) < 2 or not data[1]:
            return {"success": False, "error": "No data returned from World Bank"}

        observations = []
        for item in data[1]:
            if item.get("value") is not None:
                observations.append({
                    "period": item["date"],
                    "value": float(item["value"]),
                })
        if not observations:
            return {"success": False, "error": "All values are null"}

        return {"success": True, "observations": observations}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}
    except (KeyError, ValueError, TypeError) as e:
        return {"success": False, "error": f"Parse error: {e}"}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator/series."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    source = cfg["source"]

    if source == "cbuae_fx":
        result = _fetch_cbuae_fx_current()
        if not result["success"]:
            return {
                "success": False, "indicator": indicator,
                "name": cfg["name"], "error": result["error"],
            }
        fx_code = cfg["fx_code"]
        rate = result["rates"].get(fx_code)
        if rate is None:
            return {
                "success": False, "indicator": indicator,
                "name": cfg["name"], "error": f"Currency {fx_code} not in response",
            }

        prev_rates = _get_previous_fx_rate(fx_code)
        period_change = period_change_pct = None
        if prev_rates is not None and prev_rates != 0:
            period_change = round(rate - prev_rates, 6)
            period_change_pct = round((period_change / abs(prev_rates)) * 100, 4)

        response = {
            "success": True,
            "indicator": indicator,
            "name": cfg["name"],
            "description": cfg["description"],
            "unit": cfg["unit"],
            "frequency": cfg["frequency"],
            "latest_value": rate,
            "latest_period": datetime.now().strftime("%Y-%m-%d"),
            "period_change": period_change,
            "period_change_pct": period_change_pct,
            "data_points": [{"period": datetime.now().strftime("%Y-%m-%d"), "value": rate}],
            "total_observations": 1,
            "source": CBUAE_FX_URL,
            "timestamp": datetime.now().isoformat(),
        }
        _write_cache(cp, response)
        return response

    elif source == "worldbank":
        wb_code = cfg["wb_code"]
        result = _fetch_worldbank(wb_code)
        if not result["success"]:
            return {
                "success": False, "indicator": indicator,
                "name": cfg["name"], "error": result["error"],
            }

        observations = result["observations"]
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
            "data_points": observations[:10],
            "total_observations": len(observations),
            "source": f"{WB_BASE_URL}/{wb_code}",
            "timestamp": datetime.now().isoformat(),
        }
        _write_cache(cp, response)
        return response

    return {"success": False, "indicator": indicator, "error": "Unknown source type"}


def _get_previous_fx_rate(fx_code: str) -> Optional[float]:
    """Try to get yesterday's FX rate for delta calculation."""
    today = datetime.now()
    for offset in range(1, 5):
        prev_date = today - timedelta(days=offset)
        date_str = prev_date.strftime("%Y-%m-%d")
        result = _fetch_cbuae_fx_historical(date_str)
        if result["success"]:
            return result["rates"].get(fx_code)
    return None


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
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
        "source": "UAE Open Data / CBUAE",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_rates() -> Dict:
    """Get all current CBUAE exchange rates (76 currencies)."""
    result = _fetch_cbuae_fx_current()
    if not result["success"]:
        return result
    return {
        "success": True,
        "base": "AED",
        "rates": result["rates"],
        "count": len(result["rates"]),
        "updated": result.get("updated"),
        "timestamp": datetime.now().isoformat(),
    }


def get_macro_summary() -> Dict:
    """Get a summary of key UAE macroeconomic indicators."""
    macro_keys = [k for k, v in INDICATORS.items() if v["source"] == "worldbank"]
    results = {}
    errors = []
    for key in macro_keys:
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
        "success": bool(results),
        "country": "United Arab Emirates",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
UAE Open Data & CBUAE Module (Phase 1)

Usage:
  python uae_data.py                         # Latest values for all indicators
  python uae_data.py <INDICATOR>             # Fetch specific indicator
  python uae_data.py list                    # List available indicators
  python uae_data.py fx                      # All CBUAE exchange rates (76 currencies)
  python uae_data.py macro                   # UAE macroeconomic summary

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<22s} {cfg['name']}")
    print(f"""
Sources:
  CBUAE FX: {CBUAE_FX_URL}
  World Bank: {WB_BASE_URL}
Coverage: United Arab Emirates
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "fx":
            print(json.dumps(get_fx_rates(), indent=2, default=str))
        elif cmd == "macro":
            print(json.dumps(get_macro_summary(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
