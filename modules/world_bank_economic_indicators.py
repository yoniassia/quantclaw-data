#!/usr/bin/env python3
"""
QuantClaw Data Module: world_bank_economic_indicators

PURPOSE: Provides access to global economic data including GDP, poverty rates, and development indicators from the World Bank.

Data Source URL: https://api.worldbank.org/
Update Frequency: Data is updated by the World Bank; API responses are cached for 1 hour in this module.
Auth Info: No authentication required for public endpoints; uses free tier access.

CATEGORY: macro
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_economic_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a cached GET request.
    
    Args:
        url (str): The API endpoint URL.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters for the request.
        headers (dict, optional): Headers for the request.
    
    Returns:
        dict: The JSON response data, or cached data if available and not expired.
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

def get_countries():
    """
    Retrieve a list of countries from the World Bank API.
    
    Returns:
        dict: A dictionary containing the API response with country data, or an error dictionary.
    """
    try:
        data = _cached_get('https://api.worldbank.org/v2/countries', 'countries', params={'format': 'json', 'per_page': 50})
        return data  # Returns a dict with 'total', 'per_page', 'page', and 'countries' list
    except Exception as e:
        return {'error': str(e)}

def get_indicators():
    """
    Retrieve a list of available indicators from the World Bank API.
    
    Returns:
        dict: A dictionary containing the API response with indicator data, or an error dictionary.
    """
    try:
        data = _cached_get('https://api.worldbank.org/v2/indicators', 'indicators', params={'format': 'json', 'per_page': 50})
        return data  # Returns a dict with 'total', 'per_page', 'page', and 'indicator' list
    except Exception as e:
        return {'error': str(e)}

def get_gdp_for_country(country_code):
    """
    Retrieve GDP data for a specified country (using indicator NY.GDP.MKTP.CD).
    
    Args:
        country_code (str): The ISO country code (e.g., 'USA').
    
    Returns:
        dict: A dictionary containing the API response with GDP data, or an error dictionary.
    """
    try:
        url = f'https://api.worldbank.org/v2/countries/{country_code}/indicators/NY.GDP.MKTP.CD'
        data = _cached_get(url, f'gdp_{country_code}', params={'format': 'json', 'date': '2010:2020', 'per_page': 100})
        return data  # Returns a dict with 'total', 'per_page', 'page', and 'indicator' data points
    except Exception as e:
        return {'error': str(e)}

def get_poverty_rate_for_country(country_code):
    """
    Retrieve poverty rate data for a specified country (using indicator SI.POV.NAHC).
    
    Args:
        country_code (str): The ISO country code (e.g., 'USA').
    
    Returns:
        dict: A dictionary containing the API response with poverty rate data, or an error dictionary.
    """
    try:
        url = f'https://api.worldbank.org/v2/countries/{country_code}/indicators/SI.POV.NAHC'
        data = _cached_get(url, f'poverty_{country_code}', params={'format': 'json', 'date': '2010:2020', 'per_page': 100})
        return data  # Returns a dict with 'total', 'per_page', 'page', and 'indicator' data points
    except Exception as e:
        return {'error': str(e)}

def get_indicator_data(country_code, indicator_code):
    """
    Retrieve data for a specified indicator and country.
    
    Args:
        country_code (str): The ISO country code (e.g., 'USA').
        indicator_code (str): The World Bank indicator code (e.g., 'NY.GDP.MKTP.CD').
    
    Returns:
        dict: A dictionary containing the API response with indicator data, or an error dictionary.
    """
    try:
        url = f'https://api.worldbank.org/v2/countries/{country_code}/indicators/{indicator_code}'
        data = _cached_get(url, f'indicator_{country_code}_{indicator_code}', params={'format': 'json', 'date': '2010:2020', 'per_page': 100})
        return data  # Returns a dict with 'total', 'per_page', 'page', and 'indicator' data points
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrate key functions from the module.
    """
    # Demo 1: Get countries
    countries_data = get_countries()
    if 'error' in countries_data:
        print(f"Error in get_countries: {countries_data['error']}")
    else:
        print(f"First country from get_countries: {countries_data.get('countries', [{}])[0]}")  # Example: Print first country
    
    # Demo 2: Get GDP for USA
    gdp_data = get_gdp_for_country('USA')
    if 'error' in gdp_data:
        print(f"Error in get_gdp_for_country: {gdp_data['error']}")
    else:
        print(f"Latest GDP value for USA: {gdp_data.get('indicator', [{}])[0].get('value', 'N/A')}")  # Simplified demo
    
    # Demo 3: Get poverty rate for USA
    poverty_data = get_poverty_rate_for_country('USA')
    if 'error' in poverty_data:
        print(f"Error in get_poverty_rate_for_country: {poverty_data['error']}")
    else:
        print(f"Latest poverty rate for USA: {poverty_data.get('indicator', [{}])[0].get('value', 'N/A')}")  # Simplified demo

if __name__ == '__main__':
    main()
