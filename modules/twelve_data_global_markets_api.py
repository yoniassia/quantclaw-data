"""
Twelve Data Global Markets API

Real-time and historical market data for global stocks, forex, crypto, and emerging markets.
Data: https://api.twelvedata.com

Use cases:
- Global stock price tracking (NSE India, SSE China, B3 Brazil)
- Technical indicator calculation
- Multi-asset quote monitoring
- Symbol search and exchange discovery
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "twelve_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.twelvedata.com"

def _get_api_key() -> str:
    """Get API key from env or use demo key."""
    return os.getenv("TWELVE_DATA_API_KEY", "demo")


def get_time_series(
    symbol: str,
    interval: str = "1day",
    outputsize: int = 30,
    use_cache: bool = True
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV time series data for a symbol.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "RELIANCE.NS")
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points to return (default 30, max 5000)
        use_cache: Use cached data if available (default True)
    
    Returns:
        DataFrame with columns: datetime, open, high, low, close, volume
    """
    cache_key = f"{symbol}_{interval}_{outputsize}"
    cache_path = CACHE_DIR / f"timeseries_{cache_key}.json"
    
    # Check cache (1 hour for daily, 5 min for intraday)
    cache_duration = timedelta(hours=1) if "day" in interval or "week" in interval or "month" in interval else timedelta(minutes=5)
    
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < cache_duration:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                if cached.get("status") == "ok":
                    return pd.DataFrame(cached["values"])
    
    # Fetch from API
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": _get_api_key()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/time_series", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "error":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        if "values" not in data:
            return None
        
        df = pd.DataFrame(data["values"])
        return df
        
    except Exception as e:
        print(f"Error fetching time series for {symbol}: {e}")
        return None


def get_quote(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get real-time quote for a symbol.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL")
        use_cache: Use cached data if available (default True, 5 min cache)
    
    Returns:
        Dict with quote data: symbol, name, exchange, price, change, percent_change, volume, etc.
    """
    cache_path = CACHE_DIR / f"quote_{symbol}.json"
    
    # Check cache (5 minutes)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(minutes=5):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    params = {
        "symbol": symbol,
        "apikey": _get_api_key()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/quote", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "error":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
        
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return None


def get_technical_indicator(
    symbol: str,
    indicator: str = "RSI",
    interval: str = "1day",
    time_period: int = 14,
    use_cache: bool = True
) -> Optional[pd.DataFrame]:
    """
    Calculate technical indicator for a symbol.
    
    Args:
        symbol: Stock symbol
        indicator: Indicator name (RSI, SMA, EMA, MACD, STOCH, ADX, etc.)
        interval: Time interval (same as time_series)
        time_period: Period for calculation (default 14)
        use_cache: Use cached data if available (default True)
    
    Returns:
        DataFrame with indicator values
    """
    cache_key = f"{symbol}_{indicator}_{interval}_{time_period}"
    cache_path = CACHE_DIR / f"indicator_{cache_key}.json"
    
    # Check cache (1 hour)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                if cached.get("status") == "ok":
                    return pd.DataFrame(cached["values"])
    
    # Fetch from API (indicator endpoints are lowercase, e.g., /rsi, /sma)
    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "apikey": _get_api_key()
    }
    
    try:
        endpoint = f"{BASE_URL}/{indicator.lower()}"
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "error":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        if "values" not in data:
            return None
        
        df = pd.DataFrame(data["values"])
        return df
        
    except Exception as e:
        print(f"Error fetching {indicator} for {symbol}: {e}")
        return None


def get_exchange_list(use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get list of all supported exchanges.
    
    Returns:
        List of dicts with exchange info: name, code, country, timezone
    """
    cache_path = CACHE_DIR / "exchanges.json"
    
    # Check cache (24 hours)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                # Handle cached response format
                if isinstance(cached, dict) and "data" in cached:
                    return cached["data"]
                return cached if isinstance(cached, list) else None
    
    # Fetch from API
    params = {
        "apikey": _get_api_key()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/exchanges", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and data.get("status") == "error":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Extract data list from response
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, list):
            return data
        else:
            return None
        
    except Exception as e:
        print(f"Error fetching exchange list: {e}")
        return None


def get_emerging_market_stocks(exchange: str = "NSE", use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get stocks from an emerging market exchange.
    
    Args:
        exchange: Exchange code (NSE, SSE, B3, etc.)
        use_cache: Use cached data if available
    
    Returns:
        List of stock symbols and info for the exchange
    """
    # This uses symbol search filtered by exchange
    # Note: Full stock list requires premium API, so we'll search for common prefixes
    cache_path = CACHE_DIR / f"stocks_{exchange}.json"
    
    # Check cache (24 hours)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Note: Without a full stock list endpoint, we return exchange info
    # Users should use search_symbols() with specific queries
    exchanges = get_exchange_list(use_cache=use_cache)
    if not exchanges:
        return None
    
    # Handle different response formats
    matching = []
    for ex in exchanges:
        if isinstance(ex, dict) and ex.get("code") == exchange:
            matching.append(ex)
        elif isinstance(ex, str):
            # If exchanges return strings, skip matching
            continue
    
    result = {
        "exchange": exchange,
        "info": matching[0] if matching else None,
        "note": "Use search_symbols(query) to find specific stocks on this exchange"
    }
    
    # Cache result
    with open(cache_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return [result]


def search_symbols(query: str, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Search for symbols by name or ticker.
    
    Args:
        query: Search query (e.g., "AAPL", "Apple", "Reliance")
        use_cache: Use cached data if available
    
    Returns:
        List of matching symbols with details
    """
    cache_path = CACHE_DIR / f"search_{query}.json"
    
    # Check cache (1 hour)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    params = {
        "symbol": query,
        "apikey": _get_api_key()
    }
    
    try:
        response = requests.get(f"{BASE_URL}/symbol_search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and data.get("status") == "error":
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data.get("data", data) if isinstance(data, dict) else data
        
    except Exception as e:
        print(f"Error searching symbols for '{query}': {e}")
        return None


# CLI functions
def cli_quote(symbol: str):
    """CLI: Display real-time quote."""
    quote = get_quote(symbol)
    if not quote:
        print(f"No quote data for {symbol}")
        return
    
    print(f"\n=== Quote: {symbol} ===")
    print(f"Name: {quote.get('name', 'N/A')}")
    print(f"Exchange: {quote.get('exchange', 'N/A')}")
    print(f"Price: ${quote.get('close', 'N/A')}")
    print(f"Change: {quote.get('change', 'N/A')} ({quote.get('percent_change', 'N/A')}%)")
    print(f"Volume: {quote.get('volume', 'N/A')}")
    print(f"Timestamp: {quote.get('datetime', 'N/A')}")


def cli_search(query: str):
    """CLI: Search for symbols."""
    results = search_symbols(query)
    if not results:
        print(f"No results for '{query}'")
        return
    
    print(f"\n=== Search Results: {query} ===")
    for item in results[:10]:  # Show top 10
        symbol = item.get('symbol', 'N/A')
        name = item.get('instrument_name', 'N/A')
        exchange = item.get('exchange', 'N/A')
        currency = item.get('currency', 'N/A')
        print(f"{symbol:15s} {name:40s} [{exchange}] {currency}")


def cli_exchanges():
    """CLI: List all supported exchanges."""
    exchanges = get_exchange_list()
    if not exchanges:
        print("No exchange data available")
        return
    
    print(f"\n=== Supported Exchanges ({len(exchanges)}) ===")
    for ex in exchanges:
        code = ex.get('code', 'N/A')
        name = ex.get('name', 'N/A')
        country = ex.get('country', 'N/A')
        print(f"{code:10s} {name:40s} {country}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python twelve_data_global_markets_api.py <command> [args]")
        print("Commands:")
        print("  quote <SYMBOL>     - Get real-time quote")
        print("  search <QUERY>     - Search for symbols")
        print("  exchanges          - List supported exchanges")
        sys.exit(0)
    
    command = args[0]
    
    if command == "quote" and len(args) > 1:
        cli_quote(args[1])
    elif command == "search" and len(args) > 1:
        cli_search(args[1])
    elif command == "exchanges":
        cli_exchanges()
    else:
        print(f"Unknown command: {command}")
        print("Available: quote, search, exchanges")
        sys.exit(1)
