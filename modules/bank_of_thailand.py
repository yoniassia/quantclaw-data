#!/usr/bin/env python3
"""
Bank of Thailand (BOT) Module — Phase 1

Thai central bank data: exchange rates (THB vs 40+ currencies), BOT policy rate,
interbank rates, BIBOR, government bond yields, balance of payments,
international reserves, monetary aggregates, and annual macro (GDP, CPI).

Data Source: https://apigw1.bot.or.th/bot/public
Protocol: REST (JSON)
Auth: API key via X-IBM-Client-Id header (free registration at https://apiportal.bot.or.th/)
Refresh: Daily (FX), Monthly (rates, BoP, reserves, money), Annual (GDP, CPI)
Coverage: Thailand

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import json
import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://gateway.api.bot.or.th"
FX_ENDPOINT = "/Stat-ExchangeRate/v2/DAILY_AVG_EXG_RATE/"
OBS_ENDPOINT = "/observations/"

CACHE_DIR = Path(__file__).parent.parent / "cache" / "bank_of_thailand"
CACHE_TTL_FX = 1
CACHE_TTL_MACRO = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    "POLICY_RATE": {
        "series_code": "FMRTINTM00001",
        "name": "BOT Policy Rate",
        "description": "Bank of Thailand policy interest rate (1-day bilateral repurchase rate)",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "INTERBANK_OVERNIGHT": {
        "series_code": "FMRTINTM00002",
        "name": "Interbank Overnight Lending Rate",
        "description": "Weighted average interbank overnight lending rate",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "REPO_1D": {
        "series_code": "FMRTINTM00005",
        "name": "Repurchase Rate 1-Day",
        "description": "1-day private repurchase rate",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "BIBOR_1W": {
        "series_code": "FMRTINTM00012",
        "name": "BIBOR 1 Week",
        "description": "Bangkok Interbank Offered Rate, 1-week tenor",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "BIBOR_3M": {
        "series_code": "FMRTINTM00015",
        "name": "BIBOR 3 Months",
        "description": "Bangkok Interbank Offered Rate, 3-month tenor",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "BIBOR_6M": {
        "series_code": "FMRTINTM00016",
        "name": "BIBOR 6 Months",
        "description": "Bangkok Interbank Offered Rate, 6-month tenor",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "BIBOR_1Y": {
        "series_code": "FMRTINTM00018",
        "name": "BIBOR 1 Year",
        "description": "Bangkok Interbank Offered Rate, 1-year tenor",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "interest_rates",
    },
    "BOND_1Y": {
        "series_code": "FMRTINTM00030",
        "name": "Thai Govt Bond Yield 1Y",
        "description": "T-Bill & Government bond yield, 1-year maturity",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "BOND_5Y": {
        "series_code": "FMRTINTM00034",
        "name": "Thai Govt Bond Yield 5Y",
        "description": "Government bond yield, 5-year maturity",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "BOND_10Y": {
        "series_code": "FMRTINTM00039",
        "name": "Thai Govt Bond Yield 10Y",
        "description": "Government bond yield, 10-year maturity",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "BOND_20Y": {
        "series_code": "FMRTINTM00049",
        "name": "Thai Govt Bond Yield 20Y",
        "description": "Government bond yield, 20-year maturity",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "CURRENT_ACCOUNT_USD": {
        "series_code": "XTBOP0CA00M01893",
        "name": "Current Account Balance (USD)",
        "description": "Thailand current account balance, monthly",
        "frequency": "monthly",
        "unit": "USD mn",
        "cache_hours": 24,
        "group": "external",
    },
    "INTL_RESERVES_USD": {
        "series_code": "XTRSV00000M00698",
        "name": "International Reserves Total (USD)",
        "description": "Total international reserve position",
        "frequency": "monthly",
        "unit": "USD mn",
        "cache_hours": 24,
        "group": "external",
    },
    "FX_END_PERIOD": {
        "series_code": "XTRSV00000M00705",
        "name": "THB/USD End-of-Period Monthly",
        "description": "Exchange rate end of period monthly (Baht per 1 USD)",
        "frequency": "monthly",
        "unit": "THB/USD",
        "cache_hours": 24,
        "group": "external",
    },
    "NARROW_MONEY": {
        "series_code": "MFDC00BM00M00091",
        "name": "Narrow Money (M1)",
        "description": "Narrow money aggregate",
        "frequency": "monthly",
        "unit": "THB mn",
        "cache_hours": 24,
        "group": "monetary",
    },
    "BROAD_MONEY": {
        "series_code": "MFDC00SV00M00065",
        "name": "Broad Money",
        "description": "Broad money aggregate (depository corporations)",
        "frequency": "monthly",
        "unit": "THB mn",
        "cache_hours": 24,
        "group": "monetary",
    },
    "GDP_REAL": {
        "series_code": "EIMACROY00218",
        "name": "GDP Chain Volume Measures",
        "description": "Real GDP at chain volume measures",
        "frequency": "annual",
        "unit": "THB bn",
        "cache_hours": 24,
        "group": "macro",
    },
    "GDP_REAL_YOY": {
        "series_code": "EIMACROY00219",
        "name": "GDP Real Growth (% YoY)",
        "description": "Real GDP year-on-year growth rate",
        "frequency": "annual",
        "unit": "%",
        "cache_hours": 24,
        "group": "macro",
    },
    "GDP_NOMINAL": {
        "series_code": "EIMACROY00224",
        "name": "GDP at Current Prices",
        "description": "Nominal GDP at current prices",
        "frequency": "annual",
        "unit": "THB bn",
        "cache_hours": 24,
        "group": "macro",
    },
    "HEADLINE_CPI": {
        "series_code": "EIMACROY00227",
        "name": "Headline CPI (2015=100)",
        "description": "Headline Consumer Price Index, base year 2015=100",
        "frequency": "annual",
        "unit": "Index (2015=100)",
        "cache_hours": 24,
        "group": "macro",
    },
    "HEADLINE_CPI_YOY": {
        "series_code": "EIMACROY00228",
        "name": "Headline CPI Inflation (% YoY)",
        "description": "Headline CPI year-on-year change (inflation rate)",
        "frequency": "annual",
        "unit": "%",
        "cache_hours": 24,
        "group": "macro",
    },
    "CORE_CPI": {
        "series_code": "EIMACROY00229",
        "name": "Core CPI (2015=100)",
        "description": "Core Consumer Price Index excluding raw food and energy",
        "frequency": "annual",
        "unit": "Index (2015=100)",
        "cache_hours": 24,
        "group": "macro",
    },
    "CORE_CPI_YOY": {
        "series_code": "EIMACROY00230",
        "name": "Core CPI Inflation (% YoY)",
        "description": "Core CPI year-on-year change (core inflation rate)",
        "frequency": "annual",
        "unit": "%",
        "cache_hours": 24,
        "group": "macro",
    },
    "CB_TOTAL_ASSETS": {
        "series_code": "FICBBLSM00154",
        "name": "Commercial Banks Net Interbank Assets",
        "description": "Net interbank and money market items — assets side, domestically registered banks",
        "frequency": "monthly",
        "unit": "THB mn",
        "cache_hours": 24,
        "group": "financial_institutions",
    },
    "CB_LOANS_EX_IB": {
        "series_code": "FICBARSM00298",
        "name": "Commercial Bank Loans (excl. Interbank)",
        "description": "Total loans of commercial banks excluding interbank",
        "frequency": "monthly",
        "unit": "THB mn",
        "cache_hours": 24,
        "group": "financial_institutions",
    },
    "CB_DEPOSITS_EX_IB": {
        "series_code": "FICBARSM00299",
        "name": "Commercial Bank Deposits (excl. Interbank)",
        "description": "Total deposits of commercial banks excluding interbank",
        "frequency": "monthly",
        "unit": "THB mn",
        "cache_hours": 24,
        "group": "financial_institutions",
    },
    "CB_LDR": {
        "series_code": "FICBARSM00301",
        "name": "Loan-to-Deposit Ratio (excl. Interbank)",
        "description": "Loans to deposits and bill of exchange ratio excluding interbank",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "financial_institutions",
    },
}

FX_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CNY", "HKD", "SGD", "MYR",
    "IDR", "PHP", "INR", "KRW", "TWD", "AUD", "NZD", "CHF",
    "CAD", "SEK", "NOK", "DKK", "ZAR", "MXN", "RUB", "AED",
    "SAR", "KWD", "BND", "VND", "MMK", "KHR", "LAK",
]


def _get_api_key() -> Optional[str]:
    key = os.environ.get("BOT_API_KEY")
    if key:
        return key
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("BOT_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


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


def _api_headers() -> Dict:
    """Build request headers. New gateway uses Authorization header; legacy used X-IBM-Client-Id."""
    headers = {"Accept": "application/json"}
    api_key = _get_api_key()
    if api_key:
        headers["Authorization"] = api_key
        headers["X-IBM-Client-Id"] = api_key
    return headers


def _api_get(path: str, params: dict = None) -> Dict:
    url = BASE_URL + path
    try:
        resp = requests.get(url, headers=_api_headers(), params=params or {}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        try:
            body = e.response.text[:200] if e.response is not None else ""
        except Exception:
            pass
        if status == 401:
            return {"success": False, "error": "Unauthorized — check BOT_API_KEY in .env"}
        if status == 429:
            return {"success": False, "error": "Rate limited — 500 req/day exceeded"}
        return {"success": False, "error": f"HTTP {status}: {body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_observations(raw: Dict) -> List[Dict]:
    """Parse BOT observations API response into list of {period, value} dicts."""
    try:
        series_list = raw.get("result", {}).get("series", [])
        if not series_list:
            return []
        series = series_list[0]
        observations = series.get("observations", [])
        meta = {
            "series_name": series.get("series_name_eng", ""),
            "unit": series.get("unit_eng", ""),
            "last_updated": series.get("last_update_date", ""),
        }
        results = []
        for obs in observations:
            period = obs.get("period_start", obs.get("period", ""))
            value = obs.get("value")
            if value is not None and value != "" and value != "N/A":
                try:
                    val = float(str(value).replace(",", ""))
                except (ValueError, TypeError):
                    continue
                results.append({"period": period, "value": val, **meta})
        results.sort(key=lambda x: x["period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError):
        return []


def _parse_fx_response(raw: Dict) -> List[Dict]:
    """Parse BOT exchange rate API response into list of FX rate dicts."""
    try:
        data = raw.get("result", {}).get("data", {})
        details = data.get("data_detail", [])
        results = []
        for rec in details:
            mid = rec.get("mid_rate", "")
            if not mid or mid == "N/A":
                buying = rec.get("buying_transfer", "")
                selling = rec.get("selling", "")
                if buying and selling and buying != "N/A" and selling != "N/A":
                    try:
                        mid = str(round((float(buying) + float(selling)) / 2, 7))
                    except (ValueError, TypeError):
                        continue
                else:
                    continue
            try:
                results.append({
                    "period": rec.get("period", ""),
                    "currency": rec.get("currency_id", ""),
                    "currency_name": rec.get("currency_name_eng", ""),
                    "buying_sight": _safe_float(rec.get("buying_sight")),
                    "buying_transfer": _safe_float(rec.get("buying_transfer")),
                    "selling": _safe_float(rec.get("selling")),
                    "mid_rate": float(mid),
                })
            except (ValueError, TypeError):
                continue
        return results
    except (KeyError, IndexError, TypeError):
        return []


def _safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def fetch_fx_rates(start_period: str = None, end_period: str = None, currency: str = None) -> Dict:
    """Fetch daily average exchange rates (THB vs foreign currencies)."""
    if not start_period:
        start_period = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_period:
        end_period = datetime.now().strftime("%Y-%m-%d")

    cache_key = f"fx_rates_{currency or 'all'}"
    cp = _cache_path(cache_key, _params_hash({"s": start_period, "e": end_period, "c": currency}))
    cached = _read_cache(cp, CACHE_TTL_FX)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"start_period": start_period, "end_period": end_period}
    if currency:
        params["currency"] = currency.upper()

    result = _api_get(FX_ENDPOINT, params)
    if not result["success"]:
        return {"success": False, "error": result["error"], "endpoint": "fx_rates"}

    records = _parse_fx_response(result["data"])
    if not records:
        return {"success": False, "error": "No FX data returned", "endpoint": "fx_rates"}

    if currency:
        records = [r for r in records if r["currency"] == currency.upper()]

    latest_date = max(r["period"] for r in records)
    latest_records = [r for r in records if r["period"] == latest_date]
    currencies_available = sorted(set(r["currency"] for r in records))

    response = {
        "success": True,
        "indicator": "FX_RATES",
        "name": "Daily Average Exchange Rates (THB / Foreign Currency)",
        "description": "Average exchange rates of commercial banks in Bangkok",
        "unit": "THB per 1 unit of foreign currency",
        "source": "Bank of Thailand",
        "latest_date": latest_date,
        "latest_rates": {r["currency"]: r["mid_rate"] for r in latest_records},
        "currencies": currencies_available,
        "total_records": len(records),
        "data_points": records[:100],
        "start_period": start_period,
        "end_period": end_period,
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def fetch_data(indicator: str, start_period: str = None, end_period: str = None) -> Dict:
    """Fetch a specific indicator series via the observations endpoint."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_key = f"obs_{indicator}"
    cp = _cache_path(cache_key, _params_hash({"i": indicator, "s": start_period, "e": end_period}))
    cached = _read_cache(cp, cfg["cache_hours"])
    if cached:
        cached.pop("_cached_at", None)
        return cached

    params = {"series_code": cfg["series_code"]}
    if start_period:
        params["start_period"] = start_period
    else:
        lookback = "2000-01-01" if cfg["frequency"] == "annual" else "2020-01-01"
        params["start_period"] = lookback
    if end_period:
        params["end_period"] = end_period

    result = _api_get(OBS_ENDPOINT, params)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_observations(result["data"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations returned — check API key or series availability"}

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
        "group": cfg["group"],
        "series_code": cfg["series_code"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": "Bank of Thailand",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    items = [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "group": v["group"],
            "series_code": v["series_code"],
        }
        for k, v in INDICATORS.items()
    ]
    items.append({
        "key": "FX_RATES",
        "name": "Daily Average Exchange Rates",
        "description": f"THB exchange rates vs {len(FX_CURRENCIES)}+ currencies",
        "frequency": "daily",
        "unit": "THB per unit",
        "group": "fx",
        "series_code": "N/A (dedicated endpoint)",
    })
    return items


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        ind_upper = indicator.upper()
        if ind_upper == "FX_RATES":
            return fetch_fx_rates()
        return fetch_data(ind_upper)

    key_indicators = [
        "POLICY_RATE", "INTERBANK_OVERNIGHT", "BIBOR_3M",
        "BOND_10Y", "FX_END_PERIOD",
        "CURRENT_ACCOUNT_USD", "INTL_RESERVES_USD",
        "BROAD_MONEY",
    ]
    results = {}
    errors = []
    for key in key_indicators:
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
        "source": "Bank of Thailand",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get BOT policy rate and related short-term rates."""
    rate_keys = ["POLICY_RATE", "INTERBANK_OVERNIGHT", "REPO_1D", "BIBOR_1W", "BIBOR_3M", "BIBOR_6M", "BIBOR_1Y"]
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
        "source": "Bank of Thailand",
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Get Thai government bond yield curve."""
    maturities = ["BOND_1Y", "BOND_5Y", "BOND_10Y", "BOND_20Y"]
    curve = []
    for key in maturities:
        data = fetch_data(key)
        if data.get("success"):
            curve.append({
                "maturity": key.replace("BOND_", ""),
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
            })
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(curve),
        "curve": curve,
        "count": len(curve),
        "source": "Bank of Thailand",
        "timestamp": datetime.now().isoformat(),
    }


def get_cpi() -> Dict:
    """Get Thai CPI (headline and core) inflation data."""
    cpi_keys = ["HEADLINE_CPI", "HEADLINE_CPI_YOY", "CORE_CPI", "CORE_CPI_YOY"]
    results = {}
    for key in cpi_keys:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "data_points": data.get("data_points", [])[:10],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(results),
        "indicators": results,
        "source": "Bank of Thailand / Trade Policy and Strategy Office",
        "timestamp": datetime.now().isoformat(),
    }


def get_gdp() -> Dict:
    """Get Thai GDP data (real, nominal, growth)."""
    gdp_keys = ["GDP_REAL", "GDP_REAL_YOY", "GDP_NOMINAL"]
    results = {}
    for key in gdp_keys:
        data = fetch_data(key)
        if data.get("success"):
            results[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "unit": data["unit"],
                "data_points": data.get("data_points", [])[:10],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(results),
        "indicators": results,
        "source": "Bank of Thailand / NESDC",
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
Bank of Thailand (BOT) Module (Phase 1)

Usage:
  python bank_of_thailand.py                          # Key indicators summary
  python bank_of_thailand.py <INDICATOR>               # Fetch specific indicator
  python bank_of_thailand.py fx_rates                  # Daily exchange rates (40+ currencies)
  python bank_of_thailand.py fx_rates USD              # THB/USD rate only
  python bank_of_thailand.py policy_rate               # Alias for POLICY_RATE
  python bank_of_thailand.py policy-rates              # All BOT policy & interbank rates
  python bank_of_thailand.py yield-curve               # Thai govt bond yield curve
  python bank_of_thailand.py cpi                       # CPI headline & core
  python bank_of_thailand.py gdp                       # GDP data
  python bank_of_thailand.py list                      # List available indicators

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<28s} {cfg['name']}")
    print(f"  {'FX_RATES':<28s} Daily Average Exchange Rates (40+ currencies)")
    print(f"""
Source: {BASE_URL}
Auth: Authorization header (set BOT_API_KEY in .env, register at portal.api.bot.or.th)
Coverage: Thailand
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "fx_rates" or cmd == "fx-rates":
            currency = sys.argv[2].upper() if len(sys.argv) > 2 else None
            result = fetch_fx_rates(currency=currency)
            print(json.dumps(result, indent=2, default=str))
        elif cmd in ("policy_rate", "policy-rate"):
            result = fetch_data("POLICY_RATE")
            print(json.dumps(result, indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        elif cmd == "yield-curve":
            print(json.dumps(get_yield_curve(), indent=2, default=str))
        elif cmd == "cpi":
            print(json.dumps(get_cpi(), indent=2, default=str))
        elif cmd == "gdp":
            print(json.dumps(get_gdp(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
