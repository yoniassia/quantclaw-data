"""
IEX Cloud — Financial Data from Investors Exchange

Data Source: IEX Cloud API (https://iexcloud.io)
Update: Real-time
History: Varies by endpoint (up to 15 years for prices)
Free: Sandbox available, production requires API key

Provides:
- Real-time stock quotes (bid/ask, volume, market cap)
- Historical price data (daily OHLCV)
- Company fundamentals (key stats, financials)
- Earnings data (actual vs estimate, surprise %)
- Institutional ownership / top holders
- Market-wide stats (most active, gainers, losers)

Usage:
Set environment variable IEX_TOKEN or IEX_API_KEY with your API key.
For testing, uses sandbox endpoint (https://sandbox.iexapis.com/stable/)
For production, uses cloud endpoint (https://cloud.iexapis.com/stable/)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/iex_cloud")
os.makedirs(CACHE_DIR, exist_ok=True)

# Get API key from environment
IEX_TOKEN = os.getenv("IEX_TOKEN") or os.getenv("IEX_API_KEY") or "Tpk_default_sandbox_token"

# Determine base URL (sandbox vs production)
if "sandbox" in IEX_TOKEN.lower() or IEX_TOKEN == "Tpk_default_sandbox_token":
    BASE_URL = "https://sandbox.iexapis.com/stable"
else:
    BASE_URL = "https://cloud.iexapis.com/stable"


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Union[Dict, List]:
    """
    Make authenticated request to IEX Cloud API.
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/AAPL/quote')
        params: Optional query parameters
    
    Returns:
        JSON response as dict or list
    """
    if params is None:
        params = {}
    
    params['token'] = IEX_TOKEN
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "endpoint": endpoint}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {str(e)}", "endpoint": endpoint}


def get_quote(symbol: str, use_cache: bool = True) -> Dict:
    """
    Get real-time stock quote with bid/ask, volume, and market cap.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        use_cache: Use cached data if less than 5 minutes old
    
    Returns:
        Dict with quote data or error
    """
    cache_file = os.path.join(CACHE_DIR, f"quote_{symbol.upper()}.json")
    
    # Check cache
    if use_cache and os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(minutes=5):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/quote")
    
    if "error" not in data:
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


def get_historical_prices(symbol: str, range_: str = "1m") -> List[Dict]:
    """
    Get historical daily OHLCV price data.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        range_: Time range - '5d', '1m', '3m', '6m', '1y', '2y', '5y', 'max'
    
    Returns:
        List of dicts with daily price data or error dict
    """
    cache_file = os.path.join(CACHE_DIR, f"history_{symbol.upper()}_{range_}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/chart/{range_}")
    
    if isinstance(data, list):
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


def get_company_fundamentals(symbol: str) -> Dict:
    """
    Get company fundamentals including key stats and financials.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        Dict with company stats or error
    """
    cache_file = os.path.join(CACHE_DIR, f"stats_{symbol.upper()}.json")
    
    # Check cache (refresh daily)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=1):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/stats")
    
    if "error" not in data:
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


def get_earnings(symbol: str, last: int = 4) -> List[Dict]:
    """
    Get earnings data with actual vs estimate and surprise %.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        last: Number of quarters to return (default 4)
    
    Returns:
        List of dicts with earnings data or error dict
    """
    cache_file = os.path.join(CACHE_DIR, f"earnings_{symbol.upper()}.json")
    
    # Check cache (refresh weekly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=7):
            with open(cache_file) as f:
                cached_data = json.load(f)
                return cached_data[:last] if isinstance(cached_data, list) else cached_data
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/earnings/{last}")
    
    # IEX returns {"earnings": [...]} wrapper
    if isinstance(data, dict) and "earnings" in data:
        earnings_list = data["earnings"]
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(earnings_list, f, indent=2)
        return earnings_list
    
    return data


def get_institutional_ownership(symbol: str) -> List[Dict]:
    """
    Get institutional ownership and top holders.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        List of dicts with institutional holder data or error dict
    """
    cache_file = os.path.join(CACHE_DIR, f"institutional_{symbol.upper()}.json")
    
    # Check cache (refresh monthly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=30):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/institutional-ownership")
    
    if isinstance(data, list):
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


def get_market_movers(list_type: str = "mostactive") -> List[Dict]:
    """
    Get market-wide stats: most active, gainers, losers.
    
    Args:
        list_type: Type of list - 'mostactive', 'gainers', 'losers'
    
    Returns:
        List of dicts with stock data or error dict
    """
    valid_types = ["mostactive", "gainers", "losers"]
    if list_type not in valid_types:
        return {"error": f"Invalid list_type. Must be one of: {valid_types}"}
    
    cache_file = os.path.join(CACHE_DIR, f"movers_{list_type}.json")
    
    # Check cache (refresh every 15 minutes)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(minutes=15):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/market/list/{list_type}")
    
    if isinstance(data, list):
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


def get_company_info(symbol: str) -> Dict:
    """
    Get company information and profile.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
    
    Returns:
        Dict with company info or error
    """
    cache_file = os.path.join(CACHE_DIR, f"company_{symbol.upper()}.json")
    
    # Check cache (refresh monthly)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(days=30):
            with open(cache_file) as f:
                return json.load(f)
    
    # Fetch fresh data
    data = _make_request(f"/stock/{symbol.upper()}/company")
    
    if "error" not in data:
        # Cache successful response
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data


if __name__ == "__main__":
    # Test the module
    print("Testing IEX Cloud module...")
    print(f"Using API key: {IEX_TOKEN[:20]}...")
    print(f"Base URL: {BASE_URL}")
    print("\nTesting get_quote('AAPL')...")
    quote = get_quote("AAPL")
    print(json.dumps(quote, indent=2))
