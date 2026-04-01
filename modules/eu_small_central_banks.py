#!/usr/bin/env python3
"""
EU Small Central Banks — Unified Data Module

Covers 9 smaller EU/Eurozone central banks that primarily offer file downloads:
Bulgaria (BNB), Croatia (HNB), Cyprus (CBC), Latvia (LB), Lithuania (LB),
Luxembourg (BCL), Malta (CBM), Slovakia (NBS), Slovenia (BSI).

Data Sources:
  - BNB  bnb.bg         — XML exchange rates (daily)
  - HNB  hnb.hr         — REST JSON API for FX rates (daily)
  - NBS  nbs.sk         — CSV exchange rates (daily)
  - BSI  bsi.si         — REST JSON API: FX, inflation, ECB rates
  - LB   lb.lt          — XML SOAP web service for FX rates (daily)
  - ECB  data-api.ecb.europa.eu — Country-level HICP, MFI interest rates (SDMX)

Auth: None (all open access)
Refresh: Daily (FX), Monthly (HICP, MFI rates)
Coverage: 9 EU countries, 47 indicators

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import csv
import json
import sys
import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, List, Optional
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache" / "eu_small_central_banks"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

ECB_BASE = "https://data-api.ecb.europa.eu/service/data"
HNB_BASE = "https://api.hnb.hr/tecajn-eur/v3"
BSI_BASE = "https://api.bsi.si"
LT_FX_URL = "https://www.lb.lt/webservices/FxRates/FxRates.asmx/getCurrentFxRates"
BNB_FX_URL = "https://www.bnb.bg/Statistics/StExternalSector/StExchangeRates/StERForeignCurrencies/index.htm"
NBS_FX_URL = "https://nbs.sk/export/sk/exchange-rate/latest/csv"

LT_XML_NS = {"fx": "http://www.lb.lt/WebServices/FxRates"}

COUNTRIES = {
    "BG": {"name": "Bulgaria", "bank": "Bulgarian National Bank (BNB)", "url": "https://www.bnb.bg"},
    "HR": {"name": "Croatia", "bank": "Croatian National Bank (HNB)", "url": "https://www.hnb.hr"},
    "CY": {"name": "Cyprus", "bank": "Central Bank of Cyprus (CBC)", "url": "https://www.centralbank.cy"},
    "LV": {"name": "Latvia", "bank": "Latvijas Banka", "url": "https://www.bank.lv"},
    "LT": {"name": "Lithuania", "bank": "Lietuvos bankas", "url": "https://www.lb.lt"},
    "LU": {"name": "Luxembourg", "bank": "Banque centrale du Luxembourg (BCL)", "url": "https://www.bcl.lu"},
    "MT": {"name": "Malta", "bank": "Central Bank of Malta (CBM)", "url": "https://www.centralbankmalta.org"},
    "SK": {"name": "Slovakia", "bank": "National Bank of Slovakia (NBS)", "url": "https://www.nbs.sk"},
    "SI": {"name": "Slovenia", "bank": "Banka Slovenije (BSI)", "url": "https://www.bsi.si"},
}

# ---------------------------------------------------------------------------
# Build INDICATORS dict
# ---------------------------------------------------------------------------
INDICATORS: Dict[str, Dict] = {}

# ECB SDMX indicators for all 9 countries (HICP + MFI rates)
for _cc, _info in COUNTRIES.items():
    INDICATORS[f"{_cc}_HICP"] = {
        "name": f"HICP Inflation — {_info['name']} (% YoY)",
        "description": f"Harmonised Index of Consumer Prices, annual rate of change, {_info['name']}",
        "unit": "% YoY",
        "frequency": "monthly",
        "source": "ecb_sdmx",
        "country": _cc,
        "params": {"dataflow": "ICP", "key": f"M.{_cc}.N.000000.4.ANR"},
    }
    INDICATORS[f"{_cc}_LENDING_RATE_HH"] = {
        "name": f"MFI Lending Rate HH Housing — {_info['name']} (%)",
        "description": f"MFI interest rate, new business loans to households for house purchase, {_info['name']}",
        "unit": "%",
        "frequency": "monthly",
        "source": "ecb_sdmx",
        "country": _cc,
        "params": {"dataflow": "MIR", "key": f"M.{_cc}.B.A2C.AM.R.A.2250.EUR.N"},
    }
    INDICATORS[f"{_cc}_DEPOSIT_RATE_HH"] = {
        "name": f"MFI Deposit Rate HH — {_info['name']} (%)",
        "description": f"MFI interest rate, deposits from households with agreed maturity ≤1yr, {_info['name']}",
        "unit": "%",
        "frequency": "monthly",
        "source": "ecb_sdmx",
        "country": _cc,
        "params": {"dataflow": "MIR", "key": f"M.{_cc}.B.L22.F.R.A.2250.EUR.N"},
    }

# Native FX rates for countries with their own APIs
_FX_CCYS = ("USD", "GBP", "CHF")
_FX_SOURCES = {
    "BG": ("bnb_xml", "BNB official"),
    "HR": ("hnb_json", "HNB official mid"),
    "LT": ("lt_xml", "Lietuvos bankas ECB reference"),
    "SK": ("nbs_csv", "NBS ECB reference"),
    "SI": ("bsi_fx", "Banka Slovenije daily"),
}
for _cc, (_src, _desc) in _FX_SOURCES.items():
    for _ccy in _FX_CCYS:
        INDICATORS[f"{_cc}_FX_{_ccy}"] = {
            "name": f"EUR/{_ccy} — {COUNTRIES[_cc]['name']}",
            "description": f"{_desc} exchange rate, {_ccy} per 1 EUR",
            "unit": f"{_ccy}/EUR",
            "frequency": "daily",
            "source": _src,
            "country": _cc,
            "params": {"currency": _ccy},
        }

# Slovenia extras: native inflation + ECB policy rates via BSI API
INDICATORS["SI_INFLATION_DOMESTIC"] = {
    "name": "Inflation — Slovenia (BSI, %)",
    "description": "Banka Slovenije published inflation rate for Slovenia",
    "unit": "%",
    "frequency": "monthly",
    "source": "bsi_inflation",
    "country": "SI",
    "params": {"type": "SI"},
}
INDICATORS["SI_INFLATION_EU"] = {
    "name": "Inflation — EU (BSI, %)",
    "description": "EU inflation rate published by Banka Slovenije",
    "unit": "%",
    "frequency": "monthly",
    "source": "bsi_inflation",
    "country": "SI",
    "params": {"type": "EU"},
}
INDICATORS["SI_ECB_DEPOSIT_RATE"] = {
    "name": "ECB Deposit Facility Rate (BSI, %)",
    "description": "ECB deposit facility rate via Banka Slovenije API",
    "unit": "%",
    "frequency": "as published",
    "source": "bsi_interests",
    "country": "SI",
    "params": {"field": "value_deposit"},
}
INDICATORS["SI_ECB_REFI_RATE"] = {
    "name": "ECB Main Refinancing Rate (BSI, %)",
    "description": "ECB main refinancing operations rate via Banka Slovenije API",
    "unit": "%",
    "frequency": "as published",
    "source": "bsi_interests",
    "country": "SI",
    "params": {"field": "value_operational"},
}
INDICATORS["SI_ECB_MARGINAL_RATE"] = {
    "name": "ECB Marginal Lending Rate (BSI, %)",
    "description": "ECB marginal lending facility rate via Banka Slovenije API",
    "unit": "%",
    "frequency": "as published",
    "source": "bsi_interests",
    "country": "SI",
    "params": {"field": "value_loan"},
}

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_path(indicator: str, params_hash: str) -> Path:
    safe = indicator.replace("/", "_").replace(":", "_")
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
# Source fetchers — each returns {"success": True, "rates": {...}, "date": ...}
#                   or {"success": False, "error": ...}
# ---------------------------------------------------------------------------

def _fetch_all_bnb_rates() -> Dict:
    """Bulgaria BNB — XML exchange rates."""
    cp = _cache_path("_src_bnb", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(
            BNB_FX_URL,
            params={"download": "xml", "search": "", "lang": "EN"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        rates, date_str = {}, None
        for row in root.findall("ROW"):
            code = row.findtext("CODE")
            rate_str = row.findtext("RATE")
            curr_date = row.findtext("CURR_DATE")
            if not code or not rate_str or code == "Code":
                continue
            try:
                rates[code] = float(rate_str)
                if curr_date and curr_date != "Date":
                    date_str = curr_date
            except ValueError:
                continue
        result = {"success": True, "rates": rates, "date": date_str, "source_url": BNB_FX_URL}
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_all_hnb_rates() -> Dict:
    """Croatia HNB — JSON REST API exchange rates."""
    cp = _cache_path("_src_hnb", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(HNB_BASE, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        rates, date_str = {}, None
        for entry in data:
            ccy = entry.get("valuta")
            mid = entry.get("srednji_tecaj", "")
            if isinstance(mid, str):
                mid = mid.replace(",", ".")
            dt = entry.get("datum_primjene")
            if ccy and mid:
                try:
                    rates[ccy] = float(mid)
                    if dt:
                        date_str = dt
                except ValueError:
                    continue
        result = {"success": True, "rates": rates, "date": date_str, "source_url": HNB_BASE}
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_all_lt_rates() -> Dict:
    """Lithuania Lietuvos bankas — XML SOAP web service FX rates."""
    cp = _cache_path("_src_lt", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(LT_FX_URL, params={"tp": "EU"}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        rates, date_str = {}, None
        for fx_rate in root.findall("fx:FxRate", LT_XML_NS):
            dt = fx_rate.findtext("fx:Dt", namespaces=LT_XML_NS)
            ccys = fx_rate.findall("fx:CcyAmt", LT_XML_NS)
            if len(ccys) < 2:
                continue
            ccy = ccys[1].findtext("fx:Ccy", namespaces=LT_XML_NS)
            amt = ccys[1].findtext("fx:Amt", namespaces=LT_XML_NS)
            if ccy and amt and ccy != "EUR":
                try:
                    rates[ccy] = float(amt)
                    if dt and not date_str:
                        date_str = dt
                except ValueError:
                    continue
        result = {"success": True, "rates": rates, "date": date_str, "source_url": LT_FX_URL}
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_nbs_value(val: str) -> float:
    """Parse NBS CSV value: strip quotes/spaces, swap comma→dot."""
    return float(val.strip().strip('"').replace("\xa0", "").replace(" ", "").replace(",", "."))


def _fetch_all_nbs_rates() -> Dict:
    """Slovakia NBS — CSV exchange rates."""
    cp = _cache_path("_src_nbs", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(NBS_FX_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        reader = csv.reader(StringIO(resp.text), delimiter=";")
        rows = list(reader)
        if len(rows) < 2:
            return {"success": False, "error": "Empty CSV from NBS"}
        headers = rows[0]
        values = rows[1]
        date_str = values[0].strip() if values else None
        rates = {}
        for i, hdr in enumerate(headers[1:], start=1):
            if i < len(values):
                try:
                    rates[hdr.strip()] = _parse_nbs_value(values[i])
                except (ValueError, IndexError):
                    continue
        result = {"success": True, "rates": rates, "date": date_str, "source_url": NBS_FX_URL}
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_all_bsi_fx() -> Dict:
    """Slovenia BSI — JSON REST API daily exchange rates."""
    cp = _cache_path("_src_bsi_fx", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(f"{BSI_BASE}/exchange/daily", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            return {"success": False, "error": body.get("error", "BSI API failure")}
        rates, date_str = {}, None
        for entry in body.get("data", []):
            code = entry.get("code")
            val = entry.get("value")
            dt = entry.get("date")
            if code and val is not None:
                rates[code] = float(val)
                if dt and not date_str:
                    date_str = dt
        result = {"success": True, "rates": rates, "date": date_str, "source_url": f"{BSI_BASE}/exchange/daily"}
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_bsi_inflation(type_code: str) -> Dict:
    """Slovenia BSI — JSON REST API inflation."""
    cp = _cache_path(f"_src_bsi_infl_{type_code}", _params_hash({"type": type_code}))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(f"{BSI_BASE}/inflation", params={"type": type_code}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            return {"success": False, "error": body.get("error", "BSI API failure")}
        data = body.get("data", [])
        if not data:
            return {"success": False, "error": "No inflation data returned"}
        entry = data[-1]
        result = {
            "success": True,
            "value": float(entry["value"]),
            "date": entry.get("date"),
            "source_url": f"{BSI_BASE}/inflation?type={type_code}",
        }
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_bsi_interests() -> Dict:
    """Slovenia BSI — JSON REST API ECB interest rates."""
    cp = _cache_path("_src_bsi_int", "latest")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached
    try:
        resp = requests.get(f"{BSI_BASE}/interests", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success"):
            return {"success": False, "error": body.get("error", "BSI API failure")}
        data = body.get("data", [])
        if not data:
            return {"success": False, "error": "No interest rate data returned"}
        entry = data[-1]
        result = {
            "success": True,
            "date": entry.get("date"),
            "value_deposit": entry.get("value_deposit"),
            "value_operational": entry.get("value_operational"),
            "value_loan": entry.get("value_loan"),
            "source_url": f"{BSI_BASE}/interests",
        }
        _write_cache(cp, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_ecb_sdmx(dataflow: str, key: str, last_n: int = 24) -> Dict:
    """Fetch from ECB SDMX REST API (SDMX-JSON 1.0)."""
    url = f"{ECB_BASE}/{dataflow}/{key}"
    headers = {"Accept": "application/json"}
    params = {"lastNObservations": last_n}
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
        if status == 404:
            return {"success": False, "error": "Series not found (HTTP 404)"}
        return {"success": False, "error": f"HTTP {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_ecb_sdmx(raw: Dict) -> List[Dict]:
    """Extract time-period/value pairs from ECB SDMX-JSON response."""
    try:
        datasets = raw.get("dataSets", [])
        structure = raw.get("structure", {})
        if not datasets:
            return []
        obs_dim = structure["dimensions"]["observation"][0]
        time_values = obs_dim["values"]
        results = []
        for _sk, series_data in datasets[0].get("series", {}).items():
            for obs_idx, obs_vals in series_data.get("observations", {}).items():
                idx = int(obs_idx)
                if idx < len(time_values) and obs_vals and obs_vals[0] is not None:
                    results.append({
                        "time_period": time_values[idx]["id"],
                        "value": float(obs_vals[0]),
                    })
        results.sort(key=lambda x: x["time_period"], reverse=True)
        return results
    except (KeyError, IndexError, TypeError, ValueError):
        return []


# ---------------------------------------------------------------------------
# Unified fetch dispatcher
# ---------------------------------------------------------------------------

def _build_fx_response(indicator: str, cfg: Dict, all_rates: Dict) -> Dict:
    """Build a standard indicator response from a bulk FX fetch."""
    if not all_rates.get("success"):
        return {
            "success": False, "indicator": indicator, "name": cfg["name"],
            "error": all_rates.get("error", "Fetch failed"),
        }
    ccy = cfg["params"]["currency"]
    rates = all_rates.get("rates", {})
    if ccy not in rates:
        return {
            "success": False, "indicator": indicator, "name": cfg["name"],
            "error": f"Currency {ccy} not found in source data (available: {list(rates.keys())[:10]})",
        }
    value = rates[ccy]
    date_str = all_rates.get("date", "")
    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "country": cfg["country"],
        "country_name": COUNTRIES[cfg["country"]]["name"],
        "latest_value": value,
        "latest_period": date_str,
        "data_points": [{"period": date_str, "value": value}],
        "total_observations": 1,
        "source": all_rates.get("source_url", ""),
        "timestamp": datetime.now().isoformat(),
    }


def _build_single_response(indicator: str, cfg: Dict, value: float, date_str: str, source_url: str) -> Dict:
    """Build a standard response for a single-value indicator."""
    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "country": cfg["country"],
        "country_name": COUNTRIES[cfg["country"]]["name"],
        "latest_value": value,
        "latest_period": date_str,
        "data_points": [{"period": date_str, "value": value}],
        "total_observations": 1,
        "source": source_url,
        "timestamp": datetime.now().isoformat(),
    }


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator by key."""
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
    result: Dict

    # --- FX sources (bulk fetch, extract currency) ---
    if source == "bnb_xml":
        result = _build_fx_response(indicator, cfg, _fetch_all_bnb_rates())
    elif source == "hnb_json":
        result = _build_fx_response(indicator, cfg, _fetch_all_hnb_rates())
    elif source == "lt_xml":
        result = _build_fx_response(indicator, cfg, _fetch_all_lt_rates())
    elif source == "nbs_csv":
        result = _build_fx_response(indicator, cfg, _fetch_all_nbs_rates())
    elif source == "bsi_fx":
        result = _build_fx_response(indicator, cfg, _fetch_all_bsi_fx())

    # --- BSI inflation ---
    elif source == "bsi_inflation":
        src = _fetch_bsi_inflation(cfg["params"]["type"])
        if not src.get("success"):
            result = {"success": False, "indicator": indicator, "name": cfg["name"], "error": src.get("error", "Fetch failed")}
        else:
            result = _build_single_response(indicator, cfg, src["value"], src.get("date", ""), src.get("source_url", ""))

    # --- BSI interest rates ---
    elif source == "bsi_interests":
        field = cfg["params"]["field"]
        src = _fetch_bsi_interests()
        if not src.get("success"):
            result = {"success": False, "indicator": indicator, "name": cfg["name"], "error": src.get("error", "Fetch failed")}
        else:
            val = src.get(field)
            if val is None:
                result = {"success": False, "indicator": indicator, "name": cfg["name"], "error": f"Field {field} missing from response"}
            else:
                result = _build_single_response(indicator, cfg, float(val), src.get("date", ""), src.get("source_url", ""))

    # --- ECB SDMX ---
    elif source == "ecb_sdmx":
        dataflow = cfg["params"]["dataflow"]
        key = cfg["params"]["key"]
        last_n = 24
        raw = _fetch_ecb_sdmx(dataflow, key, last_n=last_n)
        if not raw["success"]:
            result = {"success": False, "indicator": indicator, "name": cfg["name"], "error": raw["error"]}
        else:
            observations = _parse_ecb_sdmx(raw["data"])
            if not observations:
                result = {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}
            else:
                period_change = period_change_pct = None
                if len(observations) >= 2:
                    latest_v = observations[0]["value"]
                    prev_v = observations[1]["value"]
                    if prev_v and prev_v != 0:
                        period_change = round(latest_v - prev_v, 4)
                        period_change_pct = round((period_change / abs(prev_v)) * 100, 4)
                result = {
                    "success": True,
                    "indicator": indicator,
                    "name": cfg["name"],
                    "description": cfg["description"],
                    "unit": cfg["unit"],
                    "frequency": cfg["frequency"],
                    "country": cfg["country"],
                    "country_name": COUNTRIES[cfg["country"]]["name"],
                    "latest_value": observations[0]["value"],
                    "latest_period": observations[0]["time_period"],
                    "period_change": period_change,
                    "period_change_pct": period_change_pct,
                    "data_points": [{"period": o["time_period"], "value": o["value"]} for o in observations[:24]],
                    "total_observations": len(observations),
                    "source": f"{ECB_BASE}/{dataflow}/{key}",
                    "timestamp": datetime.now().isoformat(),
                }
    else:
        result = {"success": False, "indicator": indicator, "error": f"Unknown source: {source}"}

    if result.get("success"):
        _write_cache(cp, result)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_available_indicators(country: str = None) -> List[Dict]:
    """Return list of available indicators, optionally filtered by country."""
    items = []
    for k, v in INDICATORS.items():
        if country and v["country"] != country.upper():
            continue
        items.append({
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "source": v["source"],
            "country": v["country"],
        })
    return items


def get_latest(indicator: str = None, country: str = None) -> Dict:
    """Get latest values for one indicator, one country, or all."""
    if indicator:
        return fetch_data(indicator)

    targets = list(INDICATORS.keys())
    if country:
        cc = country.upper()
        targets = [k for k in targets if INDICATORS[k]["country"] == cc]

    if not targets:
        return {"success": False, "error": f"No indicators for country: {country}"}

    results = {}
    errors = []
    for key in targets:
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
        "source": "EU Small Central Banks (unified)",
        "country_filter": country.upper() if country else None,
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
EU Small Central Banks — Unified Data Module

Usage:
  python eu_small_central_banks.py                          Show this help
  python eu_small_central_banks.py list                     List all indicators
  python eu_small_central_banks.py list <COUNTRY>           List indicators for a country
  python eu_small_central_banks.py countries                List covered countries
  python eu_small_central_banks.py <COUNTRY>                Fetch all for a country
  python eu_small_central_banks.py <COUNTRY> <INDICATOR>    Fetch specific (e.g., BG HICP)
  python eu_small_central_banks.py <FULL_KEY>               Fetch by key (e.g., BG_HICP)

Countries:""")
    for cc, info in COUNTRIES.items():
        count = sum(1 for v in INDICATORS.values() if v["country"] == cc)
        print(f"  {cc}  {info['name']:<15s}  {info['bank']:<45s}  ({count} indicators)")
    print(f"\nTotal indicators: {len(INDICATORS)}")
    print("Sources: BNB XML, HNB JSON, NBS CSV, BSI REST, lb.lt XML, ECB SDMX\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        _print_help()

    elif args[0] == "list":
        country = args[1] if len(args) > 1 else None
        print(json.dumps(get_available_indicators(country), indent=2, default=str))

    elif args[0] == "countries":
        for cc, info in COUNTRIES.items():
            count = sum(1 for v in INDICATORS.values() if v["country"] == cc)
            print(f"{cc}  {info['name']:<15s}  {info['bank']}  ({count} indicators)")

    elif args[0].upper() in COUNTRIES and len(args) == 1:
        result = get_latest(country=args[0])
        print(json.dumps(result, indent=2, default=str))

    elif args[0].upper() in COUNTRIES and len(args) >= 2:
        key = f"{args[0].upper()}_{args[1].upper()}"
        result = fetch_data(key)
        print(json.dumps(result, indent=2, default=str))

    else:
        result = fetch_data(args[0])
        print(json.dumps(result, indent=2, default=str))
