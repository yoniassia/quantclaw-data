#!/usr/bin/env python3
"""
Tiingo ETF Flows Dataset

ETF flows and pricing data from Tiingo API.
Provides access to:
- ETF creation/redemption flows
- Intraday and historical ETF prices
- Top ETF flows by volume
- ETF metadata and search

Source: https://api.tiingo.com/documentation/etf
Category: ETF & Fund Flows
Free tier: True (50,000 API calls/month)
Update frequency: intraday
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

# Tiingo API Configuration
TIINGO_BASE_URL = "https://api.tiingo.com"
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY", "")


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Tiingo API
    
    Args:
        endpoint: API endpoint path (e.g., '/tiingo/etf/flows')
        params: Optional query parameters
    
    Returns:
        JSON response as dict
    """
    if not TIINGO_API_KEY:
        return {"error": "TIINGO_API_KEY not set in environment"}
    
    url = f"{TIINGO_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Token {TIINGO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_etf_flows(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get ETF flows data (creations/redemptions) for a specific ETF
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Dict containing flows data or error
    """
    params = {"tickers": symbol.upper()}
    
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    
    return _make_request("/tiingo/etf/flows", params)


def get_etf_prices(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
    """
    Get historical/intraday ETF price data
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 1 year ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
    
    Returns:
        List of price data dicts or error dict
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    
    return _make_request(f"/tiingo/etf/{symbol.upper()}/prices", params)


def get_top_etf_flows(limit: int = 10, sort_by: str = "netFlow") -> List[Dict]:
    """
    Get top ETFs by flow metrics
    
    Args:
        limit: Number of results to return (default 10)
        sort_by: Sort field - 'netFlow', 'creations', or 'redemptions' (default 'netFlow')
    
    Returns:
        List of ETF flows sorted by specified metric
    """
    result = _make_request("/tiingo/etf/flows")
    
    if isinstance(result, dict) and "error" in result:
        return result
    
    # If result is a list, sort and limit
    if isinstance(result, list):
        try:
            sorted_data = sorted(result, key=lambda x: x.get(sort_by, 0), reverse=True)
            return sorted_data[:limit]
        except (KeyError, TypeError):
            return result[:limit]
    
    return result


def get_etf_metadata(symbol: str) -> Dict:
    """
    Get ETF metadata and profile information
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dict containing ETF metadata
    """
    return _make_request(f"/tiingo/etf/{symbol.upper()}")


def search_etfs(query: str) -> List[Dict]:
    """
    Search for ETFs by name or ticker
    
    Args:
        query: Search query (ticker or name fragment)
    
    Returns:
        List of matching ETFs
    """
    params = {"query": query}
    return _make_request("/tiingo/etf/search", params)


def fetch_data() -> Dict:
    """
    Fetch latest ETF flows data (default implementation)
    
    Returns:
        Dict with sample flows data for major ETFs
    """
    major_etfs = ["SPY", "QQQ", "IWM", "DIA"]
    results = {}
    
    for symbol in major_etfs:
        results[symbol] = get_etf_flows(symbol)
    
    return results


def get_latest() -> Dict:
    """
    Get latest flows data for top ETFs
    
    Returns:
        Dict with latest flows for major ETFs
    """
    return get_top_etf_flows(limit=20)


if __name__ == "__main__":
    # Test the module
    print(json.dumps({
        "module": "tiingo_etf_flows_dataset",
        "status": "active",
        "source": "https://api.tiingo.com/documentation/etf",
        "api_key_set": bool(TIINGO_API_KEY),
        "functions": [
            "get_etf_flows(symbol, start_date, end_date)",
            "get_etf_prices(symbol, start_date, end_date)",
            "get_top_etf_flows(limit, sort_by)",
            "get_etf_metadata(symbol)",
            "search_etfs(query)",
            "fetch_data()",
            "get_latest()"
        ]
    }, indent=2))
