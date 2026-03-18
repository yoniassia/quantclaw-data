#!/usr/bin/env python3
"""
QuantClaw Data: iexcloud_stock_data

Provides real-time and historical price data for US stocks and equities.

Data Source: https://cloud.iexapis.com
Update Frequency: Real-time data with possible delays; historical data updated as per API.
Auth Info: Uses IEX Cloud sandbox token for free access. Replace with your own sandbox token.

"""

import requests
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

IEX_TOKEN = 'Tsk_1234567890abcdef'  # Replace with your actual IEX Cloud sandbox token

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iexcloud_stock_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url: str, cache_key: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Helper function to get data with caching.
    
    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.
    
    Returns:
        dict: The fetched or cached data.
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

def get_quote(symbol: str) -> Dict[str, Any]:
    """
    Get real-time quote for the given stock symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
    
    Returns:
        dict: Quote data or error dictionary.
    """
    url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/quote"
    params = {'token': IEX_TOKEN}
    cache_key = f"quote_{symbol}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_historical_prices(symbol: str, range_: str = '1m') -> List[Dict[str, Any]]:
    """
    Get historical prices for the given stock symbol and range.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
        range_ (str): Time range (e.g., '1m', '1y', 'ytd').
    
    Returns:
        list: List of historical price data or error dictionary.
    """
    url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/chart/{range_}"
    params = {'token': IEX_TOKEN}
    cache_key = f"historical_{symbol}_{range_}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': str(e)}]

def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Get company information for the given stock symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
    
    Returns:
        dict: Company info data or error dictionary.
    """
    url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/company"
    params = {'token': IEX_TOKEN}
    cache_key = f"company_{symbol}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_latest_news(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the latest news for the given stock symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
        limit (int): Number of news items to retrieve.
    
    Returns:
        list: List of news items or error dictionary.
    """
    url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/news/last/{limit}"
    params = {'token': IEX_TOKEN}
    cache_key = f"news_{symbol}_{limit}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': str(e)}]

def get_dividends(symbol: str, range_: str = '1y') -> List[Dict[str, Any]]:
    """
    Get dividend data for the given stock symbol and range.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL').
        range_ (str): Time range (e.g., '1y', '5y').
    
    Returns:
        list: List of dividend data or error dictionary.
    """
    url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/dividends/{range_}"
    params = {'token': IEX_TOKEN}
    cache_key = f"dividends_{symbol}_{range_}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': str(e)}]

def main():
    """
    Demonstrate key functions.
    """
    import sys  # For potential error handling or output
    
    print("Demonstrating get_quote for AAPL:")
    quote_result = get_quote('AAPL')
    print(quote_result)
    
    print("\nDemonstrating get_historical_prices for AAPL with 1m range:")
    historical_result = get_historical_prices('AAPL', '1m')
    print(historical_result[:5])  # Print first 5 items for brevity
    
    print("\nDemonstrating get_company_info for AAPL:")
    company_result = get_company_info('AAPL')
    print(company_result)

if __name__ == '__main__':
    main()
