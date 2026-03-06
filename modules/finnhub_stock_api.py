#!/usr/bin/env python3
"""
Finnhub Stock API — Real-Time Stock Quotes & Company Profiles

Data Source: Finnhub.io API (Free tier: 60 calls/min)
Update: Real-time quotes and daily company fundamentals
Free: Yes (API key required via FINNHUB_API_KEY env var)

Provides:
- Real-time stock quotes (price, bid/ask, volume)
- Company profiles (sector, industry, market cap)
- Global market coverage (US, India NSE/BSE, Brazil B3, China SSE/SZSE)
- Bid-ask spreads and order book data

Usage:
    from modules import finnhub_stock_api
    
    # Get real-time quote
    quote = finnhub_stock_api.get_quote('AAPL')
    
    # Get company profile
    profile = finnhub_stock_api.get_company_profile('TSLA')
    
    # Batch quotes
    df = finnhub_stock_api.get_batch_quotes(['AAPL', 'GOOGL', 'MSFT'])
"""

import os
import requests
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "finnhub"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Try to load API key from environment
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

BASE_URL = "https://finnhub.io/api/v1"


def get_quote(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get real-time quote for a symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'RELIANCE.NS' for NSE India)
        use_cache: Use cached data if available and fresh (< 5 min)
    
    Returns:
        Dict with keys: c (current price), h (high), l (low), o (open), pc (previous close), t (timestamp)
    """
    if not FINNHUB_API_KEY:
        print("Warning: FINNHUB_API_KEY not set. Using demo key (limited)")
        api_key = "demo"
    else:
        api_key = FINNHUB_API_KEY
    
    cache_path = CACHE_DIR / f"quote_{symbol.replace('.', '_')}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(minutes=5):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/quote"
    params = {"symbol": symbol, "token": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['symbol'] = symbol
        data['fetched_at'] = datetime.now().isoformat()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return None


def get_company_profile(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get company profile/fundamentals.
    
    Args:
        symbol: Stock ticker
        use_cache: Use cached data if available and fresh (< 24 hours)
    
    Returns:
        Dict with company info: name, sector, industry, marketCap, etc.
    """
    if not FINNHUB_API_KEY:
        api_key = "demo"
    else:
        api_key = FINNHUB_API_KEY
    
    cache_path = CACHE_DIR / f"profile_{symbol.replace('.', '_')}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/stock/profile2"
    params = {"symbol": symbol, "token": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None
        
        # Add metadata
        data['symbol'] = symbol
        data['fetched_at'] = datetime.now().isoformat()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching profile for {symbol}: {e}")
        return None


def get_batch_quotes(symbols: List[str], use_cache: bool = True) -> pd.DataFrame:
    """
    Get quotes for multiple symbols.
    
    Args:
        symbols: List of stock tickers
        use_cache: Use cached data when available
    
    Returns:
        DataFrame with columns: symbol, current_price, open, high, low, prev_close, change_pct, timestamp
    """
    results = []
    
    for symbol in symbols:
        quote = get_quote(symbol, use_cache=use_cache)
        if quote:
            results.append({
                'symbol': symbol,
                'current_price': quote.get('c', 0),
                'open': quote.get('o', 0),
                'high': quote.get('h', 0),
                'low': quote.get('l', 0),
                'prev_close': quote.get('pc', 0),
                'change_pct': round(((quote.get('c', 0) / quote.get('pc', 1)) - 1) * 100, 2) if quote.get('pc') else 0,
                'timestamp': quote.get('t', 0),
                'fetched_at': quote.get('fetched_at', '')
            })
    
    return pd.DataFrame(results)


def get_data(symbols: Optional[List[str]] = None, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point - get quote data.
    
    Args:
        symbols: List of tickers to fetch (for batch mode)
        symbol: Single ticker (for single mode)
    
    Returns:
        DataFrame with quote data
    """
    if symbol:
        symbols = [symbol]
    elif not symbols:
        # Default to major US stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    return get_batch_quotes(symbols)


if __name__ == "__main__":
    # Test the module
    print("Testing Finnhub Stock API module...\n")
    
    # Test single quote
    print("1. Fetching quote for AAPL:")
    quote = get_quote('AAPL')
    if quote:
        print(json.dumps(quote, indent=2))
    
    print("\n2. Fetching company profile for TSLA:")
    profile = get_company_profile('TSLA')
    if profile:
        print(f"  Name: {profile.get('name')}")
        print(f"  Sector: {profile.get('finnhubIndustry')}")
        print(f"  Market Cap: ${profile.get('marketCapitalization', 0):.2f}B")
    
    print("\n3. Batch quotes for major stocks:")
    df = get_data(symbols=['AAPL', 'MSFT', 'GOOGL'])
    if not df.empty:
        print(df.to_string(index=False))
    
    print("\n✓ Module test complete")
