#!/usr/bin/env python3
"""
Finnhub Emerging Markets API — Real-time EM Stock Data

Specialized module for emerging market stocks from Finnhub.
Coverage includes:
- India: NSE (National Stock Exchange), BSE (Bombay Stock Exchange)
- China: SSE (Shanghai), SZSE (Shenzhen)
- Brazil: B3 (B3 - Brasil Bolsa Balcão)

Provides real-time quotes, company profiles, and stock search for EM equities.

Source: https://finnhub.io/docs/api
Category: Emerging Markets
Free tier: 60 API calls/minute
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
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "sandbox_c1234567890")

# Emerging Markets Exchange Registry
EM_EXCHANGES = {
    'INDIA': {
        'NSE': 'National Stock Exchange of India',
        'BSE': 'Bombay Stock Exchange'
    },
    'CHINA': {
        'SS': 'Shanghai Stock Exchange',
        'SZ': 'Shenzhen Stock Exchange'
    },
    'BRAZIL': {
        'SA': 'B3 - Brasil Bolsa Balcão'
    }
}

# Sample symbols for get_latest()
SAMPLE_SYMBOLS = [
    'RELIANCE.NS',  # Reliance Industries (NSE)
    'TCS.NS',       # Tata Consultancy Services (NSE)
    'INFY.NS',      # Infosys (NSE)
    '600519.SS',    # Kweichow Moutai (Shanghai)
    '000001.SZ',    # Ping An Bank (Shenzhen)
    'PETR4.SA',     # Petrobras (Brazil)
    'VALE3.SA'      # Vale (Brazil)
]


def get_em_quote(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get real-time quote for an emerging market stock
    
    Args:
        symbol: Stock symbol with exchange suffix (e.g., "RELIANCE.NS", "BABA", "600519.SS")
        api_key: Optional Finnhub API key (uses env var if not provided)
    
    Returns:
        Dict with current price, change, percent change, high, low, open, previous close
    
    Example:
        >>> get_em_quote("RELIANCE.NS")
        {'success': True, 'symbol': 'RELIANCE.NS', 'current_price': 2450.50, ...}
    """
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            "symbol": symbol,
            "token": api_key or FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Finnhub returns {'c': current, 'h': high, 'l': low, 'o': open, 'pc': previous close, 't': timestamp}
        if 'c' not in data or data.get('c') == 0:
            return {
                "success": False,
                "error": "No quote data available",
                "symbol": symbol
            }
        
        current = data['c']
        prev_close = data['pc']
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        
        return {
            "success": True,
            "symbol": symbol,
            "current_price": current,
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "high": data['h'],
            "low": data['l'],
            "open": data['o'],
            "previous_close": prev_close,
            "timestamp": datetime.fromtimestamp(data['t']).isoformat() if data.get('t') else None,
            "fetched_at": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "symbol": symbol
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


def get_em_stocks(exchange: str, api_key: Optional[str] = None) -> Dict:
    """
    List all stocks available on an emerging market exchange
    
    Args:
        exchange: Exchange code (NSE, BSE, SS, SZ, SA)
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with list of stocks including symbol, description, displaySymbol, type
    
    Example:
        >>> get_em_stocks("NSE")
        {'success': True, 'exchange': 'NSE', 'stocks': [...], 'count': 1500}
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/symbol"
        params = {
            "exchange": exchange,
            "token": api_key or FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, list):
            return {
                "success": False,
                "error": "Unexpected response format",
                "exchange": exchange
            }
        
        # Filter for common stock types
        stocks = [s for s in data if s.get('type') in ['Common Stock', 'EQS', None]]
        
        return {
            "success": True,
            "exchange": exchange,
            "exchange_name": _get_exchange_name(exchange),
            "stocks": stocks[:100],  # Limit to first 100 for performance
            "count": len(stocks),
            "total_available": len(data),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "exchange": exchange
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "exchange": exchange
        }


def get_em_company_profile(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get company profile for an emerging market stock
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS", "600519.SS")
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with company name, industry, market cap, country, currency, etc.
    
    Example:
        >>> get_em_company_profile("RELIANCE.NS")
        {'success': True, 'name': 'Reliance Industries Ltd', 'industry': 'Oil & Gas', ...}
    """
    try:
        url = f"{FINNHUB_BASE_URL}/stock/profile2"
        params = {
            "symbol": symbol,
            "token": api_key or FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'name' not in data:
            return {
                "success": False,
                "error": "No company profile available",
                "symbol": symbol
            }
        
        return {
            "success": True,
            "symbol": symbol,
            "name": data.get('name'),
            "country": data.get('country'),
            "currency": data.get('currency'),
            "exchange": data.get('exchange'),
            "industry": data.get('finnhubIndustry'),
            "ipo_date": data.get('ipo'),
            "market_cap": data.get('marketCapitalization'),
            "shares_outstanding": data.get('shareOutstanding'),
            "logo": data.get('logo'),
            "phone": data.get('phone'),
            "weburl": data.get('weburl'),
            "ticker": data.get('ticker'),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "symbol": symbol
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


def search_em_stocks(query: str, api_key: Optional[str] = None) -> Dict:
    """
    Search for emerging market stocks by name or symbol
    
    Args:
        query: Search term (company name or symbol, e.g., "Reliance", "Tata")
        api_key: Optional Finnhub API key
    
    Returns:
        Dict with search results including symbol, description, type, exchange
    
    Example:
        >>> search_em_stocks("Reliance")
        {'success': True, 'query': 'Reliance', 'results': [...], 'count': 5}
    """
    try:
        url = f"{FINNHUB_BASE_URL}/search"
        params = {
            "q": query,
            "token": api_key or FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' not in data:
            return {
                "success": False,
                "error": "No search results",
                "query": query
            }
        
        results = data['result']
        
        # Filter for emerging market exchanges
        em_results = []
        for r in results:
            symbol = r.get('symbol', '')
            # Check if symbol ends with EM exchange suffixes
            if any(symbol.endswith(suffix) for suffix in ['.NS', '.BSE', '.SS', '.SZ', '.SA', '.BO']):
                em_results.append(r)
        
        return {
            "success": True,
            "query": query,
            "results": em_results if em_results else results[:10],  # Fallback to all results if no EM matches
            "count": len(em_results) if em_results else len(results[:10]),
            "total_results": data.get('count', len(results)),
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "query": query
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def get_latest(api_key: Optional[str] = None) -> Dict:
    """
    Get sample quotes from major emerging market stocks
    Returns latest prices for representative stocks from India, China, Brazil
    
    Returns:
        Dict with quotes for major EM stocks
    
    Example:
        >>> get_latest()
        {'success': True, 'markets': {'India': [...], 'China': [...], 'Brazil': [...]}}
    """
    results = {
        'India': [],
        'China': [],
        'Brazil': []
    }
    
    symbol_map = {
        'India': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS'],
        'China': ['600519.SS', '000001.SZ'],
        'Brazil': ['PETR4.SA', 'VALE3.SA']
    }
    
    for market, symbols in symbol_map.items():
        for symbol in symbols:
            quote = get_em_quote(symbol, api_key)
            if quote['success']:
                results[market].append({
                    'symbol': symbol,
                    'price': quote['current_price'],
                    'change': quote['change'],
                    'change_pct': quote['change_percent']
                })
    
    success = any(len(quotes) > 0 for quotes in results.values())
    
    return {
        "success": success,
        "markets": results,
        "timestamp": datetime.now().isoformat(),
        "source": "Finnhub Emerging Markets API"
    }


def list_em_exchanges() -> Dict:
    """
    List all supported emerging market exchanges
    
    Returns:
        Dict with exchange codes, names, and countries
    """
    exchanges = []
    
    for region, exch_dict in EM_EXCHANGES.items():
        for code, name in exch_dict.items():
            exchanges.append({
                'code': code,
                'name': name,
                'region': region
            })
    
    return {
        "success": True,
        "exchanges": exchanges,
        "count": len(exchanges),
        "regions": list(EM_EXCHANGES.keys())
    }


def _get_exchange_name(exchange_code: str) -> str:
    """Helper to resolve exchange code to full name"""
    for region, exchanges in EM_EXCHANGES.items():
        if exchange_code in exchanges:
            return exchanges[exchange_code]
    return exchange_code


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Finnhub Emerging Markets API")
    print("=" * 60)
    
    # List supported exchanges
    exchanges = list_em_exchanges()
    print(f"\nSupported Exchanges: {exchanges['count']}")
    print(json.dumps(exchanges, indent=2))
    
    # Get sample market data
    print("\n" + "=" * 60)
    print("Latest EM Market Quotes")
    print("=" * 60)
    latest = get_latest()
    print(json.dumps(latest, indent=2))
