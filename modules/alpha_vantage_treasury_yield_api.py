#!/usr/bin/env python3
"""
Alpha Vantage Treasury Yield API — Fixed Income & Credit Markets Module

Provides real-time and historical data on U.S. Treasury yields across various maturities.
This API is useful for tracking interest rate movements and yield curves, which are essential 
for fixed income analysis and quantitative trading strategies.

Endpoints:
- TREASURY_YIELD: Daily treasury yields across 6 maturities (3month, 2year, 5year, 7year, 10year, 30year)
- FEDERAL_FUNDS_RATE: Federal funds rate (daily, weekly, monthly)
- INFLATION: Consumer price index and inflation data

Source: https://www.alphavantage.co/documentation/#treasury-yield
Category: Fixed Income & Credit
Free tier: True (requires free API key from alphavantage.co)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-06
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpha Vantage API Configuration
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# Valid maturity options
VALID_MATURITIES = ["3month", "2year", "5year", "7year", "10year", "30year"]
VALID_INTERVALS = ["daily", "weekly", "monthly"]


def _make_request(params: Dict) -> Dict:
    """
    Make HTTP request to Alpha Vantage API with error handling.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        JSON response as dictionary
        
    Raises:
        Exception: If API request fails or returns error
    """
    try:
        response = requests.get(AV_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error messages
        if "Error Message" in data:
            raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
        if "Note" in data and "higher API call frequency" in data["Note"]:
            raise Exception(f"Alpha Vantage Rate Limit: {data['Note']}")
        if "Information" in data and "demo" in data["Information"].lower():
            raise Exception(f"Demo API key limitation. Get free key at https://www.alphavantage.co/support/#api-key")
            
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")


def get_treasury_yield(maturity: str = "10year", interval: str = "daily") -> Dict:
    """
    Get treasury yield data for a specific maturity.
    
    Args:
        maturity: One of: 3month, 2year, 5year, 7year, 10year, 30year
        interval: One of: daily, weekly, monthly
        
    Returns:
        Dictionary with:
            - name: Series name
            - unit: Unit of measurement
            - interval: Data interval
            - maturity: Treasury maturity
            - data: List of {date, value} dicts sorted newest first
            
    Example:
        >>> result = get_treasury_yield("10year", "daily")
        >>> print(result['data'][0])  # Latest yield
        {'date': '2026-03-06', 'value': '4.23'}
    """
    if maturity not in VALID_MATURITIES:
        raise ValueError(f"Invalid maturity. Must be one of: {VALID_MATURITIES}")
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval. Must be one of: {VALID_INTERVALS}")
    
    params = {
        "function": "TREASURY_YIELD",
        "interval": interval,
        "maturity": maturity,
        "apikey": AV_API_KEY
    }
    
    response = _make_request(params)
    
    # Parse response
    result = {
        "name": response.get("name", f"Treasury Yield {maturity}"),
        "unit": response.get("unit", "percent"),
        "interval": response.get("interval", interval),
        "maturity": maturity,
        "data": []
    }
    
    # Extract time series data
    data_key = response.get("data", [])
    if isinstance(data_key, list):
        result["data"] = data_key
    
    return result


def get_yield_curve() -> Dict:
    """
    Get the current treasury yield curve across all maturities.
    Fetches latest yields for 3month, 2year, 5year, 7year, 10year, 30year.
    
    Returns:
        Dictionary with:
            - date: Date of yield curve
            - yields: Dict mapping maturity to yield value
            - curve: List of {maturity, years, value} sorted by duration
            - errors: List of any maturity fetch errors
            
    Example:
        >>> curve = get_yield_curve()
        >>> print(curve['yields']['10year'])
        '4.23'
    """
    yields_data = {}
    curve_date = None
    errors = []
    
    for maturity in VALID_MATURITIES:
        try:
            data = get_treasury_yield(maturity, "daily")
            if data["data"]:
                latest = data["data"][0]
                yields_data[maturity] = latest["value"]
                if curve_date is None:
                    curve_date = latest["date"]
        except Exception as e:
            error_msg = f"{maturity}: {str(e)}"
            errors.append(error_msg)
            yields_data[maturity] = None
    
    # Map maturities to years for sorting
    maturity_to_years = {
        "3month": 0.25,
        "2year": 2,
        "5year": 5,
        "7year": 7,
        "10year": 10,
        "30year": 30
    }
    
    curve = []
    for maturity, value in yields_data.items():
        if value is not None:
            curve.append({
                "maturity": maturity,
                "years": maturity_to_years[maturity],
                "value": value
            })
    
    # Sort by duration
    curve.sort(key=lambda x: x["years"])
    
    return {
        "date": curve_date or datetime.now().strftime("%Y-%m-%d"),
        "yields": yields_data,
        "curve": curve,
        "errors": errors
    }


def get_federal_funds_rate(interval: str = "daily") -> Dict:
    """
    Get federal funds rate data.
    
    Args:
        interval: One of: daily, weekly, monthly
        
    Returns:
        Dictionary with:
            - name: Series name
            - unit: Unit of measurement
            - interval: Data interval
            - data: List of {date, value} dicts sorted newest first
            
    Example:
        >>> result = get_federal_funds_rate("daily")
        >>> print(result['data'][0])  # Latest rate
        {'date': '2026-03-06', 'value': '4.50'}
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval. Must be one of: {VALID_INTERVALS}")
    
    params = {
        "function": "FEDERAL_FUNDS_RATE",
        "interval": interval,
        "apikey": AV_API_KEY
    }
    
    response = _make_request(params)
    
    result = {
        "name": response.get("name", "Federal Funds Rate"),
        "unit": response.get("unit", "percent"),
        "interval": response.get("interval", interval),
        "data": []
    }
    
    # Extract time series data
    data_key = response.get("data", [])
    if isinstance(data_key, list):
        result["data"] = data_key
    
    return result


def get_inflation_rate() -> Dict:
    """
    Get inflation data (Consumer Price Index).
    
    Returns:
        Dictionary with:
            - name: Series name
            - unit: Unit of measurement
            - data: List of {date, value} dicts sorted newest first
            
    Example:
        >>> result = get_inflation_rate()
        >>> print(result['data'][0])  # Latest inflation
        {'date': '2026-02-01', 'value': '3.2'}
    """
    params = {
        "function": "INFLATION",
        "apikey": AV_API_KEY
    }
    
    response = _make_request(params)
    
    result = {
        "name": response.get("name", "Consumer Price Index"),
        "unit": response.get("unit", "percent"),
        "data": []
    }
    
    # Extract time series data
    data_key = response.get("data", [])
    if isinstance(data_key, list):
        result["data"] = data_key
    
    return result


if __name__ == "__main__":
    """Test module functionality"""
    print(json.dumps({
        "module": "alpha_vantage_treasury_yield_api",
        "status": "implemented",
        "source": "https://www.alphavantage.co/documentation/#treasury-yield",
        "functions": [
            "get_treasury_yield",
            "get_yield_curve",
            "get_federal_funds_rate",
            "get_inflation_rate"
        ],
        "api_key": "demo" if AV_API_KEY == "demo" else "configured",
        "note": "Demo API key has limitations. Get free key at https://www.alphavantage.co/support/#api-key"
    }, indent=2))
