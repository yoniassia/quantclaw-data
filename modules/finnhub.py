#!/usr/bin/env python3
"""
Finnhub API — Market Microstructure & Real-Time Data Module

Core Finnhub integration for market microstructure data including:
- Real-time quotes and order book depth
- Market status and exchange information
- Stock candles (OHLCV)
- Company profiles and peers
- Symbol search

Source: https://finnhub.io/api/v1/
Category: Exchanges & Market Microstructure
Free tier: True (requires FINNHUB_API_KEY env var)
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


def get_quote(symbol: str = 'AAPL') -> Dict:
    """
    Get real-time quote data for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with keys: c (current price), h (high), l (low), o (open), 
                       pc (previous close), t (timestamp)
    
    Example:
        >>> quote = get_quote('AAPL')
        >>> print(f"Current: ${quote['c']}, High: ${quote['h']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['symbol'] = symbol.upper()
        data['timestamp_dt'] = datetime.fromtimestamp(data.get('t', 0)).isoformat() if data.get('t') else None
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_order_book(symbol: str = 'AAPL', exchange: str = 'US') -> Dict:
    """
    Get level 2 order book data (bid/ask with depth).
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        exchange: Exchange code (default: 'US')
    
    Returns:
        Dict with bid/ask arrays containing price and volume
    
    Example:
        >>> book = get_order_book('AAPL')
        >>> print(f"Best bid: ${book['bid'][0][0]}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/bidask"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['symbol'] = symbol.upper()
        data['exchange'] = exchange
        data['timestamp'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_market_status(exchange: str = 'US') -> Dict:
    """
    Get market open/close status for an exchange.
    
    Args:
        exchange: Exchange code (default: 'US')
    
    Returns:
        Dict with exchange, holiday, isOpen, session, timezone
    
    Example:
        >>> status = get_market_status('US')
        >>> print(f"Market open: {status['isOpen']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/market-status"
        params = {
            'exchange': exchange,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['exchange'] = exchange
        data['checked_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'exchange': exchange}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'exchange': exchange}


def get_stock_candles(symbol: str = 'AAPL', resolution: str = 'D', 
                     from_ts: Optional[int] = None, to_ts: Optional[int] = None) -> Dict:
    """
    Get OHLCV candlestick data for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        resolution: Candle resolution - 1, 5, 15, 30, 60, D, W, M (default: 'D')
        from_ts: Start timestamp (Unix seconds) - defaults to 30 days ago
        to_ts: End timestamp (Unix seconds) - defaults to now
    
    Returns:
        Dict with arrays: c (close), h (high), l (low), o (open), t (time), v (volume), s (status)
    
    Example:
        >>> candles = get_stock_candles('AAPL', 'D')
        >>> print(f"Latest close: ${candles['c'][-1]}")
    """
    try:
        # Default time range: last 30 days
        if to_ts is None:
            to_ts = int(datetime.now().timestamp())
        if from_ts is None:
            from_ts = int((datetime.now().timestamp() - (30 * 24 * 60 * 60)))
        
        url = f"{FINNHUB_BASE_URL}/stock/candle"
        params = {
            'symbol': symbol.upper(),
            'resolution': resolution,
            'from': from_ts,
            'to': to_ts,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['symbol'] = symbol.upper()
        data['resolution'] = resolution
        data['from_dt'] = datetime.fromtimestamp(from_ts).isoformat()
        data['to_dt'] = datetime.fromtimestamp(to_ts).isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_company_profile(symbol: str = 'AAPL') -> Dict:
    """
    Get company profile information.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with company data: name, ticker, exchange, ipo, marketCap, 
                               shareOutstanding, logo, phone, weburl, etc.
    
    Example:
        >>> profile = get_company_profile('AAPL')
        >>> print(f"{profile['name']} - {profile['exchange']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        if data:
            data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def search_symbol(query: str = 'apple') -> Dict:
    """
    Search for symbols by company name or ticker.
    
    Args:
        query: Search query string (default: 'apple')
    
    Returns:
        Dict with 'result' key containing array of matches with:
        description, displaySymbol, symbol, type
    
    Example:
        >>> results = search_symbol('apple')
        >>> for match in results['result'][:3]:
        ...     print(f"{match['symbol']}: {match['description']}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/search"
        params = {
            'q': query,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['query'] = query
        data['count'] = len(data.get('result', []))
        data['searched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'query': query}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'query': query}


def get_peers(symbol: str = 'AAPL') -> List[str]:
    """
    Get related/peer companies for a symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        List of peer ticker symbols
    
    Example:
        >>> peers = get_peers('AAPL')
        >>> print(f"Peers: {', '.join(peers[:5])}")
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/peers"
        params = {
            'symbol': symbol.upper(),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data if isinstance(data, list) else []
        
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "quote" and len(sys.argv) > 2:
            result = get_quote(sys.argv[2])
        elif command == "profile" and len(sys.argv) > 2:
            result = get_company_profile(sys.argv[2])
        elif command == "search" and len(sys.argv) > 2:
            result = search_symbol(sys.argv[2])
        elif command == "peers" and len(sys.argv) > 2:
            result = get_peers(sys.argv[2])
        elif command == "status":
            result = get_market_status()
        else:
            result = {
                "module": "finnhub",
                "version": "1.0",
                "usage": "python finnhub.py [quote|profile|search|peers|status] <symbol>",
                "functions": [
                    "get_quote(symbol)",
                    "get_order_book(symbol, exchange)",
                    "get_market_status(exchange)",
                    "get_stock_candles(symbol, resolution, from_ts, to_ts)",
                    "get_company_profile(symbol)",
                    "search_symbol(query)",
                    "get_peers(symbol)"
                ]
            }
    else:
        result = {
            "module": "finnhub",
            "status": "ready",
            "api_key_set": bool(FINNHUB_API_KEY),
            "functions": 7
        }
    
    print(json.dumps(result, indent=2))
