#!/usr/bin/env python3

"""
QuantClaw Data Module: coingecko_crypto_data

PURPOSE: Fetches real-time cryptocurrency prices, market cap, and volume data from CoinGecko.

Data Source URL: https://api.coingecko.com/api/v3

Update Frequency: Real-time via API, with responses cached for 1 hour in this module.

Auth Info: No authentication required; uses public endpoints.
"""

import requests
import json
import time
from pathlib import Path

# Cache setup
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/coingecko_crypto_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.

    Args:
        url (str): The API URL.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.

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

def get_coin_list():
    """
    Fetch a list of supported cryptocurrencies.

    Returns:
        list: A list of dictionaries, each containing coin details.
    """
    try:
        data = _cached_get('https://api.coingecko.com/api/v3/coins/list', 'coin_list')
        return data
    except Exception as e:
        return [{'error': str(e)}]

def get_current_price(coin_id, vs_currencies='usd'):
    """
    Fetch the current price of a specific cryptocurrency.

    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        vs_currencies (str): The currencies to price against (e.g., 'usd').

    Returns:
        dict: A dictionary with prices in the specified currencies.
    """
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs_currencies}'
    try:
        data = _cached_get(url, f'price_{coin_id}_{vs_currencies}')
        return data
    except Exception as e:
        return {'error': str(e)}

def get_coin_market_data(coin_id):
    """
    Fetch detailed market data for a specific cryptocurrency.

    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').

    Returns:
        dict: A dictionary containing market data for the coin.
    """
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    try:
        data = _cached_get(url, f'coin_market_data_{coin_id}')
        return data
    except Exception as e:
        return {'error': str(e)}

def get_global_market_data():
    """
    Fetch global cryptocurrency market data.

    Returns:
        dict: A dictionary containing global market overview.
    """
    url = 'https://api.coingecko.com/api/v3/global'
    try:
        data = _cached_get(url, 'global_market_data')
        return data
    except Exception as e:
        return {'error': str(e)}

def get_top_coins(per_page=10):
    """
    Fetch the top cryptocurrencies by market cap.

    Args:
        per_page (int): Number of coins to return.

    Returns:
        list: A list of dictionaries, each for a top coin.
    """
    url = f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={per_page}&page=1'
    try:
        data = _cached_get(url, f'top_coins_{per_page}')
        return data
    except Exception as e:
        return [{'error': str(e)}]

def main():
    """
    Demonstrate key functions.
    """
    # Demo 1: Get coin list (first 5 items)
    coin_list_result = get_coin_list()
    print("First 5 coins from get_coin_list:", coin_list_result[:5])

    # Demo 2: Get current price of Bitcoin in USD
    bitcoin_price_result = get_current_price('bitcoin', 'usd')
    print("Current price of Bitcoin in USD:", bitcoin_price_result)

    # Demo 3: Get global market data
    global_data_result = get_global_market_data()
    print("Global market data overview:", global_data_result.get('data', {}))

if __name__ == '__main__':
    main()
