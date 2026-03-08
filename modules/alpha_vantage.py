"""
Alpha Vantage — Global stock market data including emerging markets.

Real-time and historical financial market data for stocks, forex, cryptocurrencies,
and technical indicators. Supports quantitative analysis with data from global
exchanges including India (NSE/BSE), Brazil (B3), China (SSE/SZSE).

Source: https://www.alphavantage.co/documentation/
Update frequency: Real-time (5 min delay on free tier)
Category: Quant Tools & ML
Free tier: 5 API calls/min, 500 calls/day (requires free API key)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Any, Optional


API_BASE = "https://www.alphavantage.co/query"
# Demo key for testing - replace with real key for production
DEMO_KEY = "demo"


def get_quote(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get real-time quote for a stock symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'IBM', 'RELIANCE.NS', 'PETR4.SA')
        apikey: Alpha Vantage API key (uses demo if not provided)
        
    Returns:
        dict with price, volume, change data
        
    Example:
        >>> quote = get_quote('RELIANCE.NS')
        >>> print(quote.get('price'), quote.get('change_percent'))
    """
    key = apikey or DEMO_KEY
    
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": key
    }
    
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}
            
            quote = data.get("Global Quote", {})
            if not quote:
                return {"error": "No data returned", "symbol": symbol}
            
            return {
                "symbol": quote.get("01. symbol"),
                "price": float(quote.get("05. price", 0)),
                "volume": int(quote.get("06. volume", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%").rstrip('%'),
                "open": float(quote.get("02. open", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "previous_close": float(quote.get("08. previous close", 0)),
                "latest_trading_day": quote.get("07. latest trading day"),
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_daily_prices(
    symbol: str,
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get daily historical price data.
    
    Args:
        symbol: Stock ticker (e.g., 'IBM', 'VALE3.SA')
        outputsize: 'compact' (100 days) or 'full' (20+ years)
        apikey: Alpha Vantage API key (uses demo if not provided)
        
    Returns:
        dict with daily OHLCV data
        
    Example:
        >>> data = get_daily_prices('IBM', outputsize='compact')
        >>> print(len(data.get('prices', [])))
    """
    key = apikey or DEMO_KEY
    
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": key
    }
    
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}
            
            time_series = data.get("Time Series (Daily)", {})
            if not time_series:
                return {"error": "No data returned", "symbol": symbol}
            
            prices = []
            for date_str, values in time_series.items():
                prices.append({
                    "date": date_str,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })
            
            # Sort by date descending
            prices.sort(key=lambda x: x["date"], reverse=True)
            
            meta = data.get("Meta Data", {})
            return {
                "symbol": meta.get("2. Symbol"),
                "last_refreshed": meta.get("3. Last Refreshed"),
                "output_size": meta.get("4. Output Size"),
                "count": len(prices),
                "prices": prices,
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_intraday_prices(
    symbol: str,
    interval: str = "5min",
    outputsize: str = "compact",
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get intraday price data at specified intervals.
    
    Args:
        symbol: Stock ticker
        interval: '1min', '5min', '15min', '30min', '60min'
        outputsize: 'compact' (latest 100) or 'full' (trailing 30 days)
        apikey: Alpha Vantage API key (uses demo if not provided)
        
    Returns:
        dict with intraday OHLCV data
        
    Example:
        >>> data = get_intraday_prices('IBM', interval='5min')
        >>> print(data.get('prices')[0])
    """
    key = apikey or DEMO_KEY
    
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": key
    }
    
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}
            
            time_series_key = f"Time Series ({interval})"
            time_series = data.get(time_series_key, {})
            if not time_series:
                return {"error": "No data returned", "symbol": symbol}
            
            prices = []
            for timestamp, values in time_series.items():
                prices.append({
                    "timestamp": timestamp,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })
            
            # Sort by timestamp descending
            prices.sort(key=lambda x: x["timestamp"], reverse=True)
            
            meta = data.get("Meta Data", {})
            return {
                "symbol": meta.get("2. Symbol"),
                "interval": meta.get("4. Interval"),
                "last_refreshed": meta.get("3. Last Refreshed"),
                "count": len(prices),
                "prices": prices,
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_company_overview(
    symbol: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Get fundamental company data and overview.
    
    Args:
        symbol: Stock ticker (e.g., 'IBM')
        apikey: Alpha Vantage API key (uses demo if not provided)
        
    Returns:
        dict with company fundamentals, financials, ratios
        
    Example:
        >>> overview = get_company_overview('IBM')
        >>> print(overview.get('market_cap'), overview.get('pe_ratio'))
    """
    key = apikey or DEMO_KEY
    
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": key
    }
    
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}
            
            if not data or "Symbol" not in data:
                return {"error": "No data returned", "symbol": symbol}
            
            return {
                "symbol": data.get("Symbol"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "exchange": data.get("Exchange"),
                "currency": data.get("Currency"),
                "country": data.get("Country"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "market_cap": data.get("MarketCapitalization"),
                "pe_ratio": data.get("PERatio"),
                "peg_ratio": data.get("PEGRatio"),
                "book_value": data.get("BookValue"),
                "dividend_per_share": data.get("DividendPerShare"),
                "dividend_yield": data.get("DividendYield"),
                "eps": data.get("EPS"),
                "revenue_ttm": data.get("RevenueTTM"),
                "profit_margin": data.get("ProfitMargin"),
                "52_week_high": data.get("52WeekHigh"),
                "52_week_low": data.get("52WeekLow"),
                "50_day_ma": data.get("50DayMovingAverage"),
                "200_day_ma": data.get("200DayMovingAverage"),
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def search_symbols(
    keywords: str,
    apikey: Optional[str] = None
) -> dict[str, Any]:
    """
    Search for stock symbols by company name or ticker.
    
    Args:
        keywords: Company name or partial ticker
        apikey: Alpha Vantage API key (uses demo if not provided)
        
    Returns:
        dict with list of matching symbols
        
    Example:
        >>> results = search_symbols('Reliance')
        >>> print(results.get('matches'))
    """
    key = apikey or DEMO_KEY
    
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keywords,
        "apikey": key
    }
    
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode())
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            if "Note" in data:
                return {"error": "API rate limit exceeded", "note": data["Note"]}
            
            best_matches = data.get("bestMatches", [])
            
            matches = []
            for match in best_matches:
                matches.append({
                    "symbol": match.get("1. symbol"),
                    "name": match.get("2. name"),
                    "type": match.get("3. type"),
                    "region": match.get("4. region"),
                    "market_open": match.get("5. marketOpen"),
                    "market_close": match.get("6. marketClose"),
                    "timezone": match.get("7. timezone"),
                    "currency": match.get("8. currency"),
                    "match_score": match.get("9. matchScore")
                })
            
            return {
                "keywords": keywords,
                "count": len(matches),
                "matches": matches,
                "timestamp": datetime.now().isoformat(),
                "raw": data
            }
    except Exception as e:
        return {"error": str(e), "keywords": keywords}


if __name__ == "__main__":
    print(json.dumps({
        "module": "alpha_vantage",
        "status": "implemented",
        "source": "https://www.alphavantage.co/documentation/",
        "functions": [
            "get_quote",
            "get_daily_prices",
            "get_intraday_prices",
            "get_company_overview",
            "search_symbols"
        ]
    }, indent=2))
