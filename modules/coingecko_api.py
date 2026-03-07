#!/usr/bin/env python3
"""
CoinGecko API — Cryptocurrency Market Data Module

Comprehensive cryptocurrency market data from CoinGecko, including:
- Real-time price feeds
- Historical OHLC data
- Market cap, volume, supply metrics
- Trending coins
- Global crypto market metrics
- DeFi TVL and market data
- Exchange rates

Source: https://api.coingecko.com/api/v3
Category: Crypto & DeFi On-Chain
Free tier: True (30 calls/min, no API key required for basic endpoints)
Update frequency: real-time
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

# CoinGecko API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
DEFAULT_TIMEOUT = 10  # seconds

# ========== HELPER FUNCTIONS ==========

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Union[Dict, List]:
    """
    Make HTTP GET request to CoinGecko API.
    
    Args:
        endpoint: API endpoint path (e.g., '/simple/price')
        params: Query parameters
    
    Returns:
        JSON response as dict or list
    
    Raises:
        requests.exceptions.RequestException: On HTTP errors
    """
    url = f"{COINGECKO_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"CoinGecko API error: {e}")
        raise

# ========== PRICE DATA ==========

def get_coin_price(coin_id: str = "bitcoin", vs_currency: str = "usd") -> Dict:
    """
    Get current price for a cryptocurrency.
    
    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
        vs_currency: Target currency (e.g., 'usd', 'eur')
    
    Returns:
        Dict with price data including market cap and volume
    
    Example:
        >>> get_coin_price("bitcoin", "usd")
        {'bitcoin': {'usd': 67000, 'usd_market_cap': 1310000000000, 'usd_24h_vol': 28000000000}}
    """
    params = {
        'ids': coin_id,
        'vs_currencies': vs_currency,
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true'
    }
    return _make_request('/simple/price', params)

def get_coin_market_data(coin_id: str = "bitcoin", vs_currency: str = "usd") -> Dict:
    """
    Get comprehensive market data for a cryptocurrency.
    
    Args:
        coin_id: CoinGecko coin ID
        vs_currency: Target currency
    
    Returns:
        Dict with detailed market data (price, market cap, volume, supply, ATH, etc.)
    
    Example:
        >>> data = get_coin_market_data("bitcoin", "usd")
        >>> data['market_data']['current_price']['usd']
        67000
    """
    endpoint = f"/coins/{coin_id}"
    params = {
        'localization': 'false',
        'tickers': 'false',
        'community_data': 'false',
        'developer_data': 'false'
    }
    return _make_request(endpoint, params)

# ========== HISTORICAL DATA ==========

def get_coin_history(coin_id: str = "bitcoin", vs_currency: str = "usd", days: int = 30) -> Dict:
    """
    Get historical price data (market chart).
    
    Args:
        coin_id: CoinGecko coin ID
        vs_currency: Target currency
        days: Number of days (1, 7, 14, 30, 90, 180, 365, 'max')
    
    Returns:
        Dict with prices, market_caps, total_volumes arrays
    
    Example:
        >>> history = get_coin_history("bitcoin", "usd", 7)
        >>> len(history['prices'])
        168  # hourly data for 7 days
    """
    endpoint = f"/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days
    }
    return _make_request(endpoint, params)

def get_coin_ohlc(coin_id: str = "bitcoin", vs_currency: str = "usd", days: int = 14) -> List:
    """
    Get OHLC (candlestick) data.
    
    Args:
        coin_id: CoinGecko coin ID
        vs_currency: Target currency
        days: Valid values: 1, 7, 14, 30, 90, 180, 365
    
    Returns:
        List of OHLC candles [timestamp, open, high, low, close]
    
    Example:
        >>> ohlc = get_coin_ohlc("bitcoin", "usd", 7)
        >>> ohlc[0]  # [timestamp, open, high, low, close]
        [1709740800000, 66500, 67200, 66300, 66800]
    """
    endpoint = f"/coins/{coin_id}/ohlc"
    params = {
        'vs_currency': vs_currency,
        'days': days
    }
    return _make_request(endpoint, params)

# ========== TRENDING & SEARCH ==========

def get_trending_coins() -> Dict:
    """
    Get trending coins on CoinGecko (top 7).
    
    Returns:
        Dict with trending coins list
    
    Example:
        >>> trending = get_trending_coins()
        >>> trending['coins'][0]['item']['name']
        'Bitcoin'
    """
    return _make_request('/search/trending')

def search_coins(query: str = "bitcoin") -> Dict:
    """
    Search for coins by name or symbol.
    
    Args:
        query: Search term (coin name or symbol)
    
    Returns:
        Dict with coins, exchanges, categories
    
    Example:
        >>> results = search_coins("btc")
        >>> results['coins'][0]['name']
        'Bitcoin'
    """
    params = {'query': query}
    return _make_request('/search', params)

# ========== GLOBAL MARKET DATA ==========

def get_global_market_data() -> Dict:
    """
    Get global cryptocurrency market data.
    
    Returns:
        Dict with total market cap, volume, dominance, market cap change
    
    Example:
        >>> global_data = get_global_market_data()
        >>> global_data['data']['total_market_cap']['usd']
        2500000000000
    """
    return _make_request('/global')

def get_defi_data() -> Dict:
    """
    Get global DeFi market data.
    
    Returns:
        Dict with DeFi market cap, volume, TVL, dominance
    
    Example:
        >>> defi = get_defi_data()
        >>> defi['data']['defi_market_cap']
        '87000000000'
    """
    return _make_request('/global/decentralized_finance_defi')

# ========== EXCHANGE RATES ==========

def get_exchange_rates() -> Dict:
    """
    Get BTC exchange rates for all currencies.
    
    Returns:
        Dict with BTC rates for fiat and crypto currencies
    
    Example:
        >>> rates = get_exchange_rates()
        >>> rates['rates']['usd']['value']
        67000
    """
    return _make_request('/exchange_rates')

# ========== MAIN (for testing) ==========

if __name__ == "__main__":
    print("=" * 60)
    print("CoinGecko API Module Test")
    print("=" * 60)
    
    # Test 1: Get Bitcoin price
    print("\n[1] Bitcoin Price:")
    try:
        price = get_coin_price("bitcoin", "usd")
        print(json.dumps(price, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Trending coins
    print("\n[2] Trending Coins:")
    try:
        trending = get_trending_coins()
        for i, coin_data in enumerate(trending.get('coins', [])[:3], 1):
            coin = coin_data.get('item', {})
            print(f"  {i}. {coin.get('name')} ({coin.get('symbol')})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Global market data
    print("\n[3] Global Market Data:")
    try:
        global_data = get_global_market_data()
        data = global_data.get('data', {})
        total_mc = data.get('total_market_cap', {}).get('usd', 0)
        btc_dom = data.get('market_cap_percentage', {}).get('btc', 0)
        print(f"  Total Market Cap: ${total_mc:,.0f}")
        print(f"  BTC Dominance: {btc_dom:.2f}%")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Module test complete")
    print("=" * 60)
