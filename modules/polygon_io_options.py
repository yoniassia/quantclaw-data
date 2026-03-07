#!/usr/bin/env python3
"""
Polygon.io Options API — Options Market Data Module

Comprehensive options data including chains, snapshots, aggregates, and contract details.
Covers:
- Options contract search and filtering
- Real-time options chain data
- Options market snapshots by underlying asset
- Historical options aggregates (OHLCV)
- Detailed contract specifications

Source: https://polygon.io/docs/options/getting-started
Category: Options Market Data
Free tier: True (5 calls/min with POLYGON_API_KEY)
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

# Polygon.io API Configuration
POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")


def _make_request(endpoint: str, params: Dict = None) -> Optional[Dict]:
    """
    Internal helper to make authenticated requests to Polygon.io API.
    
    Args:
        endpoint: API endpoint path (e.g., '/v3/reference/options/contracts')
        params: Query parameters dict
    
    Returns:
        JSON response dict or None on error
    """
    if params is None:
        params = {}
    
    # Add API key to params
    params['apiKey'] = POLYGON_API_KEY
    
    url = f"{POLYGON_BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Polygon.io API error: {e}")
        return None


def get_options_chain(
    symbol: str,
    expiration_date_gte: Optional[str] = None,
    expiration_date_lte: Optional[str] = None,
    limit: int = 250
) -> Optional[Dict]:
    """
    Get options chain for an underlying asset.
    
    Lists available options contracts for a given underlying symbol,
    optionally filtered by expiration date range.
    
    Args:
        symbol: Underlying asset ticker (e.g., 'AAPL')
        expiration_date_gte: Min expiration date (YYYY-MM-DD format)
        expiration_date_lte: Max expiration date (YYYY-MM-DD format)
        limit: Maximum number of contracts to return (default 250, max 1000)
    
    Returns:
        Dict with 'status', 'results' (list of contracts), 'next_url' for pagination
    
    Example:
        >>> chain = get_options_chain('AAPL', expiration_date_gte='2026-03-01')
        >>> if chain and chain.get('results'):
        >>>     print(f"Found {len(chain['results'])} contracts")
    """
    params = {
        'underlying_ticker': symbol,
        'limit': limit
    }
    
    if expiration_date_gte:
        params['expiration_date.gte'] = expiration_date_gte
    if expiration_date_lte:
        params['expiration_date.lte'] = expiration_date_lte
    
    return _make_request('/v3/reference/options/contracts', params)


def get_options_snapshot(symbol: str) -> Optional[Dict]:
    """
    Get real-time snapshot of all options contracts for an underlying asset.
    
    Returns live market data including last trade, bid/ask, Greeks, open interest,
    and volume for all available options contracts.
    
    Args:
        symbol: Underlying asset ticker (e.g., 'AAPL')
    
    Returns:
        Dict with 'status', 'results' containing snapshot data for all contracts
    
    Example:
        >>> snapshot = get_options_snapshot('AAPL')
        >>> if snapshot and snapshot.get('results'):
        >>>     for contract in snapshot['results']:
        >>>         print(f"{contract['details']['ticker']}: ${contract['last_quote']['bid']}")
    """
    return _make_request(f'/v3/snapshot/options/{symbol}')


def get_options_aggregates(
    options_ticker: str,
    from_date: str,
    to_date: str,
    multiplier: int = 1,
    timespan: str = 'day'
) -> Optional[Dict]:
    """
    Get historical aggregate bars (OHLCV) for an options contract.
    
    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00150000')
        from_date: Start date (YYYY-MM-DD format)
        to_date: End date (YYYY-MM-DD format)
        multiplier: Size of the timespan multiplier (default 1)
        timespan: Size of time window ('minute', 'hour', 'day', 'week', etc.)
    
    Returns:
        Dict with 'ticker', 'queryCount', 'results' (list of OHLCV bars)
    
    Example:
        >>> aggs = get_options_aggregates('O:AAPL250321C00150000', '2026-03-01', '2026-03-07')
        >>> if aggs and aggs.get('results'):
        >>>     for bar in aggs['results']:
        >>>         print(f"{bar['t']}: O={bar['o']} H={bar['h']} L={bar['l']} C={bar['c']} V={bar['v']}")
    """
    endpoint = f'/v2/aggs/ticker/{options_ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}'
    return _make_request(endpoint)


def get_contract_details(options_ticker: str) -> Optional[Dict]:
    """
    Get detailed specifications for a specific options contract.
    
    Returns comprehensive contract information including strike, expiration,
    contract type, underlying asset, exercise style, and contract size.
    
    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00150000')
    
    Returns:
        Dict with 'status', 'results' containing contract specification details
    
    Example:
        >>> details = get_contract_details('O:AAPL250321C00150000')
        >>> if details and details.get('results'):
        >>>     contract = details['results']
        >>>     print(f"Strike: ${contract['strike_price']}, Expiry: {contract['expiration_date']}")
    """
    return _make_request(f'/v3/reference/options/contracts/{options_ticker}')


def search_options_contracts(
    underlying_ticker: Optional[str] = None,
    expiration_date: Optional[str] = None,
    strike_price: Optional[float] = None,
    contract_type: Optional[str] = None,
    limit: int = 250
) -> Optional[Dict]:
    """
    Search and filter options contracts by multiple criteria.
    
    Flexible search function to find options contracts matching specific parameters.
    All filters are optional and can be combined.
    
    Args:
        underlying_ticker: Underlying asset symbol (e.g., 'AAPL')
        expiration_date: Specific expiration date (YYYY-MM-DD)
        strike_price: Specific strike price (e.g., 150.0)
        contract_type: 'call' or 'put'
        limit: Maximum number of results (default 250, max 1000)
    
    Returns:
        Dict with 'status', 'results' (list of matching contracts), 'next_url'
    
    Example:
        >>> # Find all AAPL $150 calls expiring 2026-03-21
        >>> contracts = search_options_contracts(
        >>>     underlying_ticker='AAPL',
        >>>     expiration_date='2026-03-21',
        >>>     strike_price=150.0,
        >>>     contract_type='call'
        >>> )
    """
    params = {'limit': limit}
    
    if underlying_ticker:
        params['underlying_ticker'] = underlying_ticker
    if expiration_date:
        params['expiration_date'] = expiration_date
    if strike_price is not None:
        params['strike_price'] = strike_price
    if contract_type:
        params['contract_type'] = contract_type
    
    return _make_request('/v3/reference/options/contracts', params)


# ========== CONVENIENCE FUNCTIONS ==========

def get_near_term_chain(symbol: str, days_ahead: int = 30) -> Optional[Dict]:
    """
    Get options chain for contracts expiring within the next N days.
    
    Convenience wrapper around get_options_chain for near-term options.
    
    Args:
        symbol: Underlying asset ticker
        days_ahead: Number of days forward to include (default 30)
    
    Returns:
        Options chain data for near-term contracts
    """
    from datetime import datetime, timedelta
    today = datetime.now().strftime('%Y-%m-%d')
    future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    return get_options_chain(
        symbol=symbol,
        expiration_date_gte=today,
        expiration_date_lte=future_date
    )


def get_atm_options(symbol: str, current_price: float, expiration_date: str) -> Dict[str, Optional[Dict]]:
    """
    Find at-the-money (ATM) call and put contracts for a given expiration.
    
    Args:
        symbol: Underlying asset ticker
        current_price: Current stock price to find ATM strike
        expiration_date: Target expiration date (YYYY-MM-DD)
    
    Returns:
        Dict with 'call' and 'put' keys containing ATM contract details
    """
    # Round to nearest strike (typically $5 or $10 intervals)
    atm_strike = round(current_price / 5) * 5
    
    call = search_options_contracts(
        underlying_ticker=symbol,
        expiration_date=expiration_date,
        strike_price=atm_strike,
        contract_type='call',
        limit=1
    )
    
    put = search_options_contracts(
        underlying_ticker=symbol,
        expiration_date=expiration_date,
        strike_price=atm_strike,
        contract_type='put',
        limit=1
    )
    
    return {
        'call': call,
        'put': put,
        'strike': atm_strike
    }


if __name__ == '__main__':
    """Test the module with AAPL options data."""
    print("Testing Polygon.io Options Module")
    print("=" * 50)
    
    # Test 1: Get options chain
    print("\n[1] Testing get_options_chain('AAPL')...")
    chain = get_options_chain('AAPL', limit=5)
    if chain:
        print(f"✓ Status: {chain.get('status')}")
        if chain.get('results'):
            print(f"✓ Found {len(chain['results'])} contracts (limited to 5)")
            print(f"  Sample ticker: {chain['results'][0].get('ticker')}")
    else:
        print("✗ Failed (likely missing API key or rate limit)")
    
    # Test 2: Get options snapshot
    print("\n[2] Testing get_options_snapshot('AAPL')...")
    snapshot = get_options_snapshot('AAPL')
    if snapshot:
        print(f"✓ Status: {snapshot.get('status')}")
        if snapshot.get('results'):
            print(f"✓ Snapshot contains {len(snapshot['results'])} contracts")
    else:
        print("✗ Failed (likely missing API key or rate limit)")
    
    # Test 3: Search contracts
    print("\n[3] Testing search_options_contracts(underlying_ticker='AAPL')...")
    search = search_options_contracts(underlying_ticker='AAPL', limit=3)
    if search:
        print(f"✓ Status: {search.get('status')}")
        if search.get('results'):
            print(f"✓ Found {len(search['results'])} contracts")
    else:
        print("✗ Failed (likely missing API key or rate limit)")
    
    # Test 4: Get near-term chain
    print("\n[4] Testing get_near_term_chain('AAPL', days_ahead=30)...")
    near_term = get_near_term_chain('AAPL', days_ahead=30)
    if near_term:
        print(f"✓ Status: {near_term.get('status')}")
        if near_term.get('results'):
            print(f"✓ Found {len(near_term['results'])} near-term contracts")
    else:
        print("✗ Failed (likely missing API key or rate limit)")
    
    print("\n" + "=" * 50)
    print("Module test complete!")
    print("\nNote: 403 errors are expected without POLYGON_API_KEY in .env")
    print("Free tier: 5 calls/min at https://polygon.io")
