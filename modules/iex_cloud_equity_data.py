#!/usr/bin/env python3

"""
QuantClaw Data: iex_cloud_equity_data

PURPOSE: Provides stock quotes, company fundamentals, and historical prices for US equities

API/SOURCE: https://cloud.iexapis.com/

CATEGORY: equity

Data Source URL: https://cloud.iexapis.com/

Update frequency: Real-time data via API calls, with caching for 1 hour

Auth info: Requires a free IEX Cloud token. Pass the token as a query parameter (e.g., ?token=your_demo_token). Use a demo token from IEX Cloud's free tier.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iex_cloud_equity_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper to get data with caching.

    Args:
        url (str): The API URL.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

    Returns:
        dict or list: Cached or fetched data, or error dict on failure.
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

# IEX Cloud token (replace with your demo token)
IEX_TOKEN = 'Tpk_1234567890abcdef'  # Example; use a valid free tier token

def get_stock_quote(symbol: str) -> dict:
    """Get the current stock quote for the given symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Stock quote data or error dict.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/quote'
    params = {'token': IEX_TOKEN}
    cache_key = f'quote_{symbol}'
    return _cached_get(url, cache_key, params=params)

def get_company_fundamentals(symbol: str) -> dict:
    """Get company fundamentals for the given symbol (uses /company endpoint as proxy).

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Fundamentals data or error dict.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/company'
    params = {'token': IEX_TOKEN}
    cache_key = f'fundamentals_{symbol}'
    return _cached_get(url, cache_key, params=params)

def get_historical_prices(symbol: str, range_: str = '1m') -> list:
    """Get historical prices for the given symbol and range.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        range_ (str): Time range, e.g., '1m', '3m', '1y'.

    Returns:
        list: List of historical price data or error dict.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range_}'
    params = {'token': IEX_TOKEN}
    cache_key = f'historical_{symbol}_{range_}'
    return _cached_get(url, cache_key, params=params)

def get_company_profile(symbol: str) -> dict:
    """Get company profile for the given symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.

    Returns:
        dict: Company profile data or error dict.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/company'
    params = {'token': IEX_TOKEN}
    cache_key = f'profile_{symbol}'
    return _cached_get(url, cache_key, params=params)

def get_news(symbol: str, last: int = 10) -> list:
    """Get recent news for the given symbol.

    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        last (int): Number of news items to retrieve.

    Returns:
        list: List of news articles or error dict.
    """
    url = f'https://cloud.iexapis.com/stable/stock/{symbol}/news'
    params = {'token': IEX_TOKEN, 'last': last}
    cache_key = f'news_{symbol}_{last}'
    return _cached_get(url, cache_key, params=params)

def main():
    """Demonstrate key functions."""
    quote = get_stock_quote('AAPL')
    print("Stock quote for AAPL:", quote)
    
    historical = get_historical_prices('AAPL', '1m')
    print("First 5 historical prices for AAPL:", historical[:5] if isinstance(historical, list) else historical)
    
    profile = get_company_profile('AAPL')
    print("Company profile for AAPL:", profile)

if __name__ == '__main__':
    main()
