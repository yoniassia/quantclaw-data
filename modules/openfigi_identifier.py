#!/usr/bin/env python3
"""
QuantClaw Data Module: openfigi_identifier

PURPOSE: Maps and identifies financial instruments by providing standardized identifiers for stocks, bonds, and other securities.

Data Source: https://api.openfigi.com/
Update Frequency: On-demand via API
Auth Info: No authentication required; include a User-Agent header for requests.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path
import hashlib  # For generating cache keys for batch requests

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openfigi_identifier')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper to perform cached GET requests."""
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

def _cached_post(url, cache_key, data=None, headers=None):
    """Helper to perform cached POST requests."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        resp.raise_for_status()
        result_data = resp.json()
        cache_file.write_text(json.dumps(result_data, indent=2))
        return result_data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_figi_for_ticker(ticker: str) -> dict:
    """Retrieve FIGI mapping for a given ticker symbol.
    
    Args:
        ticker (str): The ticker symbol (e.g., 'AAPL').
    
    Returns:
        dict: A list of mapping results or an error dictionary.
    """
    url = 'https://api.openfigi.com/v2/mapping'
    data = [{"idType": "TICKER", "idValue": ticker}]
    cache_key = f'ticker_{ticker}'
    headers = {'User-Agent': 'quantclaw-data/1.0'}
    return _cached_post(url, cache_key, data=data, headers=headers)

def get_figi_for_isin(isin: str) -> dict:
    """Retrieve FIGI mapping for a given ISIN.
    
    Args:
        isin (str): The ISIN value (e.g., 'US0378331005').
    
    Returns:
        dict: A list of mapping results or an error dictionary.
    """
    url = 'https://api.openfigi.com/v2/mapping'
    data = [{"idType": "ISIN", "idValue": isin}]
    cache_key = f'isin_{isin}'
    headers = {'User-Agent': 'quantclaw-data/1.0'}
    return _cached_post(url, cache_key, data=data, headers=headers)

def get_figi_for_cusip(cusip: str) -> dict:
    """Retrieve FIGI mapping for a given CUSIP.
    
    Args:
        cusip (str): The CUSIP value (e.g., '037833100').
    
    Returns:
        dict: A list of mapping results or an error dictionary.
    """
    url = 'https://api.openfigi.com/v2/mapping'
    data = [{"idType": "CUSIP", "idValue": cusip}]
    cache_key = f'cusip_{cusip}'
    headers = {'User-Agent': 'quantclaw-data/1.0'}
    return _cached_post(url, cache_key, data=data, headers=headers)

def get_figi_for_name(name: str) -> dict:
    """Retrieve FIGI mapping for a given company name.
    
    Args:
        name (str): The company name (e.g., 'Apple Inc').
    
    Returns:
        dict: A list of mapping results or an error dictionary.
    """
    url = 'https://api.openfigi.com/v2/mapping'
    data = [{"idType": "NAME", "idValue": name}]
    cache_key = f'name_{name}'
    headers = {'User-Agent': 'quantclaw-data/1.0'}
    return _cached_post(url, cache_key, data=data, headers=headers)

def batch_get_figi(ids: list) -> list:
    """Retrieve FIGI mappings for a batch of identifiers.
    
    Args:
        ids (list): A list of dictionaries, e.g., [{"idType": "TICKER", "idValue": "AAPL"}]
    
    Returns:
        list: A list of mapping results or an error dictionary.
    """
    url = 'https://api.openfigi.com/v2/mapping'
    cache_key = 'batch_' + hashlib.md5(json.dumps(ids, sort_keys=True).encode()).hexdigest()
    headers = {'User-Agent': 'quantclaw-data/1.0'}
    return _cached_post(url, cache_key, data=ids, headers=headers)

def main():
    """Demonstrate key functions."""
    # Demo 1: Get FIGI for ticker 'AAPL'
    aapl_result = get_figi_for_ticker('AAPL')
    print("FIGI for AAPL:", aapl_result)  # Output: dict or error dict
    
    # Demo 2: Get FIGI for ISIN 'US0378331005'
    isin_result = get_figi_for_isin('US0378331005')
    print("FIGI for ISIN US0378331005:", isin_result)  # Output: dict or error dict
    
    # Demo 3: Batch get for multiple IDs
    batch_ids = [{"idType": "TICKER", "idValue": "AAPL"}, {"idType": "ISIN", "idValue": "US0378331005"}]
    batch_result = batch_get_figi(batch_ids)
    print("Batch FIGI results:", batch_result)  # Output: list or error dict

if __name__ == '__main__':
    main()
