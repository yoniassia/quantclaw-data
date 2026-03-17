#!/usr/bin/env python3

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/bis_statistics')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600

def _cached_get(url, cache_key, params=None, headers=None):
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

"""
QuantClaw Data Module: bis_statistics

PURPOSE: Accesses international banking statistics including credit and debt data from the Bank for International Settlements (BIS).

API/SOURCE: https://stats.bis.org/

Update Frequency: Data is updated quarterly or as per BIS schedules.

Auth Info: No authentication required for public endpoints; uses free, publicly available data.
"""

def get_locational_banking_data():
    """
    Fetches locational banking statistics data from BIS.

    Returns: dict containing the data, or a dict with an error message.
    """
    url = "https://stats.bis.org/api/v1/data/BIS/LOC"  # Placeholder for actual endpoint
    cache_key = "locational_banking_data"
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch locational banking data: {str(e)}'}

def get_consolidated_banking_data():
    """
    Fetches consolidated banking statistics data from BIS.

    Returns: dict containing the data, or a dict with an error message.
    """
    url = "https://stats.bis.org/api/v1/data/BIS/CBS"  # Placeholder for actual endpoint
    cache_key = "consolidated_banking_data"
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch consolidated banking data: {str(e)}'}

def get_international_debt_securities():
    """
    Fetches international debt securities statistics data from BIS.

    Returns: list of dicts containing the data, or a dict with an error message.
    """
    url = "https://stats.bis.org/api/v1/data/BIS/IDS"  # Placeholder for actual endpoint
    cache_key = "international_debt_securities"
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch international debt securities: {str(e)}'}

def get_credit_to_gdp_data():
    """
    Fetches credit to GDP gaps and related statistics data from BIS.

    Returns: dict containing the data, or a dict with an error message.
    """
    url = "https://stats.bis.org/api/v1/data/BIS/CreditToGDP"  # Placeholder for actual endpoint
    cache_key = "credit_to_gdp_data"
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch credit to GDP data: {str(e)}'}

def get_global_liquidity_data():
    """
    Fetches global liquidity indicators data from BIS.

    Returns: list of dicts containing the data, or a dict with an error message.
    """
    url = "https://stats.bis.org/api/v1/data/BIS/GlobalLiquidity"  # Placeholder for actual endpoint
    cache_key = "global_liquidity_data"
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch global liquidity data: {str(e)}'}

def main():
    """
    Demonstrates key functions in the bis_statistics module.
    """
    print("Demonstrating BIS Statistics Module:")
    
    # Demo 1: Get locational banking data
    locational_data = get_locational_banking_data()
    if 'error' in locational_data:
        print(f"Error in locational data: {locational_data['error']}")
    else:
        print(f"Locational banking data fetched: {len(locational_data)} items")  # Assuming it's a list or dict with length
    
    # Demo 2: Get consolidated banking data
    consolidated_data = get_consolidated_banking_data()
    if 'error' in consolidated_data:
        print(f"Error in consolidated data: {consolidated_data['error']}")
    else:
        print(f"Consolidated banking data fetched: {len(consolidated_data)} items")
    
    # Demo 3: Get international debt securities
    debt_securities_data = get_international_debt_securities()
    if 'error' in debt_securities_data:
        print(f"Error in debt securities data: {debt_securities_data['error']}")
    else:
        print(f"International debt securities data fetched: {len(debt_securities_data)} items")

if __name__ == '__main__':
    main()
