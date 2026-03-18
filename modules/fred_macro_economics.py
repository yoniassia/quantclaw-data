#!/usr/bin/env python3

"""
QuantClaw Data: fred_macro_economics

PURPOSE: Accesses US economic indicators like GDP, inflation, and employment data from the FRED API.

API/SOURCE: https://api.stlouisfed.org
CATEGORY: macro

Data Source URL: https://api.stlouisfed.org
Update frequency: Data updates vary by series; check FRED for specific frequencies.
Auth info: Requires a free API key. Obtain one at https://research.stlouisfed.org/useraccount/register/ and set it as the environment variable FRED_API_KEY.
"""

import requests
import os
import json
import time
from pathlib import Path
import hashlib  # For generating unique cache keys

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_macro_economics')
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

# API key handling
API_KEY = os.getenv('FRED_API_KEY', None)
if not API_KEY:
    raise ValueError("FRED_API_KEY environment variable must be set.")

def get_series_observations(series_id, **kwargs):
    """
    Fetch observations for a specific FRED series.
    
    Args:
        series_id (str): The FRED series ID (e.g., 'GDPC1' for Real GDP).
        **kwargs: Additional parameters like observation_start, observation_end, limit, etc.
    
    Returns:
        dict: The API response data, or {'error': 'message'} on failure.
    """
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        **kwargs
    }
    # Generate a unique cache key
    params_str = json.dumps(params, sort_keys=True)
    cache_key = f'observations_{series_id}_{hashlib.md5(params_str.encode()).hexdigest()}'
    
    try:
        data = _cached_get(url, cache_key, params=params)
        if 'error' in data:
            return data  # Propagate error from _cached_get
        return data
    except Exception as e:
        return {'error': str(e)}

def get_real_gdp(**kwargs):
    """
    Fetch Real Gross Domestic Product (GDPC1) data.
    
    Args:
        **kwargs: Additional parameters for get_series_observations.
    
    Returns:
        dict: The API response data, or {'error': 'message'} on failure.
    """
    return get_series_observations('GDPC1', **kwargs)

def get_cpi(**kwargs):
    """
    Fetch Consumer Price Index for All Urban Consumers (CPILFESL) data.
    
    Args:
        **kwargs: Additional parameters for get_series_observations.
    
    Returns:
        dict: The API response data, or {'error': 'message'} on failure.
    """
    return get_series_observations('CPILFESL', **kwargs)

def get_unemployment_rate(**kwargs):
    """
    Fetch Civilian Unemployment Rate (UNRATE) data.
    
    Args:
        **kwargs: Additional parameters for get_series_observations.
    
    Returns:
        dict: The API response data, or {'error': 'message'} on failure.
    """
    return get_series_observations('UNRATE', **kwargs)

def get_federal_funds_rate(**kwargs):
    """
    Fetch Effective Federal Funds Rate (FEDFUNDS) data.
    
    Args:
        **kwargs: Additional parameters for get_series_observations.
    
    Returns:
        dict: The API response data, or {'error': 'message'} on failure.
    """
    return get_series_observations('FEDFUNDS', **kwargs)

def main():
    """
    Demonstrate 2-3 key functions.
    """
    # Demo 1: Get Real GDP
    gdp_data = get_real_gdp(observation_start='2010-01-01', limit=5)
    if 'error' in gdp_data:
        print(f"GDP Error: {gdp_data['error']}")
    else:
        print(f"Real GDP Data: {gdp_data}")  # In practice, process the data
    
    # Demo 2: Get CPI
    cpi_data = get_cpi(observation_start='2020-01-01', limit=5)
    if 'error' in cpi_data:
        print(f"CPI Error: {cpi_data['error']}")
    else:
        print(f"CPI Data: {cpi_data}")  # In practice, process the data
    
    # Demo 3: Get Unemployment Rate
    unemployment_data = get_unemployment_rate(limit=5)
    if 'error' in unemployment_data:
        print(f"Unemployment Error: {unemployment_data['error']}")
    else:
        print(f"Unemployment Data: {unemployment_data}")  # In practice, process the data

if __name__ == '__main__':
    main()
