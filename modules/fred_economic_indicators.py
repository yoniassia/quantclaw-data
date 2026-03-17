#!/usr/bin/env python3
"""
Fred Economic Indicators Module

PURPOSE: Fetches US economic data indicators like GDP, unemployment rates for macroeconomic analysis.

Data Source: https://fred.stlouisfed.org/

Update Frequency: Data is updated as released by the Federal Reserve; API access is real-time.

Auth Info: Requires a free API key from https://fred.stlouisfed.org/docs/api/api_key.html. Obtain one and pass it to the functions.

CATEGORY: macro
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_economic_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.
    
    Args:
        url (str): The URL to fetch.
        cache_key (str): A unique key for caching.
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

def get_gdp(api_key: str) -> dict:
    """
    Fetches the latest GDP data for the US.
    
    Args:
        api_key (str): Your FRED API key.
    
    Returns:
        dict: The JSON response containing GDP observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {'series_id': 'GDP', 'api_key': api_key, 'file_type': 'json', 'limit': 1}
    cache_key = 'gdp_latest'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to fetch GDP: {str(e)}'}

def get_unemployment_rate(api_key: str) -> dict:
    """
    Fetches the latest unemployment rate data for the US.
    
    Args:
        api_key (str): Your FRED API key.
    
    Returns:
        dict: The JSON response containing unemployment rate observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {'series_id': 'UNRATE', 'api_key': api_key, 'file_type': 'json', 'limit': 1}
    cache_key = 'unemployment_rate_latest'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to fetch unemployment rate: {str(e)}'}

def get_cpi(api_key: str) -> dict:
    """
    Fetches the latest Consumer Price Index (CPI) data for the US.
    
    Args:
        api_key (str): Your FRED API key.
    
    Returns:
        dict: The JSON response containing CPI observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {'series_id': 'CPIAUCSL', 'api_key': api_key, 'file_type': 'json', 'limit': 1}
    cache_key = 'cpi_latest'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to fetch CPI: {str(e)}'}

def get_federal_funds_rate(api_key: str) -> dict:
    """
    Fetches the latest federal funds rate data.
    
    Args:
        api_key (str): Your FRED API key.
    
    Returns:
        dict: The JSON response containing federal funds rate observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {'series_id': 'FEDFUNDS', 'api_key': api_key, 'file_type': 'json', 'limit': 1}
    cache_key = 'federal_funds_rate_latest'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to fetch federal funds rate: {str(e)}'}

def get_series_data(api_key: str, series_id: str, **kwargs) -> dict:
    """
    Fetches data for a specified FRED series ID.
    
    Args:
        api_key (str): Your FRED API key.
        series_id (str): The FRED series ID (e.g., 'GDP').
        **kwargs: Additional parameters like limit, observation_start, etc.
    
    Returns:
        dict: The JSON response containing the series observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {'series_id': series_id, 'api_key': api_key, 'file_type': 'json'}
    params.update(kwargs)  # Add any extra parameters
    cache_key = f'series_{series_id}_{hash(frozenset(params.items()))}'  # Unique key based on params
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to fetch series {series_id}: {str(e)}'}

def main():
    """
    Demonstrates 2-3 key functions. Assumes API key is set in environment variable FRED_API_KEY.
    """
    api_key = os.environ.get('FRED_API_KEY')
    if not api_key:
        print("Error: FRED_API_KEY environment variable not set.")
        return
    
    # Demo get_gdp
    gdp_data = get_gdp(api_key)
    if 'error' in gdp_data:
        print(f"GDP Demo Error: {gdp_data['error']}")
    else:
        print(f"GDP Demo: {gdp_data.get('observations', [])}")
    
    # Demo get_unemployment_rate
    unemployment_data = get_unemployment_rate(api_key)
    if 'error' in unemployment_data:
        print(f"Unemployment Rate Demo Error: {unemployment_data['error']}")
    else:
        print(f"Unemployment Rate Demo: {unemployment_data.get('observations', [])}")
    
    # Demo get_series_data for CPI
    cpi_data = get_series_data(api_key, 'CPIAUCSL', limit=1)
    if 'error' in cpi_data:
        print(f"CPI Demo Error: {cpi_data['error']}")
    else:
        print(f"CPI Demo: {cpi_data.get('observations', [])}")

if __name__ == '__main__':
    main()
