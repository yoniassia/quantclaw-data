#!/usr/bin/env python3
"""
QuantClaw Data Module: world_bank_macro_indicators

Provides global economic indicators such as GDP, poverty rates, and development data.

Data Source: https://api.worldbank.org/
Update Frequency: Data is updated periodically by the World Bank; cached for 1 hour.
Authentication: No authentication required for public endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_macro_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

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
    except requests.RequestException as e:
        # Return an error dict if request fails
        return {'error': str(e)}

def get_countries():
    """
    Retrieves a list of countries from the World Bank API.
    
    Returns:
        list: The API response containing country data, or a dict with an error.
    """
    try:
        data = _cached_get('https://api.worldbank.org/v2/countries?format=json', 'countries')
        return data  # Returns [metadata, [countries]]
    except Exception as e:
        return {'error': str(e)}

def get_indicators():
    """
    Retrieves a list of available indicators from the World Bank API.
    
    Returns:
        list: The API response containing indicator data, or a dict with an error.
    """
    try:
        data = _cached_get('https://api.worldbank.org/v2/indicators?format=json', 'indicators')
        return data  # Returns [metadata, [indicators]]
    except Exception as e:
        return {'error': str(e)}

def get_gdp_for_country(country_code):
    """
    Retrieves GDP data for a specified country.
    
    Args:
        country_code (str): The country code (e.g., 'USA').
    
    Returns:
        list: The API response containing GDP data, or a dict with an error.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}/indicator/NY.GDP.MKTP.CD?format=json'
    try:
        data = _cached_get(url, f'gdp_{country_code}')
        return data  # Returns [metadata, [GDP data points]]
    except Exception as e:
        return {'error': str(e)}

def get_poverty_rate(country_code):
    """
    Retrieves poverty rate data for a specified country.
    
    Args:
        country_code (str): The country code (e.g., 'USA').
    
    Returns:
        list: The API response containing poverty rate data, or a dict with an error.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}/indicator/SI.POV.DDAY?format=json'
    try:
        data = _cached_get(url, f'poverty_{country_code}')
        return data  # Returns [metadata, [poverty data points]]
    except Exception as e:
        return {'error': str(e)}

def get_country_summary(country_code):
    """
    Retrieves a summary of key indicators for a specified country.
    
    Args:
        country_code (str): The country code (e.g., 'USA').
    
    Returns:
        dict: A summarized dictionary of indicators, or a dict with an error.
    """
    try:
        gdp_data = get_gdp_for_country(country_code)
        poverty_data = get_poverty_rate(country_code)
        if 'error' in gdp_data or 'error' in poverty_data:
            return {'error': 'Failed to fetch summary data'}
        summary = {
            'country': country_code,
            'gdp': gdp_data[1] if len(gdp_data) > 1 else [],
            'poverty': poverty_data[1] if len(poverty_data) > 1 else []
        }
        return summary
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    print("Demonstrating World Bank functions:")
    
    # Demo 1: Get countries
    countries = get_countries()
    if 'error' in countries:
        print("Error in get_countries:", countries['error'])
    else:
        print(f"Number of countries retrieved: {len(countries[1])}")  # Assuming structure [metadata, [countries]]
    
    # Demo 2: Get GDP for USA
    gdp_usa = get_gdp_for_country('USA')
    if 'error' in gdp_usa:
        print("Error in get_gdp_for_country:", gdp_usa['error'])
    else:
        print(f"GDP data points for USA: {len(gdp_usa[1])}")  # Assuming structure [metadata, [data points]]
    
    # Demo 3: Get country summary for USA
    summary_usa = get_country_summary('USA')
    if 'error' in summary_usa:
        print("Error in get_country_summary:", summary_usa['error'])
    else:
        print(f"Summary for USA: GDP points - {len(summary_usa['gdp'])}, Poverty points - {len(summary_usa['poverty'])}")

if __name__ == '__main__':
    main()
