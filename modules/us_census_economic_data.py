#!/usr/bin/env python3

"""
us_census_economic_data module

PURPOSE: Accesses US demographic and economic census data for alternative data applications in finance.

Data Source: https://www.census.gov/data/developers/data-sets.html
Update Frequency: Varies by dataset (e.g., annually for population estimates, quarterly for economic indicators).
Auth Info: No authentication required for public endpoints; uses free, publicly available API access.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/us_census_economic_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

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

def get_population_by_state(state_code):
    """
    Retrieves population data for a given US state code.
    
    Args:
        state_code (str): Two-letter US state code (e.g., 'CA').
    
    Returns:
        list: A list of dictionaries containing population data, or a dict with an error message.
    """
    url = f'https://api.census.gov/data/2020/pep/population?get=NAME,POP&for=state:{state_code}'
    cache_key = f'population_state_{state_code}'
    try:
        data = _cached_get(url, cache_key)
        return data  # Returns a list like [["NAME", "POP", "STATE"], ["California", "39538223", "06"]]
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to retrieve data: {str(e)}'}

def get_population_by_county(county_fips):
    """
    Retrieves population data for a given US county FIPS code.
    
    Args:
        county_fips (str): Five-digit FIPS code for a county (e.g., '06037' for Los Angeles County).
    
    Returns:
        list: A list of dictionaries containing population data, or a dict with an error message.
    """
    url = f'https://api.census.gov/data/2020/pep/population?get=NAME,POP&for=county:{county_fips}'
    cache_key = f'population_county_{county_fips}'
    try:
        data = _cached_get(url, cache_key)
        return data  # Returns a list like [["NAME", "POP", "COUNTY"], ["Los Angeles County", "10039107", "037"]]
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to retrieve data: {str(e)}'}

def get_median_income_by_state(state_code):
    """
    Retrieves median household income data for a given US state code.
    
    Args:
        state_code (str): Two-letter US state code (e.g., 'CA').
    
    Returns:
        list: A list of dictionaries containing median income data, or a dict with an error message.
    """
    url = f'https://api.census.gov/data/2019/acs/acs5?get=NAME,B19013_001E&for=state:{state_code}'
    cache_key = f'median_income_state_{state_code}'
    try:
        data = _cached_get(url, cache_key)
        return data  # Returns a list like [["NAME", "B19013_001E", "STATE"], ["California", "71428", "06"]]
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to retrieve data: {str(e)}'}

def get_unemployment_rate_by_state(state_code):
    """
    Retrieves unemployment rate data for a given US state code.
    
    Args:
        state_code (str): Two-letter US state code (e.g., 'CA').
    
    Returns:
        list: A list of dictionaries containing unemployment rate data, or a dict with an error message.
    """
    url = f'https://api.census.gov/data/timeseries/qwi/se?get=EmpTotal,UnempRate&for=state:{state_code}&year=2020'
    cache_key = f'unemployment_state_{state_code}'
    try:
        data = _cached_get(url, cache_key)
        return data  # Returns a list like [["EmpTotal", "UnempRate", "STATE", "YEAR"], ["123456", "5.2", "06", "2020"]]
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to retrieve data: {str(e)}'}

def get_housing_units_by_state(state_code):
    """
    Retrieves housing units data for a given US state code.
    
    Args:
        state_code (str): Two-letter US state code (e.g., 'CA').
    
    Returns:
        list: A list of dictionaries containing housing units data, or a dict with an error message.
    """
    url = f'https://api.census.gov/data/2019/acs/acs5?get=NAME,B25001_001E&for=state:{state_code}'
    cache_key = f'housing_units_state_{state_code}'
    try:
        data = _cached_get(url, cache_key)
        return data  # Returns a list like [["NAME", "B25001_001E", "STATE"], ["California", "14428784", "06"]]
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to retrieve data: {str(e)}'}

def main():
    """
    Demonstrates key functions from the module.
    """
    print("Demonstrating get_population_by_state for California:")
    result1 = get_population_by_state('CA')
    if 'error' in result1:
        print(result1)  # Error dict
    else:
        print(result1[:2])  # First two items of the list
    
    print("\nDemonstrating get_unemployment_rate_by_state for California:")
    result2 = get_unemployment_rate_by_state('CA')
    if 'error' in result2:
        print(result2)  # Error dict
    else:
        print(result2[:2])  # First two items of the list
    
    print("\nDemonstrating get_median_income_by_state for New York:")
    result3 = get_median_income_by_state('NY')
    if 'error' in result3:
        print(result3)  # Error dict
    else:
        print(result3[:2])  # First two items of the list

if __name__ == '__main__':
    main()
