#!/usr/bin/env python3

"""
Module for accessing US energy production, consumption, and price data from the EIA Open Data API.

Data Source: https://www.eia.gov/opendata/
Update Frequency: Data is updated daily, but specific series may vary.
Auth Info: Requires a free API key from EIA; no paid keys needed. Use the API_KEY variable in this module.

CATEGORY: commodities
"""

import requests
import os
import json
import time
from pathlib import Path

# API Key for EIA; replace with your free API key from https://www.eia.gov/opendata/
API_KEY = 'YOUR_FREE_EIA_API_KEY'  # Obtain from EIA website

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/eia_energy_statistics')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching the response.
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

def get_crude_oil_production():
    """
    Fetches US crude oil production data.

    Returns:
        dict: The API response data, or an error dictionary.
    """
    try:
        url = 'https://api.eia.gov/v2/series/'
        params = {
            'api_key': API_KEY,
            'series_id': 'PET.WCRFPUS1'  # Series ID for US crude oil production
        }
        data = _cached_get(url, cache_key='crude_oil_production', params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch crude oil production: {str(e)}'}

def get_natural_gas_consumption():
    """
    Fetches US natural gas consumption data.

    Returns:
        dict: The API response data, or an error dictionary.
    """
    try:
        url = 'https://api.eia.gov/v2/series/'
        params = {
            'api_key': API_KEY,
            'series_id': 'NG.N9070US2'  # Series ID for US natural gas consumption
        }
        data = _cached_get(url, cache_key='natural_gas_consumption', params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch natural gas consumption: {str(e)}'}

def get_gasoline_prices():
    """
    Fetches average US gasoline prices data.

    Returns:
        dict: The API response data, or an error dictionary.
    """
    try:
        url = 'https://api.eia.gov/v2/series/'
        params = {
            'api_key': API_KEY,
            'series_id': 'PET.EMI.4.TX.RGC.D'  # Series ID for US regular gasoline prices
        }
        data = _cached_get(url, cache_key='gasoline_prices', params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch gasoline prices: {str(e)}'}

def get_electricity_generation():
    """
    Fetches US electricity generation data.

    Returns:
        dict: The API response data, or an error dictionary.
    """
    try:
        url = 'https://api.eia.gov/v2/series/'
        params = {
            'api_key': API_KEY,
            'series_id': 'ELEC.GEN.ALL-95.A'  # Series ID for US total electricity generation
        }
        data = _cached_get(url, cache_key='electricity_generation', params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch electricity generation: {str(e)}'}

def get_coal_production():
    """
    Fetches US coal production data.

    Returns:
        dict: The API response data, or an error dictionary.
    """
    try:
        url = 'https://api.eia.gov/v2/series/'
        params = {
            'api_key': API_KEY,
            'series_id': 'COAL.PRODUCTION.TOTAL'  # Series ID for US coal production (example)
        }
        data = _cached_get(url, cache_key='coal_production', params=params)
        return data
    except Exception as e:
        return {'error': f'Failed to fetch coal production: {str(e)}'}

def main():
    """
    Demonstrates key functions in the module.
    """
    print("Demonstrating EIA Energy Statistics module:")

    # Demo 1: Get crude oil production
    crude_data = get_crude_oil_production()
    if 'error' in crude_data:
        print(f"Error in crude oil production: {crude_data['error']}")
    else:
        print(f"Crude oil production response: {crude_data.get('response', {})}")

    # Demo 2: Get natural gas consumption
    gas_data = get_natural_gas_consumption()
    if 'error' in gas_data:
        print(f"Error in natural gas consumption: {gas_data['error']}")
    else:
        print(f"Natural gas consumption response: {gas_data.get('response', {})}")

    # Demo 3: Get gasoline prices
    prices_data = get_gasoline_prices()
    if 'error' in prices_data:
        print(f"Error in gasoline prices: {prices_data['error']}")
    else:
        print(f"Gasoline prices response: {prices_data.get('response', {})}")

if __name__ == '__main__':
    main()
