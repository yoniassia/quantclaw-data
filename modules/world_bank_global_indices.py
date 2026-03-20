#!/usr/bin/env python3

"""
World Bank Global Indices Data Module

Provides global development indicators including stock market and economic performance data.

Data Source: https://data.worldbank.org/developer
Update Frequency: Data is updated periodically by the World Bank; check the source for details.
Auth Info: No authentication required for public endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/world_bank_global_indices')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to perform a cached GET request."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

def get_available_indicators():
    """Retrieve a list of available indicators from the World Bank API.

    Returns:
        dict: JSON response containing the list of indicators.
    """
    url = 'https://api.worldbank.org/v2/indicators?format=json&per_page=100&page=1'
    cache_key = 'available_indicators'
    try:
        return _cached_get(url, cache_key, params={'format': 'json'})
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_countries():
    """Retrieve a list of countries from the World Bank API.

    Returns:
        dict: JSON response containing the list of countries.
    """
    url = 'https://api.worldbank.org/v2/countries?format=json&per_page=500'
    cache_key = 'countries'
    try:
        return _cached_get(url, cache_key, params={'format': 'json'})
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_indicator_data(indicator_id, country_code, year):
    """Retrieve data for a specific indicator, country, and year.

    Args:
        indicator_id (str): The ID of the indicator (e.g., 'NY.GDP.MKTP.CD').
        country_code (str): The ISO code of the country (e.g., 'USA').
        year (str): The year or date range (e.g., '2020').

    Returns:
        dict: JSON response containing the indicator data.
    """
    url = f'https://api.worldbank.org/v2/countries/{country_code}/indicators/{indicator_id}'
    cache_key = f'indicator_{indicator_id}_{country_code}_{year}'
    params = {'format': 'json', 'date': year}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def search_indicators(query_string):
    """Search for indicators based on a query string.

    Args:
        query_string (str): The search term (e.g., 'gdp').

    Returns:
        dict: JSON response containing the search results.
    """
    url = f'https://api.worldbank.org/v2/indicators?format=json&per_page=100&page=1&name={query_string}'
    cache_key = f'search_indicators_{query_string}'
    try:
        return _cached_get(url, cache_key, params={'format': 'json', 'per_page': '100', 'page': '1', 'name': query_string})
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_specific_indicator(indicator_id):
    """Retrieve details for a specific indicator by ID.

    Args:
        indicator_id (str): The ID of the indicator (e.g., 'NY.GDP.MKTP.CD').

    Returns:
        dict: JSON response containing the indicator details.
    """
    url = f'https://api.worldbank.org/v2/indicators/{indicator_id}?format=json'
    cache_key = f'indicator_details_{indicator_id}'
    try:
        return _cached_get(url, cache_key, params={'format': 'json'})
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def main():
    """Demonstrate key functions from the module."""
    print("Demonstrating World Bank Global Indices module:")
    
    # Demo get_available_indicators
    indicators_result = get_available_indicators()
    if 'error' in indicators_result:
        print(f"Error in get_available_indicators: {indicators_result['error']}")
    else:
        print(f"Number of indicators retrieved: {len(indicators_result.get('indicators', []))}")
    
    # Demo get_countries
    countries_result = get_countries()
    if 'error' in countries_result:
        print(f"Error in get_countries: {countries_result['error']}")
    else:
        print(f"Number of countries retrieved: {len(countries_result.get('countries', []))}")
    
    # Demo search_indicators
    search_result = search_indicators('gdp')
    if 'error' in search_result:
        print(f"Error in search_indicators: {search_result['error']}")
    else:
        print(f"Number of search results for 'gdp': {len(search_result.get('indicators', []))}")

if __name__ == '__main__':
    main()
