#!/usr/bin/env python3

"""
QuantClaw Data Module: openaq_air_quality

Purpose: Delivers global air quality measurements for environmental and economic impact analysis

Data Source: https://api.openaq.org

Update Frequency: Real-time data, but cached responses are used with a 1-hour TTL

Auth Info: No authentication required; uses public endpoints
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openaq_air_quality')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

def get_countries():
    """Retrieve a list of countries from OpenAQ API.
    
    Returns:
        dict: API response containing a list of countries.
    """
    try:
        return _cached_get('https://api.openaq.org/v2/countries', cache_key='countries')
    except Exception as e:
        return {'error': f'Failed to retrieve countries: {str(e)}'}

def get_cities(country_code):
    """Retrieve a list of cities in a specified country.
    
    Args:
        country_code (str): ISO country code (e.g., 'US').
    
    Returns:
        dict: API response containing a list of cities.
    """
    try:
        params = {'country': country_code}
        cache_key = f'cities_{country_code}'
        return _cached_get('https://api.openaq.org/v2/cities', cache_key=cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve cities for {country_code}: {str(e)}'}

def get_latest_by_city(city, country_code):
    """Retrieve the latest air quality measurements for a specified city and country.
    
    Args:
        city (str): City name (e.g., 'New York').
        country_code (str): ISO country code (e.g., 'US').
    
    Returns:
        dict: API response containing the latest measurements.
    """
    try:
        params = {'city': city, 'country': country_code}
        cache_key = f'latest_by_city_{city}_{country_code}'
        return _cached_get('https://api.openaq.org/v2/latest', cache_key=cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve latest measurements for {city}, {country_code}: {str(e)}'}

def search_locations(query):
    """Search for locations based on a query string.
    
    Args:
        query (str): Search query (e.g., 'New York').
    
    Returns:
        dict: API response containing matching locations.
    """
    try:
        params = {'search': query}
        cache_key = f'search_locations_{query}'
        return _cached_get('https://api.openaq.org/v2/locations', cache_key=cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to search locations for "{query}": {str(e)}'}

def get_parameters():
    """Retrieve a list of available air quality parameters.
    
    Returns:
        dict: API response containing the list of parameters.
    """
    try:
        return _cached_get('https://api.openaq.org/v2/parameters', cache_key='parameters')
    except Exception as e:
        return {'error': f'Failed to retrieve parameters: {str(e)}'}

def main():
    """Demonstrate key functions from the module."""
    # Demo 1: Get countries
    countries_result = get_countries()
    if 'error' in countries_result:
        print(f"Error in get_countries: {countries_result['error']}")
    else:
        print(f"Number of countries: {len(countries_result.get('results', []))}")
    
    # Demo 2: Get latest measurements for New York, US
    latest_result = get_latest_by_city('New York', 'US')
    if 'error' in latest_result:
        print(f"Error in get_latest_by_city: {latest_result['error']}")
    else:
        print(f"Latest measurements for New York: {latest_result.get('results', [])}")
    
    # Demo 3: Get parameters
    parameters_result = get_parameters()
    if 'error' in parameters_result:
        print(f"Error in get_parameters: {parameters_result['error']}")
    else:
        print(f"Number of parameters: {len(parameters_result.get('results', []))}")

if __name__ == '__main__':
    main()
