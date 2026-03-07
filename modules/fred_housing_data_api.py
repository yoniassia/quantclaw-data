"""
FRED Housing Data API — U.S. Housing Market Indicators

Data Source: Federal Reserve Economic Data (FRED)
Update: Daily API access; series update monthly/quarterly
History: Varies by series (1975-present for most housing data)
Free: Yes (API key required, 1000 calls/day limit)

Provides:
- Case-Shiller Home Price Index (National + 20-City Composite)
- Housing Starts and Building Permits
- Existing and New Home Sales
- Mortgage Delinquency Rates
- Housing Inventory / Months Supply
- 30-Year Fixed Mortgage Rates

Usage:
- Track real estate market trends
- Forecast housing market cycles
- Correlate with REIT performance
- Monitor mortgage market stress

API Key: Set environment variable FRED_API_KEY
Get your key: https://fred.stlouisfed.org/docs/api/api_key.html
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/fred_housing")
os.makedirs(CACHE_DIR, exist_ok=True)

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# FRED Series IDs for housing data
SERIES_IDS = {
    "case_shiller_national": "CSUSHPISA",
    "case_shiller_20city": "SPCS20RSA",
    "housing_starts": "HOUST",
    "building_permits": "PERMIT",
    "existing_home_sales": "EXHOSLUSM495S",
    "new_home_sales": "HSN1F",
    "mortgage_delinquency": "DRSFRMACBS",
    "mortgage_30yr": "MORTGAGE30US",
    "housing_inventory": "MSACSR"
}


def _get_api_key() -> Optional[str]:
    """Get FRED API key from environment variable."""
    return os.environ.get("FRED_API_KEY")


def _fetch_fred_series(series_id: str, limit: int = 100, cache_hours: int = 24) -> Dict:
    """
    Internal helper to fetch FRED time series data.
    
    Args:
        series_id: FRED series identifier
        limit: Number of recent observations to return
        cache_hours: Cache validity in hours
    
    Returns:
        Dict with series metadata and observations
    """
    api_key = _get_api_key()
    if not api_key:
        return {
            "error": "FRED_API_KEY environment variable not set",
            "series_id": series_id,
            "data": []
        }
    
    cache_file = os.path.join(CACHE_DIR, f"{series_id}.json")
    
    # Check cache
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=cache_hours):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Fetch series info
        info_url = f"{FRED_BASE_URL}/series"
        info_params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json"
        }
        info_response = requests.get(info_url, params=info_params, timeout=10)
        info_response.raise_for_status()
        series_info = info_response.json().get("seriess", [{}])[0]
        
        time.sleep(0.1)  # Rate limit courtesy
        
        # Fetch observations
        obs_url = f"{FRED_BASE_URL}/series/observations"
        obs_params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        obs_response = requests.get(obs_url, params=obs_params, timeout=10)
        obs_response.raise_for_status()
        observations = obs_response.json().get("observations", [])
        
        # Clean observations (remove '.' values)
        clean_obs = []
        for obs in observations:
            if obs.get("value") != ".":
                try:
                    clean_obs.append({
                        "date": obs["date"],
                        "value": float(obs["value"])
                    })
                except (ValueError, KeyError):
                    continue
        
        result = {
            "series_id": series_id,
            "title": series_info.get("title", ""),
            "units": series_info.get("units", ""),
            "frequency": series_info.get("frequency", ""),
            "last_updated": series_info.get("last_updated", ""),
            "observations": clean_obs[:limit],
            "latest": clean_obs[0] if clean_obs else None,
            "fetched_at": datetime.now().isoformat()
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except requests.RequestException as e:
        return {
            "error": f"FRED API request failed: {str(e)}",
            "series_id": series_id,
            "data": []
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "series_id": series_id,
            "data": []
        }


def get_case_shiller_index(composite: str = "national", limit: int = 60) -> Dict:
    """
    Get S&P CoreLogic Case-Shiller Home Price Index.
    
    Args:
        composite: "national" or "20city"
        limit: Number of months to retrieve
    
    Returns:
        Dict with index values (seasonally adjusted)
    """
    series_id = SERIES_IDS.get(f"case_shiller_{composite}", SERIES_IDS["case_shiller_national"])
    return _fetch_fred_series(series_id, limit=limit)


def get_housing_starts_and_permits(limit: int = 60) -> Dict:
    """
    Get housing starts and building permits data.
    
    Args:
        limit: Number of months to retrieve
    
    Returns:
        Dict with both housing starts and building permits
    """
    starts = _fetch_fred_series(SERIES_IDS["housing_starts"], limit=limit)
    permits = _fetch_fred_series(SERIES_IDS["building_permits"], limit=limit)
    
    return {
        "housing_starts": starts,
        "building_permits": permits,
        "latest_starts": starts.get("latest"),
        "latest_permits": permits.get("latest")
    }


def get_existing_home_sales(limit: int = 60) -> Dict:
    """
    Get existing home sales (monthly, millions of units).
    
    Args:
        limit: Number of months to retrieve
    
    Returns:
        Dict with existing home sales data
    """
    return _fetch_fred_series(SERIES_IDS["existing_home_sales"], limit=limit)


def get_new_home_sales(limit: int = 60) -> Dict:
    """
    Get new home sales (monthly, thousands of units).
    
    Args:
        limit: Number of months to retrieve
    
    Returns:
        Dict with new home sales data
    """
    return _fetch_fred_series(SERIES_IDS["new_home_sales"], limit=limit)


def get_mortgage_delinquency_rate(limit: int = 40) -> Dict:
    """
    Get delinquency rate on single-family residential mortgages.
    
    Args:
        limit: Number of quarters to retrieve
    
    Returns:
        Dict with delinquency rates (quarterly, percentage)
    """
    return _fetch_fred_series(SERIES_IDS["mortgage_delinquency"], limit=limit)


def get_mortgage_rate_30yr(limit: int = 100) -> Dict:
    """
    Get 30-year fixed rate mortgage average (weekly).
    
    Args:
        limit: Number of weeks to retrieve
    
    Returns:
        Dict with 30-year mortgage rates
    """
    return _fetch_fred_series(SERIES_IDS["mortgage_30yr"], limit=limit)


def get_housing_inventory(limit: int = 60) -> Dict:
    """
    Get months' supply of houses (inventory measure).
    
    Args:
        limit: Number of months to retrieve
    
    Returns:
        Dict with housing inventory/supply data
    """
    return _fetch_fred_series(SERIES_IDS["housing_inventory"], limit=limit)


def get_housing_dashboard(limit: int = 12) -> Dict:
    """
    Get comprehensive housing market dashboard with all key indicators.
    
    Args:
        limit: Number of recent periods to retrieve per series
    
    Returns:
        Dict with all housing indicators and latest values
    """
    return {
        "case_shiller_national": get_case_shiller_index("national", limit),
        "case_shiller_20city": get_case_shiller_index("20city", limit),
        "housing_starts": _fetch_fred_series(SERIES_IDS["housing_starts"], limit),
        "building_permits": _fetch_fred_series(SERIES_IDS["building_permits"], limit),
        "existing_home_sales": get_existing_home_sales(limit),
        "new_home_sales": get_new_home_sales(limit),
        "mortgage_delinquency": get_mortgage_delinquency_rate(limit),
        "mortgage_30yr": get_mortgage_rate_30yr(limit),
        "housing_inventory": get_housing_inventory(limit),
        "generated_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Demo usage
    print("FRED Housing Data API Module")
    print("=" * 50)
    
    api_key = _get_api_key()
    if not api_key:
        print("\n⚠️  Set FRED_API_KEY environment variable")
        print("Get your key: https://fred.stlouisfed.org/docs/api/api_key.html")
    else:
        print(f"\n✓ API Key configured")
        print("\nFetching Case-Shiller National Index...")
        cs = get_case_shiller_index("national", limit=3)
        if "error" not in cs:
            print(f"Latest: {cs['latest']}")
            print(f"Title: {cs['title']}")
        else:
            print(f"Error: {cs['error']}")
