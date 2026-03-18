#!/usr/bin/env python3

"""
QuantClaw Data Module: fred_us_economic_data

Fetches US economic indicators such as GDP and unemployment from the FRED API.

Data Source: https://api.stlouisfed.org/

Update Frequency: Varies by indicator (e.g., monthly for unemployment, quarterly for GDP).

Authentication: Requires a free FRED API key. Sign up and obtain one at https://fred.stlouisfed.org/docs/api/api_key.html. Provide the key as an argument to the functions.

"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_us_economic_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching the response.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

    Returns:
        dict: The JSON response data, or cached data if available and not expired.
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
    Fetches US Real GDP data from FRED.

    Args:
        api_key (str): Your FRED API key.

    Returns:
        dict: The API response containing GDP observations, or an error dictionary.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'GDPC1',  # Real Gross Domestic Product
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': '2010-01-01',
        'frequency': 'q'  # Quarterly
    }
    cache_key = 'gdp'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_unemployment_rate(api_key):
    """
    Fetches US Unemployment Rate data from FRED.

    Args:
        api_key (str): Your FRED API key.

    Returns:
        dict: The API response containing unemployment rate observations, or an error dictionary.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'UNRATE',  # Civilian Unemployment Rate
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': '2010-01-01',
        'frequency': 'm'  # Monthly
    }
    cache_key = 'unemployment_rate'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_inflation_rate(api_key):
    """
    Fetches US CPI (Inflation) data from FRED.

    Args:
        api_key (str): Your FRED API key.

    Returns:
        dict: The API response containing CPI observations, or an error dictionary.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'CPIAUCSL',  # Consumer Price Index for All Urban Consumers
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': '2010-01-01',
        'frequency': 'm'  # Monthly
    }
    cache_key = 'inflation_rate'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_federal_funds_rate(api_key):
    """
    Fetches US Federal Funds Rate data from FRED.

    Args:
        api_key (str): Your FRED API key.

    Returns:
        dict: The API response containing federal funds rate observations, or an error dictionary.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': 'FEDFUNDS',  # Effective Federal Funds Rate
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': '2010-01-01',
        'frequency': 'd'  # Daily
    }
    cache_key = 'federal_funds_rate'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_series_observations(api_key, series_id):
    """
    Fetches observations for a specified FRED series ID.

    Args:
        api_key (str): Your FRED API key.
        series_id (str): The FRED series ID (e.g., 'GNPCA' for GDP).

    Returns:
        dict: The API response containing the series observations, or an error dictionary.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'observation_start': '2010-01-01'
    }
    cache_key = f'series_{series_id}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def main():
    """
    Demonstrates 2-3 key functions by fetching sample data.
    """
    api_key = 'your_api_key_here'  # Replace with your actual FRED API key
    print("Demonstrating get_gdp:")
    print(get_gdp(api_key))  # Returns a dict, which we print for demo
    
    print("\nDemonstrating get_unemployment_rate:")
    print(get_unemployment_rate(api_key))  # Returns a dict
    
    print("\nDemonstrating get_inflation_rate:")
    print(get_inflation_rate(api_key))  # Returns a dict

if __name__ == '__main__':
    main()
