#!/usr/bin/env python3
"""
Alpha Vantage API — Emerging Markets Extended Module

Complementary module to alpha_vantage_emerging_markets_api.py with focus on:
- Daily historical FX data for EM currencies
- Market movers (top gainers/losers) across global markets
- Global market status (open/close times for all exchanges)
- Weekly/monthly time series for EM stocks

Source: https://www.alphavantage.co/documentation/
Category: Emerging Markets (Extended)
Free tier: True (5 calls/min, 500 calls/day - requires ALPHA_VANTAGE_API_KEY)
Author: QuantClaw Data NightBuilder
Phase: 107
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

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")


def get_em_forex_daily(from_symbol: str = 'INR', to_symbol: str = 'USD', outputsize: str = 'compact') -> List[Dict]:
    """
    Get daily historical forex exchange rates for emerging market currencies.
    
    Args:
        from_symbol: Source currency code (e.g., 'INR', 'BRL', 'ZAR', 'TRY', 'MXN')
        to_symbol: Target currency code (e.g., 'USD', 'EUR', 'GBP')
        outputsize: 'compact' (100 days) or 'full' (20+ years)
    
    Returns:
        List of Dict with keys: date, open, high, low, close
    
    Example:
        >>> fx_history = get_em_forex_daily('INR', 'USD', 'compact')
        >>> print(f"Latest: {fx_history[0]['date']} @ {fx_history[0]['close']}")
    """
    try:
        params = {
            'function': 'FX_DAILY',
            'from_symbol': from_symbol,
            'to_symbol': to_symbol,
            'outputsize': outputsize,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'from_symbol': from_symbol, 'to_symbol': to_symbol}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note']}]
        
        # Parse time series
        time_series = data.get('Time Series FX (Daily)', {})
        if not time_series:
            return [{'error': 'No data returned', 'from_symbol': from_symbol, 'to_symbol': to_symbol}]
        
        result = []
        for date_str, values in sorted(time_series.items(), reverse=True):
            result.append({
                'date': date_str,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'from_symbol': from_symbol,
                'to_symbol': to_symbol
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'from_symbol': from_symbol, 'to_symbol': to_symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'from_symbol': from_symbol, 'to_symbol': to_symbol}]


def get_em_market_movers(market: str = 'india') -> Dict:
    """
    Get top gaining, losing, and most actively traded stocks globally.
    
    Note: Alpha Vantage's TOP_GAINERS_LOSERS endpoint returns global data.
    Filter by market parameter is applied post-fetch based on symbol suffixes.
    
    Args:
        market: Market filter ('india', 'brazil', 'china', 'global', or 'all')
    
    Returns:
        Dict with keys: top_gainers, top_losers, most_actively_traded, timestamp
    
    Example:
        >>> movers = get_em_market_movers('india')
        >>> print(f"Top gainer: {movers['top_gainers'][0]['ticker']}")
    """
    try:
        params = {
            'function': 'TOP_GAINERS_LOSERS',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'market': market}
        if 'Note' in data:
            return {'error': 'Rate limit exceeded', 'note': data['Note'], 'market': market}
        
        # Market suffix mappings for filtering
        market_suffixes = {
            'india': ['.BSE', '.NSE', '.BO', '.NS'],
            'brazil': ['.SAO', '.SA'],
            'china': ['.SHZ', '.SHH', '.SS', '.SZ'],
            'south_africa': ['.JNB', '.JO'],
            'mexico': ['.MEX', '.MX'],
            'global': [],  # No filtering
            'all': []  # No filtering
        }
        
        suffixes = market_suffixes.get(market.lower(), [])
        
        def filter_by_market(stocks: List[Dict]) -> List[Dict]:
            """Filter stocks by market suffix or return all if global/all"""
            if not suffixes:  # global or all
                return stocks
            return [s for s in stocks if any(s.get('ticker', '').endswith(suffix) for suffix in suffixes)]
        
        # Parse market movers
        top_gainers = data.get('top_gainers', [])
        top_losers = data.get('top_losers', [])
        most_active = data.get('most_actively_traded', [])
        
        result = {
            'market': market,
            'top_gainers': filter_by_market(top_gainers),
            'top_losers': filter_by_market(top_losers),
            'most_actively_traded': filter_by_market(most_active),
            'timestamp': datetime.utcnow().isoformat(),
            'unfiltered_counts': {
                'gainers': len(top_gainers),
                'losers': len(top_losers),
                'active': len(most_active)
            }
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}', 'market': market}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'market': market}


def get_global_market_status() -> Dict:
    """
    Get real-time status of global stock exchanges (open/closed).
    
    Returns market status for major exchanges worldwide including:
    - US markets (NYSE, NASDAQ)
    - European markets (LSE, XETRA, Euronext)
    - Asian markets (Tokyo, Hong Kong, Shanghai, Mumbai)
    - Emerging markets (BSE, NSE, B3, JSE)
    
    Returns:
        Dict with keys: markets (list), timestamp, summary
    
    Example:
        >>> status = get_global_market_status()
        >>> for market in status['markets']:
        >>>     print(f"{market['region']}: {market['current_status']}")
    """
    try:
        params = {
            'function': 'MARKET_STATUS',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return {'error': data['Error Message']}
        if 'Note' in data:
            return {'error': 'Rate limit exceeded', 'note': data['Note']}
        
        # Parse market status
        markets_raw = data.get('markets', [])
        if not markets_raw:
            return {'error': 'No market data returned'}
        
        # Organize by region and add emerging markets flag
        em_regions = ['India', 'Brazil', 'China', 'South Africa', 'Mexico', 'Turkey', 'Indonesia']
        
        markets = []
        for market in markets_raw:
            market_info = {
                'region': market.get('region', ''),
                'primary_exchanges': market.get('primary_exchanges', ''),
                'local_open': market.get('local_open', ''),
                'local_close': market.get('local_close', ''),
                'current_status': market.get('current_status', ''),
                'notes': market.get('notes', ''),
                'is_emerging_market': any(em in market.get('region', '') for em in em_regions)
            }
            markets.append(market_info)
        
        # Generate summary
        open_count = sum(1 for m in markets if m['current_status'] == 'open')
        closed_count = sum(1 for m in markets if m['current_status'] == 'closed')
        em_open = sum(1 for m in markets if m['is_emerging_market'] and m['current_status'] == 'open')
        
        result = {
            'markets': markets,
            'summary': {
                'total_markets': len(markets),
                'open': open_count,
                'closed': closed_count,
                'emerging_markets_open': em_open
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_em_weekly(symbol: str = 'RELIANCE.BSE') -> List[Dict]:
    """
    Get weekly OHLCV data for emerging market stocks.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'RELIANCE.BSE', 'VALE.SAO')
    
    Returns:
        List of Dict with keys: date, open, high, low, close, volume
    
    Example:
        >>> weekly = get_em_weekly('TCS.BSE')
        >>> print(f"Latest week: {weekly[0]['date']} close @ {weekly[0]['close']}")
    """
    try:
        params = {
            'function': 'TIME_SERIES_WEEKLY',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'symbol': symbol}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note']}]
        
        # Parse time series
        time_series = data.get('Weekly Time Series', {})
        if not time_series:
            return [{'error': 'No data returned', 'symbol': symbol}]
        
        result = []
        for date_str, values in sorted(time_series.items(), reverse=True)[:52]:  # Last year
            result.append({
                'date': date_str,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'volume': int(values.get('5. volume', 0)),
                'symbol': symbol
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'symbol': symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'symbol': symbol}]


def get_em_monthly(symbol: str = 'RELIANCE.BSE') -> List[Dict]:
    """
    Get monthly OHLCV data for emerging market stocks.
    
    Args:
        symbol: Stock ticker with exchange suffix
    
    Returns:
        List of Dict with keys: date, open, high, low, close, volume
    
    Example:
        >>> monthly = get_em_monthly('RELIANCE.BSE')
        >>> print(f"Latest month: {monthly[0]['date']} @ {monthly[0]['close']}")
    """
    try:
        params = {
            'function': 'TIME_SERIES_MONTHLY',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return [{'error': data['Error Message'], 'symbol': symbol}]
        if 'Note' in data:
            return [{'error': 'Rate limit exceeded', 'note': data['Note']}]
        
        # Parse time series
        time_series = data.get('Monthly Time Series', {})
        if not time_series:
            return [{'error': 'No data returned', 'symbol': symbol}]
        
        result = []
        for date_str, values in sorted(time_series.items(), reverse=True)[:24]:  # Last 2 years
            result.append({
                'date': date_str,
                'open': float(values.get('1. open', 0)),
                'high': float(values.get('2. high', 0)),
                'low': float(values.get('3. low', 0)),
                'close': float(values.get('4. close', 0)),
                'volume': int(values.get('5. volume', 0)),
                'symbol': symbol
            })
        
        return result
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}', 'symbol': symbol}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}', 'symbol': symbol}]


def get_em_stock_quote(symbol: str = 'RELIANCE.BSE') -> Dict:
    """
    Get real-time quote for an emerging market stock.
    Alias to main emerging_markets module for convenience.
    
    Args:
        symbol: Stock ticker with exchange suffix (e.g., 'RELIANCE.BSE', 'TCS.BSE')
    
    Returns:
        Dict with keys: symbol, price, volume, timestamp, change, change_percent
    """
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            return {'error': data['Error Message'], 'symbol': symbol}
        if 'Note' in data:
            return {'error': 'Rate limit exceeded', 'note': data['Note']}
        
        quote_data = data.get('Global Quote', {})
        if not quote_data:
            return {'error': 'No data returned', 'symbol': symbol}
        
        return {
            'symbol': quote_data.get('01. symbol', symbol),
            'price': float(quote_data.get('05. price', 0)),
            'volume': int(quote_data.get('06. volume', 0)),
            'latest_trading_day': quote_data.get('07. latest trading day'),
            'previous_close': float(quote_data.get('08. previous close', 0)),
            'change': float(quote_data.get('09. change', 0)),
            'change_percent': quote_data.get('10. change percent', '0%'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("Alpha Vantage API - Emerging Markets Extended Module")
    print("=" * 70)
    
    functions_info = {
        "module": "alpha_vantage_api",
        "status": "active",
        "phase": 107,
        "functions": [
            {
                "name": "get_em_forex_daily",
                "description": "Daily historical FX rates for EM currencies",
                "example": "get_em_forex_daily('INR', 'USD')"
            },
            {
                "name": "get_em_market_movers",
                "description": "Top gainers/losers/active stocks globally or by market",
                "example": "get_em_market_movers('india')"
            },
            {
                "name": "get_global_market_status",
                "description": "Real-time open/closed status of global exchanges",
                "example": "get_global_market_status()"
            },
            {
                "name": "get_em_weekly",
                "description": "Weekly OHLCV for EM stocks",
                "example": "get_em_weekly('RELIANCE.BSE')"
            },
            {
                "name": "get_em_monthly",
                "description": "Monthly OHLCV for EM stocks",
                "example": "get_em_monthly('RELIANCE.BSE')"
            },
            {
                "name": "get_em_stock_quote",
                "description": "Real-time quote (alias for convenience)",
                "example": "get_em_stock_quote('RELIANCE.BSE')"
            }
        ],
        "complementary_to": "alpha_vantage_emerging_markets_api.py",
        "source": "https://www.alphavantage.co/documentation/",
        "free_tier": "5 calls/min, 500 calls/day"
    }
    
    print(json.dumps(functions_info, indent=2))
