#!/usr/bin/env python3

"""
QuantClaw Data Module: fred_fixed_income_data

PURPOSE: Fetches U.S. economic time series data focused on fixed income indicators

API/SOURCE: https://api.stlouisfed.org

Data Source URL: https://fred.stlouisfed.org/

Update frequency: Data is updated as per FRED's schedule (varies by series)

Auth info: Requires a free API key. Obtain one at https://research.stlouisfed.org/docs/api/api_key.html and set it as the environment variable 'FRED_API_KEY'.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/fred_fixed_income_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

def get_api_key():
    """
    Retrieves the FRED API key from the environment variable 'FRED_API_KEY'.

    Returns:
        str: The API key if set, otherwise None.
    """
    return os.environ.get('FRED_API_KEY')

def fetch_series_observations(series_id: str) -> dict:
    """
    Fetches observations for the specified FRED series ID.

    Args:
        series_id (str): The FRED series ID, e.g., 'DGS10'.

    Returns:
        dict: The JSON response from the FRED API, or an error dictionary.
    """
    api_key = get_api_key()
    if not api_key:
        return {'error': 'FRED API key not set in environment'}
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
        'limit': '1000',  # Default limit for recent observations
    }
    
    try:
        cache_key = f'series_observations_{series_id}'
        data = _cached_get(url, cache_key, params=params)
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_treasury_yield_10yr() -> dict:
    """
    Fetches data for the 10-Year Treasury Constant Maturity Rate (series ID: DGS10).

    Returns:
        dict: The JSON response from the FRED API, or an error dictionary.
    """
    return fetch_series_observations('DGS10')

def get_federal_funds_rate() -> dict:
    """
    Fetches data for the Effective Federal Funds Rate (series ID: FEDFUNDS).

    Returns:
        dict: The JSON response from the FRED API, or an error dictionary.
    """
    return fetch_series_observations('FEDFUNDS')

def get_prime_loan_rate() -> dict:
    """
    Fetches data for the Bank Prime Loan Rate (series ID: MPRIME).

    Returns:
        dict: The JSON response from the FRED API, or an error dictionary.
    """
    return fetch_series_observations('MPRIME')

def search_series(query: str) -> dict:
    """
    Searches for FRED series matching the query string.

    Args:
        query (str): The search query, e.g., 'treasury yield'.

    Returns:
        dict: The JSON response from the FRED API, or an error dictionary.
    """
    api_key = get_api_key()
    if not api_key:
        return {'error': 'FRED API key not set in environment'}
    
    url = 'https://api.stlouisfed.org/fred/series/search'
    params = {
        'search_text': query,
        'api_key': api_key,
        'file_type': 'json',
    }
    
    try:
        cache_key = f'search_series_{query}'
        data = _cached_get(url, cache_key, params=params)
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    result1 = get_treasury_yield_10yr()
    result2 = get_federal_funds_rate()
    result3 = search_series('treasury yield')
    
    return {
        'treasury_yield_10yr': result1,
        'federal_funds_rate': result2,
        'search_results': result3
    }

if __name__ == '__main__':
    demo_results = main()
    # For demonstration, print the results (main returns a dict)
    print(demo_results)
