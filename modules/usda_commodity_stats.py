#!/usr/bin/env python3
"""
Module: usda_commodity_stats

PURPOSE: Provides data on US agricultural production, crop yields, and commodity prices from the USDA Quick Stats API.

Data Source URL: https://quickstats.nass.usda.gov/api/
Update Frequency: Data is updated periodically by USDA; check the official site for the latest.
Auth Info: This API requires an API key for full access, but basic queries may work without one. Use free tier keys only.

CATEGORY: commodities
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/usda_commodity_stats')
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

def get_commodity_prices(commodity, year):
    """
    Fetch commodity prices for a given commodity and year.
    
    Args:
        commodity (str): The commodity description (e.g., 'CORN').
        year (str): The year (e.g., '2020').
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://quickstats.nass.usda.gov/api/v1/statistics/"
    params = {
        'commodity_desc': commodity,
        'year': year,
        'statisticcat_desc': 'PRICE RECEIVED',
        'format': 'JSON'
    }
    cache_key = f'prices_{commodity}_{year}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def get_crop_production(commodity, year):
    """
    Fetch crop production data for a given commodity and year.
    
    Args:
        commodity (str): The commodity description (e.g., 'CORN').
        year (str): The year (e.g., '2020').
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://quickstats.nass.usda.gov/api/v1/statistics/"
    params = {
        'commodity_desc': commodity,
        'year': year,
        'statisticcat_desc': 'PRODUCTION',
        'format': 'JSON'
    }
    cache_key = f'production_{commodity}_{year}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def get_yield_per_acre(commodity, year):
    """
    Fetch yield per acre for a given commodity and year.
    
    Args:
        commodity (str): The commodity description (e.g., 'CORN').
        year (str): The year (e.g., '2020').
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://quickstats.nass.usda.gov/api/v1/statistics/"
    params = {
        'commodity_desc': commodity,
        'year': year,
        'statisticcat_desc': 'YIELD',
        'format': 'JSON'
    }
    cache_key = f'yield_{commodity}_{year}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def get_state_level_data(state, commodity, year):
    """
    Fetch data for a specific state, commodity, and year.
    
    Args:
        state (str): The state abbreviation (e.g., 'IA' for Iowa).
        commodity (str): The commodity description (e.g., 'CORN').
        year (str): The year (e.g., '2020').
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://quickstats.nass.usda.gov/api/v1/statistics/"
    params = {
        'state_alpha': state,
        'commodity_desc': commodity,
        'year': year,
        'agg_level_desc': 'STATE',
        'format': 'JSON'
    }
    cache_key = f'state_data_{state}_{commodity}_{year}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def search_commodities(query):
    """
    Search for commodities matching a query string.
    
    Args:
        query (str): The search query (e.g., 'corn').
    
    Returns:
        dict: The API response data or an error dictionary.
    """
    url = "https://quickstats.nass.usda.gov/api/v1/statistics/"
    params = {
        'commodity_desc': query,
        'format': 'JSON'
    }
    cache_key = f'search_{query}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrate key functions.
    """
    print("Demonstrating USDA Commodity Stats Module:")
    
    # Demo 1: Get commodity prices
    prices = get_commodity_prices('CORN', '2020')
    print("Commodity Prices:", prices)  # In a real app, process this data
    
    # Demo 2: Get crop production
    production = get_crop_production('CORN', '2020')
    print("Crop Production:", production)
    
    # Demo 3: Get yield per acre
    yield_data = get_yield_per_acre('CORN', '2020')
    print("Yield per Acre:", yield_data)

if __name__ == '__main__':
    main()
