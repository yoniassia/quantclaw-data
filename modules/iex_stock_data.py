#!/usr/bin/env python3

"""QuantClaw Data Module: iex_stock_data

PURPOSE: Provides real-time and historical stock prices, quotes, and company fundamentals for U.S. equities.

API/SOURCE: https://cloud.iexapis.com/stable/

UPDATE FREQUENCY: Real-time for quotes; historical data varies (e.g., daily updates for charts).

AUTH INFO: Requires a IEX Cloud publishable token for free tier access. Replace the token in IEX_TOKEN with your own.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iex_stock_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper to get data with caching."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

IEX_TOKEN = 'Tpk_Your_Publishable_Token'  # Replace with your IEX Cloud publishable token

def get_quote(symbol: str) -> dict:
    """Get real-time quote for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Quote data as a dictionary, or an error dictionary if failed.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
    params = {'token': IEX_TOKEN}
    cache_key = f'quote_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_historical_prices(symbol: str, range_: str = '1m') -> list:
    """Get historical prices for the given symbol and range.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        range_ (str): Time range, e.g., '1d', '1m', '3m', '1y'.

    Returns:
        list: List of historical price data, or an error dictionary if failed.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range_}"
    params = {'token': IEX_TOKEN}
    cache_key = f'historical_{symbol}_{range_}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_company_info(symbol: str) -> dict:
    """Get company fundamentals for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Company information as a dictionary, or an error dictionary if failed.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/company"
    params = {'token': IEX_TOKEN}
    cache_key = f'company_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_news(symbol: str, last: int = 5) -> list:
    """Get recent news for the given stock symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        last (int): Number of recent news items to retrieve.

    Returns:
        list: List of news items, or an error dictionary if failed.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/news/last/{last}"
    params = {'token': IEX_TOKEN}
    cache_key = f'news_{symbol}_{last}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def search_symbols(query: str) -> list:
    """Search for stock symbols matching the query.

    Args:
        query (str): Search query string, e.g., 'apple'.

    Returns:
        list: List of matching symbols and details, or an error dictionary if failed.
    """
    url = f"https://cloud.iexapis.com/stable/search/{query}"
    params = {'token': IEX_TOKEN}
    cache_key = f'search_{query}'
    try:
        data = _cached_get(url, cache_key, params=params)
        return data.get('results', [])  # Extract results list from response
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions."""
    quote = get_quote('AAPL')
    historical = get_historical_prices('AAPL', '1m')
    company = get_company_info('AAPL')
    
    return {
        'quote': quote,
        'historical_prices': historical[:5],  # Return first 5 for brevity
        'company_info': company
    }

if __name__ == '__main__':
    result = main()
    # For demonstration, the main function returns a dict; you can process it as needed
    print(result)  # This is for demo purposes only
