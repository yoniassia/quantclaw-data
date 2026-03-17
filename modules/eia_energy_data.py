#!/usr/bin/env python3
"""
eia_energy_data module

Provides access to US energy production, consumption, and price data for commodities like oil and natural gas.

Data Source: https://www.eia.gov/opendata/
Update frequency: Data is updated daily or weekly depending on the series.
Auth info: No authentication required for public endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/eia_energy_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper to get data with caching."""
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

def get_petroleum_stock_data():
    """Fetch petroleum stock data from EIA API.
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://api.eia.gov/v2/petroleum/cushing/data/"
    cache_key = "petroleum_stock"
    return _cached_get(url, cache_key)

def get_natural_gas_production_data():
    """Fetch natural gas production data from EIA API.
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://api.eia.gov/v2/natural-gas/prod/weekly/data/"
    cache_key = "natural_gas_production"
    return _cached_get(url, cache_key)

def get_crude_oil_prices():
    """Fetch crude oil price data from EIA API.
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://api.eia.gov/v2/petroleum/prices/data/?frequency=weekly&data=WTI+Spot+Price"
    cache_key = "crude_oil_prices"
    return _cached_get(url, cache_key)

def get_electricity_consumption():
    """Fetch electricity consumption data from EIA API.
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://api.eia.gov/v2/electricity/retail-sales/data/"
    cache_key = "electricity_consumption"
    return _cached_get(url, cache_key)

def get_series_data(series_id):
    """Fetch data for a specific EIA series ID.
    
    Args:
        series_id (str): The EIA series ID (e.g., "PET.WCRFPUS1.W").
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = f"https://api.eia.gov/v2/series/{series_id}/data/"
    cache_key = f"series_{series_id}"
    return _cached_get(url, cache_key)

def main():
    """Demonstrate key functions from the module."""
    print("Demonstrating EIA Energy Data Module")
    
    # Demo 1: Get petroleum stock data
    print("Fetching petroleum stock data:")
    result = get_petroleum_stock_data()
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Success: {result.get('response', 'Data retrieved')}")
    
    # Demo 2: Get crude oil prices
    print("Fetching crude oil prices:")
    result2 = get_crude_oil_prices()
    if 'error' in result2:
        print(f"Error: {result2['error']}")
    else:
        print(f"Success: {result2.get('response', 'Data retrieved')}")
    
    # Demo 3: Get series data for an example ID
    print("Fetching series data for PET.WCRFPUS1.W (Cushing crude oil stocks):")
    result3 = get_series_data("PET.WCRFPUS1.W")
    if 'error' in result3:
        print(f"Error: {result3['error']}")
    else:
        print(f"Success: {result3.get('response', 'Data retrieved')}")

if __name__ == '__main__':
    main()
