#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/un_comtrade_trade_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
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

"""
UN Comtrade Trade Data Module

Data Source: https://comtrade.un.org/api
Update Frequency: Data is updated periodically by UN Comtrade.
Auth Info: This module uses the free tier of the UN Comtrade API. No API key is required for basic access.
CATEGORY: alt_data
"""

def get_countries():
    """
    Fetches a list of countries from the UN Comtrade API.

    Returns:
        dict: A dictionary containing the list of countries or an error message.
    """
    url = "https://comtrade.un.org/api/countries"  # Hypothetical endpoint for countries
    cache_key = 'countries_list'
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': str(e)}

def get_commodities(classification):
    """
    Fetches commodities for a given classification (e.g., 'HS' or 'SITC').

    Args:
        classification (str): The classification code, such as 'HS'.

    Returns:
        dict: A dictionary containing commodities data or an error message.
    """
    base_url = "https://comtrade.un.org/api/get"
    params = {'type': 'C', 'freq': 'A', 'px': classification, 'ps': 'latest'}  # Example parameters
    cache_key = f'commodities_{classification}'
    try:
        return _cached_get(base_url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_trade_data(reporter, year, classification):
    """
    Fetches trade data for a specific reporter, year, and classification.

    Args:
        reporter (str): The reporter country code (e.g., '842' for USA).
        year (str): The year (e.g., '2020').
        classification (str): The classification code (e.g., 'HS').

    Returns:
        dict: A dictionary containing trade data or an error message.
    """
    base_url = "https://comtrade.un.org/api/get"
    params = {'type': 'C', 'freq': 'A', 'r': reporter, 'ps': year, 'px': classification}
    cache_key = f'trade_data_{reporter}_{year}_{classification}'
    try:
        return _cached_get(base_url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_partners_for_reporter(reporter, year):
    """
    Fetches trade partners for a specific reporter and year.

    Args:
        reporter (str): The reporter country code.
        year (str): The year.

    Returns:
        dict: A dictionary containing partners data or an error message.
    """
    base_url = "https://comtrade.un.org/api/get"
    params = {'type': 'C', 'freq': 'A', 'r': reporter, 'ps': year, 'px': 'HS', 'p': 'all'}
    cache_key = f'partners_{reporter}_{year}'
    try:
        return _cached_get(base_url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_global_trade_summary(year):
    """
    Fetches a global trade summary for a specific year.

    Args:
        year (str): The year.

    Returns:
        dict: A dictionary containing global trade summary data or an error message.
    """
    base_url = "https://comtrade.un.org/api/get"
    params = {'type': 'C', 'freq': 'A', 'ps': year, 'r': 'all', 'px': 'HS'}
    cache_key = f'global_summary_{year}'
    try:
        return _cached_get(base_url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    # Demo 1: Get countries
    countries_data = get_countries()
    if 'error' not in countries_data:
        print("Countries data:", countries_data)  # For demo purposes
    else:
        print("Error in get_countries:", countries_data['error'])

    # Demo 2: Get trade data for a specific reporter, year, and classification
    trade_data = get_trade_data('842', '2020', 'HS')  # USA, 2020, HS classification
    if 'error' not in trade_data:
        print("Trade data sample:", trade_data.get('dataset', []))  # Print a sample
    else:
        print("Error in get_trade_data:", trade_data['error'])

    # Demo 3: Get global trade summary
    global_summary = get_global_trade_summary('2020')
    if 'error' not in global_summary:
        print("Global trade summary sample:", global_summary.get('dataset', []))  # Print a sample
    else:
        print("Error in get_global_trade_summary:", global_summary['error'])

if __name__ == '__main__':
    main()
