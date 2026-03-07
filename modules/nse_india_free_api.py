#!/usr/bin/env python3
"""
NSE India Free API — National Stock Exchange of India

Real-time market data from NSE India including equities, indices, and derivatives.
Uses NSE's public endpoints with proper session management and cookie handling.

Source: https://www.nseindia.com
Category: Emerging Markets
Free tier: True (no API key required)
Update frequency: Real-time during market hours
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

# NSE Base Configuration
NSE_BASE_URL = "https://www.nseindia.com"
NSE_API_URL = f"{NSE_BASE_URL}/api"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.nseindia.com/',
    'Connection': 'keep-alive'
}

# Global session for cookie persistence
_session = None

def _get_session():
    """Get or create requests session with cookies from NSE homepage"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
        # Visit homepage to get session cookies
        try:
            _session.get(NSE_BASE_URL, timeout=10)
        except Exception as e:
            print(f"Warning: Could not establish NSE session: {e}")
    return _session

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make authenticated request to NSE API endpoint
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters
        
    Returns:
        JSON response as dict or None on error
    """
    try:
        session = _get_session()
        url = f"{NSE_API_URL}/{endpoint}"
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"NSE API request failed for {endpoint}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse NSE response for {endpoint}: {e}")
        return None

# ========== MARKET STATUS ==========

def get_market_status() -> Optional[Dict]:
    """
    Get current market status (open/closed) for all segments
    
    Returns:
        Dict with market status info including:
        - marketState: List of market segments with status
        - serverTime: Current server timestamp
        
    Example:
        >>> status = get_market_status()
        >>> print(status['marketState'][0]['marketStatus'])
        'Closed'
    """
    return _make_request('marketStatus')

# ========== EQUITY QUOTES ==========

def get_quote(symbol: str) -> Optional[Dict]:
    """
    Get real-time quote for a stock symbol
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        
    Returns:
        Dict with stock quote data including:
        - priceInfo: Current price, change, volume
        - metadata: Company name, ISIN, industry
        - preOpenMarket: Pre-open price data
        
    Example:
        >>> quote = get_quote('RELIANCE')
        >>> print(quote['priceInfo']['lastPrice'])
        2543.75
    """
    return _make_request(f'quote-equity', params={'symbol': symbol.upper()})

def get_trade_info(symbol: str) -> Optional[Dict]:
    """
    Get detailed trade information for a stock
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict with trade details, delivery percentage, market depth
    """
    return _make_request(f'quote-equity', params={'symbol': symbol.upper(), 'section': 'trade_info'})

# ========== INDEX DATA ==========

def get_index_data(index: str = "NIFTY 50") -> Optional[Dict]:
    """
    Get real-time index data
    
    Args:
        index: Index name (default: "NIFTY 50")
               Options: "NIFTY 50", "NIFTY BANK", "NIFTY IT", 
                       "NIFTY PHARMA", "NIFTY AUTO", etc.
        
    Returns:
        Dict with index data including:
        - name: Index name
        - last: Current value
        - variation: Points change
        - percentChange: Percentage change
        - open, high, low: OHLC data
        
    Example:
        >>> nifty = get_index_data("NIFTY 50")
        >>> print(f"{nifty['name']}: {nifty['last']}")
        NIFTY 50: 22156.80
    """
    # Map common names to NSE index symbols
    index_map = {
        "NIFTY 50": "NIFTY 50",
        "NIFTY": "NIFTY 50",
        "NIFTY BANK": "NIFTY BANK",
        "BANKNIFTY": "NIFTY BANK",
        "NIFTY IT": "NIFTY IT",
        "NIFTY AUTO": "NIFTY AUTO",
        "NIFTY PHARMA": "NIFTY PHARMA",
        "NIFTY FMCG": "NIFTY FMCG",
        "NIFTY METAL": "NIFTY METAL",
        "NIFTY REALTY": "NIFTY REALTY",
        "NIFTY ENERGY": "NIFTY ENERGY"
    }
    
    index_symbol = index_map.get(index.upper(), index)
    
    # Get all indices data and find the requested one
    data = _make_request('allIndices')
    if data and 'data' in data:
        for idx in data['data']:
            if idx.get('index', '').upper() == index_symbol.upper():
                return idx
    return None

def get_all_indices() -> Optional[List[Dict]]:
    """
    Get data for all NSE indices
    
    Returns:
        List of dicts with data for all indices
    """
    data = _make_request('allIndices')
    return data.get('data', []) if data else None

# ========== OPTIONS CHAIN ==========

def get_option_chain(symbol: str) -> Optional[Dict]:
    """
    Get options chain data for a symbol
    
    Args:
        symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
        
    Returns:
        Dict with options chain including:
        - records: Call and Put options data
        - filtered: Filtered options based on criteria
        - strikePrices: Available strike prices
        
    Example:
        >>> chain = get_option_chain('NIFTY')
        >>> print(chain['records']['strikePrices'][:5])
        [21800, 21850, 21900, 21950, 22000]
    """
    return _make_request(f'option-chain-indices', params={'symbol': symbol.upper()})

def get_option_chain_equities(symbol: str) -> Optional[Dict]:
    """
    Get options chain for individual stocks
    
    Args:
        symbol: Stock symbol with options (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        Dict with equity options chain data
    """
    return _make_request(f'option-chain-equities', params={'symbol': symbol.upper()})

# ========== MARKET MOVERS ==========

def get_top_gainers_losers() -> Optional[Dict]:
    """
    Get top gainers and losers for the day
    
    Returns:
        Dict with:
        - gainers: Top gainers from NIFTY 50
        - losers: Top losers from NIFTY 50
        
    Example:
        >>> movers = get_top_gainers_losers()
        >>> print(movers['gainers'][0]['symbol'])
        BEL
    """
    # Get gainers and losers
    gainers_data = _make_request('live-analysis-variations', params={'index': 'gainers'})
    losers_data = _make_request('live-analysis-variations', params={'index': 'losers'})
    
    result = {
        'gainers': gainers_data.get('NIFTY', {}).get('data', []) if gainers_data else [],
        'losers': losers_data.get('NIFTY', {}).get('data', []) if losers_data else []
    }
    
    return result

def get_market_turnover() -> Optional[Dict]:
    """
    Get market-wide turnover data
    
    Returns:
        Dict with turnover info for equity, F&O, currency derivatives
    """
    return _make_request('market-turnover')

# ========== CORPORATE ACTIONS ==========

def get_corporate_actions(symbol: str) -> Optional[Dict]:
    """
    Get corporate actions (dividends, splits, bonuses) for a symbol
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict with corporate action history
    """
    return _make_request('corporates-corporateActions', params={'symbol': symbol.upper()})

# ========== BULK DEALS ==========

def get_bulk_deals() -> Optional[List[Dict]]:
    """
    Get bulk deals for the trading day
    
    Returns:
        List of bulk deal transactions
    """
    data = _make_request('block-deal')
    return data if data else None

def get_block_deals() -> Optional[List[Dict]]:
    """
    Get block deals for the trading day
    
    Returns:
        List of block deal transactions
    """
    data = _make_request('block-deal')
    return data if data else None

# ========== HOLIDAY CALENDAR ==========

def get_holidays(type: str = "trading") -> Optional[List[Dict]]:
    """
    Get NSE holiday calendar
    
    Args:
        type: Holiday type - "trading" or "clearing"
        
    Returns:
        List of holidays with dates and descriptions
    """
    return _make_request('holiday-master', params={'type': type})

# ========== MODULE INFO ==========

def get_module_info() -> Dict:
    """Get module metadata"""
    return {
        "module": "nse_india_free_api",
        "version": "1.0.0",
        "source": "https://www.nseindia.com",
        "category": "Emerging Markets",
        "free_tier": True,
        "functions": [
            "get_market_status",
            "get_quote",
            "get_trade_info",
            "get_index_data",
            "get_all_indices",
            "get_option_chain",
            "get_option_chain_equities",
            "get_top_gainers_losers",
            "get_market_turnover",
            "get_corporate_actions",
            "get_bulk_deals",
            "get_block_deals",
            "get_holidays"
        ]
    }

if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
