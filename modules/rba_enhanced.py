#!/usr/bin/env python3
"""
RBA Australia Enhanced — All Major Statistical Tables (CSV feeds)

Comprehensive Reserve Bank of Australia data: money market rates, government
bond yields, indicator lending rates, exchange rates, international official
rates, financial aggregate growth, and GDP/income.

Data Source: https://www.rba.gov.au/statistics/tables/csv/
Protocol: Direct CSV download (stable URLs, no auth)
Refresh: Daily (F1/F2), Monthly (F5/F11/F13/D1), Quarterly (H1)

Tables:
  F1  — Interest Rates & Yields (Money Market)
  F2  — Capital Market Yields (Government Bonds)
  F5  — Indicator Lending Rates
  F11 — Exchange Rates
  F13 — International Official Interest Rates
  D1  — Growth in Financial Aggregates
  H1  — GDP and Income

Author: QUANTCLAW DATA Build Agent
Initiative: 0027
"""

import json
import sys
import time
import hashlib
import csv
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from io import StringIO

BASE_URL = "https://www.rba.gov.au/statistics/tables/csv"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "rba_enhanced"
REQUEST_TIMEOUT = 30

TABLES = {
    "f1": {"file": "f1-data.csv", "cache_ttl_hours": 1, "frequency": "daily"},
    "f2": {"file": "f2-data.csv", "cache_ttl_hours": 1, "frequency": "daily"},
    "f5": {"file": "f5-data.csv", "cache_ttl_hours": 1, "frequency": "monthly"},
    "f11": {"file": "f11-data.csv", "cache_ttl_hours": 24, "frequency": "monthly"},
    "f13": {"file": "f13-data.csv", "cache_ttl_hours": 24, "frequency": "monthly"},
    "d1": {"file": "d1-data.csv", "cache_ttl_hours": 24, "frequency": "monthly"},
    "h1": {"file": "h1-data.csv", "cache_ttl_hours": 24, "frequency": "quarterly"},
}

INDICATORS = {
    # --- F1: Money Market ---
    "F1_CASH_RATE_TARGET": {
        "table": "f1", "series_id": "FIRMMCRTD",
        "name": "RBA Cash Rate Target (%)",
        "description": "Official RBA cash rate target",
        "frequency": "daily", "unit": "%",
    },
    "F1_OVERNIGHT_RATE": {
        "table": "f1", "series_id": "FIRMMCRID",
        "name": "Interbank Overnight Cash Rate (%)",
        "description": "Interbank overnight cash rate",
        "frequency": "daily", "unit": "%",
    },
    "F1_3M_BABS": {
        "table": "f1", "series_id": "FIRMMBAB90D",
        "name": "3-Month BABs/NCDs Rate (%)",
        "description": "Bank accepted bills / negotiable certificates of deposit, 3 months",
        "frequency": "daily", "unit": "%",
    },
    "F1_3M_OIS": {
        "table": "f1", "series_id": "FIRMMOIS3D",
        "name": "3-Month OIS Rate (%)",
        "description": "Overnight indexed swaps, 3 months",
        "frequency": "daily", "unit": "%",
    },
    "F1_3M_TREASURY_NOTE": {
        "table": "f1", "series_id": "FIRMMTN3D",
        "name": "3-Month Treasury Note Rate (%)",
        "description": "Treasury note yield, 3 months",
        "frequency": "daily", "unit": "%",
    },
    # --- F2: Government Bond Yields ---
    "F2_GOVT_2Y": {
        "table": "f2", "series_id": "FCMYGBAG2D",
        "name": "AU Govt Bond Yield 2Y (% p.a.)",
        "description": "Australian government bond yield, interpolated, 2-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "F2_GOVT_3Y": {
        "table": "f2", "series_id": "FCMYGBAG3D",
        "name": "AU Govt Bond Yield 3Y (% p.a.)",
        "description": "Australian government bond yield, interpolated, 3-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "F2_GOVT_5Y": {
        "table": "f2", "series_id": "FCMYGBAG5D",
        "name": "AU Govt Bond Yield 5Y (% p.a.)",
        "description": "Australian government bond yield, interpolated, 5-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "F2_GOVT_10Y": {
        "table": "f2", "series_id": "FCMYGBAG10D",
        "name": "AU Govt Bond Yield 10Y (% p.a.)",
        "description": "Australian government bond yield, interpolated, 10-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    "F2_GOVT_INDEXED": {
        "table": "f2", "series_id": "FCMYGBAGID",
        "name": "AU Govt Indexed Bond Yield 10Y (% p.a.)",
        "description": "Australian government indexed bond yield, interpolated, 10-year maturity",
        "frequency": "daily", "unit": "% p.a.",
    },
    # --- F5: Lending Rates ---
    "F5_HOUSING_VARIABLE": {
        "table": "f5", "series_id": "FILRHLBVS",
        "name": "Housing Loan Rate — Variable Standard Owner-Occ (% p.a.)",
        "description": "Banks variable standard housing loan rate, owner-occupier",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F5_HOUSING_DISCOUNTED": {
        "table": "f5", "series_id": "FILRHLBVD",
        "name": "Housing Loan Rate — Variable Discounted Owner-Occ (% p.a.)",
        "description": "Banks variable discounted housing loan rate, owner-occupier",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F5_HOUSING_3YR_FIXED": {
        "table": "f5", "series_id": "FILRHL3YF",
        "name": "Housing Loan Rate — 3-Year Fixed Owner-Occ (% p.a.)",
        "description": "Banks 3-year fixed housing loan rate, owner-occupier",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F5_CREDIT_CARD_STD": {
        "table": "f5", "series_id": "FILRPLRCCS",
        "name": "Credit Card Rate — Standard (% p.a.)",
        "description": "Personal loans, revolving credit, credit cards standard rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F5_SME_VARIABLE": {
        "table": "f5", "series_id": "FILRSBVRT",
        "name": "Small Business Lending Rate — Variable Term (% p.a.)",
        "description": "Small business variable term lending rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    # --- F11: Exchange Rates ---
    "F11_AUD_USD": {
        "table": "f11", "series_id": "FXRUSD",
        "name": "AUD/USD Exchange Rate",
        "description": "Australian dollar per US dollar",
        "frequency": "monthly", "unit": "USD",
    },
    "F11_TWI": {
        "table": "f11", "series_id": "FXRTWI",
        "name": "AUD Trade-Weighted Index",
        "description": "Australian dollar trade-weighted index (May 1970 = 100)",
        "frequency": "monthly", "unit": "Index",
    },
    "F11_AUD_CNY": {
        "table": "f11", "series_id": "FXRCR",
        "name": "AUD/CNY Exchange Rate",
        "description": "Australian dollar per Chinese yuan",
        "frequency": "monthly", "unit": "CNY",
    },
    "F11_AUD_JPY": {
        "table": "f11", "series_id": "FXRJY",
        "name": "AUD/JPY Exchange Rate",
        "description": "Australian dollar per Japanese yen",
        "frequency": "monthly", "unit": "JPY",
    },
    "F11_AUD_EUR": {
        "table": "f11", "series_id": "FXREUR",
        "name": "AUD/EUR Exchange Rate",
        "description": "Australian dollar per euro",
        "frequency": "monthly", "unit": "EUR",
    },
    "F11_AUD_GBP": {
        "table": "f11", "series_id": "FXRUKPS",
        "name": "AUD/GBP Exchange Rate",
        "description": "Australian dollar per British pound sterling",
        "frequency": "monthly", "unit": "GBP",
    },
    # --- F13: International Official Interest Rates ---
    "F13_US_FED_FUNDS": {
        "table": "f13", "series_id": "FOOIRUSFFTRMX",
        "name": "US Federal Funds Max Target Rate (% p.a.)",
        "description": "US Federal Reserve maximum target for federal funds rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F13_JAPAN_RATE": {
        "table": "f13", "series_id": "FOOIRJTCR",
        "name": "Japan Policy Rate (% p.a.)",
        "description": "Bank of Japan policy rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F13_ECB_REFI": {
        "table": "f13", "series_id": "FOOIREARR",
        "name": "ECB Refinancing Rate (% p.a.)",
        "description": "European Central Bank main refinancing operations rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F13_UK_BANK_RATE": {
        "table": "f13", "series_id": "FOOIRUKOBR",
        "name": "UK Bank Rate (% p.a.)",
        "description": "Bank of England bank rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F13_CANADA_RATE": {
        "table": "f13", "series_id": "FOOIRCTR",
        "name": "Canada Target Rate (% p.a.)",
        "description": "Bank of Canada overnight target rate",
        "frequency": "monthly", "unit": "% p.a.",
    },
    "F13_AUSTRALIA_RATE": {
        "table": "f13", "series_id": "FOOIRATCR",
        "name": "Australia Target Cash Rate (% p.a.)",
        "description": "RBA target cash rate (from F13 international comparison)",
        "frequency": "monthly", "unit": "% p.a.",
    },
    # --- D1: Financial Aggregates Growth ---
    "D1_CREDIT_HOUSING_MOM": {
        "table": "d1", "series_id": "DGFACHM",
        "name": "Housing Credit — Monthly Growth (%)",
        "description": "Housing credit monthly growth, seasonally adjusted, incl. securitisations",
        "frequency": "monthly", "unit": "%",
    },
    "D1_CREDIT_HOUSING_YOY": {
        "table": "d1", "series_id": "DGFACH12",
        "name": "Housing Credit — 12-Month Growth (%)",
        "description": "Housing credit 12-month ended growth, seasonally adjusted",
        "frequency": "monthly", "unit": "%",
    },
    "D1_CREDIT_TOTAL_MOM": {
        "table": "d1", "series_id": "DGFACM",
        "name": "Total Credit — Monthly Growth (%)",
        "description": "Total credit monthly growth, seasonally adjusted, incl. securitisations",
        "frequency": "monthly", "unit": "%",
    },
    "D1_CREDIT_TOTAL_YOY": {
        "table": "d1", "series_id": "DGFAC12",
        "name": "Total Credit — 12-Month Growth (%)",
        "description": "Total credit 12-month ended growth, seasonally adjusted",
        "frequency": "monthly", "unit": "%",
    },
    "D1_M3_MOM": {
        "table": "d1", "series_id": "DGFAM3M",
        "name": "M3 — Monthly Growth (%)",
        "description": "M3 monetary aggregate monthly growth, seasonally adjusted",
        "frequency": "monthly", "unit": "%",
    },
    "D1_M3_YOY": {
        "table": "d1", "series_id": "DGFAM312",
        "name": "M3 — 12-Month Growth (%)",
        "description": "M3 monetary aggregate 12-month ended growth, seasonally adjusted",
        "frequency": "monthly", "unit": "%",
    },
    "D1_BROAD_MONEY_YOY": {
        "table": "d1", "series_id": "DGFABM12",
        "name": "Broad Money — 12-Month Growth (%)",
        "description": "Broad money 12-month ended growth, seasonally adjusted",
        "frequency": "monthly", "unit": "%",
    },
    # --- H1: GDP and Income ---
    "H1_REAL_GDP": {
        "table": "h1", "series_id": "GGDPCVGDP",
        "name": "Real GDP (AUD mn, chain volume)",
        "description": "Gross domestic product, chain volume, seasonally adjusted",
        "frequency": "quarterly", "unit": "AUD mn",
    },
    "H1_REAL_GDP_GROWTH": {
        "table": "h1", "series_id": "GGDPCVGDPY",
        "name": "Real GDP Growth — Year-Ended (%)",
        "description": "Year-ended real GDP growth, seasonally adjusted",
        "frequency": "quarterly", "unit": "%",
    },
    "H1_NOMINAL_GDP": {
        "table": "h1", "series_id": "GGDPECCPGDP",
        "name": "Nominal GDP (AUD mn, current price)",
        "description": "Gross domestic product, current price, seasonally adjusted",
        "frequency": "quarterly", "unit": "AUD mn",
    },
    "H1_NOMINAL_GDP_GROWTH": {
        "table": "h1", "series_id": "GGDPECCPGDPY",
        "name": "Nominal GDP Growth — Year-Ended (%)",
        "description": "Year-ended nominal GDP growth, seasonally adjusted",
        "frequency": "quarterly", "unit": "%",
    },
    "H1_TERMS_OF_TRADE": {
        "table": "h1", "series_id": "GOPITT",
        "name": "Terms of Trade (Index)",
        "description": "Goods & services terms of trade index, seasonally adjusted",
        "frequency": "quarterly", "unit": "Index",
    },
}

_DATE_FORMATS = ["%d-%b-%Y", "%d/%m/%Y", "%b-%Y"]
_table_cache: Dict[str, Dict] = {}


def _parse_date(raw: str) -> Optional[str]:
    """Parse RBA date string into ISO format (YYYY-MM-DD)."""
    raw = raw.strip()
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _table_cache_path(table_key: str) -> Path:
    return CACHE_DIR / f"table_{table_key}.json"


def _read_table_cache(table_key: str) -> Optional[Dict]:
    path = _table_cache_path(table_key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        ttl = TABLES[table_key]["cache_ttl_hours"]
        if datetime.now() - cached_at < timedelta(hours=ttl):
            return data
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _write_table_cache(table_key: str, data: Dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["_cached_at"] = datetime.now().isoformat()
        _table_cache_path(table_key).write_text(json.dumps(data, default=str))
    except OSError:
        pass


def _download_table(table_key: str) -> Dict:
    """Download and parse an RBA statistical table CSV.

    Returns a dict mapping series_id -> list of {period, value} dicts,
    plus metadata per series.
    """
    if table_key in _table_cache:
        cached = _table_cache[table_key]
        cached_at = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
        ttl = TABLES[table_key]["cache_ttl_hours"]
        if datetime.now() - cached_at < timedelta(hours=ttl):
            return cached

    disk_cached = _read_table_cache(table_key)
    if disk_cached:
        _table_cache[table_key] = disk_cached
        return disk_cached

    tbl = TABLES[table_key]
    url = f"{BASE_URL}/{tbl['file']}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

    rows = list(csv.reader(StringIO(resp.text)))
    if len(rows) < 10:
        return {"success": False, "error": "CSV too short"}

    meta_rows = {}
    for row in rows[:12]:
        if row and row[0].strip():
            label = row[0].strip().lower()
            if label in ("title", "description", "frequency", "units", "series id", "source"):
                meta_rows[label] = row

    series_id_row = meta_rows.get("series id")
    title_row = meta_rows.get("title")
    units_row = meta_rows.get("units")
    if not series_id_row:
        return {"success": False, "error": "No Series ID row found"}

    sid_to_col = {}
    for col_idx, sid in enumerate(series_id_row):
        sid = sid.strip()
        if sid and sid.lower() != "series id":
            sid_to_col[sid] = col_idx

    data_start = 0
    for i, row in enumerate(rows):
        if row and row[0].strip().lower() == "series id":
            data_start = i + 1
            break

    series_data: Dict[str, List] = {sid: [] for sid in sid_to_col}
    for row in rows[data_start:]:
        if not row or not row[0].strip():
            continue
        date_str = _parse_date(row[0])
        if not date_str:
            continue
        for sid, col_idx in sid_to_col.items():
            if col_idx < len(row):
                val_str = row[col_idx].strip().replace(",", "")
                if val_str:
                    try:
                        series_data[sid].append({
                            "period": date_str,
                            "value": float(val_str),
                        })
                    except ValueError:
                        pass

    for sid in series_data:
        series_data[sid].sort(key=lambda x: x["period"], reverse=True)

    series_meta = {}
    for sid, col_idx in sid_to_col.items():
        meta = {}
        if title_row and col_idx < len(title_row):
            meta["title"] = title_row[col_idx].strip()
        if units_row and col_idx < len(units_row):
            meta["unit"] = units_row[col_idx].strip()
        series_meta[sid] = meta

    result = {
        "success": True,
        "table": table_key,
        "series": series_data,
        "meta": series_meta,
        "_cached_at": datetime.now().isoformat(),
    }
    _table_cache[table_key] = result
    _write_table_cache(table_key, result)
    return result


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    table_data = _download_table(cfg["table"])
    if not table_data.get("success"):
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": table_data.get("error", "Table download failed")}

    series = table_data["series"].get(cfg["series_id"], [])
    if not series:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": f"Series {cfg['series_id']} not found in table"}

    if start_date or end_date:
        filtered = series
        if start_date:
            filtered = [p for p in filtered if p["period"] >= start_date]
        if end_date:
            filtered = [p for p in filtered if p["period"] <= end_date]
        series = filtered

    if not series:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No data in date range"}

    period_change = period_change_pct = None
    if len(series) >= 2:
        latest_v = series[0]["value"]
        prev_v = series[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 6)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    return {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": series[0]["value"],
        "latest_period": series[0]["period"],
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": series[:30],
        "total_observations": len(series),
        "source": f"{BASE_URL}/{TABLES[cfg['table']]['file']}",
        "timestamp": datetime.now().isoformat(),
    }


def get_available_indicators() -> List[Dict]:
    """Return list of available indicators with descriptions."""
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "frequency": v["frequency"],
            "unit": v["unit"],
            "table": v["table"].upper(),
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

    return {
        "success": True,
        "source": "Reserve Bank of Australia (Enhanced)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_yield_curve() -> Dict:
    """Get current Australian government bond yield curve."""
    keys = ["F2_GOVT_2Y", "F2_GOVT_3Y", "F2_GOVT_5Y", "F2_GOVT_10Y", "F2_GOVT_INDEXED"]
    curve = []
    for key in keys:
        data = fetch_data(key)
        if data.get("success"):
            label = key.replace("F2_GOVT_", "")
            curve.append({
                "maturity": label,
                "yield_pct": data["latest_value"],
                "period": data["latest_period"],
            })
    return {"success": bool(curve), "curve": curve, "count": len(curve), "timestamp": datetime.now().isoformat()}


def get_rates() -> Dict:
    """Get all current interest/policy rates."""
    rate_keys = [k for k in INDICATORS if k.startswith(("F1_", "F13_"))]
    rates = {}
    for key in rate_keys:
        data = fetch_data(key)
        if data.get("success"):
            rates[key] = {"name": data["name"], "rate": data["latest_value"], "period": data["latest_period"]}
    return {"success": bool(rates), "rates": rates, "count": len(rates), "timestamp": datetime.now().isoformat()}


def get_fx() -> Dict:
    """Get all AUD exchange rates."""
    fx_keys = [k for k in INDICATORS if k.startswith("F11_")]
    fx = {}
    for key in fx_keys:
        data = fetch_data(key)
        if data.get("success"):
            fx[key] = {"name": data["name"], "value": data["latest_value"], "period": data["latest_period"]}
    return {"success": bool(fx), "fx_rates": fx, "count": len(fx), "timestamp": datetime.now().isoformat()}


# --- CLI ---

def _print_help():
    print("""
RBA Australia Enhanced — All Major Statistical Tables

Usage:
  python rba_enhanced.py                     # Latest values for all indicators
  python rba_enhanced.py <INDICATOR>          # Fetch specific indicator
  python rba_enhanced.py list                 # List available indicators
  python rba_enhanced.py yield-curve          # AU govt bond yield curve
  python rba_enhanced.py rates                # All interest/policy rates
  python rba_enhanced.py fx                   # All AUD exchange rates

Tables: F1, F2, F5, F11, F13, D1, H1

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<30s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Protocol: Direct CSV download (no auth)
Coverage: Australia / International comparison
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
        elif cmd == "rates":
            print(json.dumps(get_rates(), indent=2, default=str))
        elif cmd == "fx":
            print(json.dumps(get_fx(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
