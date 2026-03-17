#!/usr/bin/env python3
"""
Module: iex_cloud_stock_data

Purpose: Provides real-time and historical equity market data including stock prices and quotes.

Data Source URL: https://cloud.iexapis.com/

Update Frequency: Real-time for some endpoints, with possible delays on free tier (e.g., 15-minute delayed quotes).

Auth Info: Requires a publishable API token from IEX Cloud. Use free tier tokens only; replace the placeholder in IEX_TOKEN.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iex_cloud_stock_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to get data with caching."""
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    cache_file.write_text(json.dumps(data, indent=2))
    return data

# API token placeholder - replace with your actual publishable token
IEX_TOKEN = 'your_publishable_token_here'  # e.g., from IEX Cloud free tier

def get_stock_quote(symbol: str) -> dict:
    """Fetch real-time quote for the given stock symbol.
    
    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
    
    Returns:
        dict: Quote data or {'error': 'error message'} on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
    params = {'token': IEX_TOKEN}
    cache_key = f'quote_{symbol}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_historical_prices(symbol: str, date_range: str) -> list:
    """Fetch historical prices for the given stock symbol and date range.
    
    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
        date_range (str): Date range, e.g., '1m', '1y', 'ytd'.
    
    Returns:
        list: List of historical price data or {'error': 'error message'} on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{date_range}"
    params = {'token': IEX_TOKEN}
    cache_key = f'historical_{symbol}_{date_range}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_company_info(symbol: str) -> dict:
    """Fetch company information for the given stock symbol.
    
    Args:
        symbol (str): Stock symbol, e.g., 'AAPL'.
    
    Returns:
        dict: Company info data or {'error': 'error message'} on failure.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/company"
    params = {'token': IEX_TOKEN}
    cache_key = f'company_{symbol}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_top_gainers() -> list:
    """Fetch the top gaining stocks.
    
    Returns:
        list: List of top gainers data or {'error': 'error message'} on failure.
    """
    url = "https://cloud.iexapis.com/stable/stock/market/list/gainers"
    params = {'token': IEX_TOKEN}
    cache_key = 'top_gainers'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_top_losers() -> list:
    """Fetch the top losing stocks.
    
    Returns:
        list: List of top losers data or {'error': 'error message'} on failure.
    """
    url = "https://cloud.iexapis.com/stable/stock/market/list/losers"
    params = {'token': IEX_TOKEN}
    cache_key = 'top_losers'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions from the module."""
    # Demo 1: Get stock quote
    quote = get_stock_quote('AAPL')
    if 'error' in quote:
        print("Error in quote:", quote['error'])
    else:
        print("AAPL Quote:", quote.get('latestPrice', 'N/A'))
    
    # Demo 2: Get historical prices
    historical = get_historical_prices('AAPL', '1m')
    if 'error' in historical:
        print("Error in historical prices:", historical['error'])
    else:
        print("AAPL 1m Historical Prices (first 5):", historical[:5])
    
    # Demo 3: Get top gainers
    gainers = get_top_gainers()
    if 'error' in gainers:
        print("Error in top gainers:", gainers['error'])
    else:
        print("Top Gainers (first 3):", gainers[:3])

if __name__ == '__main__':
    main()
