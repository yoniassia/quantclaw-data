#!/usr/bin/env python3
"""
Alpaca Markets API — Stock & Crypto Market Data Module

Real-time and historical market data for stocks and cryptocurrencies.
Features:
- OHLCV bars (stocks & crypto)
- Trade & quote data
- Market snapshots
- Order book snapshots (crypto)
- Free tier: 200 requests/minute

Source: https://alpaca.markets/docs/api-references/market-data-api/
Category: Exchanges & Market Microstructure
Free tier: True (requires ALPACA_API_KEY and ALPACA_SECRET_KEY env vars)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Alpaca API Configuration
ALPACA_BASE_URL = "https://data.alpaca.markets"
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "")

# Timeframe mappings
VALID_TIMEFRAMES = {
    '1Min', '5Min', '15Min', '30Min', '1Hour', '4Hour', '1Day', '1Week', '1Month'
}


def _get_headers() -> Dict[str, str]:
    """Get authentication headers for Alpaca API"""
    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }


def _make_request(url: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Alpaca API
    
    Args:
        url: Full API endpoint URL
        params: Optional query parameters
    
    Returns:
        Dict with success status and data or error
    """
    try:
        if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
            return {
                "success": False,
                "error": "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment variables"
            }
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "data": data
        }
    
    except requests.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            "status_code": e.response.status_code
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_stock_bars(
    symbol: str,
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get OHLCV bars for a stock
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
        timeframe: Bar size - '1Min', '5Min', '15Min', '30Min', '1Hour', '4Hour', '1Day', '1Week', '1Month'
        start: Start date (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')
        end: End date (ISO 8601 format)
        limit: Max number of bars to return (default 100, max 10000)
    
    Returns:
        Dict with OHLCV bars, symbol info, and metadata
    """
    if timeframe not in VALID_TIMEFRAMES:
        return {
            "success": False,
            "error": f"Invalid timeframe. Must be one of: {', '.join(VALID_TIMEFRAMES)}"
        }
    
    # Default to last 30 days if no start specified
    if not start:
        start = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
    
    if not end:
        end = datetime.now().isoformat() + 'Z'
    
    url = f"{ALPACA_BASE_URL}/v2/stocks/{symbol.upper()}/bars"
    params = {
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": limit,
        "adjustment": "split",
        "feed": "iex"
    }
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    bars = data.get("bars", [])
    
    # Calculate basic stats if bars available
    stats = {}
    if bars:
        closes = [float(b["c"]) for b in bars]
        volumes = [int(b["v"]) for b in bars]
        
        stats = {
            "latest_close": closes[-1],
            "period_high": max(closes),
            "period_low": min(closes),
            "period_change": closes[-1] - closes[0],
            "period_change_pct": ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0,
            "avg_volume": sum(volumes) // len(volumes),
            "bar_count": len(bars)
        }
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "bars": bars,
        "stats": stats,
        "next_page_token": data.get("next_page_token"),
        "timestamp": datetime.now().isoformat()
    }


def get_stock_trades(symbol: str, start: Optional[str] = None, limit: int = 100) -> Dict:
    """
    Get recent trades for a stock
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        start: Start timestamp (RFC-3339 format)
        limit: Max number of trades (default 100, max 10000)
    
    Returns:
        Dict with trade data including price, size, timestamp, conditions
    """
    if not start:
        start = (datetime.now() - timedelta(hours=1)).isoformat() + 'Z'
    
    url = f"{ALPACA_BASE_URL}/v2/stocks/{symbol.upper()}/trades"
    params = {
        "start": start,
        "limit": limit,
        "feed": "iex"
    }
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    trades = data.get("trades", [])
    
    # Calculate trade statistics
    stats = {}
    if trades:
        prices = [float(t["p"]) for t in trades]
        sizes = [int(t["s"]) for t in trades]
        
        stats = {
            "trade_count": len(trades),
            "volume": sum(sizes),
            "vwap": sum(float(t["p"]) * int(t["s"]) for t in trades) / sum(sizes) if sum(sizes) > 0 else 0,
            "latest_price": prices[-1],
            "high": max(prices),
            "low": min(prices),
            "avg_size": sum(sizes) // len(sizes)
        }
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "trades": trades,
        "stats": stats,
        "next_page_token": data.get("next_page_token"),
        "timestamp": datetime.now().isoformat()
    }


def get_stock_quotes(symbol: str, start: Optional[str] = None, limit: int = 100) -> Dict:
    """
    Get latest quotes (NBBO - National Best Bid and Offer) for a stock
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        start: Start timestamp (RFC-3339 format)
        limit: Max number of quotes (default 100)
    
    Returns:
        Dict with bid/ask prices and sizes
    """
    if not start:
        start = (datetime.now() - timedelta(hours=1)).isoformat() + 'Z'
    
    url = f"{ALPACA_BASE_URL}/v2/stocks/{symbol.upper()}/quotes"
    params = {
        "start": start,
        "limit": limit,
        "feed": "iex"
    }
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    quotes = data.get("quotes", [])
    
    # Latest quote analysis
    latest_quote = {}
    if quotes:
        last = quotes[-1]
        bid_price = float(last["bp"])
        ask_price = float(last["ap"])
        
        latest_quote = {
            "bid_price": bid_price,
            "ask_price": ask_price,
            "bid_size": int(last["bs"]),
            "ask_size": int(last["as"]),
            "spread": ask_price - bid_price,
            "spread_bps": ((ask_price - bid_price) / bid_price * 10000) if bid_price > 0 else 0,
            "mid_price": (bid_price + ask_price) / 2,
            "timestamp": last["t"]
        }
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "quotes": quotes,
        "latest": latest_quote,
        "quote_count": len(quotes),
        "next_page_token": data.get("next_page_token"),
        "timestamp": datetime.now().isoformat()
    }


def get_stock_snapshot(symbol: str) -> Dict:
    """
    Get full market snapshot for a stock
    Includes latest bar, trade, quote, daily bar, and previous daily bar
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict with comprehensive current market state
    """
    url = f"{ALPACA_BASE_URL}/v2/stocks/{symbol.upper()}/snapshot"
    params = {"feed": "iex"}
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    snapshot = result["data"]
    
    # Extract key metrics
    analysis = {}
    if "dailyBar" in snapshot and snapshot["dailyBar"]:
        daily = snapshot["dailyBar"]
        prev = snapshot.get("prevDailyBar", {})
        
        current_close = float(daily["c"])
        prev_close = float(prev.get("c", current_close))
        
        analysis = {
            "current_price": current_close,
            "daily_change": current_close - prev_close,
            "daily_change_pct": ((current_close - prev_close) / prev_close * 100) if prev_close != 0 else 0,
            "daily_high": float(daily["h"]),
            "daily_low": float(daily["l"]),
            "daily_volume": int(daily["v"]),
            "daily_vwap": float(daily.get("vw", 0))
        }
    
    if "latestTrade" in snapshot and snapshot["latestTrade"]:
        trade = snapshot["latestTrade"]
        analysis["latest_trade_price"] = float(trade["p"])
        analysis["latest_trade_size"] = int(trade["s"])
        analysis["latest_trade_time"] = trade["t"]
    
    if "latestQuote" in snapshot and snapshot["latestQuote"]:
        quote = snapshot["latestQuote"]
        bid = float(quote["bp"])
        ask = float(quote["ap"])
        analysis["bid_price"] = bid
        analysis["ask_price"] = ask
        analysis["spread"] = ask - bid
        analysis["mid_price"] = (bid + ask) / 2
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "snapshot": snapshot,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }


def get_crypto_bars(
    symbol: str,
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100
) -> Dict:
    """
    Get OHLCV bars for cryptocurrency
    
    Args:
        symbol: Crypto pair (e.g., 'BTC/USD', 'ETH/USD', 'DOGE/USD')
        timeframe: Bar size - '1Min', '5Min', '15Min', '30Min', '1Hour', '4Hour', '1Day'
        start: Start date (ISO 8601 format)
        end: End date (ISO 8601 format)
        limit: Max number of bars (default 100, max 10000)
    
    Returns:
        Dict with OHLCV bars and statistics
    """
    if timeframe not in VALID_TIMEFRAMES:
        return {
            "success": False,
            "error": f"Invalid timeframe. Must be one of: {', '.join(VALID_TIMEFRAMES)}"
        }
    
    if not start:
        start = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
    
    if not end:
        end = datetime.now().isoformat() + 'Z'
    
    url = f"{ALPACA_BASE_URL}/v1beta3/crypto/us/bars"
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": limit
    }
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    bars = data.get("bars", {}).get(symbol, [])
    
    # Calculate stats
    stats = {}
    if bars:
        closes = [float(b["c"]) for b in bars]
        volumes = [float(b["v"]) for b in bars]
        
        stats = {
            "latest_close": closes[-1],
            "period_high": max(closes),
            "period_low": min(closes),
            "period_change": closes[-1] - closes[0],
            "period_change_pct": ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0,
            "total_volume": sum(volumes),
            "avg_volume": sum(volumes) / len(volumes),
            "bar_count": len(bars)
        }
    
    return {
        "success": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": bars,
        "stats": stats,
        "next_page_token": data.get("next_page_token"),
        "timestamp": datetime.now().isoformat()
    }


def get_crypto_snapshot(symbol: str) -> Dict:
    """
    Get full market snapshot for cryptocurrency
    Includes latest trade, quote, minute bar, daily bar, and previous daily bar
    
    Args:
        symbol: Crypto pair (e.g., 'BTC/USD', 'ETH/USD')
    
    Returns:
        Dict with comprehensive crypto market state
    """
    url = f"{ALPACA_BASE_URL}/v1beta3/crypto/us/snapshots"
    params = {"symbols": symbol}
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    snapshot = data.get("snapshots", {}).get(symbol, {})
    
    if not snapshot:
        return {
            "success": False,
            "error": f"No snapshot data available for {symbol}"
        }
    
    # Extract key metrics
    analysis = {}
    
    if "dailyBar" in snapshot and snapshot["dailyBar"]:
        daily = snapshot["dailyBar"]
        prev = snapshot.get("prevDailyBar", {})
        
        current_close = float(daily["c"])
        prev_close = float(prev.get("c", current_close))
        
        analysis = {
            "current_price": current_close,
            "daily_change": current_close - prev_close,
            "daily_change_pct": ((current_close - prev_close) / prev_close * 100) if prev_close != 0 else 0,
            "daily_high": float(daily["h"]),
            "daily_low": float(daily["l"]),
            "daily_volume": float(daily["v"]),
            "daily_vwap": float(daily.get("vw", 0)),
            "daily_trade_count": int(daily.get("n", 0))
        }
    
    if "latestTrade" in snapshot and snapshot["latestTrade"]:
        trade = snapshot["latestTrade"]
        analysis["latest_trade_price"] = float(trade["p"])
        analysis["latest_trade_size"] = float(trade["s"])
        analysis["latest_trade_time"] = trade["t"]
    
    if "latestQuote" in snapshot and snapshot["latestQuote"]:
        quote = snapshot["latestQuote"]
        bid = float(quote["bp"])
        ask = float(quote["ap"])
        analysis["bid_price"] = bid
        analysis["ask_price"] = ask
        analysis["spread"] = ask - bid
        analysis["spread_pct"] = ((ask - bid) / bid * 100) if bid > 0 else 0
    
    return {
        "success": True,
        "symbol": symbol,
        "snapshot": snapshot,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }


def get_latest(symbols: Optional[List[str]] = None) -> Dict:
    """
    Get latest market snapshots for multiple stocks
    Quick overview of current prices and daily changes
    
    Args:
        symbols: List of stock tickers (default: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])
    
    Returns:
        Dict with snapshots for all requested symbols
    """
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    # Get snapshots for all symbols
    url = f"{ALPACA_BASE_URL}/v2/stocks/snapshots"
    params = {
        "symbols": ",".join([s.upper() for s in symbols]),
        "feed": "iex"
    }
    
    result = _make_request(url, params)
    
    if not result["success"]:
        return result
    
    snapshots = result["data"]
    
    # Parse and summarize
    summary = []
    for symbol, snap in snapshots.items():
        if not snap:
            continue
        
        daily = snap.get("dailyBar", {})
        prev = snap.get("prevDailyBar", {})
        
        if daily and prev:
            current = float(daily["c"])
            prev_close = float(prev["c"])
            change_pct = ((current - prev_close) / prev_close * 100) if prev_close != 0 else 0
            
            summary.append({
                "symbol": symbol,
                "price": current,
                "change": current - prev_close,
                "change_pct": change_pct,
                "volume": int(daily["v"]),
                "high": float(daily["h"]),
                "low": float(daily["l"])
            })
    
    # Sort by absolute change percentage
    summary.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    
    return {
        "success": True,
        "symbols": symbols,
        "snapshots": snapshots,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    }


def get_market_status() -> Dict:
    """
    Check if US stock market is currently open
    
    Returns:
        Dict with market status information
    """
    url = f"{ALPACA_BASE_URL}/v2/clock"
    
    result = _make_request(url)
    
    if not result["success"]:
        return result
    
    clock = result["data"]
    
    return {
        "success": True,
        "is_open": clock.get("is_open", False),
        "timestamp": clock.get("timestamp"),
        "next_open": clock.get("next_open"),
        "next_close": clock.get("next_close")
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Alpaca Markets API - Stock & Crypto Data")
    print("=" * 60)
    
    # Check market status
    status = get_market_status()
    if status["success"]:
        print(f"\nMarket Open: {status['is_open']}")
        print(f"Next Open: {status.get('next_open', 'N/A')}")
    
    # Get latest market summary
    print("\n" + "=" * 60)
    print("Latest Market Summary")
    print("=" * 60)
    latest = get_latest()
    if latest["success"]:
        for item in latest["summary"][:5]:
            sign = "+" if item["change"] >= 0 else ""
            print(f"{item['symbol']:6s} ${item['price']:8.2f}  {sign}{item['change_pct']:+6.2f}%  Vol: {item['volume']:,}")
    
    print("\n" + json.dumps({"module": "alpaca_markets_api", "status": "ready"}, indent=2))
