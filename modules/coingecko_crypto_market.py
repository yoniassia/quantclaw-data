#!/usr/bin/env python3
"""
QuantClaw Data Module: coingecko_crypto_market

Purpose: Retrieves real-time and historical cryptocurrency prices, market cap, and trading volumes.

Data Source: https://api.coingecko.com/api/v3/
Update Frequency: Real-time data, with responses cached for 1 hour.
Auth Info: No authentication required; uses public, free endpoints.
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/coingecko_crypto_market')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper function to get data with caching."""
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
        # Let the caller handle the exception
        raise

def get_coins_list():
    """Retrieves a list of supported cryptocurrencies.
    
    Returns:
        list: A list of dictionaries, each containing coin details.
    """
    try:
        return _cached_get('https://api.coingecko.com/api/v3/coins/list', 'coins_list')
    except Exception as e:
        return {'error': f'Failed to retrieve coins list: {str(e)}'}

def get_current_price(coin_id, vs_currencies='usd'):
    """Retrieves the current price of a cryptocurrency.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        vs_currencies (str): The currency to compare against (e.g., 'usd').
    
    Returns:
        dict: A dictionary with prices in the specified currencies.
    """
    try:
        params = {'ids': coin_id, 'vs_currencies': vs_currencies}
        cache_key = f'simple_price_{coin_id}_{vs_currencies}'
        return _cached_get('https://api.coingecko.com/api/v3/simple/price', cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve current price: {str(e)}'}

def get_global_market_data():
    """Retrieves global cryptocurrency market data.
    
    Returns:
        dict: A dictionary containing global market metrics.
    """
    try:
        return _cached_get('https://api.coingecko.com/api/v3/global', 'global_market_data')
    except Exception as e:
        return {'error': f'Failed to retrieve global market data: {str(e)}'}

def get_coin_by_id(coin_id):
    """Retrieves detailed information for a specific cryptocurrency.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
    
    Returns:
        dict: A dictionary with detailed coin information.
    """
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
        return _cached_get(url, f'coin_{coin_id}')
    except Exception as e:
        return {'error': f'Failed to retrieve coin by ID: {str(e)}'}

def get_coin_market_chart(coin_id, days=1, vs_currency='usd'):
    """Retrieves historical market chart data for a cryptocurrency.
    
    Args:
        coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').
        days (int): Number of days for historical data.
        vs_currency (str): The currency for the chart (e.g., 'usd').
    
    Returns:
        dict: A dictionary containing market chart data.
    """
    try:
        params = {'vs_currency': vs_currency, 'days': days}
        cache_key = f'coin_market_chart_{coin_id}_{days}_{vs_currency}'
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to retrieve market chart: {str(e)}'}

def main():
    """Demonstrates key functions from the module."""
    # Demo 1: Get list of coins
    coins_list = get_coins_list()
    if 'error' not in coins_list:
        print("First 5 coins:", coins_list[:5])  # Print first 5 for brevity
    else:
        print("Error in coins list:", coins_list)
    
    # Demo 2: Get current price of Bitcoin
    bitcoin_price = get_current_price('bitcoin')
    if 'error' not in bitcoin_price:
        print("Bitcoin current price:", bitcoin_price)
    else:
        print("Error in price retrieval:", bitcoin_price)
    
    # Demo 3: Get 7-day market chart for Bitcoin
    chart_data = get_coin_market_chart('bitcoin', days=7)
    if 'error' not in chart_data and 'prices' in chart_data:
        print("First 5 prices from Bitcoin 7-day chart:", chart_data['prices'][:5])
    else:
        print("Error in chart data:", chart_data)

if __name__ == '__main__':
    main()
