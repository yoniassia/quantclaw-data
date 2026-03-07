#!/usr/bin/env python3
"""
Finnhub Stock Ownership API — Institutional & Insider Data Module

Provides access to ownership data including:
- Institutional ownership (13F filings)
- Insider transactions
- Insider sentiment
- Fund ownership
- Comprehensive ownership summaries

Source: https://finnhub.io/docs/api/stock-ownership
Category: Insider & Institutional
Free tier: True (60 API calls per minute)
Update frequency: Quarterly for 13F, monthly for sentiment
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# ========== CORE API FUNCTIONS ==========

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make authenticated request to Finnhub API
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/ownership')
        params: Optional query parameters
    
    Returns:
        JSON response dict or None on error
    """
    if not FINNHUB_API_KEY:
        return {
            "error": "FINNHUB_API_KEY not set",
            "message": "Get free API key at https://finnhub.io/register"
        }
    
    url = f"{FINNHUB_BASE_URL}{endpoint}"
    
    # Add API key to params
    if params is None:
        params = {}
    params['token'] = FINNHUB_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return {"error": "API key invalid or rate limit exceeded"}
        elif e.response.status_code == 429:
            return {"error": "Rate limit exceeded (60 calls/min)"}
        else:
            return {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}


def get_institutional_ownership(symbol: str) -> Optional[Dict]:
    """
    Get institutional ownership data (13F filings)
    
    Lists major institutional holders and their positions.
    Data sourced from SEC 13F filings.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        Dict containing:
        - data: List of institutional holders with:
            - name: Institution name
            - share: Number of shares held
            - change: Change in shares from previous period
            - filingDate: Date of filing
    
    Example:
        >>> data = get_institutional_ownership('AAPL')
        >>> print(data['data'][0]['name'])
        'Vanguard Group Inc'
    """
    return _make_request('/stock/ownership', {'symbol': symbol.upper()})


def get_insider_transactions(
    symbol: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Optional[Dict]:
    """
    Get insider trading transactions
    
    Retrieves buy/sell transactions by company insiders.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        from_date: Start date (YYYY-MM-DD format), optional
        to_date: End date (YYYY-MM-DD format), optional
    
    Returns:
        Dict containing:
        - data: List of transactions with:
            - name: Insider name
            - share: Number of shares transacted
            - change: Change in ownership
            - filingDate: Transaction filing date
            - transactionDate: Actual transaction date
            - transactionCode: SEC transaction code
    
    Example:
        >>> data = get_insider_transactions('TSLA', from_date='2024-01-01')
        >>> for tx in data['data'][:5]:
        ...     print(f"{tx['name']}: {tx['share']} shares")
    """
    params = {'symbol': symbol.upper()}
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date
    
    return _make_request('/stock/insider-transactions', params)


def get_insider_sentiment(symbol: str, from_date: str, to_date: str) -> Optional[Dict]:
    """
    Get insider sentiment aggregated by month
    
    Provides sentiment score based on insider trading patterns.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        from_date: Start date (YYYY-MM-DD format)
        to_date: End date (YYYY-MM-DD format)
    
    Returns:
        Dict containing:
        - data: List of monthly sentiment records with:
            - symbol: Stock symbol
            - year: Year
            - month: Month
            - change: Net change in shares (buys - sells)
            - mspr: Monthly Share Purchase Ratio
    
    Example:
        >>> data = get_insider_sentiment('AAPL', '2024-01-01', '2024-12-31')
        >>> for month in data['data']:
        ...     print(f"{month['year']}-{month['month']}: MSPR={month['mspr']}")
    """
    params = {
        'symbol': symbol.upper(),
        'from': from_date,
        'to': to_date
    }
    return _make_request('/stock/insider-sentiment', params)


def get_fund_ownership(symbol: str, limit: int = 10) -> Optional[Dict]:
    """
    Get mutual fund ownership data
    
    Lists mutual funds holding the stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        limit: Number of results to return (default 10)
    
    Returns:
        Dict containing:
        - data: List of fund holders with:
            - name: Fund name
            - share: Number of shares held
            - change: Change from previous period
            - filingDate: Date of filing
    
    Example:
        >>> data = get_fund_ownership('MSFT', limit=5)
        >>> for fund in data['data']:
        ...     print(f"{fund['name']}: {fund['share']:,} shares")
    """
    params = {
        'symbol': symbol.upper(),
        'limit': limit
    }
    return _make_request('/stock/fund-ownership', params)


def get_ownership_summary(symbol: str) -> Dict:
    """
    Get comprehensive ownership summary
    
    Combines institutional, fund, and insider data into a single summary.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        Dict containing:
        - symbol: Stock symbol
        - timestamp: UTC timestamp
        - institutional: Institutional ownership data
        - funds: Fund ownership data (top 10)
        - insider_recent: Recent insider transactions (last 90 days)
    
    Example:
        >>> summary = get_ownership_summary('AAPL')
        >>> print(f"Top institutional holder: {summary['institutional']['data'][0]['name']}")
        >>> print(f"Top fund: {summary['funds']['data'][0]['name']}")
    """
    from datetime import datetime, timedelta
    
    # Calculate date range for insider transactions (last 90 days)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=90)
    
    summary = {
        'symbol': symbol.upper(),
        'timestamp': datetime.now().astimezone().isoformat(),
        'institutional': get_institutional_ownership(symbol),
        'funds': get_fund_ownership(symbol, limit=10),
        'insider_recent': get_insider_transactions(
            symbol,
            from_date=from_date.strftime('%Y-%m-%d'),
            to_date=to_date.strftime('%Y-%m-%d')
        )
    }
    
    return summary


# ========== MAIN CLI ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "module": "finnhub_stock_ownership_api",
            "status": "active",
            "source": "https://finnhub.io/docs/api/stock-ownership",
            "usage": "python finnhub_stock_ownership_api.py <SYMBOL>",
            "example": "python finnhub_stock_ownership_api.py AAPL"
        }, indent=2))
        sys.exit(0)
    
    symbol = sys.argv[1].upper()
    
    print(f"\n=== Ownership Summary for {symbol} ===\n")
    summary = get_ownership_summary(symbol)
    print(json.dumps(summary, indent=2))
