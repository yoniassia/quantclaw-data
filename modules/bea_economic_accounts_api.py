"""
BEA Economic Accounts API — U.S. Bureau of Economic Analysis

Comprehensive U.S. macroeconomic data from the Bureau of Economic Analysis:
- GDP (Gross Domestic Product) — growth rates + levels
- Personal Income (national + state)
- Personal Consumption Expenditures (PCE / Fed inflation gauge)
- International Trade Balance
- Industry Value Added (GDP by Industry)
- National Income and Product Accounts (NIPA)

Data sources (in priority order):
  1. BEA public NIPA flat files (CSV — no key needed, real data)
  2. BEA Data API (free key from https://apps.bea.gov/api/signup/)

Update frequency: Quarterly for GDP/NIPA, Monthly for trade
Coverage: Historical data back to 1929 for some series

Critical for:
- Macroeconomic modeling & recession forecasting
- Interest rate predictions
- Long-term strategic asset allocation
"""

import requests
import json
import os
import re
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "bea_economic_accounts"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_HOURS = 12  # BEA data updates infrequently

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (QuantClaw/1.0) Python/requests"
})

# ---------------------------------------------------------------------------
# BEA NIPA Series Code Reference
# ---------------------------------------------------------------------------
# Key series codes in NIPA flat files:
SERIES_CODES = {
    "A191RL": "Real GDP Percent Change (Annualized)",
    "A191RC": "Nominal GDP (Billions of dollars)",
    "A191RG": "Real GDP (Chained 2017 Dollars, Billions)",
    "DPCERL": "Real PCE Percent Change",
    "DPCERG": "Real PCE (Chained 2017 Dollars)",
    "A006RC": "Gross Private Domestic Investment (Nominal)",
    "A006RL": "Gross Private Domestic Investment % Change",
    "A822RC": "Federal Government Spending (Nominal)",
    "A822RL": "Federal Government Spending % Change",
    "B020RC": "Exports of Goods & Services (Nominal)",
    "B021RC": "Imports of Goods & Services (Nominal)",
    "A019RC": "Net Exports of Goods & Services (Nominal)",
    "A261RC": "Personal Income (Billions)",
    "A068RC": "Personal Saving (Billions)",
    "A072RC": "Personal Saving Rate (%)",
    "A001RC": "GDP (Billions, Current Dollars)",
}


def _get_cached(key: str) -> Optional[dict]:
    """Return cached JSON if still fresh."""
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if age < timedelta(hours=CACHE_HOURS):
            with open(path) as f:
                return json.load(f)
    return None


def _set_cache(key: str, data):
    """Persist data as JSON."""
    path = CACHE_DIR / f"{key}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# BEA Public NIPA Flat Files (NO KEY NEEDED)
# ---------------------------------------------------------------------------

NIPA_BASE = "https://apps.bea.gov/national/Release/TXT"


def _fetch_nipa_flat(frequency: str = "Q") -> List[dict]:
    """
    Fetch BEA NIPA flat file (CSV) — no API key needed.

    Args:
        frequency: 'Q' (quarterly), 'A' (annual)

    Returns:
        List of {series_code, period, value} dicts.
    """
    suffix = {"Q": "Q", "A": "A", "M": "Q"}.get(frequency.upper(), "Q")
    url = f"{NIPA_BASE}/NipaData{suffix}.txt"

    cache_key = f"nipa_flat_{suffix}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    resp = _SESSION.get(url, timeout=60)
    resp.raise_for_status()

    rows = []
    for line in resp.text.strip().split("\n"):
        if line.startswith("%") or not line.strip():
            continue
        parts = line.split(",", 2)
        if len(parts) == 3:
            code = parts[0].strip()
            period = parts[1].strip()
            value_str = parts[2].strip().strip('"').replace(",", "")
            try:
                value = float(value_str)
            except ValueError:
                value = value_str
            rows.append({"series_code": code, "period": period, "value": value})

    _set_cache(cache_key, rows)
    return rows


def _extract_series(series_code: str, frequency: str = "Q",
                    last_n: Optional[int] = None,
                    year: Optional[str] = None) -> List[dict]:
    """
    Extract a specific series from NIPA flat data.

    Args:
        series_code: BEA series code (e.g. 'A191RL')
        frequency: 'Q' or 'A'
        last_n: Return only last N observations
        year: Filter to specific year(s), comma-separated

    Returns:
        List of {period, value} dicts, sorted chronologically.
    """
    all_data = _fetch_nipa_flat(frequency)
    filtered = [r for r in all_data if r["series_code"] == series_code]

    if year and year.upper() != "ALL":
        years = set(y.strip() for y in year.split(","))
        filtered = [r for r in filtered if any(r["period"].startswith(y) for y in years)]

    result = [{"period": r["period"], "value": r["value"]} for r in filtered]
    result.sort(key=lambda x: x["period"])

    if last_n:
        result = result[-last_n:]

    return result


# ---------------------------------------------------------------------------
# BEA API (optional — requires free key)
# ---------------------------------------------------------------------------

BEA_API_BASE = "https://apps.bea.gov/api/data"


def _bea_api_key() -> Optional[str]:
    return os.getenv("BEA_API_KEY")


def _bea_request(params: dict) -> dict:
    """Make authenticated BEA API request. Raises if no key or API error."""
    key = _bea_api_key()
    if not key:
        raise EnvironmentError("BEA_API_KEY not set")
    params["UserID"] = key
    params["ResultFormat"] = "JSON"
    resp = _SESSION.get(BEA_API_BASE, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "BEAAPI" in data:
        results = data["BEAAPI"].get("Results", {})
        if "Error" in results:
            raise RuntimeError(results["Error"].get("APIErrorDescription", "BEA API error"))
    return data


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def get_datasets() -> List[Dict]:
    """
    List all available BEA datasets.

    Returns:
        List of dicts with 'name' and 'description' keys.
        Uses API if key available, otherwise returns curated static list.
    """
    cache_key = "datasets"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        data = _bea_request({"method": "GetDataSetList"})
        datasets = data["BEAAPI"]["Results"]["Dataset"]
        formatted = [{"name": ds["DatasetName"], "description": ds["DatasetDescription"]} for ds in datasets]
        _set_cache(cache_key, formatted)
        return formatted
    except Exception:
        pass

    static = [
        {"name": "NIPA", "description": "National Income and Product Accounts"},
        {"name": "NIUnderlyingDetail", "description": "NIPA Underlying Detail Tables"},
        {"name": "MNE", "description": "Multinational Enterprises"},
        {"name": "FixedAssets", "description": "Fixed Assets"},
        {"name": "ITA", "description": "International Transactions Accounts"},
        {"name": "IIP", "description": "International Investment Position"},
        {"name": "InputOutput", "description": "Input-Output Data"},
        {"name": "IntlServTrade", "description": "International Services Trade"},
        {"name": "GDPbyIndustry", "description": "GDP by Industry"},
        {"name": "Regional", "description": "Regional Data (Income, GDP, Employment)"},
        {"name": "UnderlyingGDPbyIndustry", "description": "Underlying GDP by Industry Detail"},
    ]
    _set_cache(cache_key, static)
    return static


def get_gdp(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. Real GDP percent change (annualized quarterly rate).

    Uses BEA public NIPA flat files — NO API KEY NEEDED.
    Series A191RL = Real GDP Percent Change from Preceding Period.

    Args:
        frequency: 'Q' (quarterly) or 'A' (annual)
        year: e.g. '2024', '2023,2024', or 'ALL'
        last_n: Return last N observations (default 20)

    Returns:
        dict with GDP growth data.

    Example:
        >>> get_gdp('Q', '2024,2025')
        {'indicator': 'Real GDP Percent Change', 'data': [...]}
    """
    data = _extract_series("A191RL", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Real GDP Percent Change (Annualized)",
        "series_code": "A191RL",
        "frequency": frequency,
        "unit": "percent",
        "count": len(data),
        "data": data,
    }


def get_gdp_level(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. Nominal GDP level (billions of current dollars).

    Series A191RC = GDP in current dollars.

    Args:
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with GDP level data.
    """
    data = _extract_series("A191RC", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Nominal GDP",
        "series_code": "A191RC",
        "frequency": frequency,
        "unit": "billions_usd",
        "count": len(data),
        "data": data,
    }


def get_gdp_real(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. Real GDP level (chained 2017 dollars, billions).

    Series A191RG.

    Args:
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with real GDP data.
    """
    data = _extract_series("A191RG", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Real GDP (Chained 2017 Dollars)",
        "series_code": "A191RG",
        "frequency": frequency,
        "unit": "billions_chained_2017_usd",
        "count": len(data),
        "data": data,
    }


def get_gdp_summary() -> dict:
    """
    Quick GDP summary — latest 8 quarters of Real GDP growth.
    Always works, no API key needed.

    Returns:
        dict with recent GDP growth rates.
    """
    return get_gdp("Q", "ALL", last_n=8)


def get_personal_income(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. Personal Income (billions of dollars).

    Series A261RC.

    Args:
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with personal income data.
    """
    data = _extract_series("A261RC", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Personal Income",
        "series_code": "A261RC",
        "frequency": frequency,
        "unit": "billions_usd",
        "count": len(data),
        "data": data,
    }


def get_personal_saving_rate(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. Personal Saving Rate (%).

    Series A072RC.

    Args:
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with saving rate data.
    """
    data = _extract_series("A072RC", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Personal Saving Rate",
        "series_code": "A072RC",
        "frequency": frequency,
        "unit": "percent",
        "count": len(data),
        "data": data,
    }


def get_pce(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get Personal Consumption Expenditures percent change.
    PCE is the Fed's preferred inflation gauge.

    Series DPCERL = Real PCE Percent Change.

    Args:
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with PCE growth data.
    """
    data = _extract_series("DPCERL", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Real PCE Percent Change",
        "series_code": "DPCERL",
        "frequency": frequency,
        "unit": "percent",
        "count": len(data),
        "data": data,
    }


def get_trade_data(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get U.S. exports and imports (nominal, billions).

    Returns:
        dict with exports (A020RC) and imports (A021RC).
    """
    exports = _extract_series("B020RC", frequency, last_n=last_n, year=year)
    imports = _extract_series("B021RC", frequency, last_n=last_n, year=year)

    # Compute trade balance
    balance = []
    imp_map = {r["period"]: r["value"] for r in imports}
    for exp in exports:
        p = exp["period"]
        if p in imp_map and isinstance(exp["value"], (int, float)) and isinstance(imp_map[p], (int, float)):
            balance.append({"period": p, "value": round(exp["value"] - imp_map[p], 1)})

    return {
        "source": "bea_nipa_flat_file",
        "frequency": frequency,
        "exports": {"series_code": "B020RC", "unit": "millions_usd", "data": exports},
        "imports": {"series_code": "B021RC", "unit": "millions_usd", "data": imports},
        "trade_balance": {"unit": "billions_usd", "data": balance},
    }


def get_investment(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get Gross Private Domestic Investment percent change.

    Series A006RL.

    Returns:
        dict with investment growth data.
    """
    data = _extract_series("A006RL", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Gross Private Domestic Investment % Change",
        "series_code": "A006RL",
        "frequency": frequency,
        "unit": "percent",
        "count": len(data),
        "data": data,
    }


def get_government_spending(frequency: str = "Q", year: str = "ALL", last_n: int = 20) -> dict:
    """
    Get Federal Government Spending percent change.

    Series A822RL.

    Returns:
        dict with government spending growth data.
    """
    data = _extract_series("A822RL", frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": "Federal Government Spending % Change",
        "series_code": "A822RL",
        "frequency": frequency,
        "unit": "percent",
        "count": len(data),
        "data": data,
    }


def get_series(series_code: str, frequency: str = "Q", year: str = "ALL",
               last_n: int = 20) -> dict:
    """
    Fetch any NIPA series by code from the public flat file.

    See SERIES_CODES dict for common codes, or use search_series().

    Args:
        series_code: BEA NIPA series code (e.g. 'A191RL')
        frequency: 'Q' or 'A'
        year: e.g. '2024' or 'ALL'
        last_n: Return last N observations

    Returns:
        dict with series data.
    """
    desc = SERIES_CODES.get(series_code, "Custom series")
    data = _extract_series(series_code, frequency, last_n=last_n, year=year)
    return {
        "source": "bea_nipa_flat_file",
        "indicator": desc,
        "series_code": series_code,
        "frequency": frequency,
        "count": len(data),
        "data": data,
    }


def get_nipa_table(table_name: str, frequency: str = "Q", year: str = "ALL") -> dict:
    """
    Fetch a NIPA table via BEA API (requires BEA_API_KEY).

    Common tables:
        T10101 - Percent Change in Real GDP
        T10105 - Nominal GDP
        T10106 - Real GDP (Chained 2017 dollars)
        T20100 - Personal Income and Disposition
        T20301 - Personal Consumption Expenditures
        T20804 - PCE Chain Price Indexes
        T30100 - Government Receipts and Expenditures
        T40100 - Foreign Transactions

    Args:
        table_name: BEA NIPA table identifier
        frequency: 'Q', 'A', or 'M'
        year: e.g. '2024' or 'ALL'

    Returns:
        dict with table data.
    """
    cache_key = f"nipa_{table_name}_{frequency}_{year}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        data = _bea_request({
            "method": "GetData",
            "datasetname": "NIPA",
            "TableName": table_name,
            "Frequency": frequency,
            "Year": year,
        })
        rows = data["BEAAPI"]["Results"]["Data"]
        result = {
            "source": "bea_api",
            "table": table_name,
            "frequency": frequency,
            "count": len(rows),
            "data": rows,
        }
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "hint": "Requires BEA_API_KEY env var. Get free key at https://apps.bea.gov/api/signup/",
            "alternative": "Use get_series() with a series code for key-free access.",
        }


def get_industry_data(industry: str = "ALL", year: str = "ALL") -> dict:
    """
    Get GDP by Industry data (requires BEA_API_KEY).

    Args:
        industry: BEA industry code or 'ALL'
        year: e.g. '2024' or 'ALL'

    Returns:
        dict with industry value added data.
    """
    cache_key = f"industry_{industry}_{year}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        data = _bea_request({
            "method": "GetData",
            "datasetname": "GDPbyIndustry",
            "Industry": industry,
            "Frequency": "A",
            "Year": year,
            "TableID": "1",
        })
        rows = data["BEAAPI"]["Results"]["Data"]
        result = {
            "source": "bea_api",
            "description": "GDP by Industry — Value Added",
            "industry": industry,
            "count": len(rows),
            "data": rows,
        }
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e), "hint": "Requires BEA_API_KEY"}


def get_state_income(state: str = "US", year: str = "ALL") -> dict:
    """
    Get personal income by state (requires BEA_API_KEY).

    Args:
        state: 'US' for all states, or 2-letter code (e.g. 'CA', 'NY')
        year: e.g. '2024' or 'ALL'

    Returns:
        dict with state income data.
    """
    cache_key = f"state_income_{state}_{year}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        geo = "STATE" if state == "US" else state
        data = _bea_request({
            "method": "GetData",
            "datasetname": "Regional",
            "TableName": "SAINC1",
            "LineCode": "1",
            "GeoFips": geo,
            "Year": year,
        })
        rows = data["BEAAPI"]["Results"]["Data"]
        result = {
            "source": "bea_api",
            "table": "SAINC1",
            "description": "State Annual Personal Income",
            "state": state,
            "count": len(rows),
            "data": rows,
        }
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e), "hint": "Requires BEA_API_KEY"}


def search_series(keyword: str) -> List[dict]:
    """
    Search known NIPA series codes by keyword.

    Args:
        keyword: Search term (e.g. 'gdp', 'income', 'saving')

    Returns:
        List of matching {series_code, description} dicts.
    """
    kw = keyword.lower()
    return [
        {"series_code": code, "description": desc}
        for code, desc in SERIES_CODES.items()
        if kw in desc.lower()
    ]


def search_tables(keyword: str) -> List[dict]:
    """
    Search NIPA tables by keyword.

    Args:
        keyword: e.g. 'consumption', 'investment', 'inflation'

    Returns:
        List of matching table references.
    """
    tables = [
        {"table": "T10101", "name": "Percent Change in Real GDP", "keywords": "gdp growth rate"},
        {"table": "T10105", "name": "Gross Domestic Product (Nominal)", "keywords": "gdp nominal level"},
        {"table": "T10106", "name": "Real GDP (Chained 2017 Dollars)", "keywords": "gdp real level"},
        {"table": "T10107", "name": "GDP Price Index", "keywords": "gdp deflator price index"},
        {"table": "T10301", "name": "Real GDP % Change by Component", "keywords": "consumption investment government exports"},
        {"table": "T20100", "name": "Personal Income and Disposition", "keywords": "income saving wages salary"},
        {"table": "T20301", "name": "Personal Consumption Expenditures", "keywords": "consumption spending consumer pce"},
        {"table": "T20304", "name": "PCE Price Index", "keywords": "pce inflation price consumer"},
        {"table": "T20804", "name": "PCE Chain Price Indexes", "keywords": "pce inflation chain deflator"},
        {"table": "T30100", "name": "Government Receipts and Expenditures", "keywords": "government spending fiscal budget deficit"},
        {"table": "T30200", "name": "Federal Government Receipts", "keywords": "federal budget deficit surplus"},
        {"table": "T40100", "name": "Foreign Transactions", "keywords": "trade exports imports current account"},
        {"table": "T50100", "name": "Saving and Investment", "keywords": "saving investment gross domestic private"},
        {"table": "T50200", "name": "Gross Private Domestic Investment", "keywords": "investment business residential fixed"},
        {"table": "T60100", "name": "National Income by Type", "keywords": "income compensation profits rental interest"},
        {"table": "T70100", "name": "GDP by Major Type of Product", "keywords": "goods services structures product"},
    ]
    kw = keyword.lower()
    return [t for t in tables if kw in t["name"].lower() or kw in t["keywords"]]


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------

MODULE_INFO = {
    "name": "bea_economic_accounts_api",
    "description": "U.S. Bureau of Economic Analysis — GDP, income, trade, investment, PCE data",
    "source": "https://apps.bea.gov/api/",
    "requires_key": False,
    "key_env_var": "BEA_API_KEY",
    "key_signup": "https://apps.bea.gov/api/signup/",
    "functions": [
        "get_datasets", "get_gdp", "get_gdp_level", "get_gdp_real",
        "get_gdp_summary", "get_personal_income", "get_personal_saving_rate",
        "get_pce", "get_trade_data", "get_investment", "get_government_spending",
        "get_series", "get_nipa_table", "get_industry_data", "get_state_income",
        "search_series", "search_tables",
    ],
}

if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
