#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_global_indicators')
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
    except Exception as e:
        return {'error': str(e)}

"""
World Bank Global Indicators Data Module

Purpose: Delivers global development data on poverty, education, and health metrics for economic insights.
CATEGORY: alt_data
Data Source URL: https://api.worldbank.org/
Update Frequency: Data is updated as per World Bank schedules, typically annually.
Auth Info: No authentication required for public endpoints.
"""

def get_countries():
    """Fetches a list of countries from the World Bank API.

    Returns:
        list: A list of country data or an error dictionary.
    """
    try:
        data = _cached_get('https://api.worldbank.org/countries?format=json', 'countries')
        return data
    except Exception as e:
        return {'error': str(e)}

def get_indicators():
    """Fetches a list of global indicators from the World Bank API.

    Returns:
        list: A list of indicator data or an error dictionary.
    """
    try:
        data = _cached_get('https://api.worldbank.org/indicators?per_page=100&format=json', 'indicators')
        return data
    except Exception as e:
        return {'error': str(e)}

def get_indicator_data(indicator_id, country_code='all', date='2020:2023'):
    """Fetches data for a specific indicator from the World Bank API.

    Args:
        indicator_id (str): The ID of the indicator (e.g., 'SI.POV.DDAY').
        country_code (str): The country code (e.g., 'USA'), default 'all'.
        date (str): The date range (e.g., '2020:2023'), default '2020:2023'.

    Returns:
        dict: The indicator data or an error dictionary.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}/indicator/{indicator_id}?date={date}&format=json'
    cache_key = f'indicator_{indicator_id}_{country_code}_{date}'
    try:
        data = _cached_get(url, cache_key)
        return data
    except Exception as e:
        return {'error': str(e)}

def search_indicators(query):
    """Searches for indicators matching the query string from the World Bank API.

    Args:
        query (str): The search query string.

    Returns:
        list: A list of matching indicators or an error dictionary.
    """
    url = 'https://api.worldbank.org/indicators'
    params = {'format': 'json', 'keyword': query}
    cache_key = f'search_{query}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def get_poverty_data(country_code):
    """Fetches poverty data (e.g., headcount ratio) for a specified country.

    Args:
        country_code (str): The country code (e.g., 'USA').

    Returns:
        dict: The poverty data or an error dictionary.
    """
    indicator_id = 'SI.POV.DDAY'  # Poverty headcount ratio at $2.15 a day
    try:
        data = get_indicator_data(indicator_id, country_code)
        return data
    except Exception as e:
        return {'error': str(e)}

def main():
    """Demonstrates key functions from the module."""
    countries = get_countries()
    print("Demo: Countries data:", countries)  # Example output for demo

    indicators = get_indicators()
    print("Demo: Indicators data:", indicators[:1])  # First item for brevity

    poverty_data = get_poverty_data('USA')
    print("Demo: Poverty data for USA:", poverty_data)

if __name__ == '__main__':
    main()
