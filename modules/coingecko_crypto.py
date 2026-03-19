#!/usr/bin/env python3
"""
QuantClaw Data Module: coingecko_crypto

PURPOSE: Provides real-time cryptocurrency prices, market capitalization, and trends for crypto market analysis.

Data Source: https://api.coingecko.com
Update Frequency: Real-time via API, with local caching for 1 hour.
Authentication: None required; uses public endpoints.

CATEGORY: crypto
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/coingecko_crypto')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data from URL, using cache if available.

    Args:
        url (str): The API endpoint URL.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.

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
    except requests.exceptions.RequestException as e:
        raise  # Let the caller handle it

def get_current_price(coin_id: str, vs_currencies: str = 'usd') -> dict:
    """
    Get the current price of a cryptocurrency.

    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        vs_currencies (str): The currency to price against (e.g., 'usd').

    Returns:
        dict: A dictionary with price data, or an error dictionary.
    """
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {'ids': coin_id, 'vs_currencies': vs_currencies}
    cache_key = f'price_{coin_id}_{vs_currencies}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch price: {str(e)}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}'}

def get_coin_markets(vs_currency: str = 'usd', per_page: int = 250, page: int = 1) -> dict:
    """
    Get a list of cryptocurrencies with market data.

    Args:
        vs_currency (str): The currency for market data (e.g., 'usd').
        per_page (int): Number of results per page.
        page (int): The page number.

    Returns:
        dict: A list of market data dictionaries, or an error dictionary.
    """
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {'vs_currency': vs_currency, 'per_page': per_page, 'page': page}
    cache_key = f'markets_{vs_currency}_{per_page}_{page}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch markets: {str(e)}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}'}

def get_global_market_data() -> dict:
    """
    Get global cryptocurrency market data.

    Returns:
        dict: Global market data, or an error dictionary.
    """
    url = 'https://api.coingecko.com/api/v3/global'
    cache_key = 'global_market'
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch global data: {str(e)}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}'}

def get_trending_coins() -> dict:
    """
    Get the list of trending cryptocurrencies.

    Returns:
        dict: Trending coins data, or an error dictionary.
    """
    url = 'https://api.coingecko.com/api/v3/search/trending'
    cache_key = 'trending_coins'
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch trending coins: {str(e)}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}'}

def get_coin_by_id(coin_id: str) -> dict:
    """
    Get detailed data for a specific cryptocurrency by ID.

    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').

    Returns:
        dict: Coin details, or an error dictionary.
    """
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    cache_key = f'coin_{coin_id}'
    try:
        return _cached_get(url, cache_key)
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch coin data: {str(e)}'}
    except Exception as e:
        return {'error': f'An unexpected error occurred: {str(e)}'}

def main():
    """
    Demonstrate key functions.
    """
    # Demo 1: Get current price of Bitcoin
    price_result = get_current_price('bitcoin')
    print("Current price result:", price_result)
    
    # Demo 2: Get trending coins
    trending_result = get_trending_coins()
    print("Trending coins result:", trending_result)
    
    # Demo 3: Get global market data
    global_result = get_global_market_data()
    print("Global market data result:", global_result)

if __name__ == '__main__':
    main()
