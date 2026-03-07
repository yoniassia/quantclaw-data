"""
Tradier API — Options & Derivatives Market Data

Brokerage API with access to real-time and historical options data, including chains,
quotes, and Greeks. Supports quantitative analysis for trading strategies like 
volatility trading and options pricing models.

Source: https://documentation.tradier.com/
Update frequency: Real-time for live accounts, 15-minute delay in sandbox
Category: Options & Derivatives
Free tier: Sandbox account with 15-min delayed data; 120 calls/min
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://sandbox.tradier.com/v1"
# Sandbox demo token (public, read-only, delayed data)
SANDBOX_TOKEN = "Bearer CHANGEME"


def get_quote(
    symbol: str,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get stock/option quote for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'SPY')
        access_token: Tradier API bearer token (optional for sandbox)
        
    Returns:
        dict with quote data including bid, ask, last, volume, change
        
    Example:
        >>> quote = get_quote('AAPL')
        >>> print(quote.get('last'), quote.get('volume'))
    """
    token = access_token or SANDBOX_TOKEN
    
    endpoint = f"{API_BASE}/markets/quotes"
    params = {"symbols": symbol.upper()}
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", token)
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            quotes = data.get("quotes", {}).get("quote", {})
            if isinstance(quotes, list):
                quotes = quotes[0] if quotes else {}
            
            return {
                "symbol": quotes.get("symbol"),
                "last": quotes.get("last"),
                "bid": quotes.get("bid"),
                "ask": quotes.get("ask"),
                "volume": quotes.get("volume"),
                "open": quotes.get("open"),
                "high": quotes.get("high"),
                "low": quotes.get("low"),
                "close": quotes.get("close"),
                "change": quotes.get("change"),
                "change_percentage": quotes.get("change_percentage"),
                "timestamp": quotes.get("trade_date"),
                "raw": quotes
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_options_expirations(
    symbol: str,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get available option expiration dates for a symbol.
    
    Args:
        symbol: Underlying ticker symbol (e.g., 'AAPL')
        access_token: Tradier API bearer token
        
    Returns:
        dict with list of expiration dates
        
    Example:
        >>> expirations = get_options_expirations('AAPL')
        >>> print(expirations.get('dates', []))
    """
    token = access_token or SANDBOX_TOKEN
    
    endpoint = f"{API_BASE}/markets/options/expirations"
    params = {"symbol": symbol.upper()}
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", token)
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            dates = data.get("expirations", {}).get("date", [])
            if not isinstance(dates, list):
                dates = [dates] if dates else []
            
            return {
                "symbol": symbol.upper(),
                "dates": dates,
                "count": len(dates),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_options_chain(
    symbol: str,
    expiration: Optional[str] = None,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get options chain for a symbol and expiration date.
    
    Args:
        symbol: Underlying ticker symbol (e.g., 'AAPL')
        expiration: Expiration date in YYYY-MM-DD format (optional, uses nearest if omitted)
        access_token: Tradier API bearer token
        
    Returns:
        dict with options chain data including calls and puts
        
    Example:
        >>> chain = get_options_chain('AAPL', '2026-06-19')
        >>> calls = [opt for opt in chain.get('options', []) if opt['option_type'] == 'call']
    """
    token = access_token or SANDBOX_TOKEN
    
    # If no expiration provided, get the nearest one
    if not expiration:
        exps = get_options_expirations(symbol, access_token)
        if exps.get("dates"):
            expiration = exps["dates"][0]
        else:
            return {"error": "No expirations available", "symbol": symbol}
    
    endpoint = f"{API_BASE}/markets/options/chains"
    params = {
        "symbol": symbol.upper(),
        "expiration": expiration
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", token)
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            options = data.get("options", {}).get("option", [])
            if not isinstance(options, list):
                options = [options] if options else []
            
            return {
                "symbol": symbol.upper(),
                "expiration": expiration,
                "options": options,
                "count": len(options),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "expiration": expiration}


def get_historical(
    symbol: str,
    interval: str = "daily",
    start: Optional[str] = None,
    end: Optional[str] = None,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get historical price data for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL')
        interval: Data interval ('daily', 'weekly', 'monthly')
        start: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end: End date in YYYY-MM-DD format (optional, defaults to today)
        access_token: Tradier API bearer token
        
    Returns:
        dict with historical OHLCV data
        
    Example:
        >>> hist = get_historical('AAPL', interval='daily', start='2026-01-01')
        >>> for bar in hist.get('data', []):
        ...     print(bar['date'], bar['close'])
    """
    token = access_token or SANDBOX_TOKEN
    
    endpoint = f"{API_BASE}/markets/history"
    params = {
        "symbol": symbol.upper(),
        "interval": interval
    }
    
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", token)
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            history = data.get("history")
            if not history:
                return {"error": "No historical data available", "symbol": symbol}
            
            bars = history.get("day", [])
            if not isinstance(bars, list):
                bars = [bars] if bars else []
            
            return {
                "symbol": symbol.upper(),
                "interval": interval,
                "start": start,
                "end": end,
                "data": bars,
                "count": len(bars),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_time_and_sales(
    symbol: str,
    interval: str = "1min",
    start: Optional[str] = None,
    end: Optional[str] = None,
    access_token: Optional[str] = None
) -> dict[str, Any]:
    """
    Get time and sales (tick) data for a symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL')
        interval: Time interval ('tick', '1min', '5min', '15min')
        start: Start time in YYYY-MM-DD HH:MM format (optional)
        end: End time in YYYY-MM-DD HH:MM format (optional)
        access_token: Tradier API bearer token
        
    Returns:
        dict with time and sales data
        
    Example:
        >>> tas = get_time_and_sales('AAPL', interval='1min')
        >>> print(len(tas.get('data', [])))
    """
    token = access_token or SANDBOX_TOKEN
    
    endpoint = f"{API_BASE}/markets/timesales"
    params = {
        "symbol": symbol.upper(),
        "interval": interval
    }
    
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", token)
        req.add_header("Accept", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            series = data.get("series")
            if not series:
                return {"error": "No time and sales data available", "symbol": symbol}
            
            ticks = series.get("data", [])
            if not isinstance(ticks, list):
                ticks = [ticks] if ticks else []
            
            return {
                "symbol": symbol.upper(),
                "interval": interval,
                "data": ticks,
                "count": len(ticks),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def demo():
    """Demo with sample data (no API key required)."""
    return {
        "module": "tradier_api",
        "status": "ready",
        "source": "https://documentation.tradier.com/",
        "sandbox_url": "https://sandbox.tradier.com",
        "note": "Using sandbox with 15-min delayed data. Set access_token for real-time.",
        "functions": [
            "get_quote(symbol)",
            "get_options_expirations(symbol)",
            "get_options_chain(symbol, expiration=None)",
            "get_historical(symbol, interval='daily', start=None, end=None)",
            "get_time_and_sales(symbol, interval='1min', start=None, end=None)"
        ]
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
