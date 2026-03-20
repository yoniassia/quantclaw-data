#!/usr/bin/env python3
"""
QuantClaw Data Module: coingecko_crypto_market_data

PURPOSE: Provides real-time cryptocurrency prices, market cap, and volume data for crypto assets.
Data Source URL: https://api.coingecko.com/api/v3/
Update Frequency: Real-time via API, with local caching for 1 hour.
Auth Info: No authentication required; uses public endpoints.
CATEGORY: crypto
"""

import requests
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/coingecko_crypto_market_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url: str, cache_key: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Helper function to get data with caching.

    Args:
        url (str): The API URL to fetch.
        cache_key (str): A unique key for caching the response.
        params (dict): Optional query parameters.
        headers (dict): Optional headers.

    Returns:
        dict: The JSON response data.
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
        return {'error': str(e)}

def get_current_price(coin_id: str, vs_currencies: str) -> Dict[str, Any]:
    """
    Fetch the current price of a cryptocurrency.

    Args:
        coin_id (str): The ID of the coin, e.g., 'bitcoin'.
        vs_currencies (str): The currencies to price against, e.g., 'usd,eur'.

    Returns:
        dict: A dictionary with prices, or an error dictionary.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price"
    cache_key = f"price_{coin_id}_{vs_currencies}"
    params = {'ids': coin_id, 'vs_currencies': vs_currencies}
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_market_chart(coin_id: str, days: int) -> Dict[str, Any]:
    """
    Fetch historical market chart data for a cryptocurrency.

    Args:
        coin_id (str): The ID of the coin, e.g., 'bitcoin'.
        days (int): The number of days of data to fetch.

    Returns:
        dict: A dictionary with market chart data, or an error dictionary.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    cache_key = f"market_chart_{coin_id}_{days}"
    params = {'vs_currency': 'usd', 'days': days}  # Using USD as default
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_coins_list() -> List[Dict[str, Any]]:
    """
    Fetch a list of all supported cryptocurrencies.

    Returns:
        list: A list of dictionaries containing coin details, or an error dictionary.
    """
    url = "https://api.coingecko.com/api/v3/coins/list"
    cache_key = "coins_list"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return [{'error': str(e)}]

def get_top_coins(per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
    """
    Fetch the top coins by market capitalization.

    Args:
        per_page (int): Number of coins per page.
        page (int): The page number.

    Returns:
        list: A list of dictionaries with top coin data, or an error dictionary.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    cache_key = f"top_coins_{per_page}_{page}"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': per_page, 'page': page}
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return [{'error': str(e)}]

def get_global_market_data() -> Dict[str, Any]:
    """
    Fetch global cryptocurrency market data.

    Returns:
        dict: A dictionary with global market data, or an error dictionary.
    """
    url = "https://api.coingecko.com/api/v3/global"
    cache_key = "global_market_data"
    try:
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': str(e)}

def main():
    """
    Demonstrate key functions.
    """
    print("Demonstrating get_current_price for Bitcoin in USD:")
    result = get_current_price('bitcoin', 'usd')
    print(result)  # Output: {'bitcoin': {'usd': 45000}} or error

    print("\nDemonstrating get_top_coins for top 5 coins:")
    top_coins = get_top_coins(5)
    print(top_coins[:2])  # Output: First two items of the list or error

    print("\nDemonstrating get_global_market_data:")
    global_data = get_global_market_data()
    print(global_data.get('data', {}))  # Output: Global data or error

if __name__ == '__main__':
    main()
