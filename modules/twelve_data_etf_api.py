#!/usr/bin/env python3
"""
Twelve Data ETF API — ETF Market Data Module

Comprehensive ETF data from Twelve Data API including:
- Real-time ETF quotes and prices
- ETF profiles and metadata
- Historical time series data
- ETF holdings and composition
- ETF search and discovery

Source: https://twelvedata.com/docs#etf
Category: ETF & Fund Flows
Free tier: True (800 calls/day, 8 req/min - requires TWELVE_DATA_API_KEY)
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Twelve Data API Configuration
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")

# Rate limiting (free tier: 8 requests per minute)
_last_request_time = 0
_min_request_interval = 7.5  # seconds between requests (8/min = 7.5s interval)


def _rate_limit():
    """Enforce rate limiting for free tier (8 req/min)"""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _min_request_interval:
        sleep_time = _min_request_interval - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Make API request to Twelve Data with error handling and rate limiting.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        API response as dict
    """
    _rate_limit()
    
    if not TWELVE_DATA_API_KEY:
        return {
            "error": "TWELVE_DATA_API_KEY not found in environment",
            "status": "error"
        }
    
    params['apikey'] = TWELVE_DATA_API_KEY
    url = f"{TWELVE_DATA_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if isinstance(data, dict) and data.get('status') == 'error':
            return {
                "error": data.get('message', 'Unknown API error'),
                "status": "error",
                "code": data.get('code', 'unknown')
            }
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Request failed: {str(e)}",
            "status": "error"
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}",
            "status": "error"
        }


def get_etf_quote(symbol: str) -> Dict:
    """
    Get real-time quote for an ETF.
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
        
    Returns:
        Dict with price, volume, and quote data
        
    Example:
        >>> quote = get_etf_quote('SPY')
        >>> print(quote['close'], quote['volume'])
    """
    params = {
        'symbol': symbol.upper(),
        'interval': '1day'
    }
    
    result = _make_request('quote', params)
    
    if result.get('status') == 'error':
        return result
    
    return {
        'symbol': result.get('symbol'),
        'name': result.get('name'),
        'exchange': result.get('exchange'),
        'currency': result.get('currency'),
        'datetime': result.get('datetime'),
        'timestamp': result.get('timestamp'),
        'open': result.get('open'),
        'high': result.get('high'),
        'low': result.get('low'),
        'close': result.get('close'),
        'volume': result.get('volume'),
        'previous_close': result.get('previous_close'),
        'change': result.get('change'),
        'percent_change': result.get('percent_change'),
        'fifty_two_week': result.get('fifty_two_week', {}),
        'status': 'ok'
    }


def get_etf_profile(symbol: str) -> Dict:
    """
    Get detailed profile information for an ETF.
    
    Args:
        symbol: ETF ticker symbol
        
    Returns:
        Dict with ETF profile data including fund family, category, AUM, etc.
    """
    params = {
        'symbol': symbol.upper()
    }
    
    result = _make_request('etf', params)
    
    if result.get('status') == 'error':
        return result
    
    return {
        'symbol': result.get('symbol'),
        'name': result.get('name'),
        'exchange': result.get('exchange'),
        'currency': result.get('currency'),
        'fund_family': result.get('fund_family'),
        'fund_category': result.get('fund_category'),
        'fund_type': result.get('fund_type'),
        'inception_date': result.get('inception_date'),
        'nav': result.get('nav'),
        'net_assets': result.get('net_assets'),
        'expense_ratio': result.get('expense_ratio'),
        'ytd_return': result.get('ytd_return'),
        'beta': result.get('beta'),
        'alpha': result.get('alpha'),
        'pe_ratio': result.get('pe_ratio'),
        'dividend_yield': result.get('dividend_yield'),
        'status': 'ok'
    }


def get_etf_time_series(
    symbol: str,
    interval: str = '1day',
    outputsize: int = 30
) -> Dict:
    """
    Get historical time series data for an ETF.
    
    Args:
        symbol: ETF ticker symbol
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points to return (default 30, max 5000)
        
    Returns:
        Dict with time series values
    """
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'outputsize': min(outputsize, 5000)
    }
    
    result = _make_request('time_series', params)
    
    if result.get('status') == 'error':
        return result
    
    return {
        'meta': result.get('meta', {}),
        'values': result.get('values', []),
        'status': result.get('status', 'ok')
    }


def get_etf_holdings(symbol: str) -> Dict:
    """
    Get top holdings for an ETF (if available).
    
    Args:
        symbol: ETF ticker symbol
        
    Returns:
        Dict with holdings data
        
    Note:
        Holdings data may require paid tier or may not be available for all ETFs
    """
    # Note: Twelve Data may require specific endpoint or premium tier for holdings
    # Using ETF endpoint which may include some holdings data
    params = {
        'symbol': symbol.upper()
    }
    
    result = _make_request('etf', params)
    
    if result.get('status') == 'error':
        return result
    
    return {
        'symbol': result.get('symbol'),
        'holdings': result.get('holdings', []),
        'top_10_holdings': result.get('top_10_holdings', {}),
        'sector_weights': result.get('sector_weights', {}),
        'status': 'ok'
    }


def search_etfs(query: str) -> List[Dict]:
    """
    Search for ETFs by name or symbol.
    
    Args:
        query: Search query (symbol or name fragment)
        
    Returns:
        List of matching ETFs
    """
    params = {
        'symbol': query,
        'outputsize': 50
    }
    
    result = _make_request('symbol_search', params)
    
    if result.get('status') == 'error':
        return [result]
    
    # Filter for ETF instrument types
    data = result.get('data', [])
    etfs = [item for item in data if item.get('instrument_type') == 'ETF']
    
    return etfs


def get_etf_list() -> List[Dict]:
    """
    Get list of available ETFs (US market).
    
    Returns:
        List of ETF symbols and basic info
        
    Note:
        This uses the stocks list endpoint filtered for ETFs
    """
    params = {
        'type': 'ETF',
        'exchange': 'NASDAQ,NYSE'
    }
    
    result = _make_request('stocks', params)
    
    if result.get('status') == 'error':
        return [result]
    
    data = result.get('data', [])
    
    return [
        {
            'symbol': item.get('symbol'),
            'name': item.get('name'),
            'exchange': item.get('exchange'),
            'currency': item.get('currency'),
            'type': item.get('type')
        }
        for item in data
    ]


def get_multiple_etf_quotes(symbols: List[str]) -> Dict[str, Dict]:
    """
    Get quotes for multiple ETFs in one call.
    
    Args:
        symbols: List of ETF ticker symbols (max 120 on free tier)
        
    Returns:
        Dict mapping symbols to quote data
        
    Note:
        Free tier allows up to 120 symbols per batch request
    """
    if not symbols:
        return {"error": "No symbols provided", "status": "error"}
    
    # Limit to 120 symbols for free tier
    symbols = symbols[:120]
    symbol_str = ','.join([s.upper() for s in symbols])
    
    params = {
        'symbol': symbol_str,
        'interval': '1day'
    }
    
    result = _make_request('quote', params)
    
    if result.get('status') == 'error':
        return result
    
    # Handle both single and multiple symbol responses
    if isinstance(result, dict) and 'symbol' in result:
        # Single symbol response
        return {result['symbol']: result}
    elif isinstance(result, dict):
        # Multiple symbols response
        quotes = {}
        for symbol in symbols:
            if symbol.upper() in result:
                quotes[symbol.upper()] = result[symbol.upper()]
        return quotes
    
    return {"error": "Unexpected response format", "status": "error"}


# Convenience function for module info
def get_module_info() -> Dict:
    """Return module metadata and configuration"""
    return {
        "module": "twelve_data_etf_api",
        "version": "1.0.0",
        "source": "https://twelvedata.com/docs#etf",
        "category": "ETF & Fund Flows",
        "free_tier": {
            "calls_per_day": 800,
            "calls_per_minute": 8,
            "active": bool(TWELVE_DATA_API_KEY)
        },
        "functions": [
            "get_etf_quote",
            "get_etf_profile",
            "get_etf_time_series",
            "get_etf_holdings",
            "search_etfs",
            "get_etf_list",
            "get_multiple_etf_quotes"
        ],
        "status": "active" if TWELVE_DATA_API_KEY else "needs_api_key"
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
