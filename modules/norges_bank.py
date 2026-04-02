#!/usr/bin/env python3
"""
Norges Bank SDMX Module — Norway Central Bank Data

Exchange rates (40+ currency pairs vs NOK), key policy rate, NOWA interbank
reference rates, government bond yields, treasury bill rates, and trade-weighted
NOK indices. Norges Bank manages the $1.7T+ Government Pension Fund Global.

Data Source: https://data.norges-bank.no/api/data/
Protocol: SDMX REST 2.1 (SDMX-JSON)
Auth: None (open access)
Refresh: Daily (FX, rates), Per-decision (policy rate)
Coverage: Norway

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

BASE_URL = "https://data.norges-bank.no/api/data"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "norges_bank"
CACHE_TTL_FX = 1        # hours — FX and short rates
CACHE_TTL_RATES = 24    # hours — policy rate, bonds
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.25

# All 40+ currencies available: HUF DKK RUB MMK XDR TRY RON NZD JPY HKD CZK
# CAD BDT USD THB PLN AUD MYR INR IDR GBP CNY BRL VND BYN SGD PKR MXN ILS EUR
# CHF HRK BGN ISK ZAR TWD SEK PHP KRW — plus I44 and TWI indices

INDICATORS = {
    # --- Exchange Rates (EXR dataflow: B.{ccy}.NOK.SP) ---
    "FX_USD_NOK": {
        "dataflow": "EXR", "key": "B.USD.NOK.SP",
        "name": "USD/NOK Exchange Rate",
        "description": "US dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per USD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_EUR_NOK": {
        "dataflow": "EXR", "key": "B.EUR.NOK.SP",
        "name": "EUR/NOK Exchange Rate",
        "description": "Euro to Norwegian krone daily spot rate (most traded NOK pair)",
        "frequency": "daily", "unit": "NOK per EUR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_GBP_NOK": {
        "dataflow": "EXR", "key": "B.GBP.NOK.SP",
        "name": "GBP/NOK Exchange Rate",
        "description": "British pound to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per GBP", "cache_hours": CACHE_TTL_FX,
    },
    "FX_SEK_NOK": {
        "dataflow": "EXR", "key": "B.SEK.NOK.SP",
        "name": "SEK/NOK Exchange Rate",
        "description": "Swedish krona to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 SEK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_DKK_NOK": {
        "dataflow": "EXR", "key": "B.DKK.NOK.SP",
        "name": "DKK/NOK Exchange Rate",
        "description": "Danish krone to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 DKK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_CHF_NOK": {
        "dataflow": "EXR", "key": "B.CHF.NOK.SP",
        "name": "CHF/NOK Exchange Rate",
        "description": "Swiss franc to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per CHF", "cache_hours": CACHE_TTL_FX,
    },
    "FX_JPY_NOK": {
        "dataflow": "EXR", "key": "B.JPY.NOK.SP",
        "name": "JPY/NOK Exchange Rate",
        "description": "Japanese yen to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 JPY", "cache_hours": CACHE_TTL_FX,
    },
    "FX_CAD_NOK": {
        "dataflow": "EXR", "key": "B.CAD.NOK.SP",
        "name": "CAD/NOK Exchange Rate",
        "description": "Canadian dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per CAD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_AUD_NOK": {
        "dataflow": "EXR", "key": "B.AUD.NOK.SP",
        "name": "AUD/NOK Exchange Rate",
        "description": "Australian dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per AUD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_NZD_NOK": {
        "dataflow": "EXR", "key": "B.NZD.NOK.SP",
        "name": "NZD/NOK Exchange Rate",
        "description": "New Zealand dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per NZD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_CNY_NOK": {
        "dataflow": "EXR", "key": "B.CNY.NOK.SP",
        "name": "CNY/NOK Exchange Rate",
        "description": "Chinese yuan to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per CNY", "cache_hours": CACHE_TTL_FX,
    },
    "FX_PLN_NOK": {
        "dataflow": "EXR", "key": "B.PLN.NOK.SP",
        "name": "PLN/NOK Exchange Rate",
        "description": "Polish zloty to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per PLN", "cache_hours": CACHE_TTL_FX,
    },
    "FX_HKD_NOK": {
        "dataflow": "EXR", "key": "B.HKD.NOK.SP",
        "name": "HKD/NOK Exchange Rate",
        "description": "Hong Kong dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per HKD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_SGD_NOK": {
        "dataflow": "EXR", "key": "B.SGD.NOK.SP",
        "name": "SGD/NOK Exchange Rate",
        "description": "Singapore dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per SGD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_KRW_NOK": {
        "dataflow": "EXR", "key": "B.KRW.NOK.SP",
        "name": "KRW/NOK Exchange Rate",
        "description": "South Korean won to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 KRW", "cache_hours": CACHE_TTL_FX,
    },
    "FX_TRY_NOK": {
        "dataflow": "EXR", "key": "B.TRY.NOK.SP",
        "name": "TRY/NOK Exchange Rate",
        "description": "Turkish lira to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per TRY", "cache_hours": CACHE_TTL_FX,
    },
    "FX_INR_NOK": {
        "dataflow": "EXR", "key": "B.INR.NOK.SP",
        "name": "INR/NOK Exchange Rate",
        "description": "Indian rupee to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 INR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_BRL_NOK": {
        "dataflow": "EXR", "key": "B.BRL.NOK.SP",
        "name": "BRL/NOK Exchange Rate",
        "description": "Brazilian real to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per BRL", "cache_hours": CACHE_TTL_FX,
    },
    "FX_MXN_NOK": {
        "dataflow": "EXR", "key": "B.MXN.NOK.SP",
        "name": "MXN/NOK Exchange Rate",
        "description": "Mexican peso to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per MXN", "cache_hours": CACHE_TTL_FX,
    },
    "FX_ZAR_NOK": {
        "dataflow": "EXR", "key": "B.ZAR.NOK.SP",
        "name": "ZAR/NOK Exchange Rate",
        "description": "South African rand to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per ZAR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_THB_NOK": {
        "dataflow": "EXR", "key": "B.THB.NOK.SP",
        "name": "THB/NOK Exchange Rate",
        "description": "Thai baht to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 THB", "cache_hours": CACHE_TTL_FX,
    },
    "FX_CZK_NOK": {
        "dataflow": "EXR", "key": "B.CZK.NOK.SP",
        "name": "CZK/NOK Exchange Rate",
        "description": "Czech koruna to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per CZK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_HUF_NOK": {
        "dataflow": "EXR", "key": "B.HUF.NOK.SP",
        "name": "HUF/NOK Exchange Rate",
        "description": "Hungarian forint to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 HUF", "cache_hours": CACHE_TTL_FX,
    },
    "FX_ISK_NOK": {
        "dataflow": "EXR", "key": "B.ISK.NOK.SP",
        "name": "ISK/NOK Exchange Rate",
        "description": "Icelandic krona to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 ISK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_ILS_NOK": {
        "dataflow": "EXR", "key": "B.ILS.NOK.SP",
        "name": "ILS/NOK Exchange Rate",
        "description": "Israeli shekel to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per ILS", "cache_hours": CACHE_TTL_FX,
    },
    "FX_RON_NOK": {
        "dataflow": "EXR", "key": "B.RON.NOK.SP",
        "name": "RON/NOK Exchange Rate",
        "description": "Romanian leu to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per RON", "cache_hours": CACHE_TTL_FX,
    },
    "FX_TWD_NOK": {
        "dataflow": "EXR", "key": "B.TWD.NOK.SP",
        "name": "TWD/NOK Exchange Rate",
        "description": "Taiwan dollar to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per TWD", "cache_hours": CACHE_TTL_FX,
    },
    "FX_PHP_NOK": {
        "dataflow": "EXR", "key": "B.PHP.NOK.SP",
        "name": "PHP/NOK Exchange Rate",
        "description": "Philippine peso to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per PHP", "cache_hours": CACHE_TTL_FX,
    },
    "FX_IDR_NOK": {
        "dataflow": "EXR", "key": "B.IDR.NOK.SP",
        "name": "IDR/NOK Exchange Rate",
        "description": "Indonesian rupiah to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per IDR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_MYR_NOK": {
        "dataflow": "EXR", "key": "B.MYR.NOK.SP",
        "name": "MYR/NOK Exchange Rate",
        "description": "Malaysian ringgit to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per MYR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_PKR_NOK": {
        "dataflow": "EXR", "key": "B.PKR.NOK.SP",
        "name": "PKR/NOK Exchange Rate",
        "description": "Pakistani rupee to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 PKR", "cache_hours": CACHE_TTL_FX,
    },
    "FX_VND_NOK": {
        "dataflow": "EXR", "key": "B.VND.NOK.SP",
        "name": "VND/NOK Exchange Rate",
        "description": "Vietnamese dong to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per VND", "cache_hours": CACHE_TTL_FX,
    },
    "FX_BDT_NOK": {
        "dataflow": "EXR", "key": "B.BDT.NOK.SP",
        "name": "BDT/NOK Exchange Rate",
        "description": "Bangladeshi taka to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per BDT", "cache_hours": CACHE_TTL_FX,
    },
    "FX_BGN_NOK": {
        "dataflow": "EXR", "key": "B.BGN.NOK.SP",
        "name": "BGN/NOK Exchange Rate",
        "description": "Bulgarian lev to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per BGN", "cache_hours": CACHE_TTL_FX,
    },
    "FX_MMK_NOK": {
        "dataflow": "EXR", "key": "B.MMK.NOK.SP",
        "name": "MMK/NOK Exchange Rate",
        "description": "Myanmar kyat to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per MMK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_RUB_NOK": {
        "dataflow": "EXR", "key": "B.RUB.NOK.SP",
        "name": "RUB/NOK Exchange Rate",
        "description": "Russian ruble to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per 100 RUB", "cache_hours": CACHE_TTL_FX,
    },
    "FX_BYN_NOK": {
        "dataflow": "EXR", "key": "B.BYN.NOK.SP",
        "name": "BYN/NOK Exchange Rate",
        "description": "Belarusian ruble to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per BYN", "cache_hours": CACHE_TTL_FX,
    },
    "FX_HRK_NOK": {
        "dataflow": "EXR", "key": "B.HRK.NOK.SP",
        "name": "HRK/NOK Exchange Rate",
        "description": "Croatian kuna to Norwegian krone daily spot rate",
        "frequency": "daily", "unit": "NOK per HRK", "cache_hours": CACHE_TTL_FX,
    },
    "FX_XDR_NOK": {
        "dataflow": "EXR", "key": "B.XDR.NOK.SP",
        "name": "XDR/NOK (IMF SDR) Exchange Rate",
        "description": "IMF Special Drawing Rights to Norwegian krone daily rate",
        "frequency": "daily", "unit": "NOK per XDR", "cache_hours": CACHE_TTL_FX,
    },

    # --- Trade-Weighted Indices (EXR dataflow) ---
    "I44_INDEX": {
        "dataflow": "EXR", "key": "B.I44.NOK.SP",
        "name": "I44 Import-Weighted NOK Index",
        "description": "Import-weighted effective exchange rate index (44 trading partners)",
        "frequency": "daily", "unit": "Index", "cache_hours": CACHE_TTL_FX,
    },
    "TWI_INDEX": {
        "dataflow": "EXR", "key": "B.TWI.NOK.SP",
        "name": "TWI Trade-Weighted NOK Index",
        "description": "Trade-weighted exchange rate index for Norwegian krone",
        "frequency": "daily", "unit": "Index", "cache_hours": CACHE_TTL_FX,
    },

    # --- Norges Bank Policy Rates (IR dataflow: B.KPRA.{tenor}.R) ---
    "POLICY_RATE": {
        "dataflow": "IR", "key": "B.KPRA.SD.R",
        "name": "Key Policy Rate (Sight Deposit Rate)",
        "description": "Norges Bank key policy rate — the sight deposit rate, primary monetary policy tool",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_RATES,
    },
    "OVERNIGHT_LENDING_RATE": {
        "dataflow": "IR", "key": "B.KPRA.OL.R",
        "name": "Overnight Lending Rate",
        "description": "Norges Bank overnight lending rate (D-loan rate), ceiling of interest rate corridor",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_RATES,
    },
    "RESERVE_RATE": {
        "dataflow": "IR", "key": "B.KPRA.RR.R",
        "name": "Reserve Rate",
        "description": "Norges Bank reserve rate on deposits above quota, floor of interest rate corridor",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_RATES,
    },

    # --- NOWA Interbank Reference Rates (SHORT_RATES dataflow) ---
    "NOWA": {
        "dataflow": "SHORT_RATES", "key": "B.NOWA.ON.R",
        "name": "NOWA Overnight Rate",
        "description": "Norwegian Overnight Weighted Average — primary NOK interbank reference rate",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_FX,
    },
    "NOWA_AVG_1M": {
        "dataflow": "SHORT_RATES", "key": "B.NOWA_AVERAGE.1M.R",
        "name": "NOWA 1-Month Average",
        "description": "1-month compounded average of NOWA overnight rate",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_FX,
    },
    "NOWA_AVG_3M": {
        "dataflow": "SHORT_RATES", "key": "B.NOWA_AVERAGE.3M.R",
        "name": "NOWA 3-Month Average",
        "description": "3-month compounded average of NOWA overnight rate",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_FX,
    },
    "NOWA_AVG_6M": {
        "dataflow": "SHORT_RATES", "key": "B.NOWA_AVERAGE.6M.R",
        "name": "NOWA 6-Month Average",
        "description": "6-month compounded average of NOWA overnight rate",
        "frequency": "daily", "unit": "% p.a.", "cache_hours": CACHE_TTL_FX,
    },

    # --- Norwegian Government Bond Yields (GOVT_GENERIC_RATES dataflow) ---
    "GOVT_BOND_3Y": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.3Y.GBON",
        "name": "Norwegian Govt Bond Yield 3Y (%)",
        "description": "Generic yield on Norwegian government bond nearest to 3-year maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
    "GOVT_BOND_5Y": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.5Y.GBON",
        "name": "Norwegian Govt Bond Yield 5Y (%)",
        "description": "Generic yield on Norwegian government bond nearest to 5-year maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
    "GOVT_BOND_7Y": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.7Y.GBON",
        "name": "Norwegian Govt Bond Yield 7Y (%)",
        "description": "Generic yield on Norwegian government bond nearest to 7-year maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
    "GOVT_BOND_10Y": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.10Y.GBON",
        "name": "Norwegian Govt Bond Yield 10Y (%)",
        "description": "Generic yield on Norwegian government bond nearest to 10-year maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },

    # --- Norwegian Treasury Bill Rates (GOVT_GENERIC_RATES dataflow) ---
    "TBILL_3M": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.3M.TBIL",
        "name": "Norwegian T-Bill Rate 3M (%)",
        "description": "Generic yield on Norwegian treasury bill nearest to 3-month maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
    "TBILL_6M": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.6M.TBIL",
        "name": "Norwegian T-Bill Rate 6M (%)",
        "description": "Generic yield on Norwegian treasury bill nearest to 6-month maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
    "TBILL_12M": {
        "dataflow": "GOVT_GENERIC_RATES", "key": "B.12M.TBIL",
        "name": "Norwegian T-Bill Rate 12M (%)",
        "description": "Generic yield on Norwegian treasury bill nearest to 12-month maturity",
        "frequency": "daily", "unit": "%", "cache_hours": CACHE_TTL_FX,
    },
}

# Mapping of currency codes for the fx_all and fx <CCY> commands
ALL_FX_CURRENCIES = [
    "USD", "EUR", "GBP", "SEK", "DKK", "CHF", "JPY", "CAD", "AUD", "NZD",
    "CNY", "PLN", "HKD", "SGD", "KRW", "TRY", "INR", "BRL", "MXN", "ZAR",
    "THB", "CZK", "HUF", "ISK", "ILS", "RON", "TWD", "PHP", "IDR", "MYR",
    "PKR", "VND", "BDT", "BGN", "MMK", "RUB", "BYN", "HRK", "XDR",
]


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


def _parse_sdmx_json(raw: Dict) -> List[Dict]:
    """Parse Norges Bank SDMX-JSON response into time-period/value pairs.

    Norges Bank returns observation values as strings (e.g. "9.6579"), with
    TIME_PERIOD in the observation dimension. Multiple series may be returned
    with dimension metadata encoded in the series key indices.
    """
    try:
        structure = raw["data"]["structure"]
        datasets = raw["data"]["dataSets"]
        if not datasets:
            return []

        obs_dim = structure["dimensions"]["observation"][0]
        time_values = obs_dim["values"]

        series_dims = structure["dimensions"]["series"]

        results = []
        for series_key, series_data in datasets[0].get("series", {}).items():
            dim_indices = [int(x) for x in series_key.split(":")]
            meta = {}
            for i, idx in enumerate(dim_indices):
                if i < len(series_dims):
                    dim = series_dims[i]
                    if idx < len(dim["values"]):
                        val_obj = dim["values"][idx]
                        meta[dim["id"].lower()] = val_obj["id"]
                        if dim["id"] in ("BASE_CUR", "INSTRUMENT_TYPE", "TENOR"):
                            meta[f"{dim['id'].lower()}_name"] = val_obj.get("name", val_obj["id"])

            for obs_idx_str, obs_vals in series_data.get("observations", {}).items():
                obs_idx = int(obs_idx_str)
                if obs_idx >= len(time_values) or not obs_vals:
                    continue
                raw_val = obs_vals[0]
                if raw_val is None:
                    continue
                try:
                    value = float(raw_val)
                except (ValueError, TypeError):
                    continue
                results.append({
                    "time_period": time_values[obs_idx]["id"],
                    "value": value,
                    **meta,
                })

        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


def _api_request(dataflow: str, key: str, last_n: Optional[int] = None,
                 start_period: Optional[str] = None, end_period: Optional[str] = None) -> Dict:
    url = f"{BASE_URL}/{dataflow}/{key}"
    params = {"format": "sdmx-json"}
    if last_n:
        params["lastNObservations"] = last_n
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.json()}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except requests.ConnectionError:
        return {"success": False, "error": "Connection failed"}
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = {}
        try:
            body = e.response.json()
        except Exception:
            pass
        msg = body.get("errors", [{}])[0].get("message", "") if body.get("errors") else ""
        if status == 404:
            return {"success": False, "error": f"Series not found (HTTP 404): {msg}".strip(": ")}
        return {"success": False, "error": f"HTTP {status}: {msg}".strip(": ")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}",
                "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, cfg.get("cache_hours", CACHE_TTL_FX))
    if cached:
        cached.pop("_cached_at", None)
        return cached

    last_n = 260 if cfg["frequency"] == "daily" else 60
    result = _api_request(cfg["dataflow"], cfg["key"],
                          last_n=last_n if not start_date else None,
                          start_period=start_date, end_period=end_date)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_sdmx_json(result["data"])
    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"],
                "error": "No observations returned"}

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
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['dataflow']}/{cfg['key']}",
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
            "dataflow": v["dataflow"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all key indicators (summary mode)."""
    if indicator:
        return fetch_data(indicator)

    summary_keys = [
        "FX_USD_NOK", "FX_EUR_NOK", "FX_GBP_NOK", "FX_SEK_NOK", "FX_DKK_NOK",
        "I44_INDEX", "POLICY_RATE", "NOWA", "NOWA_AVG_3M",
        "GOVT_BOND_10Y", "TBILL_3M",
    ]
    results = {}
    errors = []
    for key in summary_keys:
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
        "source": "Norges Bank SDMX API",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_rate(currency: str) -> Dict:
    """Get exchange rate for a specific currency against NOK."""
    currency = currency.upper()
    indicator_key = f"FX_{currency}_NOK"
    if indicator_key in INDICATORS:
        return fetch_data(indicator_key)

    if currency not in ALL_FX_CURRENCIES:
        return {"success": False, "error": f"Unknown currency: {currency}",
                "available": ALL_FX_CURRENCIES}

    result = _api_request("EXR", f"B.{currency}.NOK.SP", last_n=30)
    if not result["success"]:
        return {"success": False, "error": result["error"], "currency_pair": f"{currency}/NOK"}

    observations = _parse_sdmx_json(result["data"])
    if not observations:
        return {"success": False, "error": "No observations", "currency_pair": f"{currency}/NOK"}

    return {
        "success": True,
        "currency_pair": f"{currency}/NOK",
        "latest_value": observations[0]["value"],
        "latest_period": observations[0]["time_period"],
        "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:30]],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/EXR/B.{currency}.NOK.SP",
        "timestamp": datetime.now().isoformat(),
    }


def get_fx_all() -> Dict:
    """Get latest exchange rates for all 40+ currency pairs against NOK."""
    cache_params = {"command": "fx_all"}
    cp = _cache_path("fx_all", _params_hash(cache_params))
    cached = _read_cache(cp, CACHE_TTL_FX)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request("EXR", "B..NOK.SP", last_n=1)
    if not result["success"]:
        return {"success": False, "error": result["error"]}

    observations = _parse_sdmx_json(result["data"])
    if not observations:
        return {"success": False, "error": "No observations returned"}

    rates = {}
    for obs in observations:
        ccy = obs.get("base_cur", "UNKNOWN")
        rates[f"{ccy}/NOK"] = {
            "currency": ccy,
            "currency_name": obs.get("base_cur_name", ccy),
            "rate": obs["value"],
            "date": obs["time_period"],
        }

    response = {
        "success": True,
        "rates": rates,
        "count": len(rates),
        "source": f"{BASE_URL}/EXR/B..NOK.SP",
        "timestamp": datetime.now().isoformat(),
    }

    _write_cache(cp, response)
    return response


def get_policy_rate() -> Dict:
    """Get Norges Bank key policy rate history and corridor rates."""
    rates = {}
    rate_keys = ["POLICY_RATE", "OVERNIGHT_LENDING_RATE", "RESERVE_RATE"]
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
                "data_points": data.get("data_points", [])[:20],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


def get_nowa() -> Dict:
    """Get NOWA term structure (overnight, 1M, 3M, 6M averages)."""
    nowa_keys = ["NOWA", "NOWA_AVG_1M", "NOWA_AVG_3M", "NOWA_AVG_6M"]
    rates = {}
    for key in nowa_keys:
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
        "term_structure": rates,
        "count": len(rates),
        "timestamp": datetime.now().isoformat(),
    }


def get_i44() -> Dict:
    """Get I44 import-weighted NOK index and TWI trade-weighted index."""
    indices = {}
    for key in ["I44_INDEX", "TWI_INDEX"]:
        data = fetch_data(key)
        if data.get("success"):
            indices[key] = {
                "name": data["name"],
                "value": data["latest_value"],
                "period": data["latest_period"],
                "data_points": data.get("data_points", [])[:30],
            }
        time.sleep(REQUEST_DELAY)

    return {
        "success": bool(indices),
        "indices": indices,
        "timestamp": datetime.now().isoformat(),
    }


def get_govt_bonds() -> Dict:
    """Get Norwegian government bond yield curve and treasury bill rates."""
    bond_keys = ["TBILL_3M", "TBILL_6M", "TBILL_12M",
                 "GOVT_BOND_3Y", "GOVT_BOND_5Y", "GOVT_BOND_7Y", "GOVT_BOND_10Y"]
    curve = []
    for key in bond_keys:
        data = fetch_data(key)
        if data.get("success"):
            label = key.replace("GOVT_BOND_", "").replace("TBILL_", "T-")
            curve.append({
                "maturity": label,
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
                "indicator": key,
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
    print("""
Norges Bank SDMX Module — Norway Central Bank Data

Usage:
  python norges_bank.py                          # Latest key rates summary
  python norges_bank.py fx USD                   # USD/NOK exchange rate
  python norges_bank.py fx EUR                   # EUR/NOK exchange rate
  python norges_bank.py fx_all                   # All currency pairs latest
  python norges_bank.py policy_rate              # Key policy rate & corridor
  python norges_bank.py nowa                     # NOWA term structure
  python norges_bank.py i44                      # Trade-weighted NOK indices
  python norges_bank.py govt_bonds               # Govt bond yield curve
  python norges_bank.py <INDICATOR>              # Fetch specific indicator
  python norges_bank.py list                     # List all indicators

Key Indicators:
  FX_USD_NOK, FX_EUR_NOK, FX_GBP_NOK     Exchange rates vs NOK
  I44_INDEX, TWI_INDEX                     Trade-weighted NOK indices
  POLICY_RATE                              Key policy rate (sight deposit)
  NOWA, NOWA_AVG_3M                        Interbank reference rates
  GOVT_BOND_10Y, TBILL_3M                  Government bond/bill yields
""")
    print(f"Source: {BASE_URL}")
    print("Protocol: SDMX 2.1 REST (JSON)")
    print(f"Coverage: Norway — {len(INDICATORS)} indicators, {len(ALL_FX_CURRENCIES)} currency pairs")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "fx":
            if len(sys.argv) > 2:
                print(json.dumps(get_fx_rate(sys.argv[2]), indent=2, default=str))
            else:
                print(json.dumps({"error": "Usage: norges_bank.py fx <CURRENCY>",
                                  "example": "norges_bank.py fx USD",
                                  "available": ALL_FX_CURRENCIES}, indent=2))
        elif cmd == "fx_all":
            print(json.dumps(get_fx_all(), indent=2, default=str))
        elif cmd == "policy_rate":
            print(json.dumps(get_policy_rate(), indent=2, default=str))
        elif cmd == "nowa":
            print(json.dumps(get_nowa(), indent=2, default=str))
        elif cmd == "nibor":
            print(json.dumps(get_nowa(), indent=2, default=str))
        elif cmd == "i44":
            print(json.dumps(get_i44(), indent=2, default=str))
        elif cmd == "govt_bonds":
            print(json.dumps(get_govt_bonds(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
