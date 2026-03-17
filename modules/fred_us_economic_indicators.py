#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

API_KEY = 'your_free_fred_api_key_here'  # Replace with your free FRED API key from https://research.stlouisfed.org/useraccount/register/

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_us_economic_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

"""
QuantClaw Data Module: fred_us_economic_indicators

Provides access to US economic data series such as inflation rates, employment figures, and GDP.

Data Source: https://api.stlouisfed.org/
Update Frequency: Data is updated as per FRED's schedule (varies by series, typically monthly or quarterly).
Auth Info: Requires a free API key from https://research.stlouisfed.org/useraccount/register/. Set the API_KEY constant in this module.
"""

def get_cpi_data(series_id='CPIAUCSL', limit=10):
    """
    Fetches the latest observations for the Consumer Price Index (CPI) series.

    Args:
        series_id (str): FRED series ID (default: 'CPIAUCSL' for US CPI).
        limit (int): Number of observations to return.

    Returns:
        dict: FRED API response containing observations, or {'error': str} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': limit
    }
    cache_key = f'observations_{series_id}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_unemployment_data(series_id='UNRATE', limit=10):
    """
    Fetches the latest observations for the US unemployment rate series.

    Args:
        series_id (str): FRED series ID (default: 'UNRATE' for US unemployment rate).
        limit (int): Number of observations to return.

    Returns:
        dict: FRED API response containing observations, or {'error': str} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': limit
    }
    cache_key = f'observations_{series_id}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_gdp_data(series_id='GDP', limit=1):
    """
    Fetches the latest observation for the US GDP series.

    Args:
        series_id (str): FRED series ID (default: 'GDP' for US GDP).
        limit (int): Number of observations to return (default: 1 for latest).

    Returns:
        dict: FRED API response containing observations, or {'error': str} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': limit
    }
    cache_key = f'observations_{series_id}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_federal_funds_rate(series_id='FEDFUNDS', limit=10):
    """
    Fetches the latest observations for the federal funds rate series.

    Args:
        series_id (str): FRED series ID (default: 'FEDFUNDS' for federal funds rate).
        limit (int): Number of observations to return.

    Returns:
        dict: FRED API response containing observations, or {'error': str} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': limit
    }
    cache_key = f'observations_{series_id}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def search_fred_series(query, limit=10):
    """
    Searches for FRED series matching the query.

    Args:
        query (str): Search term for series.
        limit (int): Number of results to return.

    Returns:
        dict: FRED API response containing search results, or {'error': str} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/search'
    params = {
        'search_text': query,
        'api_key': API_KEY,
        'file_type': 'json',
        'limit': limit
    }
    cache_key = f'search_{query}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    # Demo 1: Get CPI data
    cpi_result = get_cpi_data(limit=5)
    print("CPI Data Demo:", cpi_result)  # For demonstration; in production, handle as needed

    # Demo 2: Get Unemployment data
    unemployment_result = get_unemployment_data(limit=5)
    print("Unemployment Data Demo:", unemployment_result)

    # Demo 3: Search for series
    search_result = search_fred_series(query='gdp', limit=5)
    print("Series Search Demo:", search_result)

if __name__ == '__main__':
    main()
