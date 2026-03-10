#!/usr/bin/env python3
"""
FRED API — Federal Reserve Economic Data

Comprehensive module for accessing economic data from the Federal Reserve
Bank of St. Louis. Covers macro indicators, fixed income, credit markets,
treasury yields, labor market, inflation, and more.

Source: https://fred.stlouisfed.org/docs/api/fred.html
Category: Fixed Income & Credit / Macro Economics
Free tier: True (API key required, 1000 calls/day free)
Update frequency: Daily (varies by series)
Author: QuantClaw Data NightBuilder

Usage:
    from modules.fred_api import get_series, get_macro_snapshot, search_series
    gdp = get_series("GDP")
    snapshot = get_macro_snapshot()
    results = search_series("unemployment")
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/fred_api")
os.makedirs(CACHE_DIR, exist_ok=True)

# Key economic series organized by category
MACRO_SERIES = {
    "GDP": "Gross Domestic Product",
    "GDPC1": "Real GDP",
    "UNRATE": "Unemployment Rate",
    "CPIAUCSL": "Consumer Price Index (All Urban)",
    "CPILFESL": "Core CPI (Less Food & Energy)",
    "PCEPI": "PCE Price Index",
    "PCEPILFE": "Core PCE Price Index",
    "PAYEMS": "Total Nonfarm Payrolls",
    "ICSA": "Initial Jobless Claims",
    "UMCSENT": "U of Michigan Consumer Sentiment",
    "RSAFS": "Retail Sales",
    "INDPRO": "Industrial Production Index",
    "HOUST": "Housing Starts",
    "PERMIT": "Building Permits",
}

FIXED_INCOME_SERIES = {
    "DGS10": "10-Year Treasury Yield",
    "DGS2": "2-Year Treasury Yield",
    "DGS30": "30-Year Treasury Yield",
    "DGS5": "5-Year Treasury Yield",
    "DGS1": "1-Year Treasury Yield",
    "DFF": "Federal Funds Effective Rate",
    "T10Y2Y": "10Y-2Y Treasury Spread",
    "T10Y3M": "10Y-3M Treasury Spread",
    "DFEDTARU": "Fed Funds Target Rate Upper",
    "DFEDTARL": "Fed Funds Target Rate Lower",
}

CREDIT_SERIES = {
    "BAMLC0A0CM": "ICE BofA US Corporate Index OAS",
    "BAMLH0A0HYM2": "ICE BofA US High Yield OAS",
    "AAA": "Moody's AAA Corporate Bond Yield",
    "BAA": "Moody's BAA Corporate Bond Yield",
    "TEDRATE": "TED Spread",
    "T10YIE": "10-Year Breakeven Inflation Rate",
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
    "MORTGAGE15US": "15-Year Fixed Mortgage Rate",
}

MONEY_SUPPLY_SERIES = {
    "M1SL": "M1 Money Supply",
    "M2SL": "M2 Money Supply",
    "WALCL": "Fed Total Assets",
    "BOGMBASE": "Monetary Base",
}


def _get_api_key(api_key: Optional[str] = None) -> str:
    """Resolve FRED API key from argument, env, or raise error."""
    key = api_key or FRED_API_KEY
    if not key:
        raise ValueError(
            "FRED API key required. Set FRED_API_KEY env var or pass api_key parameter. "
            "Get free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return key


def _cached_request(url: str, params: dict, cache_key: str, ttl_hours: int = 4) -> dict:
    """Make a cached HTTP request to FRED API."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")

    if os.path.exists(cache_file):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if age < timedelta(hours=ttl_hours):
            with open(cache_file) as f:
                return json.load(f)

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "error_message" in data:
            return {"error": data["error_message"]}

        with open(cache_file, "w") as f:
            json.dump(data, f)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


def get_series(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    sort_order: str = "desc",
    api_key: Optional[str] = None,
) -> Dict:
    """
    Fetch observations for a FRED series.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL', 'DGS10')
        start_date: Start date YYYY-MM-DD (default: 1 year ago)
        end_date: End date YYYY-MM-DD (default: today)
        limit: Max observations to return
        sort_order: 'asc' or 'desc'
        api_key: FRED API key (uses env var if not provided)

    Returns:
        Dict with series_id, title, observations list, and metadata
    """
    key = _get_api_key(api_key)

    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    params = {
        "series_id": series_id.upper(),
        "api_key": key,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
        "sort_order": sort_order,
        "limit": limit,
    }

    cache_key = f"series_{series_id}_{start_date}_{end_date}_{limit}"
    data = _cached_request(f"{FRED_BASE_URL}/series/observations", params, cache_key)

    if "error" in data:
        return data

    observations = []
    for obs in data.get("observations", []):
        val = obs.get("value", ".")
        observations.append({
            "date": obs.get("date"),
            "value": float(val) if val != "." else None,
        })

    # Get series info
    info = get_series_info(series_id, api_key=key)
    title = info.get("title", series_id) if "error" not in info else series_id

    return {
        "series_id": series_id.upper(),
        "title": title,
        "count": len(observations),
        "observations": observations,
        "start": start_date,
        "end": end_date,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_series_info(series_id: str, api_key: Optional[str] = None) -> Dict:
    """
    Get metadata for a FRED series.

    Args:
        series_id: FRED series ID
        api_key: FRED API key

    Returns:
        Dict with title, units, frequency, seasonal_adjustment, last_updated, etc.
    """
    key = _get_api_key(api_key)
    params = {"series_id": series_id.upper(), "api_key": key, "file_type": "json"}
    cache_key = f"info_{series_id}"
    data = _cached_request(f"{FRED_BASE_URL}/series", params, cache_key, ttl_hours=24)

    if "error" in data:
        return data

    series = data.get("seriess", [{}])[0] if data.get("seriess") else {}
    return {
        "series_id": series.get("id", series_id),
        "title": series.get("title", ""),
        "units": series.get("units", ""),
        "frequency": series.get("frequency", ""),
        "seasonal_adjustment": series.get("seasonal_adjustment", ""),
        "last_updated": series.get("last_updated", ""),
        "notes": series.get("notes", "")[:200] if series.get("notes") else "",
    }


def get_latest_value(series_id: str, api_key: Optional[str] = None) -> Dict:
    """
    Get the most recent value for a FRED series.

    Args:
        series_id: FRED series ID (e.g., 'UNRATE', 'DGS10')
        api_key: FRED API key

    Returns:
        Dict with series_id, date, value, title
    """
    result = get_series(series_id, limit=1, sort_order="desc", api_key=api_key)
    if "error" in result:
        return result

    obs = result.get("observations", [])
    # Skip missing values
    for o in obs:
        if o["value"] is not None:
            return {
                "series_id": series_id.upper(),
                "title": result.get("title", series_id),
                "date": o["date"],
                "value": o["value"],
                "source": "FRED",
            }

    return {"error": f"No valid observations found for {series_id}"}


def search_series(query: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict]:
    """
    Search for FRED series by keyword.

    Args:
        query: Search term (e.g., 'unemployment', 'GDP', 'inflation')
        limit: Max results to return
        api_key: FRED API key

    Returns:
        List of dicts with id, title, frequency, units, popularity
    """
    key = _get_api_key(api_key)
    params = {
        "search_text": query,
        "api_key": key,
        "file_type": "json",
        "limit": limit,
        "order_by": "popularity",
        "sort_order": "desc",
    }

    cache_key = f"search_{query.replace(' ', '_')}_{limit}"
    data = _cached_request(f"{FRED_BASE_URL}/series/search", params, cache_key, ttl_hours=24)

    if "error" in data:
        return [data]

    results = []
    for s in data.get("seriess", []):
        results.append({
            "id": s.get("id"),
            "title": s.get("title"),
            "frequency": s.get("frequency"),
            "units": s.get("units"),
            "seasonal_adjustment": s.get("seasonal_adjustment"),
            "popularity": s.get("popularity"),
            "last_updated": s.get("last_updated"),
        })
    return results


def get_yield_curve(date: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
    """
    Get the US Treasury yield curve (1M to 30Y).

    Args:
        date: Specific date YYYY-MM-DD (default: latest available)
        api_key: FRED API key

    Returns:
        Dict with date, yields by maturity, spread_10y_2y, curve_status
    """
    maturities = {
        "1M": "DGS1MO", "3M": "DGS3MO", "6M": "DGS6MO",
        "1Y": "DGS1", "2Y": "DGS2", "3Y": "DGS3",
        "5Y": "DGS5", "7Y": "DGS7", "10Y": "DGS10",
        "20Y": "DGS20", "30Y": "DGS30",
    }

    yields = {}
    latest_date = None
    for label, sid in maturities.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result and result.get("value") is not None:
            yields[label] = result["value"]
            if not latest_date:
                latest_date = result.get("date")

    spread_10y_2y = None
    if "10Y" in yields and "2Y" in yields:
        spread_10y_2y = round(yields["10Y"] - yields["2Y"], 3)

    curve_status = "normal"
    if spread_10y_2y is not None:
        if spread_10y_2y < 0:
            curve_status = "inverted"
        elif spread_10y_2y < 0.25:
            curve_status = "flat"

    return {
        "date": latest_date or date,
        "yields": yields,
        "spread_10y_2y": spread_10y_2y,
        "curve_status": curve_status,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_macro_snapshot(api_key: Optional[str] = None) -> Dict:
    """
    Get a snapshot of key US macro indicators.

    Returns latest values for GDP, unemployment, CPI, fed funds rate,
    10Y treasury, consumer sentiment, and more.
    """
    key_series = {
        "GDP": "GDP",
        "unemployment_rate": "UNRATE",
        "cpi_yoy": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "fed_funds_rate": "DFF",
        "10y_treasury": "DGS10",
        "2y_treasury": "DGS2",
        "consumer_sentiment": "UMCSENT",
        "initial_claims": "ICSA",
        "nonfarm_payrolls": "PAYEMS",
        "industrial_production": "INDPRO",
    }

    snapshot = {}
    for label, sid in key_series.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result:
            snapshot[label] = {
                "value": result["value"],
                "date": result["date"],
                "title": result.get("title", sid),
            }
        else:
            snapshot[label] = {"error": result.get("error", "Failed")}

    return {
        "snapshot": snapshot,
        "indicators_count": len([v for v in snapshot.values() if "value" in v]),
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_corporate_spreads(api_key: Optional[str] = None) -> Dict:
    """
    Get corporate bond spreads and credit market indicators.

    Returns ICE BofA OAS indices, Moody's yields, TED spread,
    and breakeven inflation.
    """
    spreads = {}
    for label, sid in CREDIT_SERIES.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result:
            spreads[label] = {
                "value": result["value"],
                "date": result["date"],
                "description": CREDIT_SERIES[sid] if sid in CREDIT_SERIES else result.get("title", ""),
            }

    return {
        "credit_spreads": spreads,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_money_supply(api_key: Optional[str] = None) -> Dict:
    """
    Get money supply and Fed balance sheet data.

    Returns M1, M2, Fed total assets, and monetary base.
    """
    data = {}
    for sid, desc in MONEY_SUPPLY_SERIES.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result:
            data[sid] = {
                "value": result["value"],
                "date": result["date"],
                "description": desc,
            }

    return {
        "money_supply": data,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_inflation_data(api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive inflation indicators.

    Returns CPI, Core CPI, PCE, Core PCE, breakeven inflation rates.
    """
    inflation_series = {
        "CPIAUCSL": "CPI All Urban Consumers",
        "CPILFESL": "Core CPI (Less Food & Energy)",
        "PCEPI": "PCE Price Index",
        "PCEPILFE": "Core PCE Price Index",
        "T10YIE": "10-Year Breakeven Inflation",
        "T5YIE": "5-Year Breakeven Inflation",
        "MICH": "U of Michigan Inflation Expectations",
    }

    data = {}
    for sid, desc in inflation_series.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result:
            data[sid] = {
                "value": result["value"],
                "date": result["date"],
                "description": desc,
            }

    return {
        "inflation": data,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def get_labor_market(api_key: Optional[str] = None) -> Dict:
    """
    Get labor market indicators.

    Returns unemployment rate, nonfarm payrolls, initial claims,
    job openings, participation rate.
    """
    labor_series = {
        "UNRATE": "Unemployment Rate",
        "PAYEMS": "Total Nonfarm Payrolls",
        "ICSA": "Initial Jobless Claims",
        "JTSJOL": "Job Openings (JOLTS)",
        "CIVPART": "Labor Force Participation Rate",
        "LNS12300060": "Employment-Population Ratio (25-54)",
        "AWHAETP": "Average Weekly Hours",
        "CES0500000003": "Average Hourly Earnings",
    }

    data = {}
    for sid, desc in labor_series.items():
        result = get_latest_value(sid, api_key=api_key)
        if "error" not in result:
            data[sid] = {
                "value": result["value"],
                "date": result["date"],
                "description": desc,
            }

    return {
        "labor_market": data,
        "source": "FRED",
        "fetched_at": datetime.now().isoformat(),
    }


def list_available_series() -> Dict:
    """
    List all pre-configured series organized by category.

    Returns:
        Dict with categories and their series IDs and descriptions.
    """
    return {
        "macro": MACRO_SERIES,
        "fixed_income": FIXED_INCOME_SERIES,
        "credit": CREDIT_SERIES,
        "money_supply": MONEY_SUPPLY_SERIES,
        "total_series": len(MACRO_SERIES) + len(FIXED_INCOME_SERIES) + len(CREDIT_SERIES) + len(MONEY_SUPPLY_SERIES),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        series_id = sys.argv[1]
        result = get_series(series_id, limit=5)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            "module": "fred_api",
            "status": "ready",
            "functions": [
                "get_series", "get_series_info", "get_latest_value",
                "search_series", "get_yield_curve", "get_macro_snapshot",
                "get_corporate_spreads", "get_money_supply",
                "get_inflation_data", "get_labor_market", "list_available_series",
            ],
            "source": "https://fred.stlouisfed.org/docs/api/fred.html",
        }, indent=2))
