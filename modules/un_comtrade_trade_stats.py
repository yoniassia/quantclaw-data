#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

"""
QuantClaw Data Module: un_comtrade_trade_stats

PURPOSE: Offers international trade statistics as alternative data

API/SOURCE: https://comtrade.un.org/api

CATEGORY: alt_data

Data Source URL: https://comtrade.un.org/api
Update frequency: Data is updated periodically by UN; API access is real-time for queries.
Auth info: No authentication required for basic queries; free tier.
"""

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/un_comtrade_trade_stats')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

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

def get_country_list():
    """Retrieves a list of countries from the UN Comtrade API.

    Returns:
        dict: A dictionary containing the list of countries or an error message.
    """
    url = "https://comtrade.un.org/api/get"
    params = {'type': 'countries'}
    try:
        return _cached_get(url, 'countries_list', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_commodity_list(classification='HS'):
    """Retrieves a list of commodities for the specified classification.

    Args:
        classification (str): The classification type, e.g., 'HS' or 'SITC'.

    Returns:
        dict: A dictionary containing the list of commodities or an error message.
    """
    url = "https://comtrade.un.org/api/get"
    params = {'type': 'commodities', 'px': classification}
    try:
        return _cached_get(url, f'commodity_list_{classification}', params=params)
    except Exception as e:
        return {'error': str(e)}

def fetch_trade_summary(reporter, year):
    """Fetches a trade summary for the specified reporter and year.

    Args:
        reporter (str): The reporter country code, e.g., '826' for UK.
        year (str): The year, e.g., '2020'.

    Returns:
        dict: A dictionary containing the trade data or an error message.
    """
    url = "https://comtrade.un.org/api/get"
    params = {
        'type': 'C',
        'freq': 'A',
        'px': 'HS',
        'ps': year,
        'r': reporter,
        'p': 'all',
        'rg': '1',
        'cc': 'all'
    }
    try:
        return _cached_get(url, f'trade_summary_{reporter}_{year}', params=params)
    except Exception as e:
        return {'error': str(e)}

def get_flow_types():
    """Retrieves the available flow types (e.g., imports, exports) from the UN Comtrade API.

    Returns:
        dict: A dictionary containing the flow types or an error message.
    """
    url = "https://comtrade.un.org/api/get"
    params = {'type': 'flow'}
    try:
        return _cached_get(url, 'flow_types', params=params)
    except Exception as e:
        return {'error': str(e)}

def search_commodities(query):
    """Searches for commodities matching the query string.

    Args:
        query (str): The search term for commodities.

    Returns:
        dict: A dictionary containing the search results or an error message.
    """
    url = "https://comtrade.un.org/api/get"  # Note: This is a simulated search; adjust based on actual API.
    params = {'type': 'commodities', 'search': query}  # Assuming a search parameter; verify with API docs.
    try:
        return _cached_get(url, f'commodity_search_{query}', params=params)
    except Exception as e:
        return {'error': str(e)}

def main():
    """Demonstrates key functions from the module."""
    # Demo 1: Get country list
    countries = get_country_list()
    if 'error' in countries:
        print(f"Error in get_country_list: {countries['error']}")
    else:
        print(f"Number of countries retrieved: {len(countries.get('results', []))}")
    
    # Demo 2: Get commodity list for HS classification
    commodities = get_commodity_list('HS')
    if 'error' in commodities:
        print(f"Error in get_commodity_list: {commodities['error']}")
    else:
        print(f"Number of commodities for HS: {len(commodities.get('results', []))}")
    
    # Demo 3: Fetch trade summary for UK in 2020
    trade_data = fetch_trade_summary('826', '2020')
    if 'error' in trade_data:
        print(f"Error in fetch_trade_summary: {trade_data['error']}")
    else:
        print(f"Trade data entries for UK 2020: {len(trade_data.get('dataset', []))}")

if __name__ == '__main__':
    main()
