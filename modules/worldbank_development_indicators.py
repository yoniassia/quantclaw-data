#!/usr/bin/env python3
"""
QuantClaw Data Module: worldbank_development_indicators

PURPOSE: Provides access to global development indicators from the World Bank, 
including metrics on poverty, education, and health for alternative data analysis.

Data Source URL: https://api.worldbank.org/
Update Frequency: Varies by indicator; data is updated periodically by the World Bank.
Auth Info: No authentication required for public endpoints; uses free tier access.
CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/worldbank_development_indicators')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a GET request with caching.
    
    Args:
        url (str): The URL to request.
        cache_key (str): A unique key for caching the response.
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
        # Return an error dict if request fails
        return {'error': str(e)}

def get_countries():
    """
    Retrieve a list of countries from the World Bank API.
    
    Returns:
        dict: A dictionary containing the list of countries, or an error dictionary.
    """
    url = 'https://api.worldbank.org/v2/countries'
    cache_key = 'countries'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json', 'per_page': 500})
        return data  # Typically a dict with 'total' and 'page' keys containing country data
    except Exception as e:
        return {'error': f'Failed to retrieve countries: {str(e)}'}

def get_indicators():
    """
    Retrieve a list of available indicators from the World Bank API.
    
    Returns:
        dict: A dictionary containing the list of indicators, or an error dictionary.
    """
    url = 'https://api.worldbank.org/v2/indicators'
    cache_key = 'indicators'
    try:
        data = _cached_get(url, cache_key, params={'format': 'json', 'per_page': 500})
        return data  # Typically a dict with 'total' and 'page' keys containing indicator data
    except Exception as e:
        return {'error': f'Failed to retrieve indicators: {str(e)}'}

def get_indicator_data(indicator, country, date=None):
    """
    Retrieve data for a specific indicator and country.
    
    Args:
        indicator (str): The indicator code (e.g., 'SP.DYN.LE00.IN' for life expectancy).
        country (str): The country code (e.g., 'USA').
        date (str, optional): The date or year range (e.g., '2020' or '2000:2020').
    
    Returns:
        dict: A dictionary containing the indicator data, or an error dictionary.
    """
    url = f'https://api.worldbank.org/v2/countries/{country}/indicators/{indicator}'
    cache_key = f'{country}_{indicator}_{date}' if date else f'{country}_{indicator}'
    params = {'format': 'json', 'per_page': 1000}
    if date:
        params['date'] = date
    try:
        data = _cached_get(url, cache_key, params=params)
        return data  # Typically a dict with data points
    except Exception as e:
        return {'error': f'Failed to retrieve indicator data: {str(e)}'}

def get_poverty_headcount(country):
    """
    Retrieve poverty headcount ratio data for a specific country (using indicator SI.POV.DDAY).
    
    Args:
        country (str): The country code (e.g., 'IND').
    
    Returns:
        dict: A dictionary containing the poverty data, or an error dictionary.
    """
    indicator = 'SI.POV.DDAY'  # Poverty headcount ratio at $2.15 a day
    return get_indicator_data(indicator, country)  # Reuses existing function

def get_life_expectancy(country):
    """
    Retrieve life expectancy data for a specific country (using indicator SP.DYN.LE00.IN).
    
    Args:
        country (str): The country code (e.g., 'USA').
    
    Returns:
        dict: A dictionary containing the life expectancy data, or an error dictionary.
    """
    indicator = 'SP.DYN.LE00.IN'  # Life expectancy at birth
    return get_indicator_data(indicator, country)  # Reuses existing function

def main():
    """
    Demonstrate key functions from the module.
    """
    # Demo 1: Get list of countries
    countries_data = get_countries()
    if 'error' in countries_data:
        print(f"Error in get_countries: {countries_data['error']}")
    else:
        print(f"Number of countries: {countries_data.get('total', 0)}")  # Example output
    
    # Demo 2: Get data for a specific indicator
    indicator_data = get_indicator_data('SP.DYN.LE00.IN', 'USA', date='2020')
    if 'error' in indicator_data:
        print(f"Error in get_indicator_data: {indicator_data['error']}")
    else:
        print(f"Life expectancy data for USA in 2020: {indicator_data}")  # Example output
    
    # Demo 3: Get poverty data
    poverty_data = get_poverty_headcount('IND')
    if 'error' in poverty_data:
        print(f"Error in get_poverty_headcount: {poverty_data['error']}")
    else:
        print(f"Poverty headcount data for India: {poverty_data}")  # Example output

if __name__ == '__main__':
    main()
