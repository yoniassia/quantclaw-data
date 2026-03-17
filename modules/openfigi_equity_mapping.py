#!/usr/bin/env python3

"""
QuantClaw Data Module: openfigi_equity_mapping

Purpose: Maps and identifies global equity symbols and financial instruments for analysis

Data Source: https://api.openfigi.com

Update Frequency: Real-time via API, with responses cached for 1 hour

Authentication: No API key required for basic usage; requests are rate-limited by the provider.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openfigi_equity_mapping')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper to perform a cached GET request.
    
    Args:
        url (str): The URL to request.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.
    
    Returns:
        dict: The response data or an error dict.
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
    except requests.RequestException as e:
        return {"error": str(e)}

def _cached_post(url, cache_key, data, headers=None):
    """
    Helper to perform a cached POST request.
    
    Args:
        url (str): The URL to request.
        cache_key (str): Unique key for caching, based on the data.
        data (dict): The JSON data to send.
        headers (dict): HTTP headers.
    
    Returns:
        dict or list: The response data or an error dict.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        cache_file.write_text(json.dumps(result, indent=2))
        return result
    except requests.RequestException as e:
        return {"error": str(e)}

def map_ticker_to_figi(ticker: str, exchange: str = '') -> dict:
    """
    Map a single ticker to its FIGI using OpenFIGI.
    
    Args:
        ticker (str): The equity ticker symbol.
        exchange (str): The exchange code (e.g., 'US').
    
    Returns:
        dict: The mapping response or an error dict.
    """
    request_body = [{"idType": "TICKER", "id": ticker, "exchCode": exchange}]
    cache_key = f"map_ticker_{ticker}_{exchange}"
    return _cached_post("https://api.openfigi.com/v2/mapping", cache_key, request_body)

def map_multiple_tickers(tickers: list, exchange: str = '') -> list:
    """
    Map multiple tickers to their FIGIs using OpenFIGI.
    
    Args:
        tickers (list): A list of equity ticker symbols.
        exchange (str): The exchange code (e.g., 'US').
    
    Returns:
        list: A list of mapping responses or error dicts.
    """
    request_body = [{"idType": "TICKER", "id": ticker, "exchCode": exchange} for ticker in tickers]
    cache_key = f"map_multiple_tickers_{'_'.join(tickers)}_{exchange}"
    return _cached_post("https://api.openfigi.com/v2/mapping", cache_key, request_body)

def map_name_to_figi(name: str) -> list:
    """
    Map a company name to its FIGIs using OpenFIGI.
    
    Args:
        name (str): The company name to search.
    
    Returns:
        list: A list of mapping responses or an error dict.
    """
    request_body = [{"idType": "NAME", "id": name}]
    cache_key = f"map_name_{name}"
    return _cached_post("https://api.openfigi.com/v2/mapping", cache_key, request_body)

def map_isin_to_figi(isin: str) -> dict:
    """
    Map an ISIN to its FIGI using OpenFIGI.
    
    Args:
        isin (str): The ISIN code.
    
    Returns:
        dict: The mapping response or an error dict.
    """
    request_body = [{"idType": "ID_ISIN", "id": isin}]
    cache_key = f"map_isin_{isin}"
    return _cached_post("https://api.openfigi.com/v2/mapping", cache_key, request_body)

def map_cusip_to_figi(cusip: str) -> dict:
    """
    Map a CUSIP to its FIGI using OpenFIGI.
    
    Args:
        cusip (str): The CUSIP code.
    
    Returns:
        dict: The mapping response or an error dict.
    """
    request_body = [{"idType": "ID_CUSIP", "id": cusip}]
    cache_key = f"map_cusip_{cusip}"
    return _cached_post("https://api.openfigi.com/v2/mapping", cache_key, request_body)

def main():
    """
    Demonstrate key functions from the module.
    """
    # Demo 1: Map a single ticker
    result1 = map_ticker_to_figi("AAPL", "US")
    print(result1)  # For demo purposes only; functions return data
    
    # Demo 2: Map multiple tickers
    result2 = map_multiple_tickers(["AAPL", "GOOG"])
    print(result2)
    
    # Demo 3: Map a name
    result3 = map_name_to_figi("Apple Inc")
    print(result3)

if __name__ == '__main__':
    main()
