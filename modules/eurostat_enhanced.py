#!/usr/bin/env python3
"""
Eurostat Enhanced Module — EU Government Finance, Energy & Environment

Government deficit/debt, energy balances, renewable energy share,
greenhouse gas emissions by sector, environmental taxes, and digital economy.

Data Source: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data
Protocol: REST (JSON-stat 2.0)
Auth: None (open access, ~100 req/hour)
Coverage: EU27 + all Member States
Refresh: Annual (most datasets updated Q1-Q2 for prior year)

Author: QUANTCLAW DATA Build Agent
Initiative: 0037
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
CACHE_DIR = Path(__file__).parent.parent / "cache" / "eurostat_enhanced"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.3

EU_MEMBERS = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
]

INDICATORS = {
    # --- 1. Government Deficit & Debt ---
    "GOV_DEFICIT_SURPLUS": {
        "dataset": "gov_10dd_edpt1",
        "params": {"unit": "PC_GDP", "na_item": "B9", "sector": "S13"},
        "name": "Government Deficit/Surplus (% GDP)",
        "description": "General government net lending (+) / net borrowing (-) as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Deficit & Debt",
    },
    "GOV_DEBT": {
        "dataset": "gov_10dd_edpt1",
        "params": {"unit": "PC_GDP", "na_item": "GD", "sector": "S13"},
        "name": "Government Debt (% GDP)",
        "description": "Government consolidated gross debt (Maastricht) as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Deficit & Debt",
    },
    "GOV_EXPENDITURE": {
        "dataset": "gov_10a_main",
        "params": {"unit": "PC_GDP", "na_item": "TE", "sector": "S13"},
        "name": "Government Expenditure (% GDP)",
        "description": "Total general government expenditure as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Revenue & Spending",
    },
    "GOV_REVENUE": {
        "dataset": "gov_10a_main",
        "params": {"unit": "PC_GDP", "na_item": "TR", "sector": "S13"},
        "name": "Government Revenue (% GDP)",
        "description": "Total general government revenue as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Government Revenue & Spending",
    },

    # --- 2. Energy Production & Consumption ---
    "ENERGY_PRODUCTION": {
        "dataset": "nrg_bal_s",
        "params": {"nrg_bal": "PPRD", "siec": "TOTAL", "unit": "KTOE"},
        "name": "Total Energy Production (KTOE)",
        "description": "Primary production of all energy products, thousand tonnes of oil equivalent",
        "frequency": "annual",
        "unit": "KTOE",
        "category": "Energy Balance",
    },
    "ENERGY_CONSUMPTION": {
        "dataset": "nrg_bal_s",
        "params": {"nrg_bal": "AFC", "siec": "TOTAL", "unit": "KTOE"},
        "name": "Available Final Energy Consumption (KTOE)",
        "description": "Available for final consumption, all energy products, thousand tonnes of oil equivalent",
        "frequency": "annual",
        "unit": "KTOE",
        "category": "Energy Balance",
    },
    "ENERGY_DEPENDENCY": {
        "dataset": "sdg_07_50",
        "params": {"siec": "TOTAL"},
        "name": "Energy Import Dependency (%)",
        "description": "Share of net energy imports in gross available energy",
        "frequency": "annual",
        "unit": "%",
        "category": "Energy Balance",
    },

    # --- 3. Renewable Energy ---
    "RENEWABLE_SHARE_TOTAL": {
        "dataset": "nrg_ind_ren",
        "params": {"nrg_bal": "REN"},
        "name": "Renewable Energy Share — Overall (%)",
        "description": "Share of renewable energy in gross final energy consumption",
        "frequency": "annual",
        "unit": "%",
        "category": "Renewable Energy",
    },
    "RENEWABLE_SHARE_ELECTRICITY": {
        "dataset": "nrg_ind_ren",
        "params": {"nrg_bal": "REN_ELC"},
        "name": "Renewable Energy Share — Electricity (%)",
        "description": "Share of renewable energy sources in electricity generation",
        "frequency": "annual",
        "unit": "%",
        "category": "Renewable Energy",
    },
    "RENEWABLE_SHARE_TRANSPORT": {
        "dataset": "nrg_ind_ren",
        "params": {"nrg_bal": "REN_TRA"},
        "name": "Renewable Energy Share — Transport (%)",
        "description": "Share of renewable energy sources in transport",
        "frequency": "annual",
        "unit": "%",
        "category": "Renewable Energy",
    },
    "RENEWABLE_SHARE_HEATING": {
        "dataset": "nrg_ind_ren",
        "params": {"nrg_bal": "REN_HEAT_CL"},
        "name": "Renewable Energy Share — Heating/Cooling (%)",
        "description": "Share of renewable energy sources in heating and cooling",
        "frequency": "annual",
        "unit": "%",
        "category": "Renewable Energy",
    },

    # --- 4. Greenhouse Gas Emissions ---
    "GHG_TOTAL": {
        "dataset": "env_air_gge",
        "params": {"airpol": "GHG", "src_crf": "TOTXMEMO", "unit": "MIO_T"},
        "name": "Total GHG Emissions (Mt CO₂eq)",
        "description": "Total greenhouse gas emissions excl. memo items, million tonnes CO₂ equivalent",
        "frequency": "annual",
        "unit": "Mt CO₂eq",
        "category": "Emissions",
    },
    "GHG_ENERGY": {
        "dataset": "env_air_gge",
        "params": {"airpol": "GHG", "src_crf": "CRF1", "unit": "MIO_T"},
        "name": "GHG Emissions — Energy Sector (Mt CO₂eq)",
        "description": "Greenhouse gas emissions from energy sector (CRF 1)",
        "frequency": "annual",
        "unit": "Mt CO₂eq",
        "category": "Emissions",
    },
    "GHG_INDUSTRY": {
        "dataset": "env_air_gge",
        "params": {"airpol": "GHG", "src_crf": "CRF1A2", "unit": "MIO_T"},
        "name": "GHG Emissions — Manufacturing/Construction (Mt CO₂eq)",
        "description": "Greenhouse gas emissions from manufacturing industries and construction (CRF 1.A.2)",
        "frequency": "annual",
        "unit": "Mt CO₂eq",
        "category": "Emissions",
    },
    "GHG_TRANSPORT": {
        "dataset": "env_air_gge",
        "params": {"airpol": "GHG", "src_crf": "CRF1A3", "unit": "MIO_T"},
        "name": "GHG Emissions — Transport (Mt CO₂eq)",
        "description": "Greenhouse gas emissions from transport sector (CRF 1.A.3)",
        "frequency": "annual",
        "unit": "Mt CO₂eq",
        "category": "Emissions",
    },
    "GHG_AGRICULTURE": {
        "dataset": "env_air_gge",
        "params": {"airpol": "GHG", "src_crf": "CRF3", "unit": "MIO_T"},
        "name": "GHG Emissions — Agriculture (Mt CO₂eq)",
        "description": "Greenhouse gas emissions from agriculture sector (CRF 3)",
        "frequency": "annual",
        "unit": "Mt CO₂eq",
        "category": "Emissions",
    },

    # --- 5. Environmental Taxes ---
    "ENV_TAX_TOTAL": {
        "dataset": "env_ac_tax",
        "params": {"tax": "ENV", "unit": "PC_GDP"},
        "name": "Total Environmental Taxes (% GDP)",
        "description": "Total environmental tax revenue as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Environmental Taxes",
    },
    "ENV_TAX_ENERGY": {
        "dataset": "env_ac_tax",
        "params": {"tax": "NRG", "unit": "PC_GDP"},
        "name": "Energy Taxes (% GDP)",
        "description": "Energy tax revenue as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Environmental Taxes",
    },
    "ENV_TAX_TRANSPORT": {
        "dataset": "env_ac_tax",
        "params": {"tax": "TRA", "unit": "PC_GDP"},
        "name": "Transport Taxes (% GDP)",
        "description": "Transport tax revenue as % of GDP",
        "frequency": "annual",
        "unit": "% GDP",
        "category": "Environmental Taxes",
    },

    # --- 6. Digital Economy ---
    "DIGITAL_INTERNET_ACCESS": {
        "dataset": "isoc_ci_in_h",
        "params": {"unit": "PC_HH", "hhtyp": "TOTAL"},
        "name": "Household Internet Access (%)",
        "description": "Percentage of households with internet access at home",
        "frequency": "annual",
        "unit": "% households",
        "category": "Digital Economy",
    },
    "DIGITAL_INTERNET_USE": {
        "dataset": "isoc_ci_ifp_iu",
        "params": {"indic_is": "I_IU3", "unit": "PC_IND", "ind_type": "IND_TOTAL"},
        "name": "Internet Use by Individuals (%)",
        "description": "Percentage of individuals who used the internet in the last 3 months",
        "frequency": "annual",
        "unit": "% individuals",
        "category": "Digital Economy",
    },
    "DIGITAL_ECOMMERCE": {
        "dataset": "isoc_ec_ib20",
        "params": {"indic_is": "I_BUY3", "unit": "PC_IND", "ind_type": "IND_TOTAL"},
        "name": "E-Commerce by Individuals (%)",
        "description": "Percentage of individuals who purchased online in the last 3 months",
        "frequency": "annual",
        "unit": "% individuals",
        "category": "Digital Economy",
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

    time_dim_idx = None
    geo_dim_idx = None
    for i, d in enumerate(dims):
        if d == "time":
            time_dim_idx = i
        elif d == "geo":
            geo_dim_idx = i

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


def _api_request(dataset: str, params: Dict, geo: str = "DE", last_n: int = 10) -> Dict:
    """Fetch from Eurostat JSON-stat API."""
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


def fetch_data(indicator: str, geo: str = "DE", last_n: int = 10) -> Dict:
    """Fetch a specific indicator for a given country."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}", "available": list(INDICATORS.keys())}

    cfg = INDICATORS[indicator]
    cache_params = {"indicator": indicator, "geo": geo, "last_n": last_n}
    cp = _cache_path(indicator, _params_hash(cache_params))
    cached = _read_cache(cp)
    if cached:
        cached.pop("_cached_at", None)
        return cached

    result = _api_request(cfg["dataset"], cfg["params"], geo=geo, last_n=last_n)
    if not result["success"]:
        return {"success": False, "indicator": indicator, "name": cfg["name"], "error": result["error"]}

    observations = _parse_jsonstat(result["data"])
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
        "category": cfg["category"],
        "geo": geo,
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


def get_latest(indicator: str = None, geo: str = "DE") -> Dict:
    """Get latest values for one or all indicators."""
    if indicator:
        return fetch_data(indicator, geo=geo)

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
        "source": "Eurostat Enhanced (Gov Finance + Energy + Environment)",
        "geo": geo,
        "indicators": results,
        "errors": errors if errors else None,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


def get_country_comparison(indicator: str, countries: List[str] = None) -> Dict:
    """Compare a single indicator across multiple EU Member States."""
    indicator = indicator.upper()
    if indicator not in INDICATORS:
        return {"success": False, "error": f"Unknown indicator: {indicator}"}

    if countries is None:
        countries = EU_MEMBERS

    comparison = {}
    errors = []
    for geo in countries:
        data = fetch_data(indicator, geo=geo, last_n=3)
        if data.get("success"):
            comparison[geo] = {
                "value": data["latest_value"],
                "period": data["latest_period"],
            }
        else:
            errors.append({"geo": geo, "error": data.get("error", "unknown")})
        time.sleep(REQUEST_DELAY)

    ranked = sorted(comparison.items(), key=lambda x: x[1]["value"], reverse=True)

    return {
        "success": bool(comparison),
        "indicator": indicator,
        "name": INDICATORS[indicator]["name"],
        "unit": INDICATORS[indicator]["unit"],
        "ranking": [{"geo": g, **v, "rank": i + 1} for i, (g, v) in enumerate(ranked)],
        "countries_ok": len(comparison),
        "countries_failed": len(errors),
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(),
    }


def _print_help():
    print("""
Eurostat Enhanced — EU Government Finance, Energy & Environment

Usage:
  python eurostat_enhanced.py                              # Latest values (DE) for all indicators
  python eurostat_enhanced.py <INDICATOR>                   # Fetch specific indicator (DE)
  python eurostat_enhanced.py <INDICATOR> <GEO>             # Fetch indicator for country (e.g. FR)
  python eurostat_enhanced.py list                          # List all indicators
  python eurostat_enhanced.py compare <INDICATOR>           # Compare across EU Member States

Categories:""")
    categories = {}
    for key, cfg in INDICATORS.items():
        categories.setdefault(cfg["category"], []).append((key, cfg["name"]))
    for cat, items in categories.items():
        print(f"\n  [{cat}]")
        for key, name in items:
            print(f"    {key:<35s} {name}")
    print(f"""
Source: {BASE_URL}
Coverage: EU27 Member States
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
    elif args[0] == "compare" and len(args) >= 2:
        print(json.dumps(get_country_comparison(args[1]), indent=2, default=str))
    else:
        geo = args[1] if len(args) >= 2 else "DE"
        result = fetch_data(args[0], geo=geo)
        print(json.dumps(result, indent=2, default=str))
