#!/usr/bin/env python3
"""
QuantClaw Data Module: fred_macro_data

PURPOSE: Fetches economic indicators like GDP and inflation for macroeconomic analysis.

Data Source: https://api.stlouisfed.org/fred/
Update Frequency: Data is updated as per FRED's schedule (varies by series).
Auth Info: Requires a free API key from https://research.stlouisfed.org/docs/api/api_key.html. Pass it as a parameter to functions.

CATEGORY: macro
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_macro_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper to get data with caching.

    Args:
        url (str): The API URL.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

    Returns:
        dict: The JSON response data.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_gdp(api_key):
    """
    Fetches US GDP data from FRED.

    Args:
        api_key (str): The FRED API key.

    Returns:
        dict: The API response containing GDP data, or an error dict.
    """
    try:
        return _cached_get('https://api.stlouisfed.org/fred/series/observations', 'gdp', params={'series_id': 'GDP', 'api_key': api_key, 'file_type': 'json'})
    except Exception as e:
        return {'error': f'Error fetching GDP: {str(e)}'}

def get_inflation(api_key):
    """
    Fetches US inflation data (CPI) from FRED.

    Args:
        api_key (str): The FRED API key.

    Returns:
        dict: The API response containing inflation data, or an error dict.
    """
    try:
        return _cached_get('https://api.stlouisfed.org/fred/series/observations', 'inflation', params={'series_id': 'CPIAUCSL', 'api_key': api_key, 'file_type': 'json'})
    except Exception as e:
        return {'error': f'Error fetching inflation: {str(e)}'}

def get_unemployment(api_key):
    """
    Fetches US unemployment rate data from FRED.

    Args:
        api_key (str): The FRED API key.

    Returns:
        dict: The API response containing unemployment data, or an error dict.
    """
    try:
        return _cached_get('https://api.stlouisfed.org/fred/series/observations', 'unemployment', params={'series_id': 'UNRATE', 'api_key': api_key, 'file_type': 'json'})
    except Exception as e:
        return {'error': f'Error fetching unemployment: {str(e)}'}

def get_interest_rate(api_key):
    """
    Fetches US federal funds rate data from FRED.

    Args:
        api_key (str): The FRED API key.

    Returns:
        dict: The API response containing interest rate data, or an error dict.
    """
    try:
        return _cached_get('https://api.stlouisfed.org/fred/series/observations', 'interest_rate', params={'series_id': 'FEDFUNDS', 'api_key': api_key, 'file_type': 'json'})
    except Exception as e:
        return {'error': f'Error fetching interest rate: {str(e)}'}

def get_series(api_key, series_id):
    """
    Fetches data for a specified FRED series ID.

    Args:
        api_key (str): The FRED API key.
        series_id (str): The FRED series ID (e.g., 'GDP').

    Returns:
        dict: The API response containing the series data, or an error dict.
    """
    try:
        return _cached_get('https://api.stlouisfed.org/fred/series/observations', series_id, params={'series_id': series_id, 'api_key': api_key, 'file_type': 'json'})
    except Exception as e:
        return {'error': f'Error fetching series {series_id}: {str(e)}'}

def main():
    """
    Demonstrates 2-3 key functions.
    """
    # Replace with a valid API key
    api_key = 'your_free_fred_api_key_here'
    
    print("Demo: Fetching GDP data")
    gdp_result = get_gdp(api_key)
    print(gdp_result)  # Expect a dict with data or error
    
    print("\nDemo: Fetching Inflation data")
    inflation_result = get_inflation(api_key)
    print(inflation_result)  # Expect a dict with data or error
    
    print("\nDemo: Fetching Unemployment data")
    unemployment_result = get_unemployment(api_key)
    print(unemployment_result)  # Expect a dict with data or error

if __name__ == '__main__':
    main()
