#!/usr/bin/env python3
"""
QuantClaw Data Module: world_bank_economic_data

PURPOSE: Fetches global economic indicators and development data for macroeconomic analysis.
CATEGORY: macro
DATA SOURCE URL: https://api.worldbank.org/
UPDATE FREQUENCY: Data is updated periodically by the World Bank; API responses may vary.
AUTH INFO: No authentication required for public endpoints; uses free tier access.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_economic_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching.
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

def get_countries():
    """
    Fetches a list of countries from the World Bank API.

    Returns:
        dict: A dictionary containing the list of countries or an error message.
    """
    url = 'https://api.worldbank.org/v2/countries'
    cache_key = 'countries'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json'})
        return data  # Returns a list of country objects
    except Exception as e:
        return {'error': str(e)}

def get_indicators():
    """
    Fetches a list of economic indicators from the World Bank API.

    Returns:
        dict: A dictionary containing the list of indicators or an error message.
    """
    url = 'https://api.worldbank.org/v2/indicators'
    cache_key = 'indicators'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json'})
        return data  # Returns a list of indicator objects
    except Exception as e:
        return {'error': str(e)}

def get_indicator_by_id(indicator_id):
    """
    Fetches details for a specific economic indicator.

    Args:
        indicator_id (str): The ID of the indicator (e.g., 'NY.GDP.MKTP.CD').

    Returns:
        dict: A dictionary with indicator details or an error message.
    """
    url = f'https://api.worldbank.org/v2/indicators/{indicator_id}'
    cache_key = f'indicator_{indicator_id}'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json'})
        return data
    except Exception as e:
        return {'error': str(e)}

def get_country_by_code(country_code):
    """
    Fetches details for a specific country.

    Args:
        country_code (str): The ISO country code (e.g., 'USA').

    Returns:
        dict: A dictionary with country details or an error message.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}'
    cache_key = f'country_{country_code}'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json'})
        return data
    except Exception as e:
        return {'error': str(e)}

def get_economic_data(indicator_id, country_code, year=None):
    """
    Fetches economic data for a specific indicator and country.

    Args:
        indicator_id (str): The ID of the indicator.
        country_code (str): The ISO country code.
        year (str, optional): The year for the data (e.g., '2020').

    Returns:
        dict: A dictionary with the economic data or an error message.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}/indicators/{indicator_id}'
    cache_key = f'data_{indicator_id}_{country_code}_{year or "all"}'
    params = {'format': 'json'}
    if year:
        params['date'] = year
    try:
        data = _cached_get(url, cache_key, params=params)
        return data  # Returns a list of data points
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates key functions from the module.
    """
    print("Demonstrating get_countries():")
    countries_result = get_countries()
    print(countries_result)  # For demo, but functions return data, not print

    print("\nDemonstrating get_indicators():")
    indicators_result = get_indicators()
    print(indicators_result)  # First page of indicators

    print("\nDemonstrating get_economic_data() for GDP of USA in 2020:")
    data_result = get_economic_data('NY.GDP.MKTP.CD', 'USA', '2020')
    print(data_result)

if __name__ == '__main__':
    main()
