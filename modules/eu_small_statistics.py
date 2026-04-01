#!/usr/bin/env python3
"""
EU Small Statistics Offices Batch Module

Unified data module for 12 smaller EU member states: Bulgaria, Croatia, Cyprus,
Greece, Hungary, Latvia, Lithuania, Luxembourg, Malta, Romania, Slovakia, Slovenia.

Primary source: Eurostat REST API (JSON-stat 2.0) with country-level filtering.
Covers GDP, CPI/HICP, unemployment, employment, government finance, and
industrial production for all covered countries through a single interface.

Data Source: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data
Protocol: REST (JSON-stat 2.0)
Auth: None (open access, ~100 req/hour)
Coverage: BG, HR, CY, EL, HU, LV, LT, LU, MT, RO, SK, SI
Refresh: Monthly (CPI, unemployment, industrial production), Annual (GDP, employment, debt)

Author: QUANTCLAW DATA Build Agent
Initiative: 0042
"""

import json
import sys
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
CACHE_DIR = Path(__file__).parent.parent / "cache" / "eu_small_statistics"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

COUNTRIES = {
    "BG": {"name": "Bulgaria", "office": "NSI", "domain": "nsi.bg"},
    "HR": {"name": "Croatia", "office": "DZS", "domain": "dzs.hr"},
    "CY": {"name": "Cyprus", "office": "CYSTAT", "domain": "cystat.gov.cy"},
    "EL": {"name": "Greece", "office": "ELSTAT", "domain": "statistics.gr"},
    "HU": {"name": "Hungary", "office": "KSH", "domain": "ksh.hu"},
    "LV": {"name": "Latvia", "office": "CSB", "domain": "csb.gov.lv"},
    "LT": {"name": "Lithuania", "office": "Statistics Lithuania", "domain": "stat.gov.lt"},
    "LU": {"name": "Luxembourg", "office": "STATEC", "domain": "statec.lu"},
    "MT": {"name": "Malta", "office": "NSO", "domain": "nso.gov.mt"},
    "RO": {"name": "Romania", "office": "INS", "domain": "insse.ro"},
    "SK": {"name": "Slovakia", "office": "SO SR", "domain": "statistics.sk"},
    "SI": {"name": "Slovenia", "office": "SURS", "domain": "stat.si"},
}

GEO_ALIASES = {
    "GR": "EL", "GREECE": "EL", "BULGARIA": "BG", "CROATIA": "HR",
    "CYPRUS": "CY", "HUNGARY": "HU", "LATVIA": "LV", "LITHUANIA": "LT",
    "LUXEMBOURG": "LU", "MALTA": "MT", "ROMANIA": "RO", "SLOVAKIA": "SK",
    "SLOVENIA": "SI",
}

INDICATORS = {
    # --- GDP & National Accounts (annual, from nama_10_gdp) ---
    "GDP_NOMINAL": {
        "dataset": "nama_10_gdp",
        "params": {"na_item": "B1GQ", "unit": "CP_MEUR"},
        "name": "GDP — Current Prices (EUR mn)",
        "description": "Gross domestic product at market prices, current prices, million EUR",
        "frequency": "annual",
        "unit": "EUR mn",
        "category": "GDP & National Accounts",
    },
    "GDP_REAL": {
        "dataset": "nama_10_gdp",
        "params": {"na_item": "B1GQ", "unit": "CLV10_MEUR"},
        "name": "GDP — Chain Linked Volumes 2010 (EUR mn)",
        "description": "Gross domestic product, chain linked volumes (2010), million EUR",
        "frequency": "annual",
        "unit": "EUR mn",
        "category": "GDP & National Accounts",
    },
    "GDP_GROWTH": {
        "dataset": "nama_10_gdp",
        "params": {"na_item": "B1GQ", "unit": "CLV_PCH_PRE"},
        "name": "GDP Growth Rate (%)",
        "description": "Real GDP growth, percentage change on previous year",
        "frequency": "annual",
        "unit": "%",
        "category": "GDP & National Accounts",
    },
    "GDP_PER_CAPITA": {
        "dataset": "nama_10_pc",
        "params": {"na_item": "B1GQ", "unit": "CP_EUR_HAB"},
        "name": "GDP per Capita (EUR)",
        "description": "GDP at market prices, current prices, EUR per inhabitant",
        "frequency": "annual",
        "unit": "EUR",
        "category": "GDP & National Accounts",
    },

    # --- Consumer Prices / HICP (monthly) ---
    "CPI_YOY": {
        "dataset": "prc_hicp_manr",
        "params": {"coicop": "CP00"},
        "name": "HICP Inflation — All Items YoY (%)",
        "description": "Harmonised index of consumer prices, all items, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "Consumer Prices",
    },
    "CPI_FOOD_YOY": {
        "dataset": "prc_hicp_manr",
        "params": {"coicop": "CP01"},
        "name": "HICP Food Inflation YoY (%)",
        "description": "HICP food and non-alcoholic beverages, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "Consumer Prices",
    },
    "CPI_ENERGY_YOY": {
        "dataset": "prc_hicp_manr",
        "params": {"coicop": "NRG"},
        "name": "HICP Energy Inflation YoY (%)",
        "description": "HICP energy items, annual rate of change",
        "frequency": "monthly",
        "unit": "%",
        "category": "Consumer Prices",
    },
    "CPI_INDEX": {
        "dataset": "prc_hicp_midx",
        "params": {"coicop": "CP00", "unit": "I15"},
        "name": "HICP Index (2015=100)",
        "description": "Harmonised index of consumer prices, all items, index 2015=100",
        "frequency": "monthly",
        "unit": "Index 2015=100",
        "category": "Consumer Prices",
    },

    # --- Labour Market ---
    "UNEMPLOYMENT_RATE": {
        "dataset": "une_rt_m",
        "params": {"age": "TOTAL", "sex": "T", "unit": "PC_ACT", "s_adj": "SA"},
        "name": "Unemployment Rate — Total (%)",
        "description": "Harmonised unemployment rate, total, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "Labour Market",
    },
    "YOUTH_UNEMPLOYMENT": {
        "dataset": "une_rt_m",
        "params": {"age": "Y_LT25", "sex": "T", "unit": "PC_ACT", "s_adj": "SA"},
        "name": "Youth Unemployment Rate — Under 25 (%)",
        "description": "Harmonised unemployment rate, under 25 years, seasonally adjusted",
        "frequency": "monthly",
        "unit": "%",
        "category": "Labour Market",
    },
    "EMPLOYMENT_RATE": {
        "dataset": "lfsi_emp_a",
        "params": {"indic_em": "EMP_LFS", "age": "Y20-64", "sex": "T", "unit": "PC_POP"},
        "name": "Employment Rate — 20-64 Age Group (%)",
        "description": "Employment rate, age group 20-64, percentage of population",
        "frequency": "annual",
        "unit": "%",
        "category": "Labour Market",
    },

    # --- Government Finance (annual) ---
    "GOV_DEBT": {
        "dataset": "gov_10dd_edpt1",
        "params": {"na_item": "GD", "unit": "PC_GDP", "sector": "S13"},
        "name": "Government Debt (% GDP)",
        "description": "General government consolidated gross debt as percentage of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Finance",
    },
    "GOV_DEFICIT": {
        "dataset": "gov_10dd_edpt1",
        "params": {"na_item": "B9", "unit": "PC_GDP", "sector": "S13"},
        "name": "Government Deficit/Surplus (% GDP)",
        "description": "Net lending (+) / net borrowing (-) as percentage of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Finance",
    },

    # --- Industry (annual, from national accounts GVA) ---
    "GVA_MANUFACTURING": {
        "dataset": "nama_10_a10",
        "params": {"na_item": "B1G", "unit": "CP_MEUR", "nace_r2": "C"},
        "name": "GVA Manufacturing (EUR mn)",
        "description": "Gross value added, manufacturing sector (NACE C), current prices, million EUR",
        "frequency": "annual",
        "unit": "EUR mn",
        "category": "Industry",
    },
    "CURRENT_ACCOUNT": {
        "dataset": "bop_c6_q",
        "params": {"bop_item": "CA", "stk_flow": "BAL", "currency": "MIO_EUR", "partner": "WRL_REST", "sectpart": "S1", "sector10": "S1"},
        "name": "Current Account Balance (EUR mn, quarterly)",
        "description": "Current account balance, all partners, million EUR",
        "frequency": "quarterly",
        "unit": "EUR mn",
        "category": "External Balance",
    },
}


def _resolve_geo(geo: str) -> str:
    geo = geo.upper().strip()
    if geo in COUNTRIES:
        return geo
    return GEO_ALIASES.get(geo, geo)


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


def _parse_jsonstat(raw: Dict) -> List[Dict]:
    """Parse Eurostat JSON-stat 2.0 response into time/value records."""
    dims = raw.get("id", [])
    sizes = raw.get("size", [])
    values = raw.get("value", {})
    dimension_info = raw.get("dimension", {})

    if not dims or not values:
        return []

    dim_keys = []
    for dim_id in dims:
        cat = dimension_info.get(dim_id, {}).get("category", {})
        idx = cat.get("index", {})
        labels = cat.get("label", {})
        ordered = sorted(idx.items(), key=lambda x: x[1])
        dim_keys.append([(code, labels.get(code, code)) for code, _ in ordered])

    def _idx_to_flat(indices):
        flat = 0
        multiplier = 1
        for i in range(len(sizes) - 1, -1, -1):
            flat += indices[i] * multiplier
            multiplier *= sizes[i]
        return flat

    results = []

    def _recurse(dim_pos, indices, labels):
        if dim_pos == len(dims):
            flat = _idx_to_flat(indices)
            key = str(flat)
            if key in values and values[key] is not None:
                record = {"value": values[key]}
                for i, d in enumerate(dims):
                    record[d] = labels[i][0]
                    if labels[i][1] != labels[i][0]:
                        record[f"{d}_label"] = labels[i][1]
                results.append(record)
            return
        for code, label in dim_keys[dim_pos]:
            new_indices = indices + [dim_keys[dim_pos].index((code, label))]
            new_labels = labels + [(code, label)]
            _recurse(dim_pos + 1, new_indices, new_labels)

    _recurse(0, [], [])
    results.sort(key=lambda x: x.get("time", ""), reverse=True)
    return results


def _api_request(dataset: str, params: Dict, geo: str, last_n: int = 12) -> Dict:
    url = f"{BASE_URL}/{dataset}"
    query = {**params, "geo": geo, "lastTimePeriod": last_n}
    try:
        resp = requests.get(url, params=query, timeout=REQUEST_TIMEOUT)
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


def fetch_data(indicator: str, geo: str = "BG", last_n: int = 12) -> Dict:
    """Fetch a specific indicator for a given country."""
    indicator = indicator.upper()
    geo = _resolve_geo(geo)

    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}
    if geo not in COUNTRIES:
        return {"success": False, "error": f"Country not covered: {geo}", "available": list(COUNTRIES.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "geo": geo, "last_n": last_n}
    cp = _cache_path(f"{geo}_{indicator}", _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["dataset"], cfg["params"], geo=geo, last_n=last_n)
    if not result["success"]:
        return {
            "success": False, "indicator": indicator, "geo": geo,
            "country": COUNTRIES[geo]["name"], "name": cfg["name"],
            "error": result["error"],
        }

    observations = _parse_jsonstat(result["data"])
    if not observations:
        return {
            "success": False, "indicator": indicator, "geo": geo,
            "country": COUNTRIES[geo]["name"], "name": cfg["name"],
            "error": "No observations returned",
        }

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
        "category": cfg["category"],
        "geo": geo,
        "country": COUNTRIES[geo]["name"],
        "statistics_office": COUNTRIES[geo]["office"],
        "latest_value": observations[0]["value"],
        "latest_period": observations[0].get("time", ""),
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "data_points": [{"period": o.get("time", ""), "value": o["value"]} for o in observations],
        "total_observations": len(observations),
        "source": f"{BASE_URL}/{cfg['dataset']}",
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
            "category": v["category"],
            "dataset": v["dataset"],
        }
        for k, v in INDICATORS.items()
    ]


def get_latest(indicator: str = None, geo: str = None) -> Dict:
    """Get latest values — by country, by indicator across countries, or summary."""
    if indicator and geo:
        return fetch_data(indicator, geo=geo)

    if geo:
        geo = _resolve_geo(geo)
        if geo not in COUNTRIES:
            return {"success": False, "error": f"Country not covered: {geo}"}
        results = {}
        errors = []
        for key in INDICATORS:
            data = fetch_data(key, geo=geo)
            if data.get("success"):
                results[key] = {
                    "name": data["name"],
                    "value": data["latest_value"],
                    "period": data["latest_period"],
                    "unit": data["unit"],
                    "category": data["category"],
                }
            else:
                errors.append({"indicator": key, "error": data.get("error", "unknown")})
            time.sleep(REQUEST_DELAY)
        return {
            "success": True,
            "source": "Eurostat (EU Small Statistics Offices)",
            "geo": geo,
            "country": COUNTRIES[geo]["name"],
            "statistics_office": COUNTRIES[geo]["office"],
            "indicators": results,
            "errors": errors if errors else None,
            "count": len(results),
            "timestamp": datetime.now().isoformat(),
        }

    if indicator:
        indicator = indicator.upper()
        if indicator not in INDICATORS:
            return {"success": False, "error": f"Unknown indicator: {indicator}"}
        comparison = {}
        errors = []
        for geo_code in COUNTRIES:
            data = fetch_data(indicator, geo=geo_code, last_n=3)
            if data.get("success"):
                comparison[geo_code] = {
                    "country": COUNTRIES[geo_code]["name"],
                    "value": data["latest_value"],
                    "period": data["latest_period"],
                }
            else:
                errors.append({"geo": geo_code, "error": data.get("error", "unknown")})
            time.sleep(REQUEST_DELAY)
        ranked = sorted(comparison.items(), key=lambda x: x[1]["value"], reverse=True)
        return {
            "success": True,
            "indicator": indicator,
            "name": INDICATORS[indicator]["name"],
            "unit": INDICATORS[indicator]["unit"],
            "ranking": [{"geo": g, **v, "rank": i + 1} for i, (g, v) in enumerate(ranked)],
            "countries_ok": len(comparison),
            "errors": errors if errors else None,
            "timestamp": datetime.now().isoformat(),
        }

    summary = {}
    core = ["GDP_GROWTH", "CPI_YOY", "UNEMPLOYMENT_RATE"]
    for geo_code, info in COUNTRIES.items():
        country_data = {}
        for ind in core:
            data = fetch_data(ind, geo=geo_code, last_n=3)
            if data.get("success"):
                country_data[ind] = {"value": data["latest_value"], "period": data["latest_period"]}
            time.sleep(REQUEST_DELAY)
        if country_data:
            summary[geo_code] = {"country": info["name"], "office": info["office"], **country_data}
    return {
        "success": True,
        "source": "Eurostat (EU Small Statistics Offices)",
        "core_indicators": core,
        "summary": summary,
        "countries": len(summary),
        "timestamp": datetime.now().isoformat(),
    }


def _print_help():
    print("""
EU Small Statistics Offices Batch Module (Initiative 0042)

Unified data for 12 smaller EU member states via Eurostat.

Usage:
  python eu_small_statistics.py                              # Summary (GDP growth, CPI, unemployment)
  python eu_small_statistics.py <COUNTRY>                    # All indicators for a country
  python eu_small_statistics.py <COUNTRY> <INDICATOR>        # Specific indicator for a country
  python eu_small_statistics.py list                         # List all indicators
  python eu_small_statistics.py countries                    # List covered countries
  python eu_small_statistics.py compare <INDICATOR>          # Compare indicator across all 12 countries

Countries:""")
    for code, info in COUNTRIES.items():
        print(f"  {code:<4s} {info['name']:<15s} ({info['office']}, {info['domain']})")
    print("\nIndicators:")
    categories = {}
    for key, cfg in INDICATORS.items():
        categories.setdefault(cfg["category"], []).append((key, cfg["name"]))
    for cat, items in categories.items():
        print(f"\n  [{cat}]")
        for key, name in items:
            print(f"    {key:<28s} {name}")
    print(f"""
Source: {BASE_URL}
Coverage: 12 EU Member States (BG, HR, CY, EL, HU, LV, LT, LU, MT, RO, SK, SI)
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        result = get_latest()
        print(json.dumps(result, indent=2, default=str))
    elif args[0] in ("--help", "-h", "help"):
        _print_help()
    elif args[0] == "list":
        print(json.dumps(get_available_indicators(), indent=2, default=str))
    elif args[0] == "countries":
        print(json.dumps(COUNTRIES, indent=2, default=str))
    elif args[0] == "compare" and len(args) >= 2:
        print(json.dumps(get_latest(indicator=args[1]), indent=2, default=str))
    else:
        geo = _resolve_geo(args[0])
        if geo in COUNTRIES:
            if len(args) >= 2:
                result = fetch_data(args[1], geo=geo)
            else:
                result = get_latest(geo=geo)
            print(json.dumps(result, indent=2, default=str))
        else:
            result = fetch_data(args[0])
            print(json.dumps(result, indent=2, default=str))
