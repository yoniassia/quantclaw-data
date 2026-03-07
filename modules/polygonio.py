"""
Polygon.io — Real-time and Historical Market Data API

Data Source: Polygon.io
Update: Real-time / Historical
Free tier: 5 API calls per minute, limited historical data
API Key: Set POLYGON_API_KEY env var or uses 'demo' key

Provides:
- Stock aggregates (OHLCV bars) - daily, minute, etc.
- Ticker details and company information
- Market snapshots (all tickers or specific)
- Previous close data
- Stock splits and dividends
- Grouped daily bars (full market)

Source: https://polygon.io/docs/stocks/getting-started
Category: Quant Tools & ML
Update frequency: real-time
"""

import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/polygonio")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.polygon.io"
API_KEY = os.environ.get("POLYGON_API_KEY", "demo")


def get_aggregates(
    ticker: str,
    multiplier: int = 1,
    timespan: str = "day",
    from_date: str = None,
    to_date: str = None,
    limit: int = 120
) -> Dict:
    """
    Get aggregate bars (OHLCV) for a stock ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'SPY')
        multiplier: Size of timespan multiplier (1, 5, 15, etc.)
        timespan: Size of time window ('minute', 'hour', 'day', 'week', 'month')
        from_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        to_date: End date (YYYY-MM-DD), defaults to today
        limit: Number of results to return (max 50000)
    
    Returns:
        Dict with 'results' key containing list of bars, each with:
        - v: Volume
        - vw: Volume weighted average price
        - o: Open
        - c: Close
        - h: High
        - l: Low
        - t: Timestamp (ms)
        - n: Number of transactions
    """
    ticker = ticker.upper()
    
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    cache_key = f"{ticker}_{multiplier}_{timespan}_{from_date}_{to_date}"
    cache_file = os.path.join(CACHE_DIR, f"agg_{cache_key}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": limit,
            "apiKey": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Unknown error"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_ticker_details(ticker: str) -> Dict:
    """
    Get detailed information about a ticker symbol.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'SPY')
    
    Returns:
        Dict with ticker details including:
        - name: Company name
        - market: Market type (stocks, crypto, fx)
        - locale: Locale (us, global)
        - primary_exchange: Primary exchange
        - type: Security type (CS, ETF, etc.)
        - currency_name: Currency name
        - market_cap: Market capitalization
        - share_class_shares_outstanding: Shares outstanding
        - description: Company description
        - homepage_url: Company website
        - total_employees: Employee count
        - sic_description: Industry description
    """
    ticker = ticker.upper()
    cache_file = os.path.join(CACHE_DIR, f"details_{ticker}.json")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/v3/reference/tickers/{ticker}"
        params = {"apiKey": API_KEY}
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Ticker not found"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_snapshot(ticker: Optional[str] = None) -> Dict:
    """
    Get snapshot of current market data for ticker(s).
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL'). If None, returns all tickers.
    
    Returns:
        Dict with snapshot data including current price, volume, etc.
    """
    if ticker:
        ticker = ticker.upper()
        url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
    else:
        url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
    
    try:
        params = {"apiKey": API_KEY}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Snapshot failed"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_previous_close(ticker: str) -> Dict:
    """
    Get previous day's OHLC data for a ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'SPY')
    
    Returns:
        Dict with previous close data:
        - o: Open
        - h: High
        - l: Low
        - c: Close
        - v: Volume
        - vw: Volume weighted average
        - t: Timestamp
    """
    ticker = ticker.upper()
    cache_file = os.path.join(CACHE_DIR, f"prev_{ticker}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=6):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/v2/aggs/ticker/{ticker}/prev"
        params = {
            "adjusted": "true",
            "apiKey": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Previous close not found"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_splits(ticker: str, limit: int = 100) -> Dict:
    """
    Get stock splits for a ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'TSLA')
        limit: Number of results to return
    
    Returns:
        Dict with 'results' key containing list of splits:
        - execution_date: Date of split
        - split_from: Shares before split
        - split_to: Shares after split
    """
    ticker = ticker.upper()
    cache_file = os.path.join(CACHE_DIR, f"splits_{ticker}.json")
    
    # Check cache (refresh monthly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=30):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/v3/reference/splits"
        params = {
            "ticker": ticker,
            "limit": limit,
            "apiKey": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Splits not found"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_dividends(ticker: str, limit: int = 100) -> Dict:
    """
    Get dividend history for a ticker.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'VTI')
        limit: Number of results to return
    
    Returns:
        Dict with 'results' key containing list of dividends:
        - ex_dividend_date: Ex-dividend date
        - payment_date: Payment date
        - cash_amount: Dividend amount per share
        - dividend_type: Type of dividend (CD, SC, LT, ST)
        - frequency: Payment frequency
    """
    ticker = ticker.upper()
    cache_file = os.path.join(CACHE_DIR, f"dividends_{ticker}.json")
    
    # Check cache (refresh monthly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=30):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        url = f"{BASE_URL}/v3/reference/dividends"
        params = {
            "ticker": ticker,
            "limit": limit,
            "apiKey": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Dividends not found"),
                "ticker": ticker
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "ticker": ticker
        }


def get_grouped_daily(date: Optional[str] = None, include_otc: bool = False) -> Dict:
    """
    Get OHLC data for the entire stock market for a specific date.
    
    Args:
        date: Date (YYYY-MM-DD), defaults to previous trading day
        include_otc: Include OTC securities
    
    Returns:
        Dict with 'results' key containing list of all tickers with OHLCV data
    """
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    cache_file = os.path.join(CACHE_DIR, f"grouped_{date}.json")
    
    # Check cache (don't refresh historical dates)
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)
    
    try:
        url = f"{BASE_URL}/v2/aggs/grouped/locale/us/market/stocks/{date}"
        params = {
            "adjusted": "true",
            "include_otc": str(include_otc).lower(),
            "apiKey": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            # Cache successful response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {
                "error": True,
                "message": data.get("error", "Grouped daily not found"),
                "date": date
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": f"Request failed: {str(e)}",
            "date": date
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"Unexpected error: {str(e)}",
            "date": date
        }


if __name__ == "__main__":
    # Quick test
    print("Testing Polygon.io module...")
    print("\n1. Previous close for AAPL:")
    result = get_previous_close("AAPL")
    print(json.dumps(result, indent=2)[:500])
    
    print("\n2. Ticker details for SPY:")
    result = get_ticker_details("SPY")
    print(json.dumps(result, indent=2)[:500])
