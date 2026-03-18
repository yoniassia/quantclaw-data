#!/usr/bin/env python3

"""
eia_energy_prices module

Provides energy commodity prices and statistics from the U.S. Energy Information Administration (EIA) API.

Data Source: https://api.eia.gov/
Update frequency: Data is updated by EIA on a daily or more frequent basis depending on the series; this module caches responses for 1 hour.
Auth info: Requires a free EIA API key. Obtain one from https://www.eia.gov/opendata/register.php and set the API_KEY variable in this module.

CATEGORY: commodities
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/eia_energy_prices')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to get data with caching."""
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

# API key placeholder - replace with your free EIA API key
API_KEY = 'YOUR_DEMO_API_KEY'  # Do not use a paid key; get a free one from EIA

def get_crude_oil_prices():
    """Fetch Cushing, OK crude oil prices.

    Returns: dict containing the series data or an error dict.
    """
    url = 'https://api.eia.gov/series/'
    params = {'api_key': API_KEY, 'series_id': 'PET.WCRFPUS1.W'}  # Weekly Cushing crude oil prices
    cache_key = 'crude_oil_prices'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch crude oil prices: {str(e)}'}

def get_natural_gas_prices():
    """Fetch Henry Hub natural gas spot prices.

    Returns: dict containing the series data or an error dict.
    """
    url = 'https://api.eia.gov/series/'
    params = {'api_key': API_KEY, 'series_id': 'NG.RNGWH.D'}  # Daily Henry Hub natural gas prices
    cache_key = 'natural_gas_prices'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch natural gas prices: {str(e)}'}

def get_electricity_prices():
    """Fetch average retail price of electricity in the US.

    Returns: dict containing the series data or an error dict.
    """
    url = 'https://api.eia.gov/series/'
    params = {'api_key': API_KEY, 'series_id': 'ELEC.PRICE.US'}  # US average retail price of electricity
    cache_key = 'electricity_prices'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch electricity prices: {str(e)}'}

def get_gasoline_prices():
    """Fetch US regular gasoline prices.

    Returns: dict containing the series data or an error dict.
    """
    url = 'https://api.eia.gov/series/'
    params = {'api_key': API_KEY, 'series_id': 'PET.MGRSTUS1'}  # US all grades conventional retail gasoline prices
    cache_key = 'gasoline_prices'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch gasoline prices: {str(e)}'}

def get_diesel_prices():
    """Fetch US diesel fuel prices.

    Returns: dict containing the series data or an error dict.
    """
    url = 'https://api.eia.gov/series/'
    params = {'api_key': API_KEY, 'series_id': 'PET.MGRDTUS1'}  # US No 2 diesel retail prices
    cache_key = 'diesel_prices'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch diesel prices: {str(e)}'}

def main():
    """Demonstrate 2-3 key functions."""
    print("Demonstrating get_crude_oil_prices:")
    crude_oil_result = get_crude_oil_prices()
    print(crude_oil_result)  # Expect a dict with data or error

    print("\nDemonstrating get_natural_gas_prices:")
    natural_gas_result = get_natural_gas_prices()
    print(natural_gas_result)  # Expect a dict with data or error

    print("\nDemonstrating get_electricity_prices:")
    electricity_result = get_electricity_prices()
    print(electricity_result)  # Expect a dict with data or error

if __name__ == '__main__':
    main()
