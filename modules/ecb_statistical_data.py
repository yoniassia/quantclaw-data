#!/usr/bin/env python3

"""
ECB Statistical Data Module

Fetches euro area economic statistics including interest rates and balance of payments data.

Data Source: https://sdw-wsrest.ecb.europa.eu/
Update Frequency: Data is updated periodically by the ECB; check the source for specific frequencies.
Auth Info: Public API; no authentication required for basic access.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/ecb_statistical_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

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

def get_main_refinancing_operations_rate():
    """
    Fetches the Main Refinancing Operations (MRO) rate data.

    Returns:
        dict: The JSON response containing the data, or an error dictionary.
    """
    try:
        url = "https://sdw-wsrest.ecb.europa.eu/service/data/ERT/MNA"
        data = _cached_get(url, 'mro_rate')
        return data  # Returns the full JSON response
    except Exception as e:
        return {'error': f'Failed to fetch MRO rate: {str(e)}'}

def get_balance_of_payments():
    """
    Fetches the Balance of Payments (BOP) data.

    Returns:
        dict: The JSON response containing the data, or an error dictionary.
    """
    try:
        url = "https://sdw-wsrest.ecb.europa.eu/service/data/BP6"
        data = _cached_get(url, 'bop_data')
        return data  # Returns the full JSON response
    except Exception as e:
        return {'error': f'Failed to fetch BOP data: {str(e)}'}

def get_euro_exchange_rates():
    """
    Fetches Euro foreign exchange reference rates.

    Returns:
        dict: The JSON response containing the data, or an error dictionary.
    """
    try:
        url = "https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
        data = _cached_get(url, 'exchange_rates')
        return data  # Returns the full JSON response
    except Exception as e:
        return {'error': f'Failed to fetch exchange rates: {str(e)}'}

def get_harmonized_index_of_consumer_prices():
    """
    Fetches Harmonized Index of Consumer Prices (HICP) data.

    Returns:
        dict: The JSON response containing the data, or an error dictionary.
    """
    try:
        url = "https://sdw-wsrest.ecb.europa.eu/service/data/ICP.M.U2.N.1000.Z5.Z0.Z0.EUR0"
        data = _cached_get(url, 'hicp_data')
        return data  # Returns the full JSON response
    except Exception as e:
        return {'error': f'Failed to fetch HICP data: {str(e)}'}

def get_gdp_growth_rate():
    """
    Fetches GDP growth rate data for the Euro area.

    Returns:
        dict: The JSON response containing the data, or an error dictionary.
    """
    try:
        url = "https://sdw-wsrest.ecb.europa.eu/service/data/NAI.Q.Y.Y.X.V.N.1000.Z"
        data = _cached_get(url, 'gdp_growth')
        return data  # Returns the full JSON response
    except Exception as e:
        return {'error': f'Failed to fetch GDP growth rate: {str(e)}'}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    print("Demonstrating ECB Statistical Data functions:")
    
    # Demo 1: Get Main Refinancing Operations rate
    mro_data = get_main_refinancing_operations_rate()
    if 'error' in mro_data:
        print("Error in MRO data:", mro_data['error'])
    else:
        print("MRO Data fetched successfully. Sample:", mro_data.get('structure', {}))
    
    # Demo 2: Get Balance of Payments
    bop_data = get_balance_of_payments()
    if 'error' in bop_data:
        print("Error in BOP data:", bop_data['error'])
    else:
        print("BOP Data fetched successfully. Sample:", bop_data.get('structure', {}))
    
    # Demo 3: Get Euro Exchange Rates
    exchange_data = get_euro_exchange_rates()
    if 'error' in exchange_data:
        print("Error in exchange rates:", exchange_data['error'])
    else:
        print("Exchange Rates fetched successfully. Sample:", exchange_data.get('structure', {}))

if __name__ == '__main__':
    main()
