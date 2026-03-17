#!/usr/bin/env python3

"""
Module: iex_stock_market_data

Purpose: Provides real-time and historical stock quotes, company fundamentals for equity market insights.
Category: equity

Data Source URL: https://cloud.iexapis.com/stable/
Update Frequency: Real-time for quotes; historical data updated as per IEX Cloud availability.
Auth Info: Requires an IEX Cloud API token. Use a free tier token for access (e.g., from IEX Cloud sandbox).
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iex_stock_market_data')
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

# IEX Cloud token for free tier access
IEX_TOKEN = 'your_free_iex_cloud_token_here'  # Replace with your actual free tier token

def get_stock_quote(symbol: str) -> dict:
    """Get real-time quote for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Quote data if successful, or {'error': 'error message'} on failure.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/quote'
    cache_key = f'quote_{symbol}'
    params = {'token': IEX_TOKEN}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_historical_prices(symbol: str, range_: str = '1m') -> list:
    """Get historical prices for the given stock symbol and range.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        range_ (str): Time range, e.g., '1m' for 1 month.

    Returns:
        list: List of historical price data if successful, or {'error': 'error message'} on failure.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range_}'
    cache_key = f'historical_{symbol}_{range_}'
    params = {'token': IEX_TOKEN}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_company_info(symbol: str) -> dict:
    """Get company fundamentals for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Company info data if successful, or {'error': 'error message'} on failure.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/company'
    cache_key = f'company_{symbol}'
    params = {'token': IEX_TOKEN}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_news(symbol: str, last: int = 10) -> list:
    """Get recent news for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        last (int): Number of recent news items to retrieve.

    Returns:
        list: List of news items if successful, or {'error': 'error message'} on failure.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/news/last/{last}'
    cache_key = f'news_{symbol}_{last}'
    params = {'token': IEX_TOKEN}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_top_gainers() -> list:
    """Get the list of top market gainers.

    Returns:
        list: List of top gainers data if successful, or {'error': 'error message'} on failure.
    """
    url = 'https://cloud.iexapis.com/stable/stock/market/list/gainers'
    cache_key = 'top_gainers'
    params = {'token': IEX_TOKEN}
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions from the module."""
    print("Demo of IEX Stock Market Data Module")
    
    # Demo 1: Get stock quote for AAPL
    quote = get_stock_quote('AAPL')
    print("Stock Quote for AAPL:", quote)
    
    # Demo 2: Get historical prices for AAPL (last 1 month)
    historical = get_historical_prices('AAPL', '1m')
    print("Historical Prices for AAPL (first 5 items):", historical[:5])
    
    # Demo 3: Get company info for AAPL
    company_info = get_company_info('AAPL')
    print("Company Info for AAPL:", company_info)

if __name__ == '__main__':
    main()
