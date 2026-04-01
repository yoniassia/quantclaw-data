#!/usr/bin/env python3
"""
Bank of Canada Valet Enhanced Module

Full coverage of the Bank of Canada Valet API: policy rates, GoC benchmark
bond yields (full curve), marketable bond average yields, T-bill yields,
money market rates, daily FX rates (26 currency pairs), chartered bank
posted rates, term premiums, yield volatility, commodity price index,
and Business Outlook Survey indicator.

Data Source: https://www.bankofcanada.ca/valet
Protocol: REST (JSON)
Auth: None (open access)
Refresh: Daily (FX, yields), Monthly/Quarterly (policy rates, BOS, BCPI)
Coverage: Canada

Author: QUANTCLAW DATA Build Agent
Initiative: 0028
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://www.bankofcanada.ca/valet"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "bank_of_canada_valet"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

INDICATORS = {
    # --- Policy & Overnight Rates ---
    "OVERNIGHT_RATE": {
        "series": "V122514",
        "name": "BoC Overnight Rate (%)",
        "description": "Bank of Canada overnight money market financing rate",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "policy_rates",
    },
    "BANK_RATE": {
        "series": "V122530",
        "name": "BoC Bank Rate (%)",
        "description": "Bank of Canada bank rate (upper bound of operating band)",
        "frequency": "monthly",
        "unit": "%",
        "cache_hours": 24,
        "group": "policy_rates",
    },
    "CORRA": {
        "series": "AVG.INTWO",
        "name": "CORRA — Canadian Overnight Repo Rate Average (%)",
        "description": "Canadian Overnight Repo Rate Average, risk-free overnight benchmark",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "policy_rates",
    },
    # --- GoC Benchmark Bond Yields (full curve) ---
    "GOC_2Y": {
        "series": "BD.CDN.2YR.DQ.YLD",
        "name": "GoC Benchmark Bond Yield 2Y (%)",
        "description": "Government of Canada benchmark bond yield, 2-year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_3Y": {
        "series": "BD.CDN.3YR.DQ.YLD",
        "name": "GoC Benchmark Bond Yield 3Y (%)",
        "description": "Government of Canada benchmark bond yield, 3-year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_5Y": {
        "series": "BD.CDN.5YR.DQ.YLD",
        "name": "GoC Benchmark Bond Yield 5Y (%)",
        "description": "Government of Canada benchmark bond yield, 5-year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_7Y": {
        "series": "BD.CDN.7YR.DQ.YLD",
        "name": "GoC Benchmark Bond Yield 7Y (%)",
        "description": "Government of Canada benchmark bond yield, 7-year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_10Y": {
        "series": "BD.CDN.10YR.DQ.YLD",
        "name": "GoC Benchmark Bond Yield 10Y (%)",
        "description": "Government of Canada benchmark bond yield, 10-year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_LONG": {
        "series": "BD.CDN.LONG.DQ.YLD",
        "name": "GoC Benchmark Bond Yield Long-Term (%)",
        "description": "Government of Canada benchmark bond yield, long-term (30Y)",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_RRB": {
        "series": "BD.CDN.RRB.DQ.YLD",
        "name": "GoC Real Return Bond Yield (%)",
        "description": "Government of Canada real return (inflation-linked) bond yield",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    # --- Marketable Bond Average Yields ---
    "GOC_AVG_1TO3Y": {
        "series": "CDN.AVG.1YTO3Y.AVG",
        "name": "GoC Marketable Bond Avg Yield 1-3Y (%)",
        "description": "Average yield on marketable GoC bonds, 1 to 3 year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_AVG_3TO5Y": {
        "series": "CDN.AVG.3YTO5Y.AVG",
        "name": "GoC Marketable Bond Avg Yield 3-5Y (%)",
        "description": "Average yield on marketable GoC bonds, 3 to 5 year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_AVG_5TO10Y": {
        "series": "CDN.AVG.5YTO10Y.AVG",
        "name": "GoC Marketable Bond Avg Yield 5-10Y (%)",
        "description": "Average yield on marketable GoC bonds, 5 to 10 year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    "GOC_AVG_OVER10Y": {
        "series": "CDN.AVG.OVER.10.AVG",
        "name": "GoC Marketable Bond Avg Yield >10Y (%)",
        "description": "Average yield on marketable GoC bonds, over 10 year maturity",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "bond_yields",
    },
    # --- Treasury Bill Yields ---
    "TBILL_1M": {
        "series": "V1592248173",
        "name": "T-Bill Yield 1 Month (%)",
        "description": "Government of Canada treasury bill yield, 1-month maturity",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "tbill_yields",
    },
    "TBILL_3M": {
        "series": "V80691303",
        "name": "T-Bill Yield 3 Month (%)",
        "description": "Government of Canada treasury bill yield, 3-month maturity",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "tbill_yields",
    },
    "TBILL_6M": {
        "series": "V80691304",
        "name": "T-Bill Yield 6 Month (%)",
        "description": "Government of Canada treasury bill yield, 6-month maturity",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "tbill_yields",
    },
    "TBILL_1Y": {
        "series": "V80691305",
        "name": "T-Bill Yield 1 Year (%)",
        "description": "Government of Canada treasury bill yield, 1-year maturity",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "tbill_yields",
    },
    # --- Money Market ---
    "TBILL_MID_90D": {
        "series": "TB.CDN.90D.MID",
        "name": "90-Day T-Bill Mid Rate (%)",
        "description": "Money market 90-day treasury bill mid rate",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "money_market",
    },
    # --- FX Rates (CAD vs 26 currencies) ---
    "FX_USD_CAD": {
        "series": "FXUSDCAD",
        "name": "USD/CAD Exchange Rate",
        "description": "US dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_EUR_CAD": {
        "series": "FXEURCAD",
        "name": "EUR/CAD Exchange Rate",
        "description": "Euro to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_GBP_CAD": {
        "series": "FXGBPCAD",
        "name": "GBP/CAD Exchange Rate",
        "description": "British pound to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_JPY_CAD": {
        "series": "FXJPYCAD",
        "name": "JPY/CAD Exchange Rate",
        "description": "Japanese yen to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_CHF_CAD": {
        "series": "FXCHFCAD",
        "name": "CHF/CAD Exchange Rate",
        "description": "Swiss franc to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_AUD_CAD": {
        "series": "FXAUDCAD",
        "name": "AUD/CAD Exchange Rate",
        "description": "Australian dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_NZD_CAD": {
        "series": "FXNZDCAD",
        "name": "NZD/CAD Exchange Rate",
        "description": "New Zealand dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_CNY_CAD": {
        "series": "FXCNYCAD",
        "name": "CNY/CAD Exchange Rate",
        "description": "Chinese yuan to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_HKD_CAD": {
        "series": "FXHKDCAD",
        "name": "HKD/CAD Exchange Rate",
        "description": "Hong Kong dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_INR_CAD": {
        "series": "FXINRCAD",
        "name": "INR/CAD Exchange Rate",
        "description": "Indian rupee to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_IDR_CAD": {
        "series": "FXIDRCAD",
        "name": "IDR/CAD Exchange Rate",
        "description": "Indonesian rupiah to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_MYR_CAD": {
        "series": "FXMYRCAD",
        "name": "MYR/CAD Exchange Rate",
        "description": "Malaysian ringgit to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_MXN_CAD": {
        "series": "FXMXNCAD",
        "name": "MXN/CAD Exchange Rate",
        "description": "Mexican peso to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_NOK_CAD": {
        "series": "FXNOKCAD",
        "name": "NOK/CAD Exchange Rate",
        "description": "Norwegian krone to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_PEN_CAD": {
        "series": "FXPENCAD",
        "name": "PEN/CAD Exchange Rate",
        "description": "Peruvian sol to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_RUB_CAD": {
        "series": "FXRUBCAD",
        "name": "RUB/CAD Exchange Rate",
        "description": "Russian ruble to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_SAR_CAD": {
        "series": "FXSARCAD",
        "name": "SAR/CAD Exchange Rate",
        "description": "Saudi riyal to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_SGD_CAD": {
        "series": "FXSGDCAD",
        "name": "SGD/CAD Exchange Rate",
        "description": "Singapore dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_ZAR_CAD": {
        "series": "FXZARCAD",
        "name": "ZAR/CAD Exchange Rate",
        "description": "South African rand to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_KRW_CAD": {
        "series": "FXKRWCAD",
        "name": "KRW/CAD Exchange Rate",
        "description": "South Korean won to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_SEK_CAD": {
        "series": "FXSEKCAD",
        "name": "SEK/CAD Exchange Rate",
        "description": "Swedish krona to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_TWD_CAD": {
        "series": "FXTWDCAD",
        "name": "TWD/CAD Exchange Rate",
        "description": "Taiwan dollar to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_THB_CAD": {
        "series": "FXTHBCAD",
        "name": "THB/CAD Exchange Rate",
        "description": "Thai baht to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_TRY_CAD": {
        "series": "FXTRYCAD",
        "name": "TRY/CAD Exchange Rate",
        "description": "Turkish lira to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_BRL_CAD": {
        "series": "FXBRLCAD",
        "name": "BRL/CAD Exchange Rate",
        "description": "Brazilian real to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    "FX_VND_CAD": {
        "series": "FXVNDCAD",
        "name": "VND/CAD Exchange Rate",
        "description": "Vietnamese dong to Canadian dollar daily exchange rate",
        "frequency": "daily",
        "unit": "CAD per unit",
        "cache_hours": 1,
        "group": "fx_rates",
    },
    # --- Financial Conditions / Term Premiums ---
    "YIELD_VOLATILITY_GOC": {
        "series": "FVI_YIELDVOLATILITY_GOC",
        "name": "GoC Bond Yield Volatility",
        "description": "Government of Canada bond realized yield volatility (FVI)",
        "frequency": "daily",
        "unit": "index",
        "cache_hours": 24,
        "group": "financial_conditions",
    },
    "TERM_PREMIUM_2Y": {
        "series": "FVI_TP_GOC_2Y_ACM",
        "name": "GoC 2Y Term Premium — ACM (%)",
        "description": "Estimated term premium on 2-year GoC bond (Adrian-Crump-Moench model)",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "financial_conditions",
    },
    "TERM_PREMIUM_5Y": {
        "series": "FVI_TP_GOC_5Y_ACM",
        "name": "GoC 5Y Term Premium — ACM (%)",
        "description": "Estimated term premium on 5-year GoC bond (Adrian-Crump-Moench model)",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "financial_conditions",
    },
    "TERM_PREMIUM_10Y": {
        "series": "FVI_TP_GOC_10Y_ACM",
        "name": "GoC 10Y Term Premium — ACM (%)",
        "description": "Estimated term premium on 10-year GoC bond (Adrian-Crump-Moench model)",
        "frequency": "daily",
        "unit": "%",
        "cache_hours": 24,
        "group": "financial_conditions",
    },
    # --- Business Outlook Survey ---
    "BOS_INDICATOR": {
        "series": "PC1",
        "name": "Business Outlook Survey Indicator",
        "description": "BoC Business Outlook Survey composite indicator (quarterly)",
        "frequency": "quarterly",
        "unit": "index",
        "cache_hours": 24,
        "group": "surveys",
    },
    # --- Chartered Bank Posted Rates ---
    "PRIME_RATE": {
        "series": "V80691311",
        "name": "Chartered Bank Prime Rate (%)",
        "description": "Interest rate posted by major chartered banks — prime lending rate",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    "MORTGAGE_1Y": {
        "series": "V80691339",
        "name": "Posted Mortgage Rate 1Y (%)",
        "description": "Chartered bank posted residential mortgage rate, 1-year fixed",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    "MORTGAGE_3Y": {
        "series": "V80691340",
        "name": "Posted Mortgage Rate 3Y (%)",
        "description": "Chartered bank posted residential mortgage rate, 3-year fixed",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    "MORTGAGE_5Y": {
        "series": "V80691341",
        "name": "Posted Mortgage Rate 5Y (%)",
        "description": "Chartered bank posted residential mortgage rate, 5-year fixed",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    "GIC_1Y": {
        "series": "V80691333",
        "name": "Posted GIC Rate 1Y (%)",
        "description": "Chartered bank posted GIC rate, 1-year term",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    "GIC_5Y": {
        "series": "V80691336",
        "name": "Posted GIC Rate 5Y Personal Fixed (%)",
        "description": "Chartered bank posted 5-year personal fixed term deposit rate",
        "frequency": "weekly",
        "unit": "%",
        "cache_hours": 24,
        "group": "bank_rates",
    },
    # --- Commodity Price Index ---
    "BCPI_TOTAL": {
        "series": "M.BCPI",
        "name": "BCPI Total — Monthly",
        "description": "Bank of Canada commodity price index, total (monthly)",
        "frequency": "monthly",
        "unit": "index",
        "cache_hours": 24,
        "group": "commodities",
    },
    "BCPI_ENERGY": {
        "series": "M.ENER",
        "name": "BCPI Energy — Monthly",
        "description": "Bank of Canada commodity price index, energy component (monthly)",
        "frequency": "monthly",
        "unit": "index",
        "cache_hours": 24,
        "group": "commodities",
    },
    "BCPI_METALS": {
        "series": "M.MTLS",
        "name": "BCPI Metals & Minerals — Monthly",
        "description": "Bank of Canada commodity price index, metals and minerals (monthly)",
        "frequency": "monthly",
        "unit": "index",
        "cache_hours": 24,
        "group": "commodities",
    },
}

GROUPS = {
    "policy_rates": "Policy & Overnight Rates",
    "bond_yields": "GoC Bond Yields",
    "tbill_yields": "Treasury Bill Yields",
    "money_market": "Money Market",
    "fx_rates": "Daily Exchange Rates (CAD)",
    "financial_conditions": "Financial Conditions & Term Premiums",
    "surveys": "Business Outlook Survey",
    "bank_rates": "Chartered Bank Posted Rates",
    "commodities": "Commodity Price Index (BCPI)",
}


# --- Cache ---

def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(".", "_")
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


# --- API ---

def _api_request(series: str, recent: int = 52) -> Dict:
    url = f"{BASE_URL}/observations/{series}/json"
    params = {"recent": recent}
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_observations(raw: Dict, series_key: str) -> List[Dict]:
    """Extract date/value pairs from Valet JSON response."""
    try:
        observations = raw.get("observations", [])
        results = []
        for obs in observations:
            date = obs.get("d")
            series_data = obs.get(series_key, {})
            val_str = series_data.get("v") if isinstance(series_data, dict) else None
            if date and val_str is not None:
                try:
                    results.append({"date": date, "value": float(val_str)})
                except (ValueError, TypeError):
                    continue
        results.sort(key=lambda x: x["date"], reverse=True)
        return results
    except (KeyError, TypeError):
        return []


# --- Public API ---

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    series = cfg["series"]
    cache_hours = cfg["cache_hours"]

    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, cache_hours)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    recent = 260 if cfg["frequency"] == "daily" else 60
    result = _api_request(series, recent=recent)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_observations(result["data"], series)
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
        "source": f"{BASE_URL}/observations/{series}",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_available_indicators() -> List[Dict]:
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "group": v["group"],
            "series": v["series"],
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
                "date": data["latest_date"],
                "unit": data["unit"],
                "group": data["group"],
            }
        else:
            errors.append({"indicator": key, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "source": "Bank of Canada Valet API",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Full GoC benchmark bond yield curve + T-bill front end."""
    maturities = [
        ("1M", "TBILL_1M"), ("3M", "TBILL_3M"), ("6M", "TBILL_6M"), ("1Y", "TBILL_1Y"),
        ("2Y", "GOC_2Y"), ("3Y", "GOC_3Y"), ("5Y", "GOC_5Y"),
        ("7Y", "GOC_7Y"), ("10Y", "GOC_10Y"), ("30Y", "GOC_LONG"),
    ]
    curve = []
    for label, key in maturities:
        data = fetch_data(key)
        if data.get("success"):
            curve.append({
                "maturity": label,
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


def get_fx_rates() -> Dict:
    """All 26 CAD FX pairs."""
    rates = {}
    for key, cfg in INDICATORS.items():
        if cfg["group"] != "fx_rates":
            continue
        data = fetch_data(key)
        if data.get("success"):
            pair = cfg["series"].replace("FX", "").replace("CAD", "") + "/CAD"
            rates[pair] = {
                "rate": data["latest_value"],
                "date": data["latest_date"],
                "change_pct": data.get("period_change_pct"),
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "pairs": rates,
        "count": len(rates),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Current BoC policy rates and money market rates."""
    rate_keys = ["OVERNIGHT_RATE", "BANK_RATE", "CORRA", "PRIME_RATE"]
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


# --- CLI ---

def _print_help():
    print(f"""
Bank of Canada Valet Enhanced Module (Initiative 0028)

Usage:
  python bank_of_canada_valet.py                      # Latest values for all indicators
  python bank_of_canada_valet.py <INDICATOR>           # Fetch specific indicator
  python bank_of_canada_valet.py list                  # List available indicators
  python bank_of_canada_valet.py yield-curve           # Full GoC yield curve
  python bank_of_canada_valet.py fx-rates              # All 26 FX pairs
  python bank_of_canada_valet.py policy-rates          # BoC policy & overnight rates
  python bank_of_canada_valet.py group <GROUP>         # Fetch all indicators in a group

Groups: {', '.join(GROUPS.keys())}

Indicators ({len(INDICATORS)} total):""")
    current_group = None
    for key, cfg in INDICATORS.items():
        if cfg["group"] != current_group:
            current_group = cfg["group"]
            print(f"\n  [{GROUPS.get(current_group, current_group)}]")
        print(f"    {key:<25s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: REST (JSON)
Coverage: Canada
Cache: 1h (FX), 24h (yields/rates/macro)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "yield-curve":
            print(json.dumps(get_yield_curve(), indent=2, default=str))
        elif cmd == "fx-rates":
            print(json.dumps(get_fx_rates(), indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        elif cmd == "group":
            group_name = sys.argv[2] if len(sys.argv) > 2 else None
            if not group_name or group_name not in GROUPS:
                print(f"Available groups: {', '.join(GROUPS.keys())}")
                sys.exit(1)
            results = {}
            errors = []
            for key, cfg in INDICATORS.items():
                if cfg["group"] != group_name:
                    continue
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
            print(json.dumps({"success": True, "group": group_name, "label": GROUPS[group_name],
                              "indicators": results, "errors": errors or None,
                              "count": len(results)}, indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        print("Fetching all indicators (this takes a moment)...")
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
