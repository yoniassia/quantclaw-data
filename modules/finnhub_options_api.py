#!/usr/bin/env python3
"""
Finnhub Options API — Options Chain & Derivatives Data

Real-time and historical options chain data for US stocks, including calls and puts 
with pricing, volume, open interest, greeks, and IV. Supports quantitative analysis 
for volatility modeling, options flow analysis, and derivatives trading strategies.

Key capabilities:
- Full options chains with bid/ask spreads
- Expiration dates lookup
- Greeks and implied volatility
- Volume and open interest analysis
- Put/call ratio calculations

Source: https://finnhub.io/docs/api/stock-us-options
Category: Options & Derivatives
Free tier: False (requires premium subscription - options data not included in free tier)
Update frequency: Real-time (streaming available on premium)
Author: QuantClaw Data NightBuilder
Note: Free tier API keys will return 403 Forbidden. Premium subscription required for options access.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_option_chain(symbol: str, expiration: str = None) -> dict:
    """
    Get full options chain for a symbol with all strikes and expirations.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        expiration: Optional expiration date filter (YYYY-MM-DD format)
        
    Returns:
        dict: Full options chain data with calls and puts
        
    Example:
        >>> chain = get_option_chain('AAPL')
        >>> chain = get_option_chain('AAPL', '2026-04-17')
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/option-chain"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        if expiration:
            params['date'] = expiration
            
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'symbol': symbol.upper(),
            'timestamp': datetime.now().isoformat(),
            'expiration': expiration,
            'data': data
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': f"Unexpected error: {str(e)}",
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_expirations(symbol: str) -> list:
    """
    Get all available expiration dates for a symbol's options.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        list: Available expiration dates in YYYY-MM-DD format
        
    Example:
        >>> expirations = get_expirations('AAPL')
        >>> print(expirations[:5])  # First 5 expiration dates
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/option-chain/expiration"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Return the data list if it exists, otherwise empty list
        return data.get('data', []) if isinstance(data, dict) else data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching expirations for {symbol}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def get_calls(symbol: str, expiration: str = None) -> list:
    """
    Get only call options from the options chain.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        expiration: Optional expiration date filter (YYYY-MM-DD format)
        
    Returns:
        list: Call options data with strike, bid, ask, volume, OI, greeks
        
    Example:
        >>> calls = get_calls('AAPL', '2026-04-17')
        >>> print(f"Found {len(calls)} call contracts")
    """
    try:
        chain = get_option_chain(symbol, expiration)
        
        if 'error' in chain:
            return []
            
        data = chain.get('data', {})
        
        # Extract call options from the chain data
        if isinstance(data, dict) and 'data' in data:
            options = data['data']
            calls = [opt for opt in options if opt.get('type') == 'Call']
            return calls
        elif isinstance(data, list):
            calls = [opt for opt in data if opt.get('type') == 'Call']
            return calls
        
        return []
        
    except Exception as e:
        print(f"Error filtering calls for {symbol}: {e}")
        return []


def get_puts(symbol: str, expiration: str = None) -> list:
    """
    Get only put options from the options chain.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        expiration: Optional expiration date filter (YYYY-MM-DD format)
        
    Returns:
        list: Put options data with strike, bid, ask, volume, OI, greeks
        
    Example:
        >>> puts = get_puts('AAPL', '2026-04-17')
        >>> print(f"Found {len(puts)} put contracts")
    """
    try:
        chain = get_option_chain(symbol, expiration)
        
        if 'error' in chain:
            return []
            
        data = chain.get('data', {})
        
        # Extract put options from the chain data
        if isinstance(data, dict) and 'data' in data:
            options = data['data']
            puts = [opt for opt in options if opt.get('type') == 'Put']
            return puts
        elif isinstance(data, list):
            puts = [opt for opt in data if opt.get('type') == 'Put']
            return puts
        
        return []
        
    except Exception as e:
        print(f"Error filtering puts for {symbol}: {e}")
        return []


def get_option_summary(symbol: str) -> dict:
    """
    Get summary statistics for options activity.
    
    Calculates:
    - Total call/put volume
    - Put/call volume ratio
    - Total open interest
    - Number of contracts
    - Average implied volatility
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        dict: Summary statistics for the options chain
        
    Example:
        >>> summary = get_option_summary('AAPL')
        >>> print(f"P/C Ratio: {summary['put_call_ratio']:.2f}")
    """
    try:
        chain = get_option_chain(symbol)
        
        if 'error' in chain:
            return {'error': chain['error'], 'symbol': symbol}
            
        data = chain.get('data', {})
        
        # Extract options list
        if isinstance(data, dict) and 'data' in data:
            options = data['data']
        elif isinstance(data, list):
            options = data
        else:
            options = []
            
        if not options:
            return {
                'symbol': symbol,
                'error': 'No options data available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Calculate summary stats
        calls = [opt for opt in options if opt.get('type') == 'Call']
        puts = [opt for opt in options if opt.get('type') == 'Put']
        
        call_volume = sum(opt.get('volume', 0) for opt in calls)
        put_volume = sum(opt.get('volume', 0) for opt in puts)
        
        call_oi = sum(opt.get('openInterest', 0) for opt in calls)
        put_oi = sum(opt.get('openInterest', 0) for opt in puts)
        
        put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
        
        # Average IV (if available)
        ivs = [opt.get('impliedVolatility', 0) for opt in options if opt.get('impliedVolatility')]
        avg_iv = sum(ivs) / len(ivs) if ivs else 0
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'total_contracts': len(options),
            'calls_count': len(calls),
            'puts_count': len(puts),
            'call_volume': call_volume,
            'put_volume': put_volume,
            'total_volume': call_volume + put_volume,
            'put_call_ratio': round(put_call_ratio, 3),
            'call_open_interest': call_oi,
            'put_open_interest': put_oi,
            'total_open_interest': call_oi + put_oi,
            'avg_implied_volatility': round(avg_iv, 4) if avg_iv else None
        }
        
    except Exception as e:
        return {
            'error': f"Error calculating summary: {str(e)}",
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }


def get_most_active_options(symbol: str, limit: int = 10) -> list:
    """
    Get the most actively traded options by volume.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        limit: Maximum number of contracts to return (default: 10)
        
    Returns:
        list: Most active options sorted by volume (descending)
        
    Example:
        >>> active = get_most_active_options('AAPL', limit=5)
        >>> for opt in active:
        ...     print(f"{opt['type']} ${opt['strike']} - Volume: {opt['volume']}")
    """
    try:
        chain = get_option_chain(symbol)
        
        if 'error' in chain:
            return []
            
        data = chain.get('data', {})
        
        # Extract options list
        if isinstance(data, dict) and 'data' in data:
            options = data['data']
        elif isinstance(data, list):
            options = data
        else:
            options = []
            
        if not options:
            return []
        
        # Sort by volume (descending) and return top N
        sorted_options = sorted(
            options,
            key=lambda x: x.get('volume', 0),
            reverse=True
        )
        
        return sorted_options[:limit]
        
    except Exception as e:
        print(f"Error getting most active options for {symbol}: {e}")
        return []


# ========== CLI / Testing ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "module": "finnhub_options_api",
            "status": "ready",
            "source": "https://finnhub.io/docs/api/stock-us-options",
            "functions": [
                "get_option_chain",
                "get_expirations",
                "get_calls",
                "get_puts",
                "get_option_summary",
                "get_most_active_options"
            ]
        }, indent=2))
    else:
        symbol = sys.argv[1]
        
        # Test expirations
        print(f"\n=== Expirations for {symbol} ===")
        expirations = get_expirations(symbol)
        print(f"Found {len(expirations)} expiration dates")
        if expirations:
            print(f"Next 5: {expirations[:5]}")
        
        # Test summary
        print(f"\n=== Options Summary for {symbol} ===")
        summary = get_option_summary(symbol)
        print(json.dumps(summary, indent=2))
        
        # Test most active
        print(f"\n=== Most Active Options for {symbol} ===")
        active = get_most_active_options(symbol, limit=5)
        print(f"Found {len(active)} contracts")
        for i, opt in enumerate(active, 1):
            print(f"{i}. {opt.get('type')} ${opt.get('strike')} - Vol: {opt.get('volume', 0)}")
