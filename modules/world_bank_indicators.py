#!/usr/bin/env python3
"""
World Bank Indicators Data Module

PURPOSE: Accesses global development and economic indicators for countries, including poverty and trade data.
CATEGORY: alt_data
Data Source: https://api.worldbank.org
Update Frequency: Data is updated periodically by the World Bank.
Auth Info: No authentication required for public endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_indicators')
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

def get_countries():
    """Retrieve a list of countries from the World Bank API.
    
    Returns:
        dict: The API response containing a list of countries, or an error dictionary.
    """
    try:
        url = "https://api.worldbank.org/v2/countries"
        data = _cached_get(url, 'countries_list', params={'format': 'json', 'per_page': 500})
        return data
    except Exception as e:
        return {'error': str(e)}

def get_indicators():
    """Retrieve a list of indicators from the World Bank API.
    
    Returns:
        dict: The API response containing a list of indicators, or an error dictionary.
    """
    try:
        url = "https://api.worldbank.org/v2/indicators"
        data = _cached_get(url, 'indicators_list', params={'format': 'json', 'per_page': 500})
        return data
    except Exception as e:
        return {'error': str(e)}

def get_indicator_data(country, indicator):
    """Get data for a specific indicator in a country.
    
    Args:
        country (str): The country code, e.g., 'USA'.
        indicator (str): The indicator code, e.g., 'NY.GDP.MKTP.CD'.
    
    Returns:
        dict: The API response containing the data, or an error dictionary.
    """
    try:
        url = f"https://api.worldbank.org/v2/countries/{country}/indicators/{indicator}"
        cache_key = f"{country}_{indicator}_data"
        data = _cached_get(url, cache_key, params={'format': 'json', 'per_page': 1000})
        return data
    except Exception as e:
        return {'error': str(e)}

def get_poverty_data(country):
    """Get poverty-related data for a country (e.g., poverty headcount ratio).
    
    Args:
        country (str): The country code, e.g., 'USA'.
    
    Returns:
        dict: The API response containing poverty data, or an error dictionary.
    """
    try:
        indicator = 'SI.POV.NAHC'  # Poverty headcount ratio at national poverty lines (% of population)
        return get_indicator_data(country, indicator)
    except Exception as e:
        return {'error': str(e)}

def get_trade_data(country):
    """Get trade-related data for a country (e.g., exports of goods and services as % of GDP).
    
    Args:
        country (str): The country code, e.g., 'USA'.
    
    Returns:
        dict: The API response containing trade data, or an error dictionary.
    """
    try:
        indicator = 'NE.EXP.GNFS.ZS'  # Exports of goods and services (% of GDP)
        return get_indicator_data(country, indicator)
    except Exception as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions from the module."""
    # Demo 1: Get countries
    countries = get_countries()
    if 'error' in countries:
        print("Error getting countries:", countries['error'])
    else:
        print("Number of countries retrieved:", len(countries.get('countries', [])))
    
    # Demo 2: Get indicators
    indicators = get_indicators()
    if 'error' in indicators:
        print("Error getting indicators:", indicators['error'])
    else:
        print("Number of indicators retrieved:", len(indicators.get('1', [])))  # Assuming page 1
    
    # Demo 3: Get GDP data for USA
    gdp_data = get_indicator_data('USA', 'NY.GDP.MKTP.CD')
    if 'error' in gdp_data:
        print("Error getting GDP data:", gdp_data['error'])
    else:
        print("GDP data for USA retrieved successfully")

if __name__ == '__main__':
    main()
