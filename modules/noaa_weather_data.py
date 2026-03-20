#!/usr/bin/env python3

"""
Module for QuantClaw Data: noaa_weather_data

Provides global weather data for financial forecasting in sectors like agriculture.

Data Source URL: https://www.ncdc.noaa.gov/cdo-web/api/v2/
Update frequency: Data is updated in real-time for some endpoints and daily for others, depending on the dataset.
Auth info: Requires a free NOAA token. Obtain one at https://www.ncdc.noaa.gov/cdo-web/token and pass it via the token parameter in functions.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/noaa_weather_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
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
        return {"error": str(e)}

def get_datasets(token: str) -> dict:
    """Fetch available datasets from NOAA API.
    
    Args:
        token (str): NOAA API token.
    
    Returns:
        dict: JSON response containing datasets or an error dictionary.
    """
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets"
    headers = {"token": token}
    try:
        return _cached_get(url, "datasets", headers=headers)
    except Exception as e:
        return {"error": str(e)}

def get_datacategories(token: str) -> dict:
    """Fetch available data categories from NOAA API.
    
    Args:
        token (str): NOAA API token.
    
    Returns:
        dict: JSON response containing data categories or an error dictionary.
    """
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datacategories"
    headers = {"token": token}
    try:
        return _cached_get(url, "datacategories", headers=headers)
    except Exception as e:
        return {"error": str(e)}

def search_stations(token: str, location: str) -> dict:
    """Search for weather stations based on a location string.
    
    Args:
        token (str): NOAA API token.
        location (str): Location string to search for stations.
    
    Returns:
        dict: JSON response containing search results or an error dictionary.
    """
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations"
    params = {"location": location}
    headers = {"token": token}
    cache_key = f"stations_{location}"
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {"error": str(e)}

def get_locations(token: str, locationcategoryid: str) -> dict:
    """Fetch locations based on a location category ID.
    
    Args:
        token (str): NOAA API token.
        locationcategoryid (str): ID of the location category.
    
    Returns:
        dict: JSON response containing locations or an error dictionary.
    """
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/locations"
    params = {"locationcategoryid": locationcategoryid}
    headers = {"token": token}
    cache_key = f"locations_{locationcategoryid}"
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {"error": str(e)}

def get_station_data(token: str, station_id: str, datasetid: str, startdate: str, enddate: str) -> dict:
    """Fetch data for a specific station and dataset within a date range.
    
    Args:
        token (str): NOAA API token.
        station_id (str): ID of the weather station.
        datasetid (str): ID of the dataset.
        startdate (str): Start date in YYYY-MM-DD format.
        enddate (str): End date in YYYY-MM-DD format.
    
    Returns:
        dict: JSON response containing data or an error dictionary.
    """
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
    params = {
        "stationid": station_id,
        "datasetid": datasetid,
        "startdate": startdate,
        "enddate": enddate,
        "limit": 1000  # Limit to 1000 results to avoid overwhelming responses
    }
    headers = {"token": token}
    cache_key = f"data_{station_id}_{datasetid}_{startdate}_{enddate}"
    try:
        return _cached_get(url, cache_key, params=params, headers=headers)
    except Exception as e:
        return {"error": str(e)}

def main():
    """Demonstrate 2-3 key functions."""
    token = os.getenv("NOAA_TOKEN")  # Retrieve token from environment variable
    if token:
        # Demo get_datasets
        datasets_result = get_datasets(token)
        if "error" not in datasets_result:
            print({"datasets_count": len(datasets_result.get("results", []))})
        else:
            print(datasets_result)
        
        # Demo get_datacategories
        datacategories_result = get_datacategories(token)
        if "error" not in datacategories_result:
            print({"datacategories_count": len(datacategories_result.get("results", []))})
        else:
            print(datacategories_result)
        
        # Demo search_stations
        stations_result = search_stations(token, "US")
        if "error" not in stations_result:
            print({"stations_found": len(stations_result.get("results", []))})
        else:
            print(stations_result)
    else:
        print({"error": "NOAA token not set in environment variable."})

if __name__ == "__main__":
    main()
