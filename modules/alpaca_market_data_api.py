#!/usr/bin/env python3
"""
Alpaca Market Data API — Stock & Crypto Market Data Module

Provides free access to U.S. stock and crypto market data including:
- Historical OHLCV bars (stocks & crypto)
- Real-time quotes (bid/ask)
- Latest trades
- Market snapshots
- Multi-timeframe support

Source: https://alpaca.markets/docs/api-references/market-data-api/
Category: Exchanges & Market Microstructure
Free tier: True (some endpoints require API key for extended limits)
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

# Alpaca API Configuration
STOCKS_BASE_URL = "https://data.alpaca.markets/v2"
CRYPTO_BASE_URL = "https://data.alpaca.markets/v1beta3/crypto/us"

# Check for API credentials (optional for free tier)
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY") or os.environ.get("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY")

# Timeframe mapping
TIMEFRAME_MAP = {
    "1Min": "1Min",
    "5Min": "5Min",
    "15Min": "15Min",
    "1Hour": "1Hour",
    "1Day": "1Day",
    "1Week": "1Week",
    "1Month": "1Month",
}


def _get_headers() -> Dict[str, str]:
    """Generate request headers with optional authentication."""
    headers = {
        "accept": "application/json",
    }
    
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        headers["APCA-API-KEY-ID"] = ALPACA_API_KEY
        headers["APCA-API-SECRET-KEY"] = ALPACA_SECRET_KEY
    
    return headers


def _make_request(url: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to Alpaca API with error handling.
    
    Args:
        url: Full API endpoint URL
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        Exception on HTTP errors
    """
    try:
        response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "message": "Failed to fetch data from Alpaca API"
        }


# ========== STOCK MARKET DATA ==========

def get_stock_bars(symbol: str, timeframe: str = "1Day", limit: int = 100, 
                   start: Optional[str] = None, end: Optional[str] = None) -> Dict:
    """
    Get historical OHLCV bars for a stock.
    
    Args:
        symbol: Stock ticker (e.g., "AAPL", "TSLA")
        timeframe: Bar duration - "1Min", "5Min", "15Min", "1Hour", "1Day", "1Week", "1Month"
        limit: Number of bars to return (max 10000)
        start: Start date in RFC-3339 format or YYYY-MM-DD (optional)
        end: End date in RFC-3339 format or YYYY-MM-DD (optional)
        
    Returns:
        {
            "symbol": "AAPL",
            "bars": [
                {
                    "t": "2024-01-01T00:00:00Z",
                    "o": 185.50,
                    "h": 187.20,
                    "l": 184.80,
                    "c": 186.75,
                    "v": 75000000,
                    "n": 550000,
                    "vw": 186.25
                },
                ...
            ],
            "next_page_token": null
        }
    """
    symbol = symbol.upper()
    timeframe = TIMEFRAME_MAP.get(timeframe, timeframe)
    
    url = f"{STOCKS_BASE_URL}/stocks/{symbol}/bars"
    params = {
        "timeframe": timeframe,
        "limit": min(limit, 10000),
    }
    
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    
    return _make_request(url, params)


def get_latest_quote(symbol: str) -> Dict:
    """
    Get the latest bid/ask quote for a stock.
    
    Args:
        symbol: Stock ticker (e.g., "AAPL")
        
    Returns:
        {
            "symbol": "AAPL",
            "quote": {
                "t": "2024-01-01T16:00:00Z",
                "ax": "Q",  # ask exchange
                "ap": 186.50,  # ask price
                "as": 100,  # ask size
                "bx": "Q",  # bid exchange
                "bp": 186.48,  # bid price
                "bs": 200,  # bid size
                "c": ["R"]  # conditions
            }
        }
    """
    symbol = symbol.upper()
    url = f"{STOCKS_BASE_URL}/stocks/{symbol}/quotes/latest"
    
    return _make_request(url)


def get_latest_trade(symbol: str) -> Dict:
    """
    Get the latest trade for a stock.
    
    Args:
        symbol: Stock ticker (e.g., "AAPL")
        
    Returns:
        {
            "symbol": "AAPL",
            "trade": {
                "t": "2024-01-01T16:00:00Z",
                "x": "Q",  # exchange
                "p": 186.49,  # price
                "s": 100,  # size
                "c": ["@"],  # conditions
                "i": 12345,  # trade ID
                "z": "C"  # tape
            }
        }
    """
    symbol = symbol.upper()
    url = f"{STOCKS_BASE_URL}/stocks/{symbol}/trades/latest"
    
    return _make_request(url)


def get_stock_snapshot(symbol: str) -> Dict:
    """
    Get full snapshot of current market state for a stock.
    Includes latest trade, quote, minute bar, daily bar, and previous daily bar.
    
    Args:
        symbol: Stock ticker (e.g., "AAPL")
        
    Returns:
        {
            "symbol": "AAPL",
            "latestTrade": {...},
            "latestQuote": {...},
            "minuteBar": {...},
            "dailyBar": {...},
            "prevDailyBar": {...}
        }
    """
    symbol = symbol.upper()
    url = f"{STOCKS_BASE_URL}/stocks/{symbol}/snapshot"
    
    return _make_request(url)


def get_stock_snapshots(symbols: List[str]) -> Dict:
    """
    Get snapshots for multiple stocks in a single request.
    
    Args:
        symbols: List of stock tickers (e.g., ["AAPL", "TSLA", "MSFT"])
        
    Returns:
        {
            "AAPL": {...},
            "TSLA": {...},
            "MSFT": {...}
        }
    """
    symbols_str = ",".join([s.upper() for s in symbols])
    url = f"{STOCKS_BASE_URL}/stocks/snapshots"
    params = {"symbols": symbols_str}
    
    return _make_request(url, params)


# ========== CRYPTO MARKET DATA ==========

def get_crypto_bars(symbol: str, timeframe: str = "1Day", limit: int = 100,
                    start: Optional[str] = None, end: Optional[str] = None) -> Dict:
    """
    Get historical OHLCV bars for cryptocurrency pairs.
    
    Args:
        symbol: Crypto pair (e.g., "BTC/USD", "ETH/USD", "BTCUSD")
        timeframe: Bar duration - "1Min", "5Min", "15Min", "1Hour", "1Day"
        limit: Number of bars to return (max 10000)
        start: Start date in RFC-3339 format or YYYY-MM-DD (optional)
        end: End date in RFC-3339 format or YYYY-MM-DD (optional)
        
    Returns:
        {
            "symbol": "BTC/USD",
            "bars": [
                {
                    "t": "2024-01-01T00:00:00Z",
                    "o": 42000.50,
                    "h": 42500.00,
                    "l": 41800.00,
                    "c": 42300.00,
                    "v": 1250.5,
                    "n": 15000,
                    "vw": 42150.25
                },
                ...
            ],
            "next_page_token": null
        }
    """
    # Normalize symbol format (BTC/USD or BTCUSD -> BTC/USD)
    if "/" not in symbol:
        if symbol.endswith("USD"):
            symbol = f"{symbol[:-3]}/USD"
        elif symbol.endswith("USDT"):
            symbol = f"{symbol[:-4]}/USDT"
    
    symbol = symbol.upper()
    timeframe = TIMEFRAME_MAP.get(timeframe, timeframe)
    
    url = f"{CRYPTO_BASE_URL}/bars"
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "limit": min(limit, 10000),
    }
    
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    
    return _make_request(url, params)


def get_latest_crypto_quote(symbol: str) -> Dict:
    """
    Get the latest bid/ask quote for a cryptocurrency pair.
    
    Args:
        symbol: Crypto pair (e.g., "BTC/USD", "ETH/USD")
        
    Returns:
        {
            "symbol": "BTC/USD",
            "quote": {
                "t": "2024-01-01T16:00:00Z",
                "bp": 42000.50,  # bid price
                "bs": 1.5,  # bid size
                "ap": 42001.00,  # ask price
                "as": 1.2  # ask size
            }
        }
    """
    if "/" not in symbol:
        if symbol.endswith("USD"):
            symbol = f"{symbol[:-3]}/USD"
    
    symbol = symbol.upper()
    url = f"{CRYPTO_BASE_URL}/latest/quotes"
    params = {"symbols": symbol}
    
    return _make_request(url, params)


def get_latest_crypto_trade(symbol: str) -> Dict:
    """
    Get the latest trade for a cryptocurrency pair.
    
    Args:
        symbol: Crypto pair (e.g., "BTC/USD")
        
    Returns:
        {
            "symbol": "BTC/USD",
            "trade": {
                "t": "2024-01-01T16:00:00Z",
                "p": 42000.75,  # price
                "s": 0.5,  # size
                "tks": "B"  # taker side
            }
        }
    """
    if "/" not in symbol:
        if symbol.endswith("USD"):
            symbol = f"{symbol[:-3]}/USD"
    
    symbol = symbol.upper()
    url = f"{CRYPTO_BASE_URL}/latest/trades"
    params = {"symbols": symbol}
    
    return _make_request(url, params)


def get_crypto_snapshot(symbol: str) -> Dict:
    """
    Get full snapshot for a cryptocurrency pair.
    
    Args:
        symbol: Crypto pair (e.g., "BTC/USD")
        
    Returns:
        {
            "symbol": "BTC/USD",
            "latestTrade": {...},
            "latestQuote": {...},
            "minuteBar": {...},
            "dailyBar": {...},
            "prevDailyBar": {...}
        }
    """
    if "/" not in symbol:
        if symbol.endswith("USD"):
            symbol = f"{symbol[:-3]}/USD"
    
    symbol = symbol.upper()
    url = f"{CRYPTO_BASE_URL}/snapshots"
    params = {"symbols": symbol}
    
    return _make_request(url, params)


# ========== UTILITY FUNCTIONS ==========

def get_market_status() -> Dict:
    """
    Get current market status (open/closed).
    
    Returns:
        {
            "clock": {
                "timestamp": "2024-01-01T16:00:00Z",
                "is_open": false,
                "next_open": "2024-01-02T09:30:00Z",
                "next_close": "2024-01-02T16:00:00Z"
            }
        }
    """
    # Note: This endpoint requires API key
    url = "https://api.alpaca.markets/v2/clock"
    
    return _make_request(url)


def validate_symbol(symbol: str, asset_class: str = "stock") -> bool:
    """
    Validate if a symbol exists by attempting to fetch its snapshot.
    
    Args:
        symbol: Ticker symbol
        asset_class: "stock" or "crypto"
        
    Returns:
        True if symbol is valid, False otherwise
    """
    try:
        if asset_class == "stock":
            result = get_stock_snapshot(symbol)
        else:
            result = get_crypto_snapshot(symbol)
        
        return "error" not in result
    except:
        return False


# ========== MODULE INFO ==========

def get_module_info() -> Dict:
    """
    Get module metadata and available functions.
    
    Returns:
        Module information dictionary
    """
    return {
        "module": "alpaca_market_data_api",
        "version": "1.0.0",
        "phase": 106,
        "source": "https://alpaca.markets/docs/api-references/market-data-api/",
        "category": "Exchanges & Market Microstructure",
        "free_tier": True,
        "authenticated": ALPACA_API_KEY is not None,
        "functions": {
            "stocks": [
                "get_stock_bars",
                "get_latest_quote",
                "get_latest_trade",
                "get_stock_snapshot",
                "get_stock_snapshots",
            ],
            "crypto": [
                "get_crypto_bars",
                "get_latest_crypto_quote",
                "get_latest_crypto_trade",
                "get_crypto_snapshot",
            ],
            "utility": [
                "get_market_status",
                "validate_symbol",
                "get_module_info",
            ]
        },
        "note": "Free tier available. API key optional for extended limits."
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
