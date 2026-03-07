#!/usr/bin/env python3
"""
SEC Market Structure Data API

Market structure analytics from U.S. equity markets including:
- Off-exchange trading volumes
- Order type distributions (market, limit, marketable)
- Hidden vs displayed order rates
- Cancelled order rates
- Market share by venue type

Source: https://www.sec.gov/marketstructure/datavisual.html
Category: Government & Regulatory
Free tier: True (no API key needed)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# SEC Configuration
SEC_BASE_URL = "https://www.sec.gov/files/dera/data/market-structure-statistics"
REQUEST_DELAY = 0.5  # SEC requires respectful rate limiting

# ========== DATA ENDPOINTS REGISTRY ==========

SEC_ENDPOINTS = {
    'OFF_EXCHANGE_VOLUME': 'monthly-all-off-exchange-trade-volume.csv',
    'ATS_TRADE_VOLUME': 'monthly-ats-trade-volume-by-symbol.csv',
    'ORDER_TYPES': 'monthly-order-type-by-symbol.csv',
    'HIDDEN_RATE': 'monthly-hidden-rate-by-symbol.csv',
    'CANCELLED_RATE': 'monthly-cancelled-rate-by-symbol.csv',
    'MARKETABLE_LIMIT': 'monthly-marketable-limit-order-rate-by-symbol.csv',
}

# Venue categories
VENUE_TYPES = [
    'ATS',           # Alternative Trading Systems
    'OTC',           # Over-the-counter
    'Exchange',      # Traditional exchanges
    'Single_Dealer', # Single dealer platforms
]

# Order types
ORDER_TYPES = [
    'Market',
    'Marketable_Limit',
    'Non_Marketable_Limit',
    'At_Opening',
    'At_Closing',
]


def _fetch_sec_data(endpoint: str, params: Optional[Dict] = None) -> str:
    """
    Fetch raw data from SEC with rate limiting and error handling.
    
    Args:
        endpoint: Endpoint path or full URL
        params: Optional query parameters
    
    Returns:
        Raw response text (CSV or JSON)
    
    Raises:
        Exception: On HTTP errors or rate limiting
    """
    # Respect SEC rate limits
    time.sleep(REQUEST_DELAY)
    
    # Build URL
    if endpoint.startswith('http'):
        url = endpoint
    else:
        url = f"{SEC_BASE_URL}/{endpoint}"
    
    headers = {
        'User-Agent': 'QuantClaw/1.0 (Research; Python)',
        'Accept': 'text/csv,application/json,*/*',
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 403:
            raise Exception("SEC rate limit exceeded. Try again later or use a different IP.")
        
        response.raise_for_status()
        return response.text
        
    except requests.RequestException as e:
        raise Exception(f"SEC data fetch failed: {str(e)}")


def _parse_csv_to_dicts(csv_text: str) -> List[Dict]:
    """Parse CSV text to list of dictionaries."""
    lines = csv_text.strip().split('\n')
    if len(lines) < 2:
        return []
    
    headers = [h.strip() for h in lines[0].split(',')]
    data = []
    
    for line in lines[1:]:
        values = [v.strip() for v in line.split(',')]
        if len(values) == len(headers):
            data.append(dict(zip(headers, values)))
    
    return data


def get_market_metrics(date: Optional[str] = None) -> Dict:
    """
    Get comprehensive market structure metrics.
    
    Args:
        date: Optional date string (YYYY-MM). Defaults to latest available.
    
    Returns:
        Dict with market metrics including volume, venues, order types
    """
    try:
        # Fetch off-exchange volume (primary metric)
        data_text = _fetch_sec_data(SEC_ENDPOINTS['OFF_EXCHANGE_VOLUME'])
        records = _parse_csv_to_dicts(data_text)
        
        if not records:
            return {
                'error': 'No data available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Get latest or specified date
        if date:
            records = [r for r in records if r.get('Date', '').startswith(date)]
        
        latest = records[-1] if records else {}
        
        return {
            'date': latest.get('Date', 'N/A'),
            'off_exchange_volume': latest.get('Total_Off_Exchange_Volume', 'N/A'),
            'on_exchange_volume': latest.get('Total_On_Exchange_Volume', 'N/A'),
            'total_volume': latest.get('Total_Market_Volume', 'N/A'),
            'off_exchange_pct': latest.get('Off_Exchange_Percent', 'N/A'),
            'data_points': len(records),
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_order_types(symbol: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Get order type distribution (market, limit, marketable limit, etc.).
    
    Args:
        symbol: Optional stock symbol filter
        limit: Number of recent records to return
    
    Returns:
        Dict with order type breakdown by symbol
    """
    try:
        data_text = _fetch_sec_data(SEC_ENDPOINTS['ORDER_TYPES'])
        records = _parse_csv_to_dicts(data_text)
        
        if not records:
            return {
                'error': 'No order type data available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Filter by symbol if provided
        if symbol:
            records = [r for r in records if r.get('Symbol', '').upper() == symbol.upper()]
        
        # Get most recent records
        records = records[-limit:] if len(records) > limit else records
        
        return {
            'symbol': symbol if symbol else 'all',
            'records': records,
            'count': len(records),
            'order_types': ORDER_TYPES,
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_execution_quality(symbol: Optional[str] = None) -> Dict:
    """
    Get execution quality metrics including hidden/displayed rates.
    Combines hidden rate and marketable limit order data.
    
    Args:
        symbol: Optional stock symbol filter
    
    Returns:
        Dict with execution quality metrics
    """
    try:
        # Fetch hidden rate data
        hidden_text = _fetch_sec_data(SEC_ENDPOINTS['HIDDEN_RATE'])
        hidden_records = _parse_csv_to_dicts(hidden_text)
        
        # Fetch marketable limit data
        time.sleep(REQUEST_DELAY)
        marketable_text = _fetch_sec_data(SEC_ENDPOINTS['MARKETABLE_LIMIT'])
        marketable_records = _parse_csv_to_dicts(marketable_text)
        
        result = {
            'symbol': symbol if symbol else 'all',
            'hidden_rate_records': len(hidden_records),
            'marketable_limit_records': len(marketable_records),
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
        # Filter by symbol if provided
        if symbol:
            hidden_records = [r for r in hidden_records if r.get('Symbol', '').upper() == symbol.upper()]
            marketable_records = [r for r in marketable_records if r.get('Symbol', '').upper() == symbol.upper()]
        
        if hidden_records:
            result['latest_hidden'] = hidden_records[-1]
        
        if marketable_records:
            result['latest_marketable'] = marketable_records[-1]
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_hidden_rate(symbol: str, limit: int = 12) -> Dict:
    """
    Get hidden order rate for a symbol (orders not displayed in book).
    
    Args:
        symbol: Stock symbol
        limit: Number of months to return
    
    Returns:
        Dict with hidden rate time series
    """
    try:
        data_text = _fetch_sec_data(SEC_ENDPOINTS['HIDDEN_RATE'])
        records = _parse_csv_to_dicts(data_text)
        
        # Filter by symbol
        records = [r for r in records if r.get('Symbol', '').upper() == symbol.upper()]
        records = records[-limit:] if len(records) > limit else records
        
        if not records:
            return {
                'error': f'No hidden rate data for {symbol}',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'symbol': symbol,
            'records': records,
            'count': len(records),
            'latest': records[-1] if records else None,
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_cancelled_rate(symbol: str, limit: int = 12) -> Dict:
    """
    Get cancelled order rate for a symbol.
    
    Args:
        symbol: Stock symbol
        limit: Number of months to return
    
    Returns:
        Dict with cancelled rate time series
    """
    try:
        data_text = _fetch_sec_data(SEC_ENDPOINTS['CANCELLED_RATE'])
        records = _parse_csv_to_dicts(data_text)
        
        # Filter by symbol
        records = [r for r in records if r.get('Symbol', '').upper() == symbol.upper()]
        records = records[-limit:] if len(records) > limit else records
        
        if not records:
            return {
                'error': f'No cancelled rate data for {symbol}',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'symbol': symbol,
            'records': records,
            'count': len(records),
            'latest': records[-1] if records else None,
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_ats_volume(limit: int = 50) -> Dict:
    """
    Get Alternative Trading System (ATS) volume data.
    
    Args:
        limit: Number of recent records
    
    Returns:
        Dict with ATS volume breakdown
    """
    try:
        data_text = _fetch_sec_data(SEC_ENDPOINTS['ATS_TRADE_VOLUME'])
        records = _parse_csv_to_dicts(data_text)
        
        records = records[-limit:] if len(records) > limit else records
        
        return {
            'records': records,
            'count': len(records),
            'timestamp': datetime.now().isoformat(),
            'source': 'SEC Market Structure Statistics'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def demo() -> None:
    """Run demo queries to test module functionality."""
    print("=" * 60)
    print("SEC Market Structure Data API - Demo")
    print("=" * 60)
    print()
    
    # Test 1: Market metrics
    print("1. Market Metrics (Overall Market Structure):")
    print("-" * 60)
    metrics = get_market_metrics()
    print(json.dumps(metrics, indent=2))
    print()
    
    # Test 2: Order types for AAPL
    print("2. Order Types (AAPL - last 5 records):")
    print("-" * 60)
    order_types = get_order_types(symbol='AAPL', limit=5)
    print(json.dumps(order_types, indent=2))
    print()
    
    # Test 3: Hidden rate for TSLA
    print("3. Hidden Rate (TSLA - last 6 months):")
    print("-" * 60)
    hidden = get_hidden_rate(symbol='TSLA', limit=6)
    print(json.dumps(hidden, indent=2))
    print()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
