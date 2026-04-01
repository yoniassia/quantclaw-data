#!/usr/bin/env python3
"""
CZSO Czech Republic Statistics Module

Macroeconomic data from the Czech Statistical Office (Český statistický úřad):
GDP, CPI inflation, labour market, industrial production, construction,
and foreign trade.

Data Source: https://vdb.czso.cz/pll/eweb/ (open data portal)
Protocol: REST / Open Data CSV
Auth: None (open access)
Refresh: Monthly (CPI, IPI, construction, trade), Quarterly (labour), Annual (GDP)
Coverage: Czech Republic

Author: QUANTCLAW DATA Build Agent
Phase: 1
"""

import csv
import hashlib
import io
import json
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

METADATA_URL = "https://vdb.czso.cz/pll/eweb/lkod_ld.datova_sada"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "czso_czech"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 45
REQUEST_DELAY = 0.3

DATASETS = {
    "national_accounts": "Zakladni_ukazatele_narodnich_uctu",
    "cpi": "Indexy_spotrebitelskych_cen",
    "labour": "Zamestnani_a_nezamestnani_podle_vysledku_vyberoveho_setreni_pracovnich_sil_za_kraje",
    "industrial_production": "Index_prumyslove_produkce",
    "construction": "Index_stavebni_produkce",
    "foreign_trade": "Zahranicni_obchod_se_zbozim_podle_vybranych_zemi",
    "building_permits": "Stavebni_povoleni",
}

INDICATORS = {
    # --- GDP / National Accounts (annual) ---
    "GDP_NOMINAL": {
        "dataset": "national_accounts",
        "name": "GDP at Current Prices (CZK mn)",
        "description": "Czech Republic gross domestic product, nominal, current prices",
        "frequency": "annual",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Hrubý domácí produkt", "oceneni_txt": "běžné ceny", "casz_txt": ""},
        "time_mode": "year",
    },
    "GDP_REAL": {
        "dataset": "national_accounts",
        "name": "GDP at Constant 2020 Prices (CZK mn)",
        "description": "Czech Republic gross domestic product, constant 2020 prices",
        "frequency": "annual",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Hrubý domácí produkt", "oceneni_txt": "stálé ceny roku 2020", "casz_txt": ""},
        "time_mode": "year",
    },
    "GDP_GROWTH": {
        "dataset": "national_accounts",
        "name": "GDP Growth YoY (%)",
        "description": "Czech Republic GDP year-on-year growth rate, previous year prices",
        "frequency": "annual",
        "unit": "%",
        "filters": {"stapro_txt": "Hrubý domácí produkt", "oceneni_txt": "ceny předchozího roku (průměrné)", "casz_txt": "předchozí období"},
        "time_mode": "year",
    },
    "GVA_NOMINAL": {
        "dataset": "national_accounts",
        "name": "Gross Value Added, Current Prices (CZK mn)",
        "description": "Czech Republic gross value added, current prices",
        "frequency": "annual",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Hrubá přidaná hodnota", "oceneni_txt": "běžné ceny", "casz_txt": ""},
        "time_mode": "year",
    },
    "GFCF_NOMINAL": {
        "dataset": "national_accounts",
        "name": "Gross Fixed Capital Formation (CZK mn)",
        "description": "Czech Republic gross fixed capital formation, current prices",
        "frequency": "annual",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Tvorba hrubého fixního kapitálu", "oceneni_txt": "běžné ceny", "casz_txt": ""},
        "time_mode": "year",
    },
    # --- Consumer Price Indices (monthly) ---
    "CPI_YOY": {
        "dataset": "cpi",
        "name": "CPI Year-on-Year (%)",
        "description": "Consumer price index, all items, same period of previous year",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ucel_kod": "", "casz_kod": "C"},
        "time_mode": "year_month",
    },
    "CPI_MOM": {
        "dataset": "cpi",
        "name": "CPI Month-on-Month (%)",
        "description": "Consumer price index, all items, previous period",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ucel_kod": "", "casz_kod": "B"},
        "time_mode": "year_month",
    },
    "CPI_INDEX": {
        "dataset": "cpi",
        "name": "CPI Index (2015=100)",
        "description": "Consumer price index, all items, base year 2015 average",
        "frequency": "monthly",
        "unit": "index 2015=100",
        "filters": {"ucel_kod": "", "casz_kod": "Z"},
        "time_mode": "year_month",
    },
    "CPI_FOOD_YOY": {
        "dataset": "cpi",
        "name": "CPI Food & Non-Alcoholic Beverages YoY (%)",
        "description": "Consumer price index, food and non-alcoholic beverages, YoY",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ucel_kod": "01", "casz_kod": "C"},
        "time_mode": "year_month",
    },
    "CPI_HOUSING_YOY": {
        "dataset": "cpi",
        "name": "CPI Housing, Water, Energy YoY (%)",
        "description": "Consumer price index, housing/water/energy/fuels, YoY",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ucel_kod": "04", "casz_kod": "C"},
        "time_mode": "year_month",
    },
    "CPI_TRANSPORT_YOY": {
        "dataset": "cpi",
        "name": "CPI Transport YoY (%)",
        "description": "Consumer price index, transport, YoY",
        "frequency": "monthly",
        "unit": "%",
        "filters": {"ucel_kod": "07", "casz_kod": "C"},
        "time_mode": "year_month",
    },
    # --- Labour Market (quarterly) ---
    "UNEMPLOYMENT_RATE": {
        "dataset": "labour",
        "name": "General Unemployment Rate (%)",
        "description": "Labour force survey, general unemployment rate, total, Czech Republic",
        "frequency": "quarterly",
        "unit": "%",
        "filters": {"stapro_txt": "Obecná míra nezaměstnanosti", "uzemi_kod": "19", "pohlavi_kod": ""},
        "time_mode": "year_quarter",
    },
    "EMPLOYMENT_RATE": {
        "dataset": "labour",
        "name": "Employment Rate (%)",
        "description": "Labour force survey, employment rate, total, Czech Republic",
        "frequency": "quarterly",
        "unit": "%",
        "filters": {"stapro_txt": "Míra zaměstnanosti", "uzemi_kod": "19", "pohlavi_kod": ""},
        "time_mode": "year_quarter",
    },
    "EMPLOYED": {
        "dataset": "labour",
        "name": "Employed Persons (thousands)",
        "description": "Labour force survey, total employed, Czech Republic",
        "frequency": "quarterly",
        "unit": "thousands",
        "filters": {"ekak_kod": "3", "uzemi_kod": "19", "pohlavi_kod": ""},
        "time_mode": "year_quarter",
    },
    "UNEMPLOYED": {
        "dataset": "labour",
        "name": "Unemployed Persons (thousands)",
        "description": "Labour force survey, total unemployed, Czech Republic",
        "frequency": "quarterly",
        "unit": "thousands",
        "filters": {"ekak_kod": "4", "uzemi_kod": "19", "pohlavi_kod": ""},
        "time_mode": "year_quarter",
    },
    # --- Industrial Production (monthly) ---
    "IPI_TOTAL": {
        "dataset": "industrial_production",
        "name": "Industrial Production Index — Total YoY (%)",
        "description": "Industrial production index, total industry (B+C+D), same period of previous year",
        "frequency": "monthly",
        "unit": "% YoY",
        "filters": {"cznace_kod": "05350001", "casz_txt": "stejné období předchozího roku"},
        "time_mode": "year_month",
    },
    "IPI_AUTO": {
        "dataset": "industrial_production",
        "name": "Motor Vehicles Production Index YoY (%)",
        "description": "Industrial production index, motor vehicles (NACE 29), YoY",
        "frequency": "monthly",
        "unit": "% YoY",
        "filters": {"cznace_kod": "29", "casz_txt": "stejné období předchozího roku"},
        "time_mode": "year_month",
    },
    # --- Construction (monthly) ---
    "CONSTRUCTION_INDEX": {
        "dataset": "construction",
        "name": "Construction Output Index YoY (%)",
        "description": "Construction output index, total, current prices, YoY, not seasonally adjusted",
        "frequency": "monthly",
        "unit": "% YoY",
        "filters": {"stavprace_kod": "", "casz_txt": "stejné období předchozího roku", "oceneni_txt": "běžné ceny", "ocisteni_txt": "neočištěno"},
        "time_mode": "year_month",
    },
    # --- Foreign Trade (monthly) ---
    "TRADE_EXPORTS": {
        "dataset": "foreign_trade",
        "name": "Total Goods Exports (CZK mn)",
        "description": "Czech Republic total goods exports, all countries",
        "frequency": "monthly",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Hodnota vývozu zboží", "czem_kod": ""},
        "time_mode": "year_month",
    },
    "TRADE_IMPORTS": {
        "dataset": "foreign_trade",
        "name": "Total Goods Imports (CZK mn)",
        "description": "Czech Republic total goods imports, all countries",
        "frequency": "monthly",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Hodnota dovozu zboží", "czem_kod": ""},
        "time_mode": "year_month",
    },
    "TRADE_BALANCE": {
        "dataset": "foreign_trade",
        "name": "Trade Balance — Goods (CZK mn)",
        "description": "Czech Republic goods trade balance, all countries",
        "frequency": "monthly",
        "unit": "CZK mn",
        "filters": {"stapro_txt": "Bilance zboží", "czem_kod": ""},
        "time_mode": "year_month",
    },
}


def _cache_path(name: str, suffix: str = "json") -> Path:
    safe = name.replace("/", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}.{suffix}"


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
        path.write_text(json.dumps(data, default=str, ensure_ascii=False))
    except OSError:
        pass


def _get_csv_url(dataset_name: str) -> Optional[str]:
    """Resolve the current CSV download URL for a dataset via CZSO metadata API."""
    cache_key = f"url_{dataset_name}"
    cp = _cache_path(cache_key)
    cached = _read_cache(cp)
    if cached and cached.get("url"):
        return cached["url"]

    try:
        resp = requests.get(
            METADATA_URL, params={"nazev": dataset_name},
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        meta = resp.json()
        distributions = meta.get("distribuce", [])
        for dist in distributions:
            fmt = dist.get("formát", dist.get("form\u00e1t", ""))
            url = dist.get("soubor_ke_sta\u017een\u00ed") or dist.get("p\u0159\u00edstupov\u00e9_url", "")
            if url and ("CSV" in fmt.upper() or url.lower().endswith(".csv")):
                _write_cache(cp, {"url": url})
                return url
        for dist in distributions:
            url = dist.get("soubor_ke_sta\u017een\u00ed") or dist.get("p\u0159\u00edstupov\u00e9_url", "")
            if url:
                _write_cache(cp, {"url": url})
                return url
    except Exception:
        pass
    return None


def _download_csv(dataset_name: str) -> Optional[List[Dict]]:
    """Download and parse a CZSO dataset CSV, with caching."""
    cp = _cache_path(f"data_{dataset_name}")
    cached = _read_cache(cp)
    if cached and cached.get("rows"):
        return cached["rows"]

    url = _get_csv_url(dataset_name)
    if not url:
        return None

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = [row for row in reader]
        if rows:
            _write_cache(cp, {"rows": rows, "count": len(rows), "url": url})
        return rows
    except Exception:
        return None


def _make_period(row: Dict, time_mode: str) -> str:
    """Construct a sortable time period string from CSV row fields."""
    rok = row.get("rok", "")
    if time_mode == "year":
        return rok
    elif time_mode == "year_month":
        mesic = row.get("mesic", "")
        return f"{rok}-{mesic.zfill(2)}" if mesic else rok
    elif time_mode == "year_quarter":
        q = row.get("ctvrtleti", "")
        return f"{rok}-Q{q}" if q else rok
    return rok


def _match_row(row: Dict, filters: Dict) -> bool:
    """Check if a CSV row matches all filter criteria.
    Empty string filter value means the column must be empty/missing.
    """
    for col, expected in filters.items():
        actual = (row.get(col) or "").strip()
        if expected == "":
            if actual != "":
                return False
        else:
            if actual != expected:
                return False
    return True


def _extract_observations(dataset_name: str, filters: Dict, time_mode: str) -> List[Dict]:
    """Download dataset and extract matching observations sorted newest-first."""
    rows = _download_csv(dataset_name)
    if not rows:
        return []

    results = []
    for row in rows:
        if not _match_row(row, filters):
            continue
        val_str = (row.get("hodnota") or "").strip()
        if not val_str:
            continue
        try:
            value = float(val_str)
        except ValueError:
            continue
        period = _make_period(row, time_mode)
        if period:
            results.append({"period": period, "value": value})

    results.sort(key=lambda x: x["period"], reverse=True)
    return results


def fetch_data(indicator: str, start_date: str = None, end_date: str = None) -> Dict:
    """Fetch a specific indicator with optional date range."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "start": start_date, "end": end_date}
    cp = _cache_path(f"result_{indicator}_{_params_hash(cache_params)}")
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    dataset_name = DATASETS[cfg["dataset"]]
    observations = _extract_observations(dataset_name, cfg["filters"], cfg["time_mode"])

    if start_date:
        observations = [o for o in observations if o["period"] >= start_date]
    if end_date:
        observations = [o for o in observations if o["period"] <= end_date]

    if not observations:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": "No observations returned"}

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
        "data_points": observations[:30],
        "total_observations": len(observations),
        "source": f"{METADATA_URL}?nazev={dataset_name}",
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
            "dataset": v["dataset"],
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
        "source": "CZSO Czech Republic Statistics",
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_catalog() -> Dict:
    """Discover available CZSO open datasets."""
    results = []
    for key, dataset_name in DATASETS.items():
        try:
            resp = requests.get(
                METADATA_URL, params={"nazev": dataset_name},
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            meta = resp.json()
            title = meta.get("název", {}).get("cs", "N/A")
            desc = meta.get("popis", {}).get("cs", "N/A")
            period = meta.get("časové_rozlišení", "N/A")
            time_range = meta.get("časové_pokrytí", {})
            results.append({
                "key": key,
                "dataset_name": dataset_name,
                "title": title,
                "description": desc,
                "periodicity": period,
                "time_start": time_range.get("začátek"),
                "time_end": time_range.get("konec"),
            })
        except Exception as e:
            results.append({"key": key, "dataset_name": dataset_name, "error": str(e)})
        time.sleep(REQUEST_DELAY)

    return {
        "success": True,
        "datasets": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# --- CLI ---

def _print_help():
    print("""
CZSO Czech Republic Statistics Module

Usage:
  python czso_czech.py                       # Latest values for all indicators
  python czso_czech.py <INDICATOR>           # Fetch specific indicator
  python czso_czech.py list                  # List available indicators
  python czso_czech.py catalog               # Discover CZSO datasets

Indicators:""")
    for key, cfg in INDICATORS.items():
        print(f"  {key:<25s} {cfg['name']}")
    print(f"""
Source: {METADATA_URL}
Protocol: REST / Open Data CSV
Coverage: Czech Republic
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h", "help"):
            _print_help()
        elif cmd == "list":
            print(json.dumps(get_available_indicators(), indent=2, default=str, ensure_ascii=False))
        elif cmd == "catalog":
            print(json.dumps(get_catalog(), indent=2, default=str, ensure_ascii=False))
        else:
            result = fetch_data(cmd)
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    else:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
