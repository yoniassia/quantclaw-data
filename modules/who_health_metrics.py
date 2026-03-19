#!/usr/bin/env python3

"""
QuantClaw Data Module: who_health_metrics

PURPOSE: Offers global health data on pandemics, influencing market sentiment and economic forecasts

Data Source URL: https://covid19.who.int/

Update Frequency: Daily (based on source availability)

Auth Info: No authentication required; public endpoint
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/who_health_metrics')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to perform a cached GET request.

    Args:
        url (str): The URL to fetch.
        cache_key (str): Key for caching the response.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

    Returns:
        dict: The JSON response data or an error dictionary.
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

def get_global_summary():
    """Fetches the global summary of COVID-19 data from the WHO API.

    Returns:
        dict: A dictionary containing global summary data or an error dictionary.
    """
    url = 'https://covid19.who.int/WHO-COVID-19-global-data.json'
    try:
        return _cached_get(url, 'global_summary')
    except Exception as e:
        return {'error': str(e)}

def get_country_data(country):
    """Fetches COVID-19 data for a specific country by filtering global data.

    Args:
        country (str): The name of the country (e.g., 'United States').

    Returns:
        list: A list of dictionaries containing data for the specified country, or an error dictionary.
    """
    url = 'https://covid19.who.int/WHO-COVID-19-global-data.json'
    try:
        data = _cached_get(url, 'global_data')
        if 'error' in data:
            return data
        filtered_data = [item for item in data.get('data', []) if item.get('Country') == country]
        return filtered_data
    except Exception as e:
        return {'error': str(e)}

def get_latest_global_cases():
    """Fetches the latest global cases from the WHO API data.

    Returns:
        dict: A dictionary containing the latest global cases summary or an error dictionary.
    """
    try:
        global_data = get_global_summary()
        if 'error' in global_data:
            return global_data
        # Assuming the data structure has a way to extract latest; return the full data for simplicity
        return global_data  # Could be processed further in real use
    except Exception as e:
        return {'error': str(e)}

def get_global_statistics():
    """Fetches and returns basic global statistics derived from the WHO data.

    Returns:
        dict: A dictionary with derived statistics (e.g., total cases) or an error dictionary.
    """
    try:
        global_data = get_global_summary()
        if 'error' in global_data:
            return global_data
        # Derive simple stats; assuming 'data' is a list, sum relevant fields
        total_cases = sum(item.get('Cumulative_cases', 0) for item in global_data.get('data', []))
        return {'total_global_cases': total_cases}
    except Exception as e:
        return {'error': str(e)}

def get_data_by_date(date):
    """Fetches COVID-19 data for a specific date by filtering global data.

    Args:
        date (str): The date in the format expected by the API (e.g., '2023-01-01').

    Returns:
        list: A list of dictionaries containing data for the specified date, or an error dictionary.
    """
    url = 'https://covid19.who.int/WHO-COVID-19-global-data.json'
    try:
        data = _cached_get(url, 'data_by_date_' + date)
        if 'error' in data:
            return data
        filtered_data = [item for item in data.get('data', []) if item.get('Date_reported') == date]
        return filtered_data
    except Exception as e:
        return {'error': str(e)}

def main():
    """Demonstrates key functions from the module."""
    global_summary = get_global_summary()
    if 'error' not in global_summary:
        print("Global Summary:", global_summary)  # Example output; in production, process further
    else:
        print("Error in global summary:", global_summary)

    country_data = get_country_data('United States')
    if 'error' not in country_data:
        print("Country Data for United States:", country_data)
    else:
        print("Error in country data:", country_data)

    latest_cases = get_latest_global_cases()
    if 'error' not in latest_cases:
        print("Latest Global Cases:", latest_cases)
    else:
        print("Error in latest cases:", latest_cases)

if __name__ == '__main__':
    main()
