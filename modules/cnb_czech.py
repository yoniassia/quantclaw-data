#!/usr/bin/env python3
"""
Czech National Bank (CNB) Module — Phase 1

CZK daily FX fixing, PRIBOR interbank rates, and CNB official policy rates
(2W repo, discount, Lombard). Optional ARAD time-series API for deeper data.

Data Sources:
  - FX fixing:    https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/
  - PRIBOR:       https://www.cnb.cz/en/financial-markets/money-market/pribor/
  - Policy rates: https://www.cnb.cz/en/monetary-policy/instruments/
  - ARAD API:     https://www.cnb.cz/aradb/api/v1 (requires free API key)

Protocol: REST TXT/CSV (open feeds), REST JSON (ARAD w/ key)
Auth: Open for FX/PRIBOR/policy-rate feeds; ARAD requires ARAD_API_KEY env var
Refresh: Daily (FX, PRIBOR), static history (policy rates)
Coverage: Czech Republic

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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FX_DAILY_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt"
)
FX_YEAR_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/year.txt"
)
PRIBOR_DAILY_URL = (
    "https://www.cnb.cz/en/financial-markets/money-market/pribor/"
    "fixing-of-interest-rates-on-interbank-deposits-pribor/daily.txt"
)
PRIBOR_YEAR_URL = (
    "https://www.cnb.cz/en/financial-markets/money-market/pribor/"
    "fixing-of-interest-rates-on-interbank-deposits-pribor/year.txt"
)
POLICY_RATE_URLS = {
    "2W_REPO": "https://www.cnb.cz/en/faq/.galleries/development_of_the_cnb_2w_repo_rate.txt",
    "DISCOUNT": "https://www.cnb.cz/en/faq/.galleries/development_of_the_cnb_discount_rate.txt",
    "LOMBARD": "https://www.cnb.cz/en/faq/.galleries/development_of_the_cnb_lombard_rate.txt",
}
ARAD_BASE_URL = "https://www.cnb.cz/aradb/api/v1"

CACHE_DIR = Path(__file__).parent.parent / "cache" / "cnb_czech"
CACHE_TTL_FX = 1       # hours
CACHE_TTL_PRIBOR = 1   # hours
CACHE_TTL_POLICY = 24  # hours
CACHE_TTL_ARAD = 24    # hours
REQUEST_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

INDICATORS = {
    # --- FX Daily Fixing (CZK per unit, daily) ---
    "FX_USD": {
        "source": "fx", "code": "USD", "amount": 1,
        "name": "CZK/USD Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 USD",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_EUR": {
        "source": "fx", "code": "EUR", "amount": 1,
        "name": "CZK/EUR Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 EUR",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_GBP": {
        "source": "fx", "code": "GBP", "amount": 1,
        "name": "CZK/GBP Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 GBP",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_CHF": {
        "source": "fx", "code": "CHF", "amount": 1,
        "name": "CZK/CHF Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 CHF",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_JPY": {
        "source": "fx", "code": "JPY", "amount": 100,
        "name": "CZK/JPY Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 100 JPY",
        "frequency": "daily", "unit": "CZK/100",
    },
    "FX_CAD": {
        "source": "fx", "code": "CAD", "amount": 1,
        "name": "CZK/CAD Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 CAD",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_AUD": {
        "source": "fx", "code": "AUD", "amount": 1,
        "name": "CZK/AUD Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 AUD",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_PLN": {
        "source": "fx", "code": "PLN", "amount": 1,
        "name": "CZK/PLN Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 PLN",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_HUF": {
        "source": "fx", "code": "HUF", "amount": 100,
        "name": "CZK/HUF Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 100 HUF",
        "frequency": "daily", "unit": "CZK/100",
    },
    "FX_SEK": {
        "source": "fx", "code": "SEK", "amount": 1,
        "name": "CZK/SEK Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 SEK",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_NOK": {
        "source": "fx", "code": "NOK", "amount": 1,
        "name": "CZK/NOK Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 NOK",
        "frequency": "daily", "unit": "CZK",
    },
    "FX_CNY": {
        "source": "fx", "code": "CNY", "amount": 1,
        "name": "CZK/CNY Daily Fixing",
        "description": "CNB official daily fixing rate, CZK per 1 CNY",
        "frequency": "daily", "unit": "CZK",
    },
    # --- PRIBOR Interbank Rates (daily, 48h delayed) ---
    "PRIBOR_1D": {
        "source": "pribor", "term": "1 day",
        "name": "PRIBOR Overnight (% p.a.)",
        "description": "Prague Interbank Offered Rate, 1-day maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_1W": {
        "source": "pribor", "term": "1 week",
        "name": "PRIBOR 1 Week (% p.a.)",
        "description": "Prague Interbank Offered Rate, 1-week maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_2W": {
        "source": "pribor", "term": "2 weeks",
        "name": "PRIBOR 2 Weeks (% p.a.)",
        "description": "Prague Interbank Offered Rate, 2-week maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_1M": {
        "source": "pribor", "term": "1 month",
        "name": "PRIBOR 1 Month (% p.a.)",
        "description": "Prague Interbank Offered Rate, 1-month maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_3M": {
        "source": "pribor", "term": "3 months",
        "name": "PRIBOR 3 Months (% p.a.)",
        "description": "Prague Interbank Offered Rate, 3-month maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_6M": {
        "source": "pribor", "term": "6 months",
        "name": "PRIBOR 6 Months (% p.a.)",
        "description": "Prague Interbank Offered Rate, 6-month maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "PRIBOR_1Y": {
        "source": "pribor", "term": "1 year",
        "name": "PRIBOR 1 Year (% p.a.)",
        "description": "Prague Interbank Offered Rate, 1-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    # --- CNB Official Policy Rates (event-driven) ---
    "CNB_2W_REPO": {
        "source": "policy", "rate_key": "2W_REPO",
        "name": "CNB 2-Week Repo Rate (%)",
        "description": "CNB main monetary-policy rate, upper limit for 2W repo operations",
        "frequency": "event", "unit": "%",
    },
    "CNB_DISCOUNT": {
        "source": "policy", "rate_key": "DISCOUNT",
        "name": "CNB Discount Rate (%)",
        "description": "CNB discount rate, lower bound of the interest-rate corridor",
        "frequency": "event", "unit": "%",
    },
    "CNB_LOMBARD": {
        "source": "policy", "rate_key": "LOMBARD",
        "name": "CNB Lombard Rate (%)",
        "description": "CNB Lombard (marginal lending) rate, upper bound of the corridor",
        "frequency": "event", "unit": "%",
    },
}

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

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


def _parse_dd_mm_yyyy(s: str) -> str:
    """Convert DD.MM.YYYY to YYYY-MM-DD for proper sorting."""
    try:
        parts = s.strip().split(".")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except (ValueError, IndexError):
        pass
    return s


def _parse_pribor_date(s: str) -> str:
    """Convert 'DD Mon YYYY' to YYYY-MM-DD for sorting."""
    try:
        dt = datetime.strptime(s.strip(), "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return s


def _strip_cache_meta(d: Dict) -> Dict:
    d.pop("_cached_at", None)
    return d


def _ttl_for(indicator_cfg: dict) -> int:
    src = indicator_cfg["source"]
    if src == "fx":
        return CACHE_TTL_FX
    if src == "pribor":
        return CACHE_TTL_PRIBOR
    if src == "policy":
        return CACHE_TTL_POLICY
    return CACHE_TTL_ARAD

# ---------------------------------------------------------------------------
# FX feed parser
# ---------------------------------------------------------------------------

def _fetch_fx_daily(date_str: str = None) -> Dict:
    """Fetch the CNB daily FX fixing TXT feed. Returns {code: {rate, amount, date}}."""
    url = FX_DAILY_URL
    params = {}
    if date_str:
        params["date"] = date_str
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

    lines = text.split("\n")
    if len(lines) < 3:
        return {"success": False, "error": "Unexpected FX feed format"}

    date_line = lines[0].strip()
    rates = {}
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) != 5:
            continue
        country, currency, amount, code, rate_str = [p.strip() for p in parts]
        try:
            rates[code] = {
                "rate": float(rate_str),
                "amount": int(amount),
                "country": country,
                "currency": currency,
            }
        except ValueError:
            continue

    return {"success": True, "date": date_line, "rates": rates}


def _fetch_fx_year(year: int) -> List[Dict]:
    """Fetch yearly FX data. Returns list of {date, code, rate} dicts."""
    try:
        resp = requests.get(FX_YEAR_URL, params={"year": year}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
    except requests.RequestException as e:
        return []

    lines = text.split("\n")
    if len(lines) < 2:
        return []

    header = lines[0]
    header_parts = header.split("|")
    code_map = {}
    for i, h in enumerate(header_parts):
        if i == 0:
            continue
        h = h.strip()
        if not h:
            continue
        parts = h.split()
        if len(parts) >= 2:
            amount = int(parts[0])
            code = parts[1]
        else:
            amount = 1
            code = h
        code_map[i] = (code, amount)

    results = []
    for line in lines[1:]:
        cols = line.split("|")
        if len(cols) < 2:
            continue
        raw_date = cols[0].strip()
        for idx, (code, amount) in code_map.items():
            if idx < len(cols) and cols[idx].strip():
                try:
                    results.append({
                        "date": raw_date,
                        "code": code,
                        "amount": amount,
                        "rate": float(cols[idx].strip()),
                    })
                except ValueError:
                    continue

    return results

# ---------------------------------------------------------------------------
# PRIBOR feed parser
# ---------------------------------------------------------------------------

def _fetch_pribor_daily(date_str: str = None) -> Dict:
    """Fetch daily PRIBOR rates. Returns {term: rate}."""
    url = PRIBOR_DAILY_URL
    params = {}
    if date_str:
        params["date"] = date_str
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

    lines = text.split("\n")
    if len(lines) < 3:
        return {"success": False, "error": "Unexpected PRIBOR format"}

    date_line = lines[0].strip()
    rates = {}
    for line in lines[2:]:
        parts = line.split("|")
        if len(parts) < 3:
            continue
        term = parts[0].strip()
        pribor_val = parts[2].strip() if len(parts) > 2 else parts[1].strip()
        if pribor_val:
            try:
                rates[term] = float(pribor_val)
            except ValueError:
                continue

    return {"success": True, "date": date_line, "rates": rates}


def _fetch_pribor_year(year: int) -> List[Dict]:
    """Fetch yearly PRIBOR history. Returns list of {date, term, rate}.

    Header lists ALL terms (including discontinued), but data rows only contain
    active terms. We determine active terms from actual data column count.
    """
    try:
        resp = requests.get(PRIBOR_YEAR_URL, params={"year": year}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
    except requests.RequestException:
        return []

    lines = text.split("\n")
    if len(lines) < 3:
        return []

    header_terms = [p.strip() for p in lines[0].split("|") if p.strip()]

    first_data = lines[2].split("|")
    n_pairs = (len(first_data) - 1) // 2

    if n_pairs == len(header_terms):
        active_terms = header_terms
    elif n_pairs < len(header_terms):
        daily = _fetch_pribor_daily()
        if daily.get("success"):
            active_terms = [t for t in header_terms if t in daily["rates"]]
        else:
            active_terms = header_terms[:n_pairs]
    else:
        active_terms = header_terms

    results = []
    for line in lines[2:]:
        cols = line.split("|")
        if len(cols) < 3:
            continue
        raw_date = cols[0].strip()
        if not raw_date:
            continue
        for i, term in enumerate(active_terms):
            pribor_col = 1 + i * 2 + 1
            if pribor_col < len(cols) and cols[pribor_col].strip():
                try:
                    results.append({
                        "date": raw_date,
                        "term": term,
                        "rate": float(cols[pribor_col].strip()),
                    })
                except ValueError:
                    continue

    return results

# ---------------------------------------------------------------------------
# Policy rate parser
# ---------------------------------------------------------------------------

def _fetch_policy_rate(rate_key: str) -> List[Dict]:
    """Fetch full history of a CNB policy rate. Returns list of {date, rate}."""
    url = POLICY_RATE_URLS.get(rate_key)
    if not url:
        return []
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text.strip()
    except requests.RequestException:
        return []

    lines = text.split("\n")
    if len(lines) < 2:
        return []

    results = []
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) != 2:
            continue
        raw_date = parts[0].strip()
        try:
            dt = datetime.strptime(raw_date, "%Y%m%d")
            results.append({
                "date": dt.strftime("%Y-%m-%d"),
                "rate": float(parts[1].strip()),
            })
        except (ValueError, IndexError):
            continue

    results.sort(key=lambda x: x["date"], reverse=True)
    return results

# ---------------------------------------------------------------------------
# ARAD API (optional, requires API key)
# ---------------------------------------------------------------------------

def _get_arad_key() -> Optional[str]:
    return os.environ.get("ARAD_API_KEY")


def _arad_request(endpoint: str, params: dict = None) -> Dict:
    key = _get_arad_key()
    if not key:
        return {"success": False, "error": "ARAD_API_KEY not set"}
    url = f"{ARAD_BASE_URL}/{endpoint}"
    p = dict(params or {})
    p["api_key"] = key
    try:
        resp = requests.get(url, params=p, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return {"success": True, "data": resp.text}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {
            "success": False,
            "error": f"Unknown indicator: {indicator}",
            "available": list(INDICATORS.keys()),
        }

    cfg = INDICATORS[indicator]
    ttl = _ttl_for(cfg)
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp, ttl)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    src = cfg["source"]

    if src == "fx":
        return _fetch_fx_indicator(indicator, cfg, cp, start_date)
    elif src == "pribor":
        return _fetch_pribor_indicator(indicator, cfg, cp, start_date)
    elif src == "policy":
        return _fetch_policy_indicator(indicator, cfg, cp)
    else:
        return {"success": False, "error": f"Unknown source type: {src}"}


def _fetch_fx_indicator(indicator: str, cfg: dict, cp: Path, date_str: str = None) -> Dict:
    code = cfg["code"]

    if date_str:
        daily = _fetch_fx_daily(date_str)
    else:
        daily = _fetch_fx_daily()

    if not daily.get("success"):
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": daily.get("error", "FX fetch failed")}

    if code not in daily["rates"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": f"Currency {code} not in daily fixing"}

    latest = daily["rates"][code]["rate"]
    latest_date = daily["date"]

    year_data = _fetch_fx_year(datetime.now().year)
    history = [
        {"period": r["date"], "value": r["rate"]}
        for r in year_data if r["code"] == code
    ]
    history.sort(key=lambda x: _parse_dd_mm_yyyy(x["period"]), reverse=True)

    period_change = period_change_pct = None
    if len(history) >= 2:
        prev = history[1]["value"]
        if prev and prev != 0:
            period_change = round(latest - prev, 4)
            period_change_pct = round((period_change / abs(prev)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest,
        "latest_period": latest_date,
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": history[:30],
        "total_observations": len(history),
        "source": FX_DAILY_URL,
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return _strip_cache_meta(response)


def _fetch_pribor_indicator(indicator: str, cfg: dict, cp: Path, date_str: str = None) -> Dict:
    term = cfg["term"]

    if date_str:
        daily = _fetch_pribor_daily(date_str)
    else:
        daily = _fetch_pribor_daily()

    if not daily.get("success"):
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": daily.get("error", "PRIBOR fetch failed")}

    if term not in daily["rates"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": f"Term {term} not in PRIBOR data"}

    latest = daily["rates"][term]
    latest_date = daily["date"]

    year_data = _fetch_pribor_year(datetime.now().year)
    history = [
        {"period": r["date"], "value": r["rate"]}
        for r in year_data if r["term"] == term
    ]
    history.sort(key=lambda x: _parse_pribor_date(x["period"]), reverse=True)

    period_change = period_change_pct = None
    if len(history) >= 2:
        prev = history[1]["value"]
        if prev and prev != 0:
            period_change = round(latest - prev, 4)
            period_change_pct = round((period_change / abs(prev)) * 100, 4)

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest,
        "latest_period": latest_date,
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": history[:30],
        "total_observations": len(history),
        "source": PRIBOR_DAILY_URL,
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return _strip_cache_meta(response)


def _fetch_policy_indicator(indicator: str, cfg: dict, cp: Path) -> Dict:
    rate_key = cfg["rate_key"]
    history = _fetch_policy_rate(rate_key)
    if not history:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Policy rate fetch failed"}

    latest = history[0]["rate"]
    latest_date = history[0]["date"]

    period_change = period_change_pct = None
    if len(history) >= 2:
        prev = history[1]["rate"]
        if prev and prev != 0:
            period_change = round(latest - prev, 4)
            period_change_pct = round((period_change / abs(prev)) * 100, 4)

    data_points = [{"period": h["date"], "value": h["rate"]} for h in history[:30]]

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": latest,
        "latest_period": latest_date,
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": data_points,
        "total_observations": len(history),
        "source": POLICY_RATE_URLS[rate_key],
        "timestamp": datetime.now().isoformat(),
    }
    _write_cache(cp, response)
    return _strip_cache_meta(response)


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
    fx_daily = _fetch_fx_daily()
    pribor_daily = _fetch_pribor_daily()

    for key, cfg in INDICATORS.items():
        src = cfg["source"]
        try:
            if src == "fx":
                if fx_daily.get("success") and cfg["code"] in fx_daily["rates"]:
                    results[key] = {
                        "name": cfg["name"],
                        "value": fx_daily["rates"][cfg["code"]]["rate"],
                        "period": fx_daily["date"],
                        "unit": cfg["unit"],
                    }
                else:
                    errors.append({"indicator": key, "error": f"FX code {cfg['code']} unavailable"})
            elif src == "pribor":
                if pribor_daily.get("success") and cfg["term"] in pribor_daily["rates"]:
                    results[key] = {
                        "name": cfg["name"],
                        "value": pribor_daily["rates"][cfg["term"]],
                        "period": pribor_daily["date"],
                        "unit": cfg["unit"],
                    }
                else:
                    errors.append({"indicator": key, "error": f"PRIBOR term {cfg['term']} unavailable"})
            elif src == "policy":
                history = _fetch_policy_rate(cfg["rate_key"])
                if history:
                    results[key] = {
                        "name": cfg["name"],
                        "value": history[0]["rate"],
                        "period": history[0]["date"],
                        "unit": cfg["unit"],
                    }
                else:
                    errors.append({"indicator": key, "error": "Policy rate fetch failed"})
        except Exception as e:
            errors.append({"indicator": key, "error": str(e)})

    return {
        "success": True,
        "source": "Czech National Bank (CNB)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_policy_rates() -> Dict:
    """Get current CNB official policy rates."""
    rate_keys = ["CNB_2W_REPO", "CNB_DISCOUNT", "CNB_LOMBARD"]
    rates = {}
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {
                "name": data["name"],
                "rate": data["latest_value"],
                "period": data["latest_period"],
            }

    return {
        "success": bool(rates),
        "rates": rates,
        "timestamp": datetime.now().isoformat(),
    }


def get_pribor_curve() -> Dict:
    """Get current PRIBOR term structure."""
    maturities = ["PRIBOR_1D", "PRIBOR_1W", "PRIBOR_2W", "PRIBOR_1M", "PRIBOR_3M", "PRIBOR_6M", "PRIBOR_1Y"]
    curve = []
    daily = _fetch_pribor_daily()
    if not daily.get("success"):
        return {"success": False, "error": daily.get("error", "PRIBOR fetch failed")}

    for key in maturities:
        cfg = INDICATORS[key]
        term = cfg["term"]
        if term in daily["rates"]:
            curve.append({
                "maturity": term,
                "rate_pct": daily["rates"][term],
                "period": daily["date"],
            })

    return {
        "success": bool(curve),
        "curve": curve,
        "count": len(curve),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_help():
    print("""
Czech National Bank (CNB) Module (Phase 1)

Usage:
  python cnb_czech.py                       # Latest values for all indicators
  python cnb_czech.py <INDICATOR>            # Fetch specific indicator
  python cnb_czech.py list                   # List available indicators
  python cnb_czech.py policy-rates           # CNB official policy rates
  python cnb_czech.py pribor-curve           # PRIBOR term structure

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<20s} {cfg['name']}")
    print(f"""
Sources:
  FX fixing:    {FX_DAILY_URL}
  PRIBOR:       {PRIBOR_DAILY_URL}
  Policy rates: https://www.cnb.cz/en/monetary-policy/instruments/
  ARAD API:     {ARAD_BASE_URL} (set ARAD_API_KEY env var)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "policy-rates":
            print(json.dumps(get_policy_rates(), indent=2, default=str))
        elif cmd == "pribor-curve":
            print(json.dumps(get_pribor_curve(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
