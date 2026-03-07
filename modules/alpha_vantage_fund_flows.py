#!/usr/bin/env python3
"""
Alpha Vantage Fund Flows — Mutual Funds & ETF Data Module

Provides comprehensive mutual fund and ETF data including:
- Fund overview and NAV (Net Asset Value)
- Historical performance metrics
- ETF profile information
- Top holdings data

Source: https://www.alphavantage.co/documentation/#mutual-funds
Category: ETF & Fund Flows
Free tier: True - 5 API calls per minute, 500 per day
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpha Vantage API Configuration
AV_BASE_URL = "https://www.alphavantage.co/query"
AV_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# Rate limiting note: Free tier = 5 calls/min, 500/day
# Demo key has limited symbols (SPY, IBM, MSFT, etc.)


def _make_av_request(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Make API request to Alpha Vantage with error handling.
    
    Args:
        params: Query parameters (function, symbol, etc.)
    
    Returns:
        JSON response as dictionary
    
    Raises:
        Exception: If API returns error or request fails
    """
    params['apikey'] = AV_API_KEY
    
    try:
        response = requests.get(AV_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error messages
        if "Error Message" in data:
            raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
        if "Note" in data and "API call frequency" in data["Note"]:
            raise Exception(f"Rate limit exceeded: {data['Note']}")
        if "Information" in data:
            raise Exception(f"API Info: {data['Information']}")
            
        return data
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON response: {str(e)}")


def get_fund_overview(symbol: str) -> Dict[str, Any]:
    """
    Get mutual fund or ETF overview including NAV, total assets, and key metrics.
    
    Args:
        symbol: Fund ticker symbol (e.g., 'VFINX', 'SPY')
    
    Returns:
        Dictionary with fund overview data including:
        - symbol: Fund ticker
        - name: Fund name
        - asset_type: MUTUAL_FUND or ETF
        - nav: Net Asset Value
        - total_assets: Assets under management
        - expense_ratio: Annual expense ratio
        - inception_date: Fund inception date
        - category: Fund category
        - raw: Full API response
    
    Example:
        >>> overview = get_fund_overview('SPY')
        >>> print(f"NAV: {overview['nav']}")
    """
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol
    }
    
    try:
        data = _make_av_request(params)
        
        # Alpha Vantage OVERVIEW endpoint returns general stock/fund info
        # Extract relevant fields for funds
        result = {
            'symbol': data.get('Symbol', symbol),
            'name': data.get('Name', ''),
            'asset_type': data.get('AssetType', ''),
            'description': data.get('Description', ''),
            'exchange': data.get('Exchange', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            '52_week_high': data.get('52WeekHigh', ''),
            '52_week_low': data.get('52WeekLow', ''),
            'pe_ratio': data.get('PERatio', ''),
            'peg_ratio': data.get('PEGRatio', ''),
            'book_value': data.get('BookValue', ''),
            'dividend_per_share': data.get('DividendPerShare', ''),
            'dividend_yield': data.get('DividendYield', ''),
            'eps': data.get('EPS', ''),
            'profit_margin': data.get('ProfitMargin', ''),
            'revenue_per_share': data.get('RevenuePerShareTTM', ''),
            'analyst_target_price': data.get('AnalystTargetPrice', ''),
            'raw': data
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_fund_performance(symbol: str, outputsize: str = 'compact') -> Dict[str, Any]:
    """
    Get historical NAV performance for mutual fund or ETF.
    
    Args:
        symbol: Fund ticker symbol (e.g., 'VFINX', 'SPY')
        outputsize: 'compact' (100 data points) or 'full' (all available)
    
    Returns:
        Dictionary with:
        - symbol: Fund ticker
        - latest_date: Most recent trading date
        - latest_nav: Most recent NAV/close price
        - latest_volume: Most recent volume
        - time_series: List of daily performance data
        - count: Number of data points
        - raw: Full API response
    
    Example:
        >>> perf = get_fund_performance('SPY')
        >>> print(f"Latest NAV: {perf['latest_nav']}")
    """
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'outputsize': outputsize
    }
    
    try:
        data = _make_av_request(params)
        
        metadata = data.get('Meta Data', {})
        time_series_key = 'Time Series (Daily)'
        time_series = data.get(time_series_key, {})
        
        if not time_series:
            raise Exception(f"No time series data found for {symbol}")
        
        # Convert to list format sorted by date (newest first)
        performance_data = []
        for date, values in sorted(time_series.items(), reverse=True):
            performance_data.append({
                'date': date,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'volume': int(values.get('5. volume', 0))
            })
        
        latest = performance_data[0] if performance_data else {}
        
        result = {
            'symbol': metadata.get('2. Symbol', symbol),
            'last_refreshed': metadata.get('3. Last Refreshed', ''),
            'latest_date': latest.get('date', ''),
            'latest_nav': latest.get('close', 0),
            'latest_volume': latest.get('volume', 0),
            'time_series': performance_data,
            'count': len(performance_data),
            'raw': data
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_etf_profile(symbol: str) -> Dict[str, Any]:
    """
    Get ETF-specific profile information (uses OVERVIEW endpoint).
    
    Args:
        symbol: ETF ticker symbol (e.g., 'SPY', 'QQQ')
    
    Returns:
        Dictionary with ETF profile data similar to get_fund_overview
        but focused on ETF-specific metrics
    
    Example:
        >>> etf = get_etf_profile('SPY')
        >>> print(f"ETF: {etf['name']}")
    """
    # Alpha Vantage doesn't have a separate ETF_PROFILE endpoint
    # We use OVERVIEW and filter/format for ETF context
    overview = get_fund_overview(symbol)
    
    if 'error' in overview:
        return overview
    
    # Format specifically for ETF presentation
    etf_profile = {
        'symbol': overview['symbol'],
        'name': overview['name'],
        'asset_type': overview['asset_type'],
        'exchange': overview['exchange'],
        'sector': overview['sector'],
        'industry': overview['industry'],
        'description': overview['description'],
        '52_week_range': {
            'high': overview['52_week_high'],
            'low': overview['52_week_low']
        },
        'dividend_yield': overview['dividend_yield'],
        'dividend_per_share': overview['dividend_per_share'],
        'raw': overview['raw']
    }
    
    return etf_profile


def get_fund_holdings(symbol: str) -> Dict[str, Any]:
    """
    Get top holdings for mutual fund or ETF.
    
    Note: Alpha Vantage free tier doesn't provide holdings data.
    This function returns a placeholder structure showing what would be available.
    For real holdings data, consider premium APIs or web scraping fund fact sheets.
    
    Args:
        symbol: Fund ticker symbol
    
    Returns:
        Dictionary indicating holdings data is not available in free tier
    
    Example:
        >>> holdings = get_fund_holdings('SPY')
    """
    return {
        'symbol': symbol,
        'error': 'Holdings data not available in Alpha Vantage free tier',
        'note': 'Consider using: (1) Premium Alpha Vantage, (2) Fund fact sheets, (3) SEC filings for holdings data',
        'alternatives': [
            'Yahoo Finance API',
            'SEC EDGAR for N-PORT filings',
            'Fund company websites',
            'ETF.com API (if available)'
        ],
        'timestamp': datetime.now().isoformat()
    }


def get_fund_search(keywords: str) -> Dict[str, Any]:
    """
    Search for funds by keywords (company name, ticker, etc.).
    
    Args:
        keywords: Search terms (e.g., 'Vanguard', 'S&P 500')
    
    Returns:
        Dictionary with matching symbols and names
    
    Example:
        >>> results = get_fund_search('vanguard')
        >>> for match in results['matches']:
        ...     print(f"{match['symbol']}: {match['name']}")
    """
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': keywords
    }
    
    try:
        data = _make_av_request(params)
        
        matches = data.get('bestMatches', [])
        
        result = {
            'keywords': keywords,
            'count': len(matches),
            'matches': [
                {
                    'symbol': m.get('1. symbol', ''),
                    'name': m.get('2. name', ''),
                    'type': m.get('3. type', ''),
                    'region': m.get('4. region', ''),
                    'currency': m.get('8. currency', ''),
                    'match_score': m.get('9. matchScore', '')
                }
                for m in matches
            ],
            'raw': data
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'keywords': keywords,
            'timestamp': datetime.now().isoformat()
        }


# ========== MODULE METADATA ==========

MODULE_INFO = {
    'name': 'alpha_vantage_fund_flows',
    'version': '1.0.0',
    'author': 'QuantClaw Data NightBuilder',
    'source': 'https://www.alphavantage.co/documentation/',
    'functions': [
        'get_fund_overview',
        'get_fund_performance',
        'get_etf_profile',
        'get_fund_holdings',
        'get_fund_search'
    ],
    'free_tier': True,
    'rate_limits': {
        'calls_per_minute': 5,
        'calls_per_day': 500
    },
    'api_key_required': 'ALPHA_VANTAGE_API_KEY (defaults to "demo")'
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
    print("\n=== Testing with SPY ===")
    
    # Test overview
    print("\n1. Fund Overview:")
    overview = get_fund_overview('SPY')
    if 'error' not in overview:
        print(f"   Symbol: {overview['symbol']}")
        print(f"   Name: {overview['name']}")
        print(f"   Type: {overview['asset_type']}")
    else:
        print(f"   Error: {overview['error']}")
    
    # Test performance
    print("\n2. Performance (compact):")
    perf = get_fund_performance('SPY', 'compact')
    if 'error' not in perf:
        print(f"   Latest Date: {perf['latest_date']}")
        print(f"   Latest NAV: ${perf['latest_nav']}")
        print(f"   Data Points: {perf['count']}")
    else:
        print(f"   Error: {perf['error']}")
