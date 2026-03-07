#!/usr/bin/env python3
"""
EODHD Insider Data API — Insider Trading & Institutional Holdings

EOD Historical Data (EODHD) API provides insider trading and institutional holdings data
for global markets, sourced from regulatory filings (SEC Form 4, 13F, etc.).
Offers historical datasets for backtesting quant models and real-time insider alerts.

Data Points:
- Insider transactions (buys, sells, options exercises)
- Institutional holdings (13F filings)
- Transaction details: date, shares, value, filing date
- Insider details: name, title, relationship

Updated: Daily for insider transactions, quarterly for institutional holdings
History: 10+ years depending on symbol
Source: https://eodhistoricaldata.com/financial-apis
Category: Alternative Data — Insider & Institutional
Free tier: True - 20 API calls per day, 'demo' key works for AAPL.US
API Key: Set EODHD_API_KEY env var, defaults to 'demo' for testing
Author: QuantClaw Data NightBuilder
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Constants
BASE_URL = "https://eodhistoricaldata.com/api"
API_KEY = os.environ.get('EODHD_API_KEY', 'demo')

# Simple in-memory cache to avoid burning through 20 API calls/day
_CACHE = {}
_CACHE_DURATION = timedelta(hours=6)  # Data updates daily, 6hr cache is reasonable


def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Internal helper for API requests with error handling and caching
    
    Args:
        endpoint: API endpoint (e.g., 'insider-transactions')
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        Exception if API call fails
    """
    cache_key = f"{endpoint}_{str(sorted(params.items()))}"
    
    # Check cache
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return {**cached_data, 'cached': True, 'cache_age_hours': round((datetime.now() - cached_time).total_seconds() / 3600, 1)}
    
    # Add API key to params
    params['api_token'] = API_KEY
    
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Cache successful response
        _CACHE[cache_key] = (datetime.now(), data)
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'endpoint': endpoint,
            'params': {k: v for k, v in params.items() if k != 'api_token'},
            'timestamp': datetime.now().isoformat()
        }


def get_insider_transactions(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 100) -> Dict:
    """
    Get insider trading transactions for a symbol
    
    Retrieves insider buy/sell transactions from SEC Form 4 filings.
    Useful for tracking smart money flows and insider sentiment.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'AAPL.US', 'TSLA.US')
        from_date: Start date in YYYY-MM-DD format (default: 90 days ago)
        to_date: End date in YYYY-MM-DD format (default: today)
        limit: Max number of transactions to return (default: 100)
        
    Returns:
        Dict with insider transaction data including:
        - date: Transaction date
        - ownerName: Insider name
        - ownerTitle: Insider title/relationship
        - transactionType: Buy, sell, option exercise, etc.
        - transactionShares: Number of shares
        - transactionPricePerShare: Price per share
        - transactionValue: Total transaction value
        - filingDate: Date filed with SEC
        
    Example:
        >>> data = get_insider_transactions('AAPL.US', from_date='2026-01-01')
        >>> if 'data' in data:
        >>>     for txn in data['data'][:3]:
        >>>         print(f"{txn['date']}: {txn['ownerName']} {txn['transactionType']} {txn['transactionShares']} shares")
    """
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    if to_date is None:
        to_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'from': from_date,
        'to': to_date,
        'limit': limit
    }
    
    endpoint = f"insider-transactions/{symbol}"
    result = _make_request(endpoint, params)
    
    # Add metadata
    result['symbol'] = symbol
    result['from_date'] = from_date
    result['to_date'] = to_date
    result['fetched_at'] = datetime.now().isoformat()
    
    return result


def get_institutional_holdings(symbol: str, limit: int = 50) -> Dict:
    """
    Get institutional holdings (13F filings) for a symbol
    
    Retrieves latest institutional investor positions from SEC 13F filings.
    Shows which hedge funds, mutual funds, and institutions own the stock.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'AAPL.US', 'TSLA.US')
        limit: Max number of holders to return (default: 50)
        
    Returns:
        Dict with institutional holdings data including:
        - date: Reporting period date
        - investorName: Institution name
        - shares: Number of shares held
        - value: Market value of position
        - changeInShares: Change from previous quarter
        - percentOfPortfolio: What % of their portfolio this is
        
    Example:
        >>> data = get_institutional_holdings('AAPL.US')
        >>> if 'data' in data:
        >>>     for holder in data['data'][:5]:
        >>>         print(f"{holder['investorName']}: {holder['shares']:,} shares (${holder['value']:,.0f})")
    """
    params = {'limit': limit}
    
    endpoint = f"institutional-holdings/{symbol}"
    result = _make_request(endpoint, params)
    
    # Add metadata
    result['symbol'] = symbol
    result['fetched_at'] = datetime.now().isoformat()
    
    return result


def get_latest_insider_activity(symbol: str) -> Dict:
    """
    Get most recent insider transactions (last 30 days)
    
    Convenience function for quick check of recent insider activity.
    Good for daily monitoring of insider sentiment.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'AAPL.US')
        
    Returns:
        Dict with recent insider transactions and summary stats:
        - transactions: List of recent transactions
        - summary: Aggregated buy/sell volumes and counts
        - net_insider_sentiment: 'bullish', 'bearish', or 'neutral'
        
    Example:
        >>> data = get_latest_insider_activity('AAPL.US')
        >>> if 'summary' in data:
        >>>     print(f"Insider sentiment: {data['net_insider_sentiment']}")
        >>>     print(f"Buys: {data['summary']['buy_count']}, Sells: {data['summary']['sell_count']}")
    """
    from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    result = get_insider_transactions(symbol, from_date=from_date, limit=50)
    
    # Add sentiment analysis if data available
    if 'data' in result and isinstance(result['data'], list):
        buys = [t for t in result['data'] if 'buy' in str(t.get('transactionType', '')).lower()]
        sells = [t for t in result['data'] if 'sell' in str(t.get('transactionType', '')).lower()]
        
        buy_volume = sum(t.get('transactionShares', 0) for t in buys)
        sell_volume = sum(t.get('transactionShares', 0) for t in sells)
        
        result['summary'] = {
            'buy_count': len(buys),
            'sell_count': len(sells),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'net_volume': buy_volume - sell_volume
        }
        
        # Simple sentiment signal
        if len(buys) > len(sells) * 2:
            sentiment = 'bullish'
        elif len(sells) > len(buys) * 2:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
            
        result['net_insider_sentiment'] = sentiment
    
    return result


def get_top_institutional_buyers(symbol: str, quarters_back: int = 2) -> Dict:
    """
    Identify institutions increasing their positions (smart money tracker)
    
    NOTE: This endpoint may require paid tier. Free tier only supports
    current institutional holdings snapshot.
    
    Args:
        symbol: Stock ticker with exchange suffix
        quarters_back: How many quarters to analyze (default: 2)
        
    Returns:
        Dict with institutions that increased positions most
        
    Example:
        >>> data = get_top_institutional_buyers('AAPL.US')
        >>> # May return error if paid tier required
    """
    result = get_institutional_holdings(symbol, limit=100)
    
    # Filter for position increases if data has changeInShares
    if 'data' in result and isinstance(result['data'], list):
        buyers = [h for h in result['data'] if h.get('changeInShares', 0) > 0]
        buyers_sorted = sorted(buyers, key=lambda x: x.get('changeInShares', 0), reverse=True)
        
        result['top_buyers'] = buyers_sorted[:10]
        result['total_net_buying'] = sum(h.get('changeInShares', 0) for h in buyers)
    
    return result


def clear_cache():
    """Clear the in-memory cache (useful for testing or forcing fresh data)"""
    global _CACHE
    _CACHE = {}
    return {'status': 'cache_cleared', 'timestamp': datetime.now().isoformat()}


if __name__ == "__main__":
    import json
    
    print("EODHD Insider Data API Module — Test Run\n")
    print("=" * 60)
    
    # Test with AAPL.US (works with demo key)
    symbol = 'AAPL.US'
    
    print(f"\n1. Testing insider transactions for {symbol}...")
    transactions = get_insider_transactions(symbol, from_date='2026-01-01')
    if 'error' in transactions:
        print(f"   ❌ Error: {transactions['error']}")
    elif 'data' in transactions:
        print(f"   ✅ Retrieved {len(transactions.get('data', []))} transactions")
        if transactions.get('data'):
            print(f"   Sample: {transactions['data'][0].get('ownerName', 'N/A')} - {transactions['data'][0].get('transactionType', 'N/A')}")
    else:
        print(f"   ⚠️  Unexpected response format")
    
    print(f"\n2. Testing latest insider activity for {symbol}...")
    latest = get_latest_insider_activity(symbol)
    if 'summary' in latest:
        print(f"   ✅ Sentiment: {latest.get('net_insider_sentiment', 'N/A')}")
        print(f"   Buys: {latest['summary']['buy_count']}, Sells: {latest['summary']['sell_count']}")
    elif 'error' in latest:
        print(f"   ❌ Error: {latest['error']}")
    
    print(f"\n3. Testing institutional holdings for {symbol}...")
    holdings = get_institutional_holdings(symbol)
    if 'error' in holdings:
        print(f"   ❌ Error: {holdings['error']}")
    elif 'data' in holdings:
        print(f"   ✅ Retrieved {len(holdings.get('data', []))} institutional holders")
        if holdings.get('data'):
            print(f"   Top holder: {holdings['data'][0].get('investorName', 'N/A')}")
    else:
        print(f"   ⚠️  Unexpected response format")
    
    print("\n" + "=" * 60)
    print("Module test complete. Check results above.")
    print(f"API Key in use: {'demo' if API_KEY == 'demo' else 'custom (from env)'}")
