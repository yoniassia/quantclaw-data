"""
Polygon Options Aggregates — Options Market Data & Analytics

Data Source: Polygon.io Options API
Update: Real-time streaming + historical data
History: Full options chain history available
Free: Yes (5 calls/min, 100k messages/day)

Provides:
- Options contract details (strike, expiration, type)
- OHLCV aggregates (daily bars for specific contracts)
- Options chain snapshot for underlying ticker
- Recent trades for options contracts
- Previous day close data
- Options ticker search and lookup

Options Ticker Format: O:UNDERLYING+YYMMDD+C/P+STRIKE*1000
Example: O:AAPL250321C00250000 = AAPL $250 Call expiring March 21, 2025

Source: https://polygon.io/docs/options/getting-started
Category: Options & Derivatives
Free tier: true - 5 API calls per minute, basic options data included
Update frequency: real-time
"""

import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/polygon_options")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.polygon.io"
API_KEY = os.getenv("POLYGON_API_KEY", "")

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Internal helper to make Polygon API requests with rate limiting and error handling.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Dict with response data or error
    """
    if not API_KEY:
        return {"error": "POLYGON_API_KEY environment variable not set"}
    
    if params is None:
        params = {}
    
    params["apiKey"] = API_KEY
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        # Handle rate limiting
        if response.status_code == 429:
            return {"error": "Rate limit exceeded (5 calls/min)", "status_code": 429}
        
        response.raise_for_status()
        data = response.json()
        
        # Check for API-level errors
        if data.get("status") == "ERROR":
            return {"error": data.get("error", "Unknown API error"), "status": "ERROR"}
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from API"}


def get_contract_details(options_ticker: str) -> Dict:
    """
    Get detailed information about a specific options contract.
    
    Args:
        options_ticker: Options ticker (e.g., "O:AAPL250321C00250000")
        
    Returns:
        Dict with contract details including strike, expiration, underlying ticker,
        contract type (call/put), exercise style, etc.
        
    Example:
        >>> details = get_contract_details("O:AAPL250321C00250000")
        >>> print(details["strike_price"], details["expiration_date"])
    """
    endpoint = f"/v3/reference/options/contracts/{options_ticker}"
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    if "results" in result:
        contract = result["results"]
        return {
            "ticker": contract.get("ticker"),
            "underlying_ticker": contract.get("underlying_ticker"),
            "strike_price": contract.get("strike_price"),
            "expiration_date": contract.get("expiration_date"),
            "contract_type": contract.get("contract_type"),  # call or put
            "exercise_style": contract.get("exercise_style"),  # american/european
            "shares_per_contract": contract.get("shares_per_contract", 100),
            "primary_exchange": contract.get("primary_exchange"),
            "cfi": contract.get("cfi"),  # Classification of Financial Instruments code
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No contract details found"}


def get_options_aggregates(options_ticker: str, from_date: str, to_date: str, 
                           timespan: str = "day") -> Dict:
    """
    Get OHLCV aggregate bars for an options contract.
    
    Args:
        options_ticker: Options ticker (e.g., "O:AAPL250321C00250000")
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        timespan: Bar size (minute/hour/day/week/month/quarter/year)
        
    Returns:
        Dict with OHLCV data and metadata
        
    Example:
        >>> data = get_options_aggregates("O:AAPL250321C00250000", "2026-03-01", "2026-03-07")
        >>> for bar in data["results"]:
        ...     print(bar["t"], bar["c"])  # timestamp, close price
    """
    endpoint = f"/v2/aggs/ticker/{options_ticker}/range/1/{timespan}/{from_date}/{to_date}"
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    if "results" in result:
        return {
            "ticker": result.get("ticker"),
            "results_count": result.get("resultsCount", 0),
            "results": [
                {
                    "timestamp": bar.get("t"),
                    "date": datetime.fromtimestamp(bar.get("t", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "open": bar.get("o"),
                    "high": bar.get("h"),
                    "low": bar.get("l"),
                    "close": bar.get("c"),
                    "volume": bar.get("v"),
                    "vwap": bar.get("vw"),  # Volume weighted average price
                    "num_transactions": bar.get("n")
                }
                for bar in result.get("results", [])
            ],
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No aggregate data found", "note": "Contract may not have traded in this period"}


def get_options_chain_snapshot(underlying_ticker: str, expiration_date: Optional[str] = None) -> Dict:
    """
    Get snapshot of entire options chain for an underlying ticker.
    
    Args:
        underlying_ticker: Stock ticker (e.g., "AAPL")
        expiration_date: Optional specific expiration date (YYYY-MM-DD)
        
    Returns:
        Dict with options chain data including all strikes and contract types
        
    Example:
        >>> chain = get_options_chain_snapshot("AAPL", "2025-03-21")
        >>> for contract in chain["results"]:
        ...     print(contract["ticker"], contract["last_price"])
    """
    endpoint = f"/v3/snapshot/options/{underlying_ticker}"
    
    params = {}
    if expiration_date:
        params["expiration_date"] = expiration_date
    
    result = _make_request(endpoint, params)
    
    if "error" in result:
        return result
    
    if "results" in result:
        return {
            "underlying_ticker": underlying_ticker,
            "expiration_date": expiration_date,
            "results_count": len(result.get("results", [])),
            "results": [
                {
                    "ticker": contract.get("details", {}).get("ticker"),
                    "strike": contract.get("details", {}).get("strike_price"),
                    "expiration": contract.get("details", {}).get("expiration_date"),
                    "contract_type": contract.get("details", {}).get("contract_type"),
                    "last_price": contract.get("last_quote", {}).get("last_price"),
                    "bid": contract.get("last_quote", {}).get("bid"),
                    "ask": contract.get("last_quote", {}).get("ask"),
                    "bid_size": contract.get("last_quote", {}).get("bid_size"),
                    "ask_size": contract.get("last_quote", {}).get("ask_size"),
                    "volume": contract.get("day", {}).get("volume"),
                    "open_interest": contract.get("open_interest"),
                    "implied_volatility": contract.get("implied_volatility")
                }
                for contract in result.get("results", [])
            ],
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No options chain data found"}


def get_options_trades(options_ticker: str, limit: int = 10) -> Dict:
    """
    Get recent trades for a specific options contract.
    
    Args:
        options_ticker: Options ticker (e.g., "O:AAPL250321C00250000")
        limit: Maximum number of trades to return (default 10, max 50000)
        
    Returns:
        Dict with recent trade data including price, size, timestamp, conditions
        
    Example:
        >>> trades = get_options_trades("O:AAPL250321C00250000", limit=5)
        >>> for trade in trades["results"]:
        ...     print(trade["price"], trade["size"])
    """
    endpoint = f"/v3/trades/{options_ticker}"
    params = {"limit": min(limit, 50000)}
    
    result = _make_request(endpoint, params)
    
    if "error" in result:
        return result
    
    if "results" in result:
        return {
            "ticker": options_ticker,
            "results_count": len(result.get("results", [])),
            "results": [
                {
                    "timestamp": trade.get("sip_timestamp"),
                    "date": datetime.fromtimestamp(trade.get("sip_timestamp", 0) / 1000000000).strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "price": trade.get("price"),
                    "size": trade.get("size"),
                    "exchange": trade.get("exchange"),
                    "conditions": trade.get("conditions", []),
                    "sequence_number": trade.get("sequence_number")
                }
                for trade in result.get("results", [])
            ],
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No trade data found"}


def get_previous_close(options_ticker: str) -> Dict:
    """
    Get previous day's close data for an options contract.
    
    Args:
        options_ticker: Options ticker (e.g., "O:AAPL250321C00250000")
        
    Returns:
        Dict with previous close OHLCV data
        
    Example:
        >>> prev = get_previous_close("O:AAPL250321C00250000")
        >>> print(prev["close"], prev["volume"])
    """
    endpoint = f"/v2/aggs/ticker/{options_ticker}/prev"
    result = _make_request(endpoint)
    
    if "error" in result:
        return result
    
    if "results" in result and len(result["results"]) > 0:
        bar = result["results"][0]
        return {
            "ticker": result.get("ticker"),
            "timestamp": bar.get("t"),
            "date": datetime.fromtimestamp(bar.get("t", 0) / 1000).strftime("%Y-%m-%d"),
            "open": bar.get("o"),
            "high": bar.get("h"),
            "low": bar.get("l"),
            "close": bar.get("c"),
            "volume": bar.get("v"),
            "vwap": bar.get("vw"),
            "num_transactions": bar.get("n"),
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No previous close data found"}


def search_options_contracts(underlying_ticker: str, contract_type: Optional[str] = None,
                             expiration_date_gte: Optional[str] = None,
                             expiration_date_lte: Optional[str] = None,
                             limit: int = 100) -> Dict:
    """
    Search and filter options contracts by criteria.
    
    Args:
        underlying_ticker: Stock ticker (e.g., "AAPL")
        contract_type: Filter by "call" or "put"
        expiration_date_gte: Min expiration date (YYYY-MM-DD)
        expiration_date_lte: Max expiration date (YYYY-MM-DD)
        limit: Max results to return (default 100, max 1000)
        
    Returns:
        Dict with list of matching contracts
        
    Example:
        >>> contracts = search_options_contracts("AAPL", contract_type="call", 
        ...                                       expiration_date_gte="2026-03-01",
        ...                                       limit=50)
        >>> for c in contracts["results"]:
        ...     print(c["ticker"], c["strike_price"])
    """
    endpoint = "/v3/reference/options/contracts"
    
    params = {
        "underlying_ticker": underlying_ticker,
        "limit": min(limit, 1000)
    }
    
    if contract_type:
        params["contract_type"] = contract_type
    if expiration_date_gte:
        params["expiration_date.gte"] = expiration_date_gte
    if expiration_date_lte:
        params["expiration_date.lte"] = expiration_date_lte
    
    result = _make_request(endpoint, params)
    
    if "error" in result:
        return result
    
    if "results" in result:
        return {
            "underlying_ticker": underlying_ticker,
            "results_count": len(result.get("results", [])),
            "results": [
                {
                    "ticker": contract.get("ticker"),
                    "strike_price": contract.get("strike_price"),
                    "expiration_date": contract.get("expiration_date"),
                    "contract_type": contract.get("contract_type"),
                    "exercise_style": contract.get("exercise_style"),
                    "cfi": contract.get("cfi")
                }
                for contract in result.get("results", [])
            ],
            "next_url": result.get("next_url"),
            "fetched_at": datetime.now().isoformat()
        }
    
    return {"error": "No contracts found"}


if __name__ == "__main__":
    # Module info
    info = {
        "module": "polygon_options_aggregates",
        "status": "active",
        "source": "https://polygon.io/docs/options/getting-started",
        "functions": [
            "get_contract_details",
            "get_options_aggregates",
            "get_options_chain_snapshot",
            "get_options_trades",
            "get_previous_close",
            "search_options_contracts"
        ],
        "requires_api_key": True,
        "env_var": "POLYGON_API_KEY",
        "free_tier": "5 calls/min, 100k messages/day"
    }
    print(json.dumps(info, indent=2))
