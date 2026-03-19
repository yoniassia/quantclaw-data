#!/usr/bin/env python3
"""
QuantClaw Data: fred_us_economy

Provides access to US economic data series like GDP and inflation for macroeconomic analysis.

Data Source: https://api.stlouisfed.org/fred/
Update frequency: Data updates vary by series; API access is real-time.
Auth info: Requires a free API key from https://research.stlouisfed.org/docs/api/api_key.html. Set the environment variable FRED_API_KEY for use in this module.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_us_economy')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
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

API_KEY = os.getenv('FRED_API_KEY')

def get_gdp():
    """
    Retrieve US GDP data series observations.

    Returns:
        dict: FRED API response containing observations, or an error dictionary.
    """
    if not API_KEY:
        return {'error': 'FRED_API_KEY environment variable is not set.'}
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'GDPC1',
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': '2000-01-01'
        }
        return _cached_get(url, 'gdp', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_cpi():
    """
    Retrieve US CPI data series observations for inflation analysis.

    Returns:
        dict: FRED API response containing observations, or an error dictionary.
    """
    if not API_KEY:
        return {'error': 'FRED_API_KEY environment variable is not set.'}
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'CPIAUCSL',
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': '2000-01-01'
        }
        return _cached_get(url, 'cpi', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_unemployment_rate():
    """
    Retrieve US unemployment rate data series observations.

    Returns:
        dict: FRED API response containing observations, or an error dictionary.
    """
    if not API_KEY:
        return {'error': 'FRED_API_KEY environment variable is not set.'}
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'UNRATE',
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': '2000-01-01'
        }
        return _cached_get(url, 'unemployment_rate', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_federal_funds_rate():
    """
    Retrieve US federal funds rate data series observations.

    Returns:
        dict: FRED API response containing observations, or an error dictionary.
    """
    if not API_KEY:
        return {'error': 'FRED_API_KEY environment variable is not set.'}
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'FEDFUNDS',
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': '2000-01-01'
        }
        return _cached_get(url, 'federal_funds_rate', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_series(series_id):
    """
    Retrieve observations for a specified FRED series ID.

    Args:
        series_id (str): The FRED series ID (e.g., 'GDPC1' for GDP).

    Returns:
        dict: FRED API response containing observations, or an error dictionary.
    """
    if not API_KEY:
        return {'error': 'FRED_API_KEY environment variable is not set.'}
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': '2000-01-01'
        }
        return _cached_get(url, f'series_{series_id}', params=params)
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrate key functions.
    """
    gdp_data = get_gdp()
    cpi_data = get_cpi()
    print("Demo GDP data:", gdp_data)  # For demo purposes
    print("Demo CPI data:", cpi_data)  # For demo purposes

if __name__ == '__main__':
    main()
