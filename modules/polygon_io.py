"""
Polygon.io — Real-time and historical stock market data.

Professional-grade financial market data including stocks, options, forex, and crypto.
Free tier provides delayed data (15-minute delay) and historical data.

Source: https://polygon.io/docs
Update frequency: 15-minute delay on free tier
Category: Quant Tools & ML
Free tier: Delayed quotes, historical data, company details (requires free API key)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional


API_BASE = "https://api.polygon.io"
# Free tier key - users should replace with their own
DEMO_KEY = "DEMO_KEY"


def get_quote(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get the last trade for a stock (15-minute delayed on free tier).
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        apikey: Polygon.io API key (uses demo if not provided)
        
    Returns:
        dict with last trade price and volume
        
    Example:
        >>> quote = get_quote('AAPL')
        >>> print(quote.get('price'), quote.get('volume'))
    """
    key = apikey or DEMO_KEY
    symbol = symbol.upper()
    
    url = f"{API_BASE}/v2/last/trade/{symbol}?apiKey={key}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == "ERROR":
                return {"error": data.get("error", "Unknown error"), "symbol": symbol}
            
            if data.get("status") != "OK":
                return {"error": f"API returned status: {data.get('status')}", "symbol": symbol}
            
            results = data.get("results", {})
            if not results:
                return {"error": "No data returned", "symbol": symbol}
            
            return {
                "symbol": symbol,
                "price": results.get("p", 0),
                "size": results.get("s", 0),
                "exchange": results.get("x"),
                "conditions": results.get("c", []),
                "timestamp_ns": results.get("t"),
                "timestamp": datetime.fromtimestamp(results.get("t", 0) / 1e9).isoformat() if results.get("t") else None,
                "fetched_at": datetime.now().isoformat(),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_previous_close(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get the previous day's OHLCV for a stock.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'SPY')
        apikey: Polygon.io API key (uses demo if not provided)
        
    Returns:
        dict with previous day OHLCV data
        
    Example:
        >>> prev = get_previous_close('SPY')
        >>> print(prev.get('close'), prev.get('volume'))
    """
    key = apikey or DEMO_KEY
    symbol = symbol.upper()
    
    url = f"{API_BASE}/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={key}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == "ERROR":
                return {"error": data.get("error", "Unknown error"), "symbol": symbol}
            
            if data.get("status") != "OK":
                return {"error": f"API returned status: {data.get('status')}", "symbol": symbol}
            
            results = data.get("results", [])
            if not results:
                return {"error": "No data returned", "symbol": symbol}
            
            bar = results[0]
            return {
                "symbol": symbol,
                "open": bar.get("o", 0),
                "high": bar.get("h", 0),
                "low": bar.get("l", 0),
                "close": bar.get("c", 0),
                "volume": bar.get("v", 0),
                "vwap": bar.get("vw"),
                "transactions": bar.get("n"),
                "timestamp_ms": bar.get("t"),
                "date": datetime.fromtimestamp(bar.get("t", 0) / 1000).date().isoformat() if bar.get("t") else None,
                "fetched_at": datetime.now().isoformat(),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_aggregates(
    symbol: str,
    timespan: str = "day",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 120,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get aggregate bars (OHLCV) for a stock over a date range.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        timespan: 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'
        from_date: Start date (YYYY-MM-DD), defaults to 120 days ago
        to_date: End date (YYYY-MM-DD), defaults to today
        limit: Max number of bars (default 120, max 50000)
        apikey: Polygon.io API key (uses demo if not provided)
        
    Returns:
        dict with list of OHLCV bars
        
    Example:
        >>> data = get_aggregates('AAPL', timespan='day', limit=30)
        >>> print(len(data.get('bars', [])))
    """
    key = apikey or DEMO_KEY
    symbol = symbol.upper()
    
    if not from_date:
        from_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    # Timespan multiplier (1 for daily, hourly, etc.)
    multiplier = 1
    
    url = f"{API_BASE}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=desc&limit={limit}&apiKey={key}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == "ERROR":
                return {"error": data.get("error", "Unknown error"), "symbol": symbol}
            
            if data.get("status") != "OK":
                return {"error": f"API returned status: {data.get('status')}", "symbol": symbol}
            
            results = data.get("results", [])
            if not results:
                return {"error": "No data returned", "symbol": symbol, "from": from_date, "to": to_date}
            
            bars = []
            for bar in results:
                bars.append({
                    "timestamp_ms": bar.get("t"),
                    "date": datetime.fromtimestamp(bar.get("t", 0) / 1000).date().isoformat() if bar.get("t") else None,
                    "open": bar.get("o", 0),
                    "high": bar.get("h", 0),
                    "low": bar.get("l", 0),
                    "close": bar.get("c", 0),
                    "volume": bar.get("v", 0),
                    "vwap": bar.get("vw"),
                    "transactions": bar.get("n")
                })
            
            return {
                "symbol": symbol,
                "timespan": timespan,
                "from_date": from_date,
                "to_date": to_date,
                "count": data.get("resultsCount", len(bars)),
                "bars": bars,
                "fetched_at": datetime.now().isoformat(),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_ticker_details(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get detailed company information for a ticker.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        apikey: Polygon.io API key (uses demo if not provided)
        
    Returns:
        dict with company details, market cap, description
        
    Example:
        >>> details = get_ticker_details('AAPL')
        >>> print(details.get('name'), details.get('market_cap'))
    """
    key = apikey or DEMO_KEY
    symbol = symbol.upper()
    
    url = f"{API_BASE}/v3/reference/tickers/{symbol}?apiKey={key}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == "ERROR":
                return {"error": data.get("error", "Unknown error"), "symbol": symbol}
            
            if data.get("status") != "OK":
                return {"error": f"API returned status: {data.get('status')}", "symbol": symbol}
            
            results = data.get("results", {})
            if not results:
                return {"error": "No data returned", "symbol": symbol}
            
            return {
                "symbol": results.get("ticker"),
                "name": results.get("name"),
                "market": results.get("market"),
                "locale": results.get("locale"),
                "primary_exchange": results.get("primary_exchange"),
                "type": results.get("type"),
                "active": results.get("active"),
                "currency_name": results.get("currency_name"),
                "cik": results.get("cik"),
                "composite_figi": results.get("composite_figi"),
                "share_class_figi": results.get("share_class_figi"),
                "market_cap": results.get("market_cap"),
                "phone_number": results.get("phone_number"),
                "address": results.get("address", {}),
                "description": results.get("description"),
                "sic_code": results.get("sic_code"),
                "sic_description": results.get("sic_description"),
                "homepage_url": results.get("homepage_url"),
                "total_employees": results.get("total_employees"),
                "list_date": results.get("list_date"),
                "branding": results.get("branding", {}),
                "fetched_at": datetime.now().isoformat(),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def search_tickers(
    query: str,
    market: str = "stocks",
    active: bool = True,
    limit: int = 10,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for tickers by company name or symbol.
    
    Args:
        query: Search query (company name or partial ticker)
        market: 'stocks', 'crypto', 'fx', 'otc'
        active: Only return active tickers
        limit: Max number of results (default 10)
        apikey: Polygon.io API key (uses demo if not provided)
        
    Returns:
        dict with list of matching tickers
        
    Example:
        >>> results = search_tickers('Apple')
        >>> print(results.get('tickers'))
    """
    key = apikey or DEMO_KEY
    
    params = {
        "search": query,
        "market": market,
        "active": str(active).lower(),
        "limit": limit,
        "apiKey": key
    }
    
    url = f"{API_BASE}/v3/reference/tickers?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == "ERROR":
                return {"error": data.get("error", "Unknown error"), "query": query}
            
            if data.get("status") != "OK":
                return {"error": f"API returned status: {data.get('status')}", "query": query}
            
            results = data.get("results", [])
            
            tickers = []
            for ticker in results:
                tickers.append({
                    "symbol": ticker.get("ticker"),
                    "name": ticker.get("name"),
                    "market": ticker.get("market"),
                    "locale": ticker.get("locale"),
                    "primary_exchange": ticker.get("primary_exchange"),
                    "type": ticker.get("type"),
                    "active": ticker.get("active"),
                    "currency_name": ticker.get("currency_name"),
                    "cik": ticker.get("cik"),
                    "composite_figi": ticker.get("composite_figi")
                })
            
            return {
                "query": query,
                "market": market,
                "count": data.get("count", len(tickers)),
                "tickers": tickers,
                "fetched_at": datetime.now().isoformat(),
                "raw": data
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "query": query}
    except Exception as e:
        return {"error": str(e), "query": query}


if __name__ == "__main__":
    print(json.dumps({
        "module": "polygon_io",
        "status": "implemented",
        "source": "https://polygon.io/docs",
        "tier": "free (15-min delayed)",
        "functions": [
            "get_quote",
            "get_previous_close",
            "get_aggregates",
            "get_ticker_details",
            "search_tickers"
        ]
    }, indent=2))
