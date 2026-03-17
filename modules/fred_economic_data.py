#!/usr/bin/env python3

"""
QuantClaw Data Module: fred_economic_data

PURPOSE: Fetches economic indicators such as GDP, inflation, and employment data from the FRED API.

API/SOURCE: https://api.stlouisfed.org/fred/
CATEGORY: macro

Data Source URL: https://api.stlouisfed.org/fred/
Update frequency: Data is updated as per FRED's schedule; API responses are cached for 1 hour in this module.
Auth info: Requires a free API key obtainable from https://research.stlouisfed.org/useraccount/register/. Replace the placeholder in API_KEY with your key.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_economic_data')
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

# API Key placeholder - replace with your free FRED API key
API_KEY = 'your_free_fred_api_key_here'

def fetch_gdp() -> dict:
    """
    Fetches the latest GDP observations from FRED.
    
    Returns:
        dict: The API response containing observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'GDP',
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': '1',  # Get the latest observation
    }
    cache_key = 'gdp_observations'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def fetch_inflation() -> dict:
    """
    Fetches the latest CPI data as a measure of inflation from FRED.
    
    Returns:
        dict: The API response containing observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'CPIAUCSL',
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': '1',  # Get the latest observation
    }
    cache_key = 'cpi_observations'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def fetch_unemployment() -> dict:
    """
    Fetches the latest unemployment rate data from FRED.
    
    Returns:
        dict: The API response containing observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'UNRATE',
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': '1',  # Get the latest observation
    }
    cache_key = 'unrate_observations'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def fetch_series(series_id: str) -> dict:
    """
    Fetches observations for a specified FRED series ID.
    
    Args:
        series_id (str): The FRED series ID.
    
    Returns:
        dict: The API response containing observations, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': '1',  # Get the latest observation
    }
    cache_key = f'series_{series_id}_observations'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def search_series(query: str) -> dict:
    """
    Searches for FRED series matching the query string.
    
    Args:
        query (str): The search query.
    
    Returns:
        dict: The API response containing search results, or an error dictionary.
    """
    url = 'https://api.stlouisfed.org/fred/series/search'
    params = {
        'search_text': query,
        'api_key': API_KEY,
        'file_type': 'json',
    }
    cache_key = f'search_{query.replace(" ", "_")}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates key functions in the module.
    """
    print("Demonstrating FRED Economic Data Module")
    
    # Demo 1: Fetch GDP
    gdp_data = fetch_gdp()
    if 'error' in gdp_data:
        print("Error fetching GDP:", gdp_data['error'])
    else:
        print("Latest GDP data:", gdp_data.get('observations', []))
    
    # Demo 2: Fetch Inflation
    inflation_data = fetch_inflation()
    if 'error' in inflation_data:
        print("Error fetching inflation:", inflation_data['error'])
    else:
        print("Latest inflation data:", inflation_data.get('observations', []))
    
    # Demo 3: Search for series
    search_results = search_series("GDP")
    if 'error' in search_results:
        print("Error searching series:", search_results['error'])
    else:
        print("Search results for 'GDP':", search_results.get('seriess', []))

if __name__ == '__main__':
    main()
