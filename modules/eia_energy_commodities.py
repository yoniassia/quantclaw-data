#!/usr/bin/env python3

"""
eia_energy_commodities module

PURPOSE: Accesses US energy statistics and forecasts for oil, gas, and electricity prices and production

Data Source: https://www.eia.gov/opendata/
Update frequency: Varies by dataset (e.g., daily for prices, weekly for reports)
Auth info: Requires a free API key from EIA; use as a parameter in requests
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/eia_energy_commodities')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper to get data with caching.
    
    Args:
        url (str): The URL to fetch.
        cache_key (str): Key for caching the response.
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
    except requests.RequestException as e:
        return {'error': str(e)}

def get_crude_oil_prices():
    """
    Fetches recent crude oil prices (e.g., WTI) from EIA API.
    
    Returns:
        dict: The API response containing price data, or an error dict.
    """
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        return {'error': 'EIA_API_KEY environment variable not set'}
    url = 'https://api.eia.gov/v2/petroleum/pri/id/RWTC/data/'
    params = {'api_key': api_key, 'freq': 'W'}  # Weekly frequency as example
    return _cached_get(url, 'crude_oil_prices', params=params)

def get_natural_gas_prices():
    """
    Fetches recent natural gas prices from EIA API.
    
    Returns:
        dict: The API response containing price data, or an error dict.
    """
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        return {'error': 'EIA_API_KEY environment variable not set'}
    url = 'https://api.eia.gov/v2/natural-gas/pri/pri_gnd_id/data/'
    params = {'api_key': api_key, 'freq': 'M'}  # Monthly frequency as example
    return _cached_get(url, 'natural_gas_prices', params=params)

def get_electricity_production():
    """
    Fetches electricity production data from EIA API.
    
    Returns:
        dict: The API response containing production data, or an error dict.
    """
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        return {'error': 'EIA_API_KEY environment variable not set'}
    url = 'https://api.eia.gov/v2/electricity/retail-sales/data/'
    params = {'api_key': api_key, 'freq': 'A'}  # Annual frequency as example
    return _cached_get(url, 'electricity_production', params=params)

def get_petroleum_supply():
    """
    Fetches petroleum supply data from EIA API.
    
    Returns:
        dict: The API response containing supply data, or an error dict.
    """
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        return {'error': 'EIA_API_KEY environment variable not set'}
    url = 'https://api.eia.gov/v2/petroleum/supply/weekly/data/'
    params = {'api_key': api_key}  # Default parameters
    return _cached_get(url, 'petroleum_supply', params=params)

def get_energy_forecasts():
    """
    Fetches energy forecasts (e.g., STEO) from EIA API.
    
    Returns:
        dict: The API response containing forecast data, or an error dict.
    """
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        return {'error': 'EIA_API_KEY environment variable not set'}
    url = 'https://api.eia.gov/v2/stéo/data/'
    params = {'api_key': api_key}  # STEO endpoint as example
    return _cached_get(url, 'energy_forecasts', params=params)

def main():
    """
    Demonstrates 2-3 key functions by fetching and summarizing data.
    
    Returns:
        None
    """
    print("Demonstrating get_crude_oil_prices:")
    crude_data = get_crude_oil_prices()
    if 'error' in crude_data:
        print(f"Error: {crude_data['error']}")
    else:
        print(f"Crude oil data: {crude_data.get('response', {}).get('data', [])}")  # Summarize
    
    print("\nDemonstrating get_natural_gas_prices:")
    gas_data = get_natural_gas_prices()
    if 'error' in gas_data:
        print(f"Error: {gas_data['error']}")
    else:
        print(f"Natural gas data: {gas_data.get('response', {}).get('data', [])}")  # Summarize
    
    print("\nDemonstrating get_electricity_production:")
    elec_data = get_electricity_production()
    if 'error' in elec_data:
        print(f"Error: {elec_data['error']}")
    else:
        print(f"Electricity production data: {elec_data.get('response', {}).get('data', [])}")  # Summarize

if __name__ == '__main__':
    main()
