#!/usr/bin/env python3

"""
QuantClaw Data Module: cme_futures_derivatives

PURPOSE: Provides access to real-time and historical futures and options market data from CME Group.

Data Source URL: https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc
Update Frequency: Real-time data available, with responses cached for 1 hour.
Auth Info: No authentication required for public endpoints; uses free tier access.
CATEGORY: derivatives
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/cme_futures_derivatives')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a cached GET request.

    Args:
        url (str): The URL to fetch.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

    Returns:
        dict: The JSON response data, or cached data if available and not expired.
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

def get_futures_quotes(symbol: str) -> dict:
    """
    Fetches current futures quotes for a given symbol.

    Args:
        symbol (str): The futures symbol (e.g., 'ES' for E-mini S&P 500).

    Returns:
        dict: A dictionary containing the quotes data, or an error dictionary on failure.
    """
    url = f"https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc/Futures/{symbol}"
    cache_key = f"futures_quotes_{symbol}"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f"Failed to fetch futures quotes: {str(e)}"}

def get_options_quotes(symbol: str) -> dict:
    """
    Fetches current options quotes for a given symbol.

    Args:
        symbol (str): The options symbol (e.g., 'ES' for E-mini S&P 500 options).

    Returns:
        dict: A dictionary containing the options quotes data, or an error dictionary on failure.
    """
    url = f"https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc/Options/{symbol}"
    cache_key = f"options_quotes_{symbol}"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f"Failed to fetch options quotes: {str(e)}"}

def get_historical_prices(symbol: str, date: str) -> list:
    """
    Fetches historical prices for a given symbol and date.

    Args:
        symbol (str): The futures or options symbol.
        date (str): The date in YYYY-MM-DD format.

    Returns:
        list: A list of historical price data points, or an error dictionary on failure.
    """
    url = f"https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc/Historical/{symbol}?date={date}"
    cache_key = f"historical_prices_{symbol}_{date}"
    try:
        return _cached_get(url, cache_key).get('data', [])  # Assuming the response has a 'data' key
    except Exception as e:
        return [{'error': f"Failed to fetch historical prices: {str(e)}"}]

def list_available_contracts() -> list:
    """
    Fetches a list of available futures contracts.

    Returns:
        list: A list of available contracts, or an error dictionary on failure.
    """
    url = "https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc/Contracts"
    cache_key = "available_contracts"
    try:
        return _cached_get(url, cache_key).get('contracts', [])  # Assuming the response has a 'contracts' key
    except Exception as e:
        return [{'error': f"Failed to fetch available contracts: {str(e)}"}]

def get_market_status() -> dict:
    """
    Fetches the current market status.

    Returns:
        dict: A dictionary containing the market status, or an error dictionary on failure.
    """
    url = "https://www.cmegroup.com/CmeWS/mvc/Quotes/Quotes.svc/Status"
    cache_key = "market_status"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f"Failed to fetch market status: {str(e)}"}

def main():
    """
    Demonstrates 2-3 key functions from the module.
    """
    print("Demonstrating get_futures_quotes for symbol 'ES':")
    result1 = get_futures_quotes('ES')
    print(result1)  # Output the result dictionary

    print("\nDemonstrating list_available_contracts:")
    result2 = list_available_contracts()
    print(result2[:5])  # Output the first 5 items or the error

    print("\nDemonstrating get_options_quotes for symbol 'ES':")
    result3 = get_options_quotes('ES')
    print(result3)  # Output the result dictionary

if __name__ == '__main__':
    main()
