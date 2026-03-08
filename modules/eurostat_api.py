#!/usr/bin/env python3
"""
Eurostat API — European Union macroeconomic data via Eurostat REST API.

Source: https://ec.europa.eu/eurostat/web/main/data/web-services
Category: Labor & Demographics / Macroeconomics
Free tier: true — No API key required, rate limit ~100 calls/hour
Update frequency: Monthly/Quarterly/Annual depending on dataset
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional


BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
TIMEOUT = 30

# Common geo codes
GEO_EU27 = "EU27_2020"
GEO_EA20 = "EA20"  # Euro area
MAJOR_ECONOMIES = ["DE", "FR", "IT", "ES", "NL", "PL", "SE", "BE", "AT", "IE"]

# Dataset IDs
DATASETS = {
    "gdp": "nama_10_gdp",
    "gdp_growth": "namq_10_gdp",
    "unemployment_monthly": "une_rt_m",
    "unemployment_annual": "une_rt_a",
    "hicp_inflation": "prc_hicp_manr",
    "population": "demo_pjan",
    "government_debt": "gov_10dd_edpt1",
    "government_deficit": "gov_10dd_edpt1",
    "trade_balance": "bop_c6_m",
    "industrial_production": "sts_inpr_m",
}


def _fetch(dataset: str, params: dict) -> dict:
    """
    Internal: fetch data from Eurostat JSON API and return parsed response.

    Args:
        dataset: Eurostat dataset code (e.g. 'nama_10_gdp')
        params: Query parameters dict

    Returns:
        Parsed JSON response dict

    Raises:
        requests.RequestException on network errors
        ValueError on API errors
    """
    params.setdefault("format", "JSON")
    params.setdefault("lang", "EN")
    url = f"{BASE_URL}/{dataset}"
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"Eurostat API error: {data['error']}")
    return data


def _parse_response(data: dict) -> List[dict]:
    """
    Parse Eurostat JSON-stat response into a list of flat records.

    Each record is a dict with dimension labels as keys plus a 'value' key.

    Args:
        data: Raw Eurostat API JSON response

    Returns:
        List of dicts, one per data point
    """
    dims = data.get("id", [])
    sizes = data.get("size", [])
    dimension_info = data.get("dimension", {})
    values = data.get("value", {})

    # Build index-to-label maps for each dimension
    dim_labels = {}
    dim_indices = {}
    for dim_name in dims:
        cat = dimension_info.get(dim_name, {}).get("category", {})
        idx_map = cat.get("index", {})
        label_map = cat.get("label", {})
        # index maps code -> position; we need position -> code
        pos_to_code = {v: k for k, v in idx_map.items()}
        dim_labels[dim_name] = label_map
        dim_indices[dim_name] = pos_to_code

    # Iterate through all possible index combinations
    records = []
    total = 1
    for s in sizes:
        total *= s

    for flat_idx in range(total):
        str_idx = str(flat_idx)
        if str_idx not in values:
            continue

        # Decompose flat index into per-dimension indices
        record = {}
        remainder = flat_idx
        for i in range(len(dims) - 1, -1, -1):
            dim_name = dims[i]
            pos = remainder % sizes[i]
            remainder //= sizes[i]
            code = dim_indices[dim_name].get(pos, str(pos))
            record[dim_name] = code
            record[f"{dim_name}_label"] = dim_labels[dim_name].get(code, code)

        record["value"] = values[str_idx]
        records.append(record)

    return records


def get_gdp(geo: Optional[List[str]] = None, years: int = 5,
            unit: str = "CP_MEUR") -> Dict:
    """
    Get annual GDP for EU countries.

    Args:
        geo: List of country codes (default: EU27 aggregate)
        years: Number of recent years to fetch (default: 5)
        unit: Unit — CP_MEUR (current prices, million EUR),
              CLV10_MEUR (chain-linked volumes 2010)

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27]
    params = {
        "unit": unit,
        "na_item": "B1GQ",  # GDP at market prices
        "lastTimePeriod": str(years),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["gdp"], params)
    records = _parse_response(raw)
    return {
        "indicator": "GDP",
        "dataset": DATASETS["gdp"],
        "unit": unit,
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_unemployment(geo: Optional[List[str]] = None, months: int = 12,
                     sex: str = "T", age: str = "TOTAL") -> Dict:
    """
    Get monthly unemployment rate (seasonally adjusted).

    Args:
        geo: List of country codes (default: EU27, DE, FR)
        months: Number of recent months (default: 12)
        sex: T (total), M (male), F (female)
        age: TOTAL, Y_LT25 (youth), Y25-74

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27, "DE", "FR"]
    params = {
        "s_adj": "SA",
        "age": age,
        "unit": "PC_ACT",
        "sex": sex,
        "lastTimePeriod": str(months),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["unemployment_monthly"], params)
    records = _parse_response(raw)
    return {
        "indicator": "Unemployment Rate",
        "dataset": DATASETS["unemployment_monthly"],
        "unit": "% of active population",
        "seasonally_adjusted": True,
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_inflation(geo: Optional[List[str]] = None, months: int = 12,
                  coicop: str = "CP00") -> Dict:
    """
    Get HICP inflation rate (annual rate of change, monthly).

    Args:
        geo: List of country codes (default: EU27, EA20)
        months: Number of recent months (default: 12)
        coicop: COICOP classification — CP00 (all items),
                CP01 (food), CP04 (housing), CP07 (transport), NRG (energy)

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27, GEO_EA20]
    params = {
        "coicop": coicop,
        "lastTimePeriod": str(months),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["hicp_inflation"], params)
    records = _parse_response(raw)
    return {
        "indicator": "HICP Inflation (annual rate of change)",
        "dataset": DATASETS["hicp_inflation"],
        "unit": "% change on same period of previous year",
        "coicop": coicop,
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_population(geo: Optional[List[str]] = None, years: int = 5,
                   sex: str = "T", age: str = "TOTAL") -> Dict:
    """
    Get annual population on 1 January.

    Args:
        geo: List of country codes (default: EU27 + major economies)
        years: Number of recent years (default: 5)
        sex: T (total), M (male), F (female)
        age: TOTAL, or specific age like Y20, Y_LT15, Y_GE65

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27, "DE", "FR", "IT", "ES"]
    params = {
        "sex": sex,
        "age": age,
        "lastTimePeriod": str(years),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["population"], params)
    records = _parse_response(raw)
    return {
        "indicator": "Population (1 January)",
        "dataset": DATASETS["population"],
        "unit": "Persons",
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_government_debt(geo: Optional[List[str]] = None, years: int = 5) -> Dict:
    """
    Get government consolidated gross debt as % of GDP.

    Args:
        geo: List of country codes (default: EU27 + major economies)
        years: Number of recent years (default: 5)

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27, "DE", "FR", "IT", "ES", "GR"]
    params = {
        "unit": "PC_GDP",
        "sector": "S13",  # General government
        "na_item": "GD",  # Gross debt
        "lastTimePeriod": str(years),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["government_debt"], params)
    records = _parse_response(raw)
    return {
        "indicator": "Government Debt",
        "dataset": DATASETS["government_debt"],
        "unit": "% of GDP",
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_industrial_production(geo: Optional[List[str]] = None,
                               months: int = 12) -> Dict:
    """
    Get monthly industrial production index (seasonally adjusted).

    Args:
        geo: List of country codes (default: EU27, DE, FR)
        months: Number of recent months (default: 12)

    Returns:
        Dict with 'records' list and metadata
    """
    if geo is None:
        geo = [GEO_EU27, "DE", "FR"]
    params = {
        "s_adj": "SCA",  # Seasonally and calendar adjusted
        "unit": "I15",   # Index 2015=100
        "nace_r2": "B-D",  # Total industry
        "lastTimePeriod": str(months),
    }
    for g in geo:
        params.setdefault("geo", [])
        if isinstance(params["geo"], list):
            params["geo"].append(g)
        else:
            params["geo"] = [params["geo"], g]

    raw = _fetch(DATASETS["industrial_production"], params)
    records = _parse_response(raw)
    return {
        "indicator": "Industrial Production Index",
        "dataset": DATASETS["industrial_production"],
        "unit": "Index (2015=100)",
        "seasonally_adjusted": True,
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def get_dataset(dataset_code: str, params: dict) -> Dict:
    """
    Generic function to query any Eurostat dataset by code.

    Args:
        dataset_code: Eurostat dataset code (e.g. 'nama_10_gdp')
        params: Dict of query parameters (geo, unit, time, etc.)

    Returns:
        Dict with parsed records and metadata
    """
    raw = _fetch(dataset_code, params)
    records = _parse_response(raw)
    return {
        "dataset": dataset_code,
        "label": raw.get("label", ""),
        "source": "Eurostat",
        "updated": raw.get("updated", ""),
        "records": records,
        "count": len(records),
    }


def search_datasets(query: str, limit: int = 10) -> List[dict]:
    """
    Search Eurostat dataset catalog by keyword.

    Args:
        query: Search term (e.g. 'GDP', 'unemployment')
        limit: Max results to return

    Returns:
        List of dicts with dataset code, title, last update
    """
    try:
        url = "https://ec.europa.eu/eurostat/api/dissemination/catalogue/toc"
        params = {"lang": "EN"}
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()

        items = resp.json() if isinstance(resp.json(), list) else resp.json().get("items", [])
        query_lower = query.lower()
        results = []

        if isinstance(items, dict):
            return _search_common_datasets(query_lower, limit)

        for item in items:
            title = item.get("title", "")
            code = item.get("code", "")
            if query_lower in title.lower() or query_lower in code.lower():
                results.append({
                    "code": code,
                    "title": title,
                    "last_update": item.get("lastUpdate", ""),
                })
                if len(results) >= limit:
                    break

        return results if results else _search_common_datasets(query_lower, limit)
    except Exception:
        # Catalog endpoint may not be available; use curated list
        return _search_common_datasets(query.lower(), limit)


def _search_common_datasets(query: str, limit: int) -> List[dict]:
    """Fallback: search in a curated list of common Eurostat datasets."""
    common = [
        {"code": "nama_10_gdp", "title": "GDP and main components (output, expenditure and income)"},
        {"code": "namq_10_gdp", "title": "GDP and main components - quarterly data"},
        {"code": "une_rt_m", "title": "Unemployment rate - monthly data"},
        {"code": "une_rt_a", "title": "Unemployment rate - annual data"},
        {"code": "prc_hicp_manr", "title": "HICP - annual rate of change (monthly)"},
        {"code": "prc_hicp_midx", "title": "HICP - monthly index"},
        {"code": "demo_pjan", "title": "Population on 1 January by age and sex"},
        {"code": "demo_gind", "title": "Population change - births, deaths, migration"},
        {"code": "gov_10dd_edpt1", "title": "Government deficit/surplus, debt - annual data"},
        {"code": "sts_inpr_m", "title": "Industrial production - monthly data"},
        {"code": "bop_c6_m", "title": "Balance of payments - monthly data"},
        {"code": "lfsa_ergan", "title": "Employment by sex, age and economic activity"},
        {"code": "lfsa_urgan", "title": "Unemployment by sex, age and economic activity"},
        {"code": "earn_ses_annual", "title": "Structure of earnings survey - annual"},
        {"code": "tec00001", "title": "GDP per capita in PPS"},
        {"code": "tec00115", "title": "Real GDP growth rate"},
        {"code": "tec00118", "title": "Government deficit/surplus as % of GDP"},
        {"code": "tipslm80", "title": "Long-term unemployment rate"},
        {"code": "tps00001", "title": "Population total"},
        {"code": "ei_bsci_m_r2", "title": "Economic Sentiment Indicator"},
    ]
    results = []
    for ds in common:
        if query in ds["code"].lower() or query in ds["title"].lower():
            results.append(ds)
            if len(results) >= limit:
                break
    return results


def get_eu_dashboard() -> Dict:
    """
    Get a quick EU economic dashboard: GDP, unemployment, inflation.

    Returns:
        Dict with key EU economic indicators
    """
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "source": "Eurostat",
        "indicators": {},
    }
    try:
        dashboard["indicators"]["gdp"] = get_gdp(years=3)
    except Exception as e:
        dashboard["indicators"]["gdp"] = {"error": str(e)}
    try:
        dashboard["indicators"]["unemployment"] = get_unemployment(months=6)
    except Exception as e:
        dashboard["indicators"]["unemployment"] = {"error": str(e)}
    try:
        dashboard["indicators"]["inflation"] = get_inflation(months=6)
    except Exception as e:
        dashboard["indicators"]["inflation"] = {"error": str(e)}

    return dashboard


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: eurostat_api.py <command> [args]")
        print("Commands: gdp, unemployment, inflation, population, debt,")
        print("          industrial, search <query>, dashboard")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "gdp":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_gdp(geo=geo)
    elif command == "unemployment":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_unemployment(geo=geo)
    elif command == "inflation":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_inflation(geo=geo)
    elif command == "population":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_population(geo=geo)
    elif command == "debt":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_government_debt(geo=geo)
    elif command == "industrial":
        geo = sys.argv[2:] if len(sys.argv) > 2 else None
        result = get_industrial_production(geo=geo)
    elif command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "gdp"
        result = search_datasets(query)
    elif command == "dashboard":
        result = get_eu_dashboard()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
