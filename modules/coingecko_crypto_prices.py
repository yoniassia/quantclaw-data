#!/usr/bin/env python3

"""
QuantClaw Data Module: coingecko_crypto_prices

PURPOSE: Retrieves current and historical cryptocurrency prices, market cap, and exchange rates from CoinGecko API.

Data Source: https://api.coingecko.com/api/v3/
Update Frequency: Real-time data available; responses cached for 1 hour.
Auth Info: No authentication required; uses public endpoints only.

CATEGORY: crypto
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/coingecko_crypto_prices')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data from URL, using cache if available and not expired.
    
    Args:
        url (str): The API endpoint URL.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters for the request.
        headers (dict, optional): Headers for the request.
    
    Returns:
        dict: The JSON response data, or cached data if valid.
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

def get_current_price(coin_id: str, vs_currency: str = 'usd') -> dict:
    """
    Retrieves the current price of a cryptocurrency in the specified currency.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        vs_currency (str): The currency to price against (e.g., 'usd'). Default is 'usd'.
    
    Returns:
        dict: A dictionary with the price data, e.g., {'bitcoin': {'usd': 50000}}.
              If an error occurs, returns {'error': 'error message'}.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    cache_key = f"current_price_{coin_id}_{vs_currency}"
    params = {'ids': coin_id, 'vs_currencies': vs_currency}
    try:
        data = _cached_get(url, cache_key, params=params)
        if 'error' in data:
            return data  # Propagate error from _cached_get
        return data
    except Exception as e:
        return {'error': str(e)}

def get_historical_price(coin_id: str, date: str) -> dict:
    """
    Retrieves the historical price of a cryptocurrency on a specific date.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        date (str): The date in YYYY-MM-DD format (e.g., '2023-01-01').
    
    Returns:
        dict: A dictionary with the historical market data.
              If an error occurs, returns {'error': 'error message'}.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
    cache_key = f"historical_price_{coin_id}_{date}"
    params = {'date': date}
    try:
        data = _cached_get(url, cache_key, params=params)
        if 'error' in data:
            return data
        return data
    except Exception as e:
        return {'error': str(e)}

def get_coin_market_data(coin_id: str) -> dict:
    """
    Retrieves market data for a specific cryptocurrency, including market cap.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
    
    Returns:
        dict: A dictionary with the coin's market data.
              If an error occurs, returns {'error': 'error message'}.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    cache_key = f"coin_market_data_{coin_id}"
    try:
        data = _cached_get(url, cache_key)
        if 'error' in data:
            return data
        return data
    except Exception as e:
        return {'error': str(e)}

def get_exchange_rates() -> dict:
    """
    Retrieves global exchange rates from CoinGecko.
    
    Returns:
        dict: A dictionary with exchange rates data.
              If an error occurs, returns {'error': 'error message'}.
    """
    url = "https://api.coingecko.com/api/v3/exchange_rates"
    cache_key = "exchange_rates"
    try:
        data = _cached_get(url, cache_key)
        if 'error' in data:
            return data
        return data
    except Exception as e:
        return {'error': str(e)}

def get_top_coins(per_page: int = 10, page: int = 1) -> list:
    """
    Retrieves a list of top cryptocurrencies by market cap.
    
    Args:
        per_page (int): Number of coins per page. Default is 10.
        page (int): The page number. Default is 1.
    
    Returns:
        list: A list of dictionaries, each representing a coin's data.
              If an error occurs, returns [{'error': 'error message'}].
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    cache_key = f"top_coins_{per_page}_{page}"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': per_page, 'page': page}
    try:
        data = _cached_get(url, cache_key, params=params)
        if 'error' in data and isinstance(data, dict):
            return [{'error': data['error']}]
        return data  # Expect a list
    except Exception as e:
        return [{'error': str(e)}]

def main():
    """
    Demonstrates key functions from the module.
    """
    print(get_current_price('bitcoin'))  # Demo: Current price of Bitcoin in USD
    print(get_historical_price('bitcoin', '2023-01-01'))  # Demo: Historical price of Bitcoin
    print(get_top_coins(5))  # Demo: Top 5 coins by market cap

if __name__ == '__main__':
    main()
