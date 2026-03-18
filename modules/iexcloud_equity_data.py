#!/usr/bin/env python3

"""QuantClaw Data: iexcloud_equity_data

Provides free access to US stock quotes, historical prices, and company fundamentals.

Data Source: https://cloud.iexapis.com/stable/
Update Frequency: Real-time for quotes; historical and fundamentals data updated as per IEX Cloud free tier.
Auth Info: Uses IEX Cloud demo token for unauthenticated access; no paid keys required.

"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/iexcloud_equity_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """Helper to get data with caching."""
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

DEMO_TOKEN = 'Tpk_1234567890abcdef'  # Replace with actual IEX Cloud demo token

def get_quote(symbol: str) -> dict:
    """Get real-time quote for the given stock symbol.
    
    Returns a dictionary with quote data or an error dictionary.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
    params = {'token': DEMO_TOKEN}
    cache_key = f'quote_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': str(e)}

def get_historical_prices(symbol: str, range_: str = '1m') -> list:
    """Get historical prices for the given symbol and range (e.g., '1m', '3m', '1y').
    
    Returns a list of historical price data or an error dictionary.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range_}"
    params = {'token': DEMO_TOKEN}
    cache_key = f'historical_{symbol}_{range_}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_company_info(symbol: str) -> dict:
    """Get company fundamentals for the given symbol.
    
    Returns a dictionary with company data or an error dictionary.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/company"
    params = {'token': DEMO_TOKEN}
    cache_key = f'company_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_news(symbol: str, limit: int = 10) -> list:
    """Get recent news for the given symbol.
    
    Returns a list of news items or an error dictionary.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/news"
    params = {'token': DEMO_TOKEN, 'last': limit}
    cache_key = f'news_{symbol}_{limit}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_earnings(symbol: str) -> dict:
    """Get earnings data for the given symbol.
    
    Returns a dictionary with earnings data or an error dictionary.
    """
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/earnings"
    params = {'token': DEMO_TOKEN}
    cache_key = f'earnings_{symbol}'
    try:
        return _cached_get(url, cache_key, params=params)
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def main():
    """Demonstrate key functions."""
    # Demo get_quote
    quote_result = get_quote('AAPL')
    if 'error' in quote_result:
        print(f"Error getting quote: {quote_result['error']}")
    else:
        print(f"AAPL Quote: {quote_result.get('latestPrice', 'N/A')}")
    
    # Demo get_historical_prices
    historical_result = get_historical_prices('AAPL', '1m')
    if 'error' in historical_result:
        print(f"Error getting historical prices: {historical_result['error']}")
    else:
        print(f"AAPL Historical Prices (1m): {len(historical_result)} entries")
    
    # Demo get_company_info
    company_result = get_company_info('AAPL')
    if 'error' in company_result:
        print(f"Error getting company info: {company_result['error']}")
    else:
        print(f"AAPL Company Name: {company_result.get('companyName', 'N/A')}")

if __name__ == '__main__':
    main()
