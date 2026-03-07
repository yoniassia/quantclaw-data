#!/usr/bin/env python3
"""
Polygon.io Options API — Real-Time Options Data Module

Provides real-time and historical options data for US equities, including:
- Options chains (strike, expiration, bid/ask, volume)
- Greeks (delta, gamma, theta, vega)
- Implied volatility
- Options trades and aggregates

Source: https://polygon.io/docs/options/getting-started
Category: Options & Derivatives
Free tier: True (5 API calls/min, 5 years historical data, requires free API key)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Polygon.io API Configuration
BASE_URL = "https://api.polygon.io"
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")


def get_options_chain(ticker: str, expiration_date: Optional[str] = None) -> Dict:
    """
    Get full options chain for a ticker.
    
    Args:
        ticker: Underlying stock ticker (e.g., 'AAPL')
        expiration_date: Optional expiration date filter (YYYY-MM-DD)
        
    Returns:
        Dict containing options chain data with strikes, bids, asks, volume
        
    Example:
        >>> chain = get_options_chain('AAPL', '2026-12-18')
    """
    try:
        url = f"{BASE_URL}/v3/snapshot/options/{ticker.upper()}"
        params = {"apiKey": POLYGON_API_KEY}
        
        if expiration_date:
            params["expiration_date"] = expiration_date
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "expiration_date": expiration_date,
            "timestamp": datetime.now().isoformat(),
            "results": data.get("results", []),
            "count": len(data.get("results", []))
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker,
            "message": "Failed to fetch options chain"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker
        }


def get_options_snapshot(ticker: str) -> Dict:
    """
    Get real-time options snapshot with Greeks for a ticker.
    
    Args:
        ticker: Underlying stock ticker (e.g., 'AAPL')
        
    Returns:
        Dict containing real-time options data including Greeks (delta, gamma, theta, vega)
        
    Example:
        >>> snapshot = get_options_snapshot('AAPL')
    """
    try:
        url = f"{BASE_URL}/v3/snapshot/options/{ticker.upper()}"
        params = {"apiKey": POLYGON_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        # Extract Greeks from results
        options_with_greeks = []
        for option in results:
            greeks = option.get("greeks", {})
            options_with_greeks.append({
                "ticker": option.get("details", {}).get("ticker"),
                "strike": option.get("details", {}).get("strike_price"),
                "expiration": option.get("details", {}).get("expiration_date"),
                "type": option.get("details", {}).get("contract_type"),
                "last_price": option.get("last_quote", {}).get("last_price"),
                "bid": option.get("last_quote", {}).get("bid"),
                "ask": option.get("last_quote", {}).get("ask"),
                "volume": option.get("day", {}).get("volume"),
                "open_interest": option.get("open_interest"),
                "implied_volatility": option.get("implied_volatility"),
                "delta": greeks.get("delta"),
                "gamma": greeks.get("gamma"),
                "theta": greeks.get("theta"),
                "vega": greeks.get("vega")
            })
        
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "timestamp": datetime.now().isoformat(),
            "count": len(options_with_greeks),
            "options": options_with_greeks
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker,
            "message": "Failed to fetch options snapshot"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker
        }


def get_options_contracts(ticker: str, contract_type: Optional[str] = None, 
                         expiration_date: Optional[str] = None) -> Dict:
    """
    List available options contracts for a ticker.
    
    Args:
        ticker: Underlying stock ticker (e.g., 'AAPL')
        contract_type: Optional filter - 'call' or 'put'
        expiration_date: Optional expiration date filter (YYYY-MM-DD)
        
    Returns:
        Dict containing list of available options contracts
        
    Example:
        >>> contracts = get_options_contracts('AAPL', contract_type='call', expiration_date='2026-12-18')
    """
    try:
        url = f"{BASE_URL}/v3/reference/options/contracts"
        params = {
            "underlying_ticker": ticker.upper(),
            "apiKey": POLYGON_API_KEY
        }
        
        if contract_type:
            params["contract_type"] = contract_type.lower()
        if expiration_date:
            params["expiration_date"] = expiration_date
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "contract_type": contract_type,
            "expiration_date": expiration_date,
            "timestamp": datetime.now().isoformat(),
            "results": data.get("results", []),
            "count": len(data.get("results", [])),
            "next_url": data.get("next_url")
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker,
            "message": "Failed to fetch options contracts"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ticker": ticker
        }


def get_options_trades(options_ticker: str, limit: int = 100) -> Dict:
    """
    Get recent trades for a specific options contract.
    
    Args:
        options_ticker: Options contract ticker (e.g., 'O:AAPL251219C00150000')
        limit: Maximum number of trades to return (default 100)
        
    Returns:
        Dict containing recent trades for the options contract
        
    Example:
        >>> trades = get_options_trades('O:AAPL251219C00150000', limit=50)
    """
    try:
        url = f"{BASE_URL}/v3/trades/{options_ticker}"
        params = {
            "apiKey": POLYGON_API_KEY,
            "limit": limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "status": "success",
            "options_ticker": options_ticker,
            "timestamp": datetime.now().isoformat(),
            "results": data.get("results", []),
            "count": len(data.get("results", [])),
            "next_url": data.get("next_url")
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "options_ticker": options_ticker,
            "message": "Failed to fetch options trades"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "options_ticker": options_ticker
        }


def get_options_aggregates(options_ticker: str, timespan: str = 'day',
                          from_date: Optional[str] = None, 
                          to_date: Optional[str] = None) -> Dict:
    """
    Get OHLCV bars for options contract.
    
    Args:
        options_ticker: Options contract ticker (e.g., 'O:AAPL251219C00150000')
        timespan: Time span - 'minute', 'hour', 'day', 'week', 'month' (default 'day')
        from_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        to_date: End date (YYYY-MM-DD), defaults to today
        
    Returns:
        Dict containing OHLCV aggregates for the options contract
        
    Example:
        >>> aggs = get_options_aggregates('O:AAPL251219C00150000', timespan='hour', 
        ...                               from_date='2026-03-01', to_date='2026-03-07')
    """
    try:
        # Default date range if not provided
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/v2/aggs/ticker/{options_ticker}/range/1/{timespan}/{from_date}/{to_date}"
        params = {"apiKey": POLYGON_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "status": "success",
            "options_ticker": options_ticker,
            "timespan": timespan,
            "from_date": from_date,
            "to_date": to_date,
            "timestamp": datetime.now().isoformat(),
            "results": data.get("results", []),
            "count": len(data.get("results", [])),
            "resultsCount": data.get("resultsCount", 0)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "options_ticker": options_ticker,
            "message": "Failed to fetch options aggregates"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "options_ticker": options_ticker
        }


if __name__ == "__main__":
    # Test module
    print(json.dumps({
        "module": "polygonio_options_api",
        "status": "ready",
        "functions": [
            "get_options_chain",
            "get_options_snapshot",
            "get_options_contracts",
            "get_options_trades",
            "get_options_aggregates"
        ],
        "api_key_configured": bool(POLYGON_API_KEY)
    }, indent=2))
