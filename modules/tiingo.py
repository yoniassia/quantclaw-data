#!/usr/bin/env python3
"""
Tiingo — Stock & Crypto Market Data Module

Tiingo provides APIs for end-of-day and real-time stock prices, fundamentals, 
news, and crypto data. Free tier includes 50 calls/hour and 500/day.

Data Points:
- Daily OHLCV price data (end-of-day)
- Stock metadata (name, exchange, industry)
- Cryptocurrency prices (Bitcoin, Ethereum, etc.)
- Financial news with sentiment
- Latest real-time prices (IEX)

Updated: Real-time / End-of-day
History: Multiple years available
Source: https://api.tiingo.com/documentation/general
Category: Market Data — Stocks & Crypto
Free tier: True (50 calls/hour, 500/day with API key)
Author: QuantClaw Data NightBuilder
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Constants
BASE_URL = "https://api.tiingo.com"
DEFAULT_API_KEY = "demo"  # Tiingo provides a demo token for testing

# Get API key from environment or use demo
API_KEY = os.environ.get('TIINGO_API_KEY', DEFAULT_API_KEY)

# Simple in-memory cache to respect rate limits
_CACHE = {}
_CACHE_DURATION = timedelta(minutes=5)

USER_AGENT = 'QuantClaw/1.0 (https://quantclaw.ai)'


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Tiingo API with caching
    
    Args:
        endpoint: API endpoint path
        params: Query parameters (token added automatically)
        
    Returns:
        Dict with API response or error information
    """
    # Build cache key
    cache_key = f"{endpoint}:{str(params)}"
    
    # Check cache
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            result = cached_data.copy()
            result['cached'] = True
            return result
    
    # Prepare request
    if params is None:
        params = {}
    params['token'] = API_KEY
    
    url = f"{BASE_URL}{endpoint}"
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json'
    }
    
    try:
        # Rate limiting: small delay between requests
        time.sleep(0.1)
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache successful response
        _CACHE[cache_key] = (datetime.now(), data)
        
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return {
                "success": False,
                "error": "Invalid API key",
                "note": "Set TIINGO_API_KEY environment variable or use demo token",
                "status_code": 401
            }
        elif e.response.status_code == 429:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "note": "Free tier: 50 calls/hour, 500/day",
                "status_code": 429
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code
            }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_daily_prices(ticker: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> List[Dict]:
    """
    Get daily OHLCV price data for a stock ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        
    Returns:
        List of daily price records with date, open, high, low, close, volume
        
    Example:
        >>> prices = get_daily_prices('AAPL', '2024-01-01', '2024-01-31')
        >>> print(f"Close: ${prices[0]['close']:.2f}")
    """
    ticker = ticker.upper()
    
    # Default to last 30 days if no start date
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    params = {'startDate': start_date}
    if end_date:
        params['endDate'] = end_date
    
    endpoint = f"/tiingo/daily/{ticker}/prices"
    result = _make_request(endpoint, params)
    
    # Check if error response
    if isinstance(result, dict) and result.get('success') == False:
        return [result]
    
    # Transform response
    if isinstance(result, list):
        prices = []
        for record in result:
            prices.append({
                'date': record.get('date', '').split('T')[0],
                'open': record.get('open'),
                'high': record.get('high'),
                'low': record.get('low'),
                'close': record.get('close'),
                'volume': record.get('volume'),
                'adj_open': record.get('adjOpen'),
                'adj_high': record.get('adjHigh'),
                'adj_low': record.get('adjLow'),
                'adj_close': record.get('adjClose'),
                'adj_volume': record.get('adjVolume'),
                'ticker': ticker
            })
        return prices
    
    return [{"success": False, "error": "Unexpected response format", "data": result}]


def get_metadata(ticker: str) -> Dict:
    """
    Get company metadata and fundamentals
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Dict with company name, exchange, description, industry, sector, etc.
        
    Example:
        >>> meta = get_metadata('AAPL')
        >>> print(f"Name: {meta['name']}")
        >>> print(f"Exchange: {meta['exchange']}")
    """
    ticker = ticker.upper()
    endpoint = f"/tiingo/daily/{ticker}"
    
    result = _make_request(endpoint)
    
    # Check if error response
    if isinstance(result, dict) and result.get('success') == False:
        return result
    
    # Transform response
    if isinstance(result, dict):
        return {
            'success': True,
            'ticker': result.get('ticker'),
            'name': result.get('name'),
            'exchange': result.get('exchangeCode'),
            'description': result.get('description'),
            'start_date': result.get('startDate'),
            'end_date': result.get('endDate'),
            'cached': result.get('cached', False)
        }
    
    return {"success": False, "error": "Unexpected response format", "data": result}


def get_crypto_prices(ticker: str = "btcusd", start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict]:
    """
    Get cryptocurrency price data
    
    Args:
        ticker: Crypto ticker (e.g., 'btcusd', 'ethusd', 'btceur')
        start_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        
    Returns:
        List of crypto price records with timestamp, open, high, low, close, volume
        
    Example:
        >>> btc = get_crypto_prices('btcusd', '2024-01-01')
        >>> print(f"BTC Price: ${btc[0]['close']:.2f}")
    """
    ticker = ticker.lower()
    
    # Default to last 7 days for crypto
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {'startDate': start_date, 'resampleFreq': 'daily'}
    if end_date:
        params['endDate'] = end_date
    
    endpoint = f"/tiingo/crypto/prices"
    params['tickers'] = ticker
    
    result = _make_request(endpoint, params)
    
    # Check if error response
    if isinstance(result, dict) and result.get('success') == False:
        return [result]
    
    # Transform response (crypto endpoint returns nested structure)
    if isinstance(result, list) and len(result) > 0:
        prices = []
        ticker_data = result[0]
        
        if 'priceData' in ticker_data:
            for record in ticker_data['priceData']:
                prices.append({
                    'date': record.get('date', '').split('T')[0],
                    'open': record.get('open'),
                    'high': record.get('high'),
                    'low': record.get('low'),
                    'close': record.get('close'),
                    'volume': record.get('volume'),
                    'volume_notional': record.get('volumeNotional'),
                    'ticker': ticker
                })
        return prices
    
    return [{"success": False, "error": "Unexpected response format", "data": result}]


def get_news(tickers: Optional[List[str]] = None, limit: int = 10, 
             start_date: Optional[str] = None) -> List[Dict]:
    """
    Get financial news articles with sentiment
    
    Args:
        tickers: List of ticker symbols to filter by (default: None = all news)
        limit: Maximum number of articles to return (default: 10)
        start_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        
    Returns:
        List of news articles with title, description, url, published date, source
        
    Example:
        >>> news = get_news(['AAPL', 'MSFT'], limit=5)
        >>> for article in news:
        >>>     print(f"{article['title']} - {article['source']}")
    """
    # Default to last 7 days
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {
        'startDate': start_date,
        'limit': limit
    }
    
    if tickers:
        params['tickers'] = ','.join([t.upper() for t in tickers])
    
    endpoint = "/tiingo/news"
    result = _make_request(endpoint, params)
    
    # Check if error response
    if isinstance(result, dict) and result.get('success') == False:
        return [result]
    
    # Transform response
    if isinstance(result, list):
        articles = []
        for item in result:
            articles.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'description': item.get('description'),
                'url': item.get('url'),
                'published_date': item.get('publishedDate', '').split('T')[0],
                'source': item.get('source'),
                'tickers': item.get('tickers', []),
                'tags': item.get('tags', [])
            })
        return articles
    
    return [{"success": False, "error": "Unexpected response format", "data": result}]


def get_latest_price(ticker: str) -> Dict:
    """
    Get latest real-time price for a stock ticker
    
    Uses IEX endpoint for intraday/real-time data (15-min delayed on free tier).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Dict with latest price, timestamp, bid/ask, volume
        
    Example:
        >>> latest = get_latest_price('AAPL')
        >>> print(f"Last: ${latest['last']:.2f} @ {latest['timestamp']}")
    """
    ticker = ticker.upper()
    endpoint = f"/iex/{ticker}"
    
    result = _make_request(endpoint)
    
    # Check if error response
    if isinstance(result, dict) and result.get('success') == False:
        return result
    
    # Transform response (IEX returns list of ticks, get most recent)
    if isinstance(result, list) and len(result) > 0:
        latest = result[-1]  # Last element is most recent
        return {
            'success': True,
            'ticker': ticker,
            'last': latest.get('last'),
            'timestamp': latest.get('timestamp'),
            'bid_size': latest.get('bidSize'),
            'bid_price': latest.get('bidPrice'),
            'ask_size': latest.get('askSize'),
            'ask_price': latest.get('askPrice'),
            'volume': latest.get('volume'),
            'cached': result[0].get('cached', False) if isinstance(result[0], dict) else False
        }
    
    return {"success": False, "error": "No data available", "data": result}


# Convenience aliases
get_prices = get_daily_prices
get_stock_metadata = get_metadata
get_crypto = get_crypto_prices
get_financial_news = get_news
get_quote = get_latest_price


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("Tiingo Market Data Module - QuantClaw Data")
    print("=" * 70)
    print(f"API Key: {'[DEMO]' if API_KEY == DEFAULT_API_KEY else '[SET]'}")
    print("=" * 70)
    
    # Test metadata
    print("\n1. Stock Metadata (AAPL):")
    meta = get_metadata('AAPL')
    print(json.dumps(meta, indent=2))
    
    # Test daily prices
    print("\n2. Daily Prices (AAPL, last 5 days):")
    prices = get_daily_prices('AAPL', 
                              start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'))
    if prices and len(prices) > 0:
        print(f"Records: {len(prices)}")
        if prices[0].get('success') != False:
            print(json.dumps(prices[0], indent=2))
        else:
            print(json.dumps(prices[0], indent=2))
    
    # Test crypto
    print("\n3. Crypto Prices (btcusd, last 3 days):")
    crypto = get_crypto_prices('btcusd',
                               start_date=(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'))
    if crypto and len(crypto) > 0:
        print(f"Records: {len(crypto)}")
        print(json.dumps(crypto[0], indent=2))
    
    # Test news
    print("\n4. Financial News (AAPL, last 3):")
    news = get_news(['AAPL'], limit=3)
    if news and len(news) > 0:
        print(f"Articles: {len(news)}")
        if news[0].get('success') != False:
            print(json.dumps(news[0], indent=2))
        else:
            print(json.dumps(news[0], indent=2))
    
    # Test latest price
    print("\n5. Latest Price (AAPL):")
    latest = get_latest_price('AAPL')
    print(json.dumps(latest, indent=2))
