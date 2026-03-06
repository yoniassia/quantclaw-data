#!/usr/bin/env python3
"""
FRED Housing Price Index Module
Provides access to US housing market data from FRED (Federal Reserve Economic Data).

Data sources:
- Case-Shiller National Home Price Index (CSUSHPISA)
- Case-Shiller 20-City Composite (SPCS20RSA)
- Housing Starts (HOUST)
- Existing Home Sales (EXHOSLUSM495S)
- 30-Year Mortgage Rates (MORTGAGE30US)
- Months of Supply (MSACSR)

API: https://fred.stlouisfed.org/docs/api/fred/
Free tier: 1,000 calls/day
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Try to load API key from multiple sources
FRED_API_KEY = None

# Try credentials file first
try:
    creds_path = os.path.expanduser("~/.openclaw/workspace/.credentials/fred-api.json")
    if os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            FRED_API_KEY = creds.get("fredApiKey")
except:
    pass

# Fallback to environment variable
if not FRED_API_KEY:
    FRED_API_KEY = os.environ.get("FRED_API_KEY")

BASE_URL = "https://api.stlouisfed.org/fred"

# Major housing series IDs
SERIES_IDS = {
    "case_shiller_national": "CSUSHPISA",
    "case_shiller_20_city": "SPCS20RSA",
    "housing_starts": "HOUST",
    "existing_home_sales": "EXHOSLUSM495S",
    "mortgage_30yr": "MORTGAGE30US",
    "months_supply": "MSACSR",
    "median_sales_price": "MSPUS",
    "housing_affordability_index": "FIXHAI",
    "new_home_sales": "HSN1F",
    "building_permits": "PERMIT",
}

def _fetch_series(series_id: str, start_date: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    Internal function to fetch FRED series data.
    
    Args:
        series_id: FRED series identifier
        start_date: Optional start date (YYYY-MM-DD)
        limit: Maximum number of observations
    
    Returns:
        List of observations with date and value
    """
    if not FRED_API_KEY:
        return [{"error": "FRED_API_KEY not configured. Set in ~/.openclaw/workspace/.credentials/fred-api.json"}]
    
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": limit,
        "sort_order": "desc"
    }
    
    if start_date:
        params["observation_start"] = start_date
    
    try:
        response = requests.get(
            f"{BASE_URL}/series/observations",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if "observations" not in data:
            return [{"error": f"No observations found for series {series_id}"}]
        
        # Clean and format observations
        observations = []
        for obs in data["observations"]:
            if obs["value"] != ".":  # FRED uses "." for missing data
                observations.append({
                    "date": obs["date"],
                    "value": float(obs["value"]),
                    "series_id": series_id
                })
        
        return observations
    
    except requests.exceptions.RequestException as e:
        return [{"error": f"API request failed: {str(e)}"}]
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        return [{"error": f"Data parsing failed: {str(e)}"}]


def get_case_shiller_national(months: int = 24) -> Dict:
    """
    Get S&P CoreLogic Case-Shiller US National Home Price Index.
    Seasonally adjusted. 2000-01 = 100.
    
    Args:
        months: Number of months of history to return
    
    Returns:
        Dict with latest value, change metrics, and historical data
    """
    data = _fetch_series(SERIES_IDS["case_shiller_national"], limit=months)
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    prior_year = data[12] if len(data) > 12 else None
    prior_month = data[1] if len(data) > 1 else None
    
    result = {
        "index": "S&P Case-Shiller National Home Price Index",
        "series_id": SERIES_IDS["case_shiller_national"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Index 2000-01=100",
        "change_mom": round(((latest["value"] / prior_month["value"]) - 1) * 100, 2) if prior_month else None,
        "change_yoy": round(((latest["value"] / prior_year["value"]) - 1) * 100, 2) if prior_year else None,
        "historical": data[:months]
    }
    
    return result


def get_case_shiller_20_city() -> Dict:
    """
    Get S&P CoreLogic Case-Shiller 20-City Composite Home Price Index.
    Seasonally adjusted.
    
    Returns:
        Dict with latest value and change metrics
    """
    data = _fetch_series(SERIES_IDS["case_shiller_20_city"], limit=13)
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    prior_year = data[12] if len(data) > 12 else None
    prior_month = data[1] if len(data) > 1 else None
    
    return {
        "index": "Case-Shiller 20-City Composite",
        "series_id": SERIES_IDS["case_shiller_20_city"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Index",
        "change_mom": round(((latest["value"] / prior_month["value"]) - 1) * 100, 2) if prior_month else None,
        "change_yoy": round(((latest["value"] / prior_year["value"]) - 1) * 100, 2) if prior_year else None,
    }


def get_housing_starts() -> Dict:
    """
    Get new privately-owned housing units started (HOUST).
    Seasonally adjusted annual rate, thousands of units.
    
    Returns:
        Dict with latest starts and trend
    """
    data = _fetch_series(SERIES_IDS["housing_starts"], limit=13)
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    prior_year = data[12] if len(data) > 12 else None
    
    return {
        "metric": "Housing Starts",
        "series_id": SERIES_IDS["housing_starts"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Thousands of Units (SAAR)",
        "change_yoy": round(((latest["value"] / prior_year["value"]) - 1) * 100, 2) if prior_year else None,
    }


def get_existing_home_sales() -> Dict:
    """
    Get existing home sales volume.
    Seasonally adjusted annual rate, millions of units.
    
    Returns:
        Dict with latest sales volume and trend
    """
    data = _fetch_series(SERIES_IDS["existing_home_sales"], limit=13)
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    prior_year = data[12] if len(data) > 12 else None
    
    return {
        "metric": "Existing Home Sales",
        "series_id": SERIES_IDS["existing_home_sales"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Millions of Units (SAAR)",
        "change_yoy": round(((latest["value"] / prior_year["value"]) - 1) * 100, 2) if prior_year else None,
    }


def get_mortgage_rates() -> Dict:
    """
    Get 30-year fixed mortgage rate average.
    
    Returns:
        Dict with current rate and historical levels
    """
    data = _fetch_series(SERIES_IDS["mortgage_30yr"], limit=52)  # 1 year weekly data
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    prior_year = data[52] if len(data) > 52 else data[-1]
    
    # Calculate moving averages
    ma_4wk = sum(d["value"] for d in data[:4]) / 4 if len(data) >= 4 else None
    ma_13wk = sum(d["value"] for d in data[:13]) / 13 if len(data) >= 13 else None
    
    return {
        "metric": "30-Year Fixed Mortgage Rate",
        "series_id": SERIES_IDS["mortgage_30yr"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Percent",
        "ma_4week": round(ma_4wk, 2) if ma_4wk else None,
        "ma_13week": round(ma_13wk, 2) if ma_13wk else None,
        "change_52w": round(latest["value"] - prior_year["value"], 2),
    }


def get_months_supply() -> Dict:
    """
    Get months' supply of houses for sale.
    Ratio of houses for sale to houses sold.
    
    Returns:
        Dict with current supply level
    """
    data = _fetch_series(SERIES_IDS["months_supply"], limit=13)
    
    if not data or "error" in data[0]:
        return {"error": data[0].get("error", "Unknown error")}
    
    latest = data[0]
    
    # Housing market balance interpretation
    if latest["value"] < 5:
        market_condition = "Seller's Market"
    elif latest["value"] > 7:
        market_condition = "Buyer's Market"
    else:
        market_condition = "Balanced Market"
    
    return {
        "metric": "Months' Supply of Houses",
        "series_id": SERIES_IDS["months_supply"],
        "latest_value": latest["value"],
        "latest_date": latest["date"],
        "unit": "Months",
        "market_condition": market_condition,
    }


def get_housing_dashboard() -> Dict:
    """
    Get comprehensive housing market dashboard with all key metrics.
    
    Returns:
        Dict with complete housing market overview
    """
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "data_source": "FRED (Federal Reserve Economic Data)",
        "prices": get_case_shiller_national(months=6),
        "supply": get_months_supply(),
        "sales": get_existing_home_sales(),
        "starts": get_housing_starts(),
        "financing": get_mortgage_rates(),
    }
    
    # Add market summary
    if "error" not in dashboard["prices"]:
        yoy_change = dashboard["prices"].get("change_yoy")
        if yoy_change is not None:
            if yoy_change > 5:
                trend = "Strong appreciation"
            elif yoy_change > 0:
                trend = "Modest appreciation"
            elif yoy_change > -5:
                trend = "Slight depreciation"
            else:
                trend = "Significant depreciation"
            
            dashboard["market_summary"] = {
                "price_trend": trend,
                "yoy_change_pct": yoy_change,
            }
    
    return dashboard


def get_latest() -> Dict:
    """
    Get latest housing price data (main entry point).
    
    Returns:
        Dict with current Case-Shiller National index
    """
    return get_case_shiller_national(months=12)


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "dashboard":
            result = get_housing_dashboard()
        elif command == "case-shiller":
            result = get_case_shiller_national(months=24)
        elif command == "mortgage":
            result = get_mortgage_rates()
        elif command == "sales":
            result = get_existing_home_sales()
        elif command == "starts":
            result = get_housing_starts()
        elif command == "supply":
            result = get_months_supply()
        else:
            result = {"error": "Unknown command. Use: dashboard, case-shiller, mortgage, sales, starts, supply"}
    else:
        result = get_latest()
    
    print(json.dumps(result, indent=2, default=str))
