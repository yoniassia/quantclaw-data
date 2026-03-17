#!/usr/bin/env python3

"""
NOAA Weather Alternative Data Module

This module provides access to weather data from the National Oceanic and Atmospheric Administration (NOAA) 
for use as alternative data in predicting commodity impacts, such as in agriculture or energy sectors.

Data Source URL: https://www.ncdc.noaa.gov/cdo-web/webservices/v2/
Update Frequency: Data is updated in near real-time for most endpoints.
Auth Info: Requires a free API token obtained from NOAA's website. Include the token in the 'token' header for requests.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/noaa_weather_alt_data')
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

def get_datasets(token: str) -> dict:
    """
    Retrieve a list of available datasets from NOAA.

    Args:
        token (str): NOAA API token.

    Returns:
        dict: A dictionary containing the datasets or an error message.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets'
    headers = {'token': token}
    cache_key = 'datasets'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Error fetching datasets: {str(e)}'}

def get_data_categories(token: str) -> dict:
    """
    Retrieve a list of data categories from NOAA.

    Args:
        token (str): NOAA API token.

    Returns:
        dict: A dictionary containing the data categories or an error message.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/datacategories'
    headers = {'token': token}
    cache_key = 'data_categories'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Error fetching data categories: {str(e)}'}

def get_stations(token: str, location: str) -> dict:
    """
    Retrieve stations based on a location query.

    Args:
        token (str): NOAA API token.
        location (str): Location string (e.g., 'New York').

    Returns:
        dict: A dictionary containing the stations or an error message.
    """
    url = f'https://www.ncdc.noaa.gov/cdo-web/api/v2/stations?location={location}'
    headers = {'token': token}
    cache_key = f'stations_{location}'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Error fetching stations: {str(e)}'}

def get_datatypes(token: str, datasetid: str) -> dict:
    """
    Retrieve data types for a specific dataset.

    Args:
        token (str): NOAA API token.
        datasetid (str): ID of the dataset.

    Returns:
        dict: A dictionary containing the data types or an error message.
    """
    url = f'https://www.ncdc.noaa.gov/cdo-web/api/v2/datatypes?datasetid={datasetid}'
    headers = {'token': token}
    cache_key = f'datatypes_{datasetid}'
    try:
        return _cached_get(url, cache_key, headers=headers)
    except Exception as e:
        return {'error': f'Error fetching data types: {str(e)}'}

def get_data(token: str, datasetid: str, stationid: str, startdate: str, enddate: str) -> dict:
    """
    Retrieve weather data for a specific dataset, station, and date range.

    Args:
        token (str): NOAA API token.
        datasetid (str): ID of the dataset.
        stationid (str): ID of the station.
        startdate (str): Start date in YYYY-MM-DD format.
        enddate (str): End date in YYYY-MM-DD format.

    Returns:
        dict: A dictionary containing the data or an error message.
    """
    url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data'
    params = {
        'datasetid': datasetid,
        'stationid': stationid,
        'startdate': startdate,
        'enddate': enddate,
        'limit': 1000  # Limit to 1000 results to avoid overwhelming the API
    }
    headers = {'token': token}
    cache_key = f'data_{datasetid}_{stationid}_{startdate}_{enddate}'
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {'error': f'Error fetching data: {str(e)}'}

def main():
    """
    Demonstrate key functions using a placeholder token.
    Note: Replace 'your_demo_token_here' with a valid NOAA token for actual use.
    """
    demo_token = 'your_demo_token_here'
    
    # Demo 1: Get datasets
    datasets_result = get_datasets(demo_token)
    if 'error' in datasets_result:
        print(f"Datasets error: {datasets_result['error']}")
    else:
        print(f"Number of datasets: {len(datasets_result.get('results', []))}")
    
    # Demo 2: Get data categories
    categories_result = get_data_categories(demo_token)
    if 'error' in categories_result:
        print(f"Data categories error: {categories_result['error']}")
    else:
        print(f"Number of data categories: {len(categories_result.get('results', []))}")
    
    # Demo 3: Get stations for a location
    stations_result = get_stations(demo_token, 'New York')
    if 'error' in stations_result:
        print(f"Stations error: {stations_result['error']}")
    else:
        print(f"Number of stations for New York: {len(stations_result.get('results', []))}")

if __name__ == '__main__':
    main()
