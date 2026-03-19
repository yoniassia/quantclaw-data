#!/usr/bin/env python3

"""
NOAA Climate Data Module

This module provides access to weather and climate datasets from NOAA for use in alternative data applications, such as financial modeling.

Data Source: https://www.ncdc.noaa.gov/cdo-web/webservices/v2/
Update Frequency: Data is updated in real-time by NOAA as new observations are recorded.
Authentication: Requires a free API token. Obtain one by registering at https://www.ncdc.noaa.gov/cdo-web/token. Pass the token to functions as an argument.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache settings
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/noaa_climate_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a GET request with caching.
    
    Args:
        url (str): The URL to request.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters.
        headers (dict, optional): Request headers.
    
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

def get_datasets(token):
    """
    Retrieve a list of available datasets from NOAA.
    
    Args:
        token (str): The NOAA API token.
    
    Returns:
        dict: A dictionary containing the list of datasets, or an error dictionary.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets'
    headers = {'token': token}
    cache_key = 'datasets'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Failed to get datasets: {str(e)}'}

def get_datacategories(token):
    """
    Retrieve a list of data categories from NOAA.
    
    Args:
        token (str): The NOAA API token.
    
    Returns:
        dict: A dictionary containing the list of data categories, or an error dictionary.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/datacategories'
    headers = {'token': token}
    cache_key = 'datacategories'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Failed to get datacategories: {str(e)}'}

def get_locations(token, locationcategoryid):
    """
    Retrieve locations for a specified location category.
    
    Args:
        token (str): The NOAA API token.
        locationcategoryid (str): The ID of the location category.
    
    Returns:
        dict: A dictionary containing the list of locations, or an error dictionary.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/locations'
    params = {'locationcategoryid': locationcategoryid}
    headers = {'token': token}
    cache_key = f'locations_{locationcategoryid}'
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {'error': f'Failed to get locations: {str(e)}'}

def get_stations(token, locationid):
    """
    Retrieve stations for a specified location.
    
    Args:
        token (str): The NOAA API token.
        locationid (str): The ID of the location.
    
    Returns:
        dict: A dictionary containing the list of stations, or an error dictionary.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations'
    params = {'locationid': locationid}
    headers = {'token': token}
    cache_key = f'stations_{locationid}'
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {'error': f'Failed to get stations: {str(e)}'}

def get_data(token, datasetid, stationid, startdate, enddate):
    """
    Retrieve data for a specified dataset, station, and date range.
    
    Args:
        token (str): The NOAA API token.
        datasetid (str): The ID of the dataset.
        stationid (str): The ID of the station.
        startdate (str): The start date in YYYY-MM-DD format.
        enddate (str): The end date in YYYY-MM-DD format.
    
    Returns:
        dict: A dictionary containing the data, or an error dictionary.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'
    params = {
        'datasetid': datasetid,
        'stationid': stationid,
        'startdate': startdate,
        'enddate': enddate
    }
    headers = {'token': token}
    cache_key = f'data_{datasetid}_{stationid}_{startdate}_{enddate}'
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {'error': f'Failed to get data: {str(e)}'}

def main():
    """
    Demonstrate 2-3 key functions from the module.
    """
    demo_token = 'your_demo_token'  # Replace with a valid NOAA demo token
    print("Demonstrating get_datasets:")
    datasets_result = get_datasets(demo_token)
    if 'error' in datasets_result:
        print(f"Error: {datasets_result['error']}")
    else:
        print(f"Number of datasets: {len(datasets_result.get('results', []))}")
    
    print("\nDemonstrating get_datacategories:")
    datacategories_result = get_datacategories(demo_token)
    if 'error' in datacategories_result:
        print(f"Error: {datacategories_result['error']}")
    else:
        print(f"Number of datacategories: {len(datacategories_result.get('results', []))}")
    
    print("\nDemonstrating get_locations for a sample category (e.g., 'CITY'):")
    locations_result = get_locations(demo_token, 'CITY')
    if 'error' in locations_result:
        print(f"Error: {locations_result['error']}")
    else:
        print(f"Number of locations: {len(locations_result.get('results', []))}")

if __name__ == '__main__':
    main()
