#!/usr/bin/env python3

"""
QuantClaw Data Module: cftc_commitments

PURPOSE: Retrieves commitments of traders reports for futures and options markets to analyze market positioning.

Data Source: https://www.cftc.gov/sites/default/files/files/opa/data.htm
Update Frequency: Weekly (reports are typically released on Fridays)
Auth Info: No authentication required; data is publicly available.

CATEGORY: derivatives
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/cftc_commitments')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a cached GET request.

    Args:
        url (str): The URL to fetch.
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
        return {'error': str(e)}

def get_futures_commitments() -> dict:
    """
    Fetches the latest futures commitments of traders report.

    Returns:
        dict: The report data as a dictionary, or an error dictionary if failed.
    """
    url = 'https://www.cftc.gov/api/futures_commitments.json'  # Hypothetical URL for demonstration
    try:
        return _cached_get(url, 'futures_commitments')
    except Exception as e:
        return {'error': f'Failed to fetch futures commitments: {str(e)}'}

def get_options_commitments() -> dict:
    """
    Fetches the latest options commitments of traders report.

    Returns:
        dict: The report data as a dictionary, or an error dictionary if failed.
    """
    url = 'https://www.cftc.gov/api/options_commitments.json'  # Hypothetical URL for demonstration
    try:
        return _cached_get(url, 'options_commitments')
    except Exception as e:
        return {'error': f'Failed to fetch options commitments: {str(e)}'}

def get_report_by_date(date: str) -> dict:
    """
    Fetches the commitments report for a specific date.

    Args:
        date (str): The date in YYYY-MM-DD format.

    Returns:
        dict: The report data as a dictionary, or an error dictionary if failed.
    """
    url = f'https://www.cftc.gov/api/commitments/{date}.json'  # Hypothetical URL for demonstration
    try:
        return _cached_get(url, f'commitments_{date}')
    except Exception as e:
        return {'error': f'Failed to fetch report for {date}: {str(e)}'}

def get_commodity_data(commodity: str) -> dict:
    """
    Fetches commitments data for a specific commodity.

    Args:
        commodity (str): The commodity name (e.g., 'crude_oil').

    Returns:
        dict: The commodity data as a dictionary, or an error dictionary if failed.
    """
    url = f'https://www.cftc.gov/api/commodity/{commodity}.json'  # Hypothetical URL for demonstration
    try:
        return _cached_get(url, f'commodity_{commodity}')
    except Exception as e:
        return {'error': f'Failed to fetch data for {commodity}: {str(e)}'}

def list_available_commodities() -> list:
    """
    Fetches a list of available commodities for commitments reports.

    Returns:
        list: A list of commodities, or a list containing an error dictionary if failed.
    """
    url = 'https://www.cftc.gov/api/commodities.json'  # Hypothetical URL for demonstration
    try:
        data = _cached_get(url, 'available_commodities')
        return data.get('commodities', [])  # Assuming the response has a 'commodities' key
    except Exception as e:
        return [{'error': f'Failed to list commodities: {str(e)}'}]

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    print("Demonstrating CFTC Commitments Module:")
    
    # Demo 1: Get futures commitments
    futures_data = get_futures_commitments()
    if 'error' in futures_data:
        print(f"Futures commitments error: {futures_data['error']}")
    else:
        print(f"Futures commitments fetched successfully. Sample: {futures_data.get('sample_key', 'No sample')}")  # Replace with actual key
    
    # Demo 2: Get report by date
    report_data = get_report_by_date('2023-01-01')  # Example date
    if 'error' in report_data:
        print(f"Report by date error: {report_data['error']}")
    else:
        print(f"Report for 2023-01-01 fetched successfully. Sample: {report_data.get('sample_key', 'No sample')}")  # Replace with actual key
    
    # Demo 3: Get commodity data
    commodity_data = get_commodity_data('crude_oil')
    if 'error' in commodity_data:
        print(f"Commodity data error: {commodity_data['error']}")
    else:
        print(f"Crude oil data fetched successfully. Sample: {commodity_data.get('sample_key', 'No sample')}")  # Replace with actual key

if __name__ == '__main__':
    main()
