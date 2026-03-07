"""
Twelve Data API — Real-time market data for stocks, forex, and crypto.

Provides real-time quotes, time series OHLCV data, exchange rates, and symbol search.
Free tier: 800 API calls/day, 8 symbols per request.

Source: https://api.twelvedata.com
Update frequency: Real-time
Category: Exchanges & Market Microstructure
Free tier: 800 calls/day
"""

import json
import os
import urllib.request
import urllib.parse
from typing import Any, Optional


API_BASE = "https://api.twelvedata.com"
# API key from environment or fallback to demo key
DEFAULT_KEY = os.environ.get("TWELVE_DATA_API_KEY", "demo")


def get_quote(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time quote for a ticker symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'MSFT')
        api_key: Twelve Data API key (uses env var or demo if not provided)
        
    Returns:
        dict with quote data including price, volume, open, high, low, close
        
    Example:
        >>> quote = get_quote('AAPL')
        >>> print(quote.get('price'), quote.get('change_percent'))
    """
    key = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol,
        "apikey": key
    }
    
    url = f"{API_BASE}/quote?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "code" in data and data["code"] >= 400:
                return {"error": data.get("message", "API error"), "symbol": symbol}
            
            return {
                "symbol": data.get("symbol"),
                "name": data.get("name"),
                "exchange": data.get("exchange"),
                "currency": data.get("currency"),
                "price": float(data.get("close", 0)) if data.get("close") else None,
                "open": float(data.get("open", 0)) if data.get("open") else None,
                "high": float(data.get("high", 0)) if data.get("high") else None,
                "low": float(data.get("low", 0)) if data.get("low") else None,
                "volume": int(data.get("volume", 0)) if data.get("volume") else None,
                "previous_close": float(data.get("previous_close", 0)) if data.get("previous_close") else None,
                "change": float(data.get("change", 0)) if data.get("change") else None,
                "change_percent": float(data.get("percent_change", 0)) if data.get("percent_change") else None,
                "timestamp": data.get("datetime"),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_time_series(
    symbol: str,
    interval: str = "1day",
    outputsize: int = 30,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get OHLCV time series data for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
        interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
        outputsize: Number of data points to return (max 5000)
        api_key: Twelve Data API key
        
    Returns:
        dict with time series data
        
    Example:
        >>> ts = get_time_series('SPY', interval='1day', outputsize=10)
        >>> for bar in ts.get('values', []):
        ...     print(bar['datetime'], bar['close'])
    """
    key = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": min(outputsize, 5000),
        "apikey": key
    }
    
    url = f"{API_BASE}/time_series?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "code" in data and data["code"] >= 400:
                return {"error": data.get("message", "API error"), "symbol": symbol}
            
            values = data.get("values", [])
            
            # Convert string values to floats
            for bar in values:
                for field in ["open", "high", "low", "close"]:
                    if field in bar:
                        bar[field] = float(bar[field])
                if "volume" in bar:
                    bar["volume"] = int(bar["volume"])
            
            return {
                "symbol": symbol,
                "interval": interval,
                "currency": data.get("meta", {}).get("currency"),
                "exchange": data.get("meta", {}).get("exchange"),
                "type": data.get("meta", {}).get("type"),
                "count": len(values),
                "values": values,
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_price(
    symbol: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get simple current price for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC/USD')
        api_key: Twelve Data API key
        
    Returns:
        dict with current price
        
    Example:
        >>> price_data = get_price('AAPL')
        >>> print(price_data.get('price'))
    """
    key = api_key or DEFAULT_KEY
    
    params = {
        "symbol": symbol,
        "apikey": key
    }
    
    url = f"{API_BASE}/price?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "code" in data and data["code"] >= 400:
                return {"error": data.get("message", "API error"), "symbol": symbol}
            
            return {
                "symbol": symbol,
                "price": float(data.get("price", 0)) if data.get("price") else None,
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Get exchange rate between two currencies.
    
    Args:
        from_currency: Source currency code (e.g., 'USD', 'EUR')
        to_currency: Target currency code (e.g., 'EUR', 'GBP')
        api_key: Twelve Data API key
        
    Returns:
        dict with exchange rate
        
    Example:
        >>> rate = get_exchange_rate('USD', 'EUR')
        >>> print(rate.get('rate'))
    """
    key = api_key or DEFAULT_KEY
    
    symbol = f"{from_currency}/{to_currency}"
    
    params = {
        "symbol": symbol,
        "apikey": key
    }
    
    url = f"{API_BASE}/exchange_rate?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "code" in data and data["code"] >= 400:
                return {"error": data.get("message", "API error"), "pair": symbol}
            
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "symbol": symbol,
                "rate": float(data.get("rate", 0)) if data.get("rate") else None,
                "timestamp": data.get("timestamp"),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "pair": symbol}


def search_symbol(
    query: str,
    api_key: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for symbols by keyword.
    
    Args:
        query: Search query (e.g., 'Apple', 'Tesla')
        api_key: Twelve Data API key
        
    Returns:
        dict with list of matching symbols
        
    Example:
        >>> results = search_symbol('Apple')
        >>> for item in results.get('symbols', []):
        ...     print(item['symbol'], item['instrument_name'])
    """
    key = api_key or DEFAULT_KEY
    
    params = {
        "symbol": query,
        "apikey": key
    }
    
    url = f"{API_BASE}/symbol_search?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "code" in data and data["code"] >= 400:
                return {"error": data.get("message", "API error"), "query": query}
            
            symbols = data.get("data", [])
            
            return {
                "query": query,
                "count": len(symbols),
                "symbols": symbols,
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "query": query}


# Demo function for testing
def demo():
    """Demo with sample stock data (uses demo API key)."""
    print("Testing Twelve Data API module...")
    print("\n1. Price check:")
    print(json.dumps(get_price("AAPL"), indent=2))
    print("\n2. Quote:")
    print(json.dumps(get_quote("AAPL"), indent=2))
    print("\n3. Symbol search:")
    print(json.dumps(search_symbol("Apple"), indent=2))


if __name__ == "__main__":
    demo()
