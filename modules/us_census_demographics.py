#!/usr/bin/env python3

"""
us_census_demographics module

PURPOSE: Accesses US population, housing, and economic demographic data for alternative data analysis.
CATEGORY: alt_data
Data Source: https://www.census.gov/data/developers/data-sets.html
Update Frequency: Data is updated periodically by the US Census Bureau (e.g., annually for ACS datasets).
Auth Info: No authentication required; uses public endpoints from the Census API.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/us_census_demographics')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a cached GET request.

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
        raise  # Let the caller handle the exception

def get_population_by_state(state_code, year='2020'):
    """
    Retrieves population estimates for a given US state and year from the ACS API.

    Args:
        state_code (str): Two-digit FIPS state code (e.g., '06' for California).
        year (str): The year for the data (e.g., '2020').

    Returns:
        list: A list of lists containing the data, or a dict with an 'error' key if failed.
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'
    params = {
        'get': 'NAME,B01001_001E',  # Total population estimate
        'for': f'state:{state_code}'
    }
    cache_key = f'population_{state_code}_{year}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve population data: {str(e)}'}

def get_housing_units_by_state(state_code, year='2020'):
    """
    Retrieves housing units data for a given US state and year from the ACS API.

    Args:
        state_code (str): Two-digit FIPS state code.
        year (str): The year for the data.

    Returns:
        list: A list of lists containing the data, or a dict with an 'error' key if failed.
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'
    params = {
        'get': 'NAME,B25001_001E',  # Total housing units
        'for': f'state:{state_code}'
    }
    cache_key = f'housing_{state_code}_{year}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve housing data: {str(e)}'}

def get_median_income_by_state(state_code, year='2020'):
    """
    Retrieves median household income for a given US state and year from the ACS API.

    Args:
        state_code (str): Two-digit FIPS state code.
        year (str): The year for the data.

    Returns:
        list: A list of lists containing the data, or a dict with an 'error' key if failed.
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'
    params = {
        'get': 'NAME,B19013_001E',  # Median household income
        'for': f'state:{state_code}'
    }
    cache_key = f'income_{state_code}_{year}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve income data: {str(e)}'}

def get_unemployment_rate_by_state(state_code, year='2020'):
    """
    Retrieves unemployment rate for a given US state and year from the ACS API.

    Args:
        state_code (str): Two-digit FIPS state code.
        year (str): The year for the data.

    Returns:
        list: A list of lists containing the data, or a dict with an 'error' key if failed.
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'
    params = {
        'get': 'NAME,S2301_C03_001E',  # Unemployment rate
        'for': f'state:{state_code}'
    }
    cache_key = f'unemployment_{state_code}_{year}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve unemployment data: {str(e)}'}

def get_education_levels_by_state(state_code, year='2020'):
    """
    Retrieves education level data for a given US state and year from the ACS API.

    Args:
        state_code (str): Two-digit FIPS state code.
        year (str): The year for the data.

    Returns:
        list: A list of lists containing the data, or a dict with an 'error' key if failed.
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'
    params = {
        'get': 'NAME,B15003_002E,B15003_017E,B15003_022E',  # Examples: Less than high school, Bachelor's, Graduate degree
        'for': f'state:{state_code}'
    }
    cache_key = f'education_{state_code}_{year}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve education data: {str(e)}'}

def main():
    """
    Demonstrates key functions in the module.
    """
    print("Demoing us_census_demographics module:")

    # Demo 1: Get population for California (state_code '06')
    population_data = get_population_by_state('06', '2020')
    print("Population data for California:", population_data)

    # Demo 2: Get median income for New York (state_code '36')
    income_data = get_median_income_by_state('36', '2020')
    print("Median income data for New York:", income_data)

    # Demo 3: Get housing units for Texas (state_code '48')
    housing_data = get_housing_units_by_state('48', '2020')
    print("Housing units data for Texas:", housing_data)

if __name__ == '__main__':
    main()
