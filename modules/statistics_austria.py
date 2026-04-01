#!/usr/bin/env python3
"""
Statistics Austria Open Data Module

Austrian macroeconomic data from the Konjunkturmonitor (Economic Trend Monitor):
GDP (nominal/real), CPI, producer prices, employment, foreign trade,
tourism, industrial production, construction, and investment.

Data Source: https://data.statistik.gv.at (Open Government Data portal)
Protocol: OGD CSV download (semicolon-delimited, European decimal format)
Auth: None (open access, CC BY 4.0)
Refresh: Updated as needed (monthly/quarterly depending on indicator)
Coverage: Austria

Author: QUANTCLAW DATA Build Agent
Initiative: 0033
"""

import json
import sys
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://data.statistik.gv.at"
DATASET_ID = "OGD_konjunkturmonitor_KonMon_1"
DATA_CSV_URL = f"{BASE_URL}/data/{DATASET_ID}.csv"
HEADER_CSV_URL = f"{BASE_URL}/data/{DATASET_ID}_HEADER.csv"

CACHE_DIR = Path(__file__).parent.parent / "cache" / "statistics_austria"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45

QUOTE_VALUE = "1"
QUOTE_MOM_PCT = "2"
QUOTE_YOY_PCT = "3"

INDICATORS = {
    # --- GDP (quarterly) ---
    "GDP_NOMINAL_Q": {
        "column": "F-FAKT-77",
        "name": "GDP Nominal, Quarterly (EUR mn)",
        "description": "Gross domestic product, nominal, quarterly, in million EUR",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GDP_REAL_Q": {
        "column": "F-FAKT-83",
        "name": "GDP Real, Quarterly (EUR mn)",
        "description": "Gross domestic product, real (chain-linked), unadjusted, quarterly, in million EUR",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GDP_NOMINAL_Y": {
        "column": "F-FAKT-82",
        "name": "GDP Nominal, Annual (EUR mn)",
        "description": "Gross domestic product, nominal, annual, in million EUR",
        "frequency": "annual",
        "unit": "EUR mn",
    },
    # --- Prices (monthly) ---
    "CPI": {
        "column": "F-FAKT-68",
        "name": "Consumer Price Index (2015=100)",
        "description": "Verbraucherpreisindex — Austrian CPI, base year 2015=100",
        "frequency": "monthly",
        "unit": "index (2015=100)",
    },
    "PRODUCER_PRICE_INDEX": {
        "column": "F-FAKT-10",
        "name": "Industrial Output Price Index (2021=100)",
        "description": "Erzeugerpreisindex — producer price index for the producing sector, NACE B-E",
        "frequency": "monthly",
        "unit": "index (2021=100)",
    },
    "WHOLESALE_PRICE_INDEX": {
        "column": "F-FAKT-69",
        "name": "Wholesale Trade Price Index (2025=100)",
        "description": "Großhandelspreisindex — wholesale trade price index",
        "frequency": "monthly",
        "unit": "index (2025=100)",
    },
    # --- Labour market (quarterly) ---
    "EMPLOYED": {
        "column": "F-FAKT-78",
        "name": "Employed Persons (thousands)",
        "description": "Total employed persons, quarterly, in thousands",
        "frequency": "quarterly",
        "unit": "thousands",
    },
    "UNEMPLOYED": {
        "column": "F-FAKT-79",
        "name": "Unemployed Persons (thousands)",
        "description": "Total unemployed persons, quarterly, in thousands",
        "frequency": "quarterly",
        "unit": "thousands",
    },
    # --- Foreign trade (monthly) ---
    "IMPORTS_TOTAL": {
        "column": "F-FAKT-32",
        "name": "Total Imports (EUR)",
        "description": "Total goods imports, monthly, in EUR",
        "frequency": "monthly",
        "unit": "EUR",
    },
    "EXPORTS_TOTAL": {
        "column": "F-FAKT-46",
        "name": "Total Exports (EUR)",
        "description": "Total goods exports, monthly, in EUR",
        "frequency": "monthly",
        "unit": "EUR",
    },
    # --- Tourism (monthly) ---
    "OVERNIGHT_STAYS": {
        "column": "F-FAKT-67",
        "name": "Tourism Overnight Stays",
        "description": "Nächtigungen — total tourist overnight stays, monthly",
        "frequency": "monthly",
        "unit": "count",
    },
    "TOURISM_TURNOVER_INDEX": {
        "column": "F-FAKT-65",
        "name": "Tourism Turnover Index (2021=100)",
        "description": "Turnover index for accommodation and food service, nominal, quarterly",
        "frequency": "quarterly",
        "unit": "index (2021=100)",
    },
    "NEW_CAR_REGISTRATIONS": {
        "column": "F-FAKT-64",
        "name": "New Passenger Car Registrations",
        "description": "Pkw-Neuzulassungen — new passenger car registrations, monthly",
        "frequency": "monthly",
        "unit": "count",
    },
    # --- Industrial production (monthly) ---
    "INDUSTRIAL_PRODUCTION_INDEX": {
        "column": "F-FAKT-1",
        "name": "Industrial Production Index (2021=100)",
        "description": "Produktionsindex Industrie — working-day adjusted production index for industry",
        "frequency": "monthly",
        "unit": "index (2021=100)",
    },
    "CONSTRUCTION_PRODUCTION_INDEX": {
        "column": "F-FAKT-11",
        "name": "Construction Production Index (2021=100)",
        "description": "Produktionsindex Bau — working-day adjusted production index for construction",
        "frequency": "monthly",
        "unit": "index (2021=100)",
    },
    # --- Consumption & investment (quarterly) ---
    "HOUSEHOLD_CONSUMPTION": {
        "column": "F-FAKT-72",
        "name": "Household Consumption Expenditure (EUR mn)",
        "description": "Consumption expenditure of private households, nominal, quarterly, in million EUR",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
    "GROSS_FIXED_CAPITAL_FORMATION": {
        "column": "F-FAKT-76",
        "name": "Gross Fixed Capital Formation (EUR mn)",
        "description": "Bruttoanlageinvestitionen, nominal, quarterly, in million EUR",
        "frequency": "quarterly",
        "unit": "EUR mn",
    },
}

PERIOD_LEN = {"monthly": 6, "quarterly": 5, "annual": 4}


def _cache_path(name: str, params_hash: str) -> Path:
    safe = name.replace("/", "_")
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


def _parse_euro_decimal(val: str) -> Optional[float]:
    """Convert European decimal format '1.234,5' -> 1234.5. Returns None for zero/empty."""
    val = val.strip()
    if not val:
        return None
    try:
        val = val.replace(".", "").replace(",", ".")
        f = float(val)
        return f if f != 0.0 else None
    except ValueError:
        return None


def _download_csv() -> Optional[str]:
    """Download the Konjunkturmonitor CSV, with 24h raw-file caching."""
    raw_cache = CACHE_DIR / "konjunkturmonitor_raw.csv"
    if raw_cache.exists():
        try:
            mtime = datetime.fromtimestamp(raw_cache.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=CACHE_TTL_HOURS):
                return raw_cache.read_text(encoding="utf-8")
        except OSError:
            pass

    try:
        resp = requests.get(DATA_CSV_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        text = resp.text
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        raw_cache.write_text(text, encoding="utf-8")
        return text
    except requests.RequestException as e:
        return None


def _parse_csv(csv_text: str) -> List[Dict]:
    """Parse the semicolon-delimited CSV into list of row dicts."""
    lines = csv_text.strip().split("\n")
    if not lines:
        return []
    headers = lines[0].split(";")
    rows = []
    for line in lines[1:]:
        fields = line.split(";")
        if len(fields) == len(headers):
            rows.append(dict(zip(headers, fields)))
    return rows


def _extract_series(rows: List[Dict], column: str, frequency: str, quote: str = QUOTE_VALUE) -> List[Dict]:
    """Extract time series for a given column, frequency and quote type."""
    expected_len = PERIOD_LEN.get(frequency)
    series = []
    for row in rows:
        period = row.get("C-KMMONAT-0", "")
        row_quote = row.get("C-QUOTE-1", "")
        if row_quote != quote:
            continue
        if expected_len and len(period) != expected_len:
            continue
        val = _parse_euro_decimal(row.get(column, ""))
        if val is not None:
            series.append({"period": period, "value": val})
    series.sort(key=lambda x: x["period"], reverse=True)
    return series


def _format_period(period: str) -> str:
    """Human-readable period: 202501->2025-01, 20251->2025-Q1, 2025->2025."""
    if len(period) == 6:
        return f"{period[:4]}-{period[4:]}"
    if len(period) == 5:
        return f"{period[:4]}-Q{period[4:]}"
    return period


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date filters."""
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

    csv_text = _download_csv()
    if csv_text is None:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "Failed to download data from Statistics Austria"}

    rows = _parse_csv(csv_text)
    if not rows:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "CSV parse returned no rows"}

    series = _extract_series(rows, cfg["column"], cfg["frequency"])

    if start_date:
        series = [s for s in series if s["period"] >= start_date.replace("-", "").replace("Q", "")]
    if end_date:
        series = [s for s in series if s["period"] <= end_date.replace("-", "").replace("Q", "")]

    if not series:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations found for this indicator"}

    yoy_series = _extract_series(rows, cfg["column"], cfg["frequency"], quote=QUOTE_YOY_PCT)
    yoy_map = {s["period"]: s["value"] for s in yoy_series}

    period_change = period_change_pct = None
    if len(series) >= 2:
        latest_v = series[0]["value"]
        prev_v = series[1]["value"]
        if prev_v and prev_v != 0:
            period_change = round(latest_v - prev_v, 4)
            period_change_pct = round((period_change / abs(prev_v)) * 100, 4)

    latest_yoy = yoy_map.get(series[0]["period"])

    response = {
        "success": True,
        "indicator": indicator,
        "name": cfg["name"],
        "description": cfg["description"],
        "unit": cfg["unit"],
        "frequency": cfg["frequency"],
        "latest_value": series[0]["value"],
        "latest_period": _format_period(series[0]["period"]),
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "yoy_change_pct": latest_yoy,
        "data_points": [
            {"period": _format_period(s["period"]), "value": s["value"], "yoy_pct": yoy_map.get(s["period"])}
            for s in series[:30]
        ],
        "total_observations": len(series),
        "source": DATA_CSV_URL,
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
            "column": v["column"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None) -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator)

    csv_text = _download_csv()
    if csv_text is None:
        return {"success": False, "error": "Failed to download data from Statistics Austria"}

    rows = _parse_csv(csv_text)
    results = {}
    errors = []

    for key, cfg in INDICATORS.items():
        series = _extract_series(rows, cfg["column"], cfg["frequency"])
        if series:
            results[key] = {
                "name": cfg["name"],
                "value": series[0]["value"],
                "period": _format_period(series[0]["period"]),
                "unit": cfg["unit"],
            }
        else:
            errors.append({"indicator": key, "error": "No data available"})

    return {
        "success": True,
        "source": "Statistics Austria — Konjunkturmonitor (Economic Trend Monitor)",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def discover_catalog() -> Dict:
    """Discover dataset metadata from the OGD JSON endpoint."""
    url = f"{BASE_URL}/ogd/json?dataset={DATASET_ID}"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        meta = resp.json()
        return {
            "success": True,
            "dataset_id": DATASET_ID,
            "title": meta.get("title"),
            "en_title": meta.get("extras", {}).get("en_title_and_desc"),
            "license": meta.get("license"),
            "publisher": meta.get("extras", {}).get("publisher"),
            "last_modified": meta.get("extras", {}).get("metadata_modified"),
            "update_frequency": meta.get("extras", {}).get("update_frequency"),
            "categories": meta.get("extras", {}).get("categorization"),
            "resources": [{"name": r["name"], "url": r["url"], "format": r["format"]} for r in meta.get("resources", [])],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- CLI ---

def _print_help():
    print(f"""
Statistics Austria Open Data Module (Initiative 0033)

Usage:
  python statistics_austria.py                   # Latest values for all indicators
  python statistics_austria.py <INDICATOR>        # Fetch specific indicator
  python statistics_austria.py list               # List available indicators
  python statistics_austria.py catalog            # Discover dataset metadata

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<38s} {cfg['name']}")
    print(f"""
Source: {BASE_URL}
Dataset: {DATASET_ID} (Konjunkturmonitor / Economic Trend Monitor)
Protocol: OGD CSV (open access, CC BY 4.0)
Coverage: Austria
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str))
        elif cmd == "catalog":
            print(json.dumps(discover_catalog(), indent=2, default=str))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
