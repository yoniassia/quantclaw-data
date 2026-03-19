#!/usr/bin/env python3
"""
QuantClaw Data Module: iex_cloud_stocks

PURPOSE: Provides US stock market data including real-time quotes and historical prices for equity research.
CATEGORY: equity
DATA SOURCE URL: https://cloud.iexapis.com/
UPDATE FREQUENCY: Real-time via API; cached responses in this module expire after 1 hour.
AUTH INFO: Requires a free IEX Cloud API token. Set the IEX_TOKEN variable in this module to your token (e.g., from the IEX Cloud sandbox for testing). Do not use paid tokens.

This module uses the IEX Cloud API to fetch stock data. All functions return dictionaries or lists, and errors are handled by returning error dictionaries.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iex_cloud_stocks')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a GET request with caching.

    Args:
        url (str): The URL to request.
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

# API token placeholder
IEX_TOKEN = 'YOUR_IEX_TOKEN'  # Replace with your actual free IEX Cloud token (e.g., from sandbox)

def get_stock_quote(symbol: str) -> dict:
    """
    Fetch real-time quote for a given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        dict: The quote data, or an error dictionary on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
    params = {'token': IEX_TOKEN}
    cache_key = f'quote_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get stock quote: {str(e)}'}

def get_historical_prices(symbol: str, range: str = '1m') -> list:
    """
    Fetch historical prices for a given stock symbol and range.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        range (str): The time range (e.g., '1m' for 1 month, '1y' for 1 year).

    Returns:
        list: A list of historical price data points, or an error dictionary on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range}"
    params = {'token': IEX_TOKEN}
    cache_key = f'historical_{symbol}_{range}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': f'Failed to get historical prices: {str(e)}'}]

def get_company_info(symbol: str) -> dict:
    """
    Fetch company information for a given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        dict: The company info data, or an error dictionary on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/company"
    params = {'token': IEX_TOKEN}
    cache_key = f'company_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get company info: {str(e)}'}

def get_latest_news(symbol: str, last: int = 5) -> list:
    """
    Fetch the latest news for a given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        last (int): The number of news items to retrieve.

    Returns:
        list: A list of news items, or an error dictionary on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/news/last/{last}"
    params = {'token': IEX_TOKEN}
    cache_key = f'news_{symbol}_{last}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': f'Failed to get latest news: {str(e)}'}]

def get_peers(symbol: str) -> list:
    """
    Fetch peer companies for a given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        list: A list of peer symbols, or an error dictionary on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/peers"
    params = {'token': IEX_TOKEN}
    cache_key = f'peers_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': f'Failed to get peers: {str(e)}'}]

def main():
    """
    Demonstrate key functions from the module.
    """
    # Demo 1: Get stock quote for AAPL
    aapl_quote = get_stock_quote('AAPL')
    print("AAPL Stock Quote:", aapl_quote)
    
    # Demo 2: Get historical prices for AAPL (1 month range)
    aapl_history = get_historical_prices('AAPL', '1m')
    print("AAPL Historical Prices (1m):", aapl_history[:5])  # Print first 5 for brevity
    
    # Demo 3: Get company info for AAPL
    aapl_company = get_company_info('AAPL')
    print("AAPL Company Info:", aapl_company)

if __name__ == '__main__':
    main()
