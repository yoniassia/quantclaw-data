#!/usr/bin/env python3

"""
QuantClaw Data: fred_macro_indicators

PURPOSE: Fetches U.S. economic indicators such as GDP, unemployment rates, and inflation data for macroeconomic analysis.

Data Source: https://fred.stlouisfed.org/docs/api/

Update Frequency: Data is updated as per FRED's schedule (varies by series).

Auth Info: Requires a free FRED API key. Set the environment variable FRED_API_KEY for authentication.

CATEGORY: macro
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_macro_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to get data with caching."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

def get_real_gdp():
    """Fetch Real Gross Domestic Product data.
    
    Returns:
        dict: The JSON response from FRED API, or an error dictionary.
    """
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    if not FRED_API_KEY:
        return {'error': 'FRED_API_KEY environment variable not set.'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'GDPC1',
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': '2010-01-01'
    }
    try:
        return _cached_get(url, cache_key='real_gdp', params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_unemployment_rate():
    """Fetch Civilian Unemployment Rate data.
    
    Returns:
        dict: The JSON response from FRED API, or an error dictionary.
    """
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    if not FRED_API_KEY:
        return {'error': 'FRED_API_KEY environment variable not set.'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'UNRATE',
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    try:
        return _cached_get(url, cache_key='unemployment_rate', params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_cpi():
    """Fetch Consumer Price Index data for inflation analysis.
    
    Returns:
        dict: The JSON response from FRED API, or an error dictionary.
    """
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    if not FRED_API_KEY:
        return {'error': 'FRED_API_KEY environment variable not set.'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'CPIAUCSL',
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    try:
        return _cached_get(url, cache_key='cpi', params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_federal_funds_rate():
    """Fetch Effective Federal Funds Rate data.
    
    Returns:
        dict: The JSON response from FRED API, or an error dictionary.
    """
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    if not FRED_API_KEY:
        return {'error': 'FRED_API_KEY environment variable not set.'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'FEDFUNDS',
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    try:
        return _cached_get(url, cache_key='federal_funds_rate', params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_industrial_production():
    """Fetch Industrial Production Index data.
    
    Returns:
        dict: The JSON response from FRED API, or an error dictionary.
    """
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    if not FRED_API_KEY:
        return {'error': 'FRED_API_KEY environment variable not set.'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': 'INDPRO',
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    try:
        return _cached_get(url, cache_key='industrial_production', params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions by fetching and summarizing data."""
    gdp_data = get_real_gdp()
    unemployment_data = get_unemployment_rate()
    cpi_data = get_cpi()
    
    return {
        'gdp_summary': {'observations': len(gdp_data.get('observations', []))} if 'observations' in gdp_data else gdp_data,
        'unemployment_summary': {'observations': len(unemployment_data.get('observations', []))} if 'observations' in unemployment_data else unemployment_data,
        'cpi_summary': {'observations': len(cpi_data.get('observations', []))} if 'observations' in cpi_data else cpi_data
    }

if __name__ == '__main__':
    main_result = main()
    # For demonstration, you can process main_result further in your application.
