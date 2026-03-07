#!/usr/bin/env python3
"""
OrderFlow Free Feed — Binance Public API Implementation
Provides order flow and market microstructure data via Binance public endpoints.
Includes order book depth, aggregate trades, and WebSocket streaming.

Source: Binance Public API (fallback from https://orderflowfeed.com/docs)
Category: Exchanges & Market Microstructure
Free tier: true - No API key required for public endpoints
Update frequency: real-time
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Generator
import time

BASE_URL = "https://api.binance.com"

def get_order_book(symbol: str = "BTCUSDT", limit: int = 100) -> Dict:
    """
    Fetch order book depth from Binance.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        limit: Depth limit (5, 10, 20, 50, 100, 500, 1000, 5000)
    
    Returns:
        Dict with lastUpdateId, bids, asks
    """
    try:
        url = f"{BASE_URL}/api/v3/depth"
        params = {"symbol": symbol.upper(), "limit": limit}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse bids and asks
        bids = [[float(price), float(qty)] for price, qty in data.get("bids", [])]
        asks = [[float(price), float(qty)] for price, qty in data.get("asks", [])]
        
        return {
            "symbol": symbol.upper(),
            "timestamp": int(time.time() * 1000),
            "lastUpdateId": data.get("lastUpdateId"),
            "bids": bids,
            "asks": asks,
            "bid_volume": sum(qty for _, qty in bids),
            "ask_volume": sum(qty for _, qty in asks)
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_aggregate_trades(symbol: str = "BTCUSDT", limit: int = 100, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict]:
    """
    Fetch aggregate trades from Binance.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        limit: Number of trades to fetch (max 1000)
        start_time: Start time in milliseconds (optional)
        end_time: End time in milliseconds (optional)
    
    Returns:
        List of aggregate trade dictionaries
    """
    try:
        url = f"{BASE_URL}/api/v3/aggTrades"
        params = {"symbol": symbol.upper(), "limit": min(limit, 1000)}
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        trades = response.json()
        
        # Parse and enrich trade data
        result = []
        for trade in trades:
            result.append({
                "agg_trade_id": trade.get("a"),
                "price": float(trade.get("p")),
                "quantity": float(trade.get("q")),
                "first_trade_id": trade.get("f"),
                "last_trade_id": trade.get("l"),
                "timestamp": trade.get("T"),
                "is_buyer_maker": trade.get("m"),
                "side": "sell" if trade.get("m") else "buy"
            })
        
        return result
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "symbol": symbol}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "symbol": symbol}]


def get_order_flow_snapshot(symbol: str = "BTCUSDT") -> Dict:
    """
    Get combined order flow snapshot: order book + recent trades.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
    
    Returns:
        Dict with order book and trade flow data
    """
    try:
        order_book = get_order_book(symbol, limit=100)
        trades = get_aggregate_trades(symbol, limit=50)
        
        # Calculate trade flow metrics
        buy_volume = sum(t["quantity"] for t in trades if not isinstance(t, dict) or "error" not in t and t.get("side") == "buy")
        sell_volume = sum(t["quantity"] for t in trades if not isinstance(t, dict) or "error" not in t and t.get("side") == "sell")
        
        return {
            "symbol": symbol.upper(),
            "timestamp": int(time.time() * 1000),
            "order_book": {
                "bids": order_book.get("bids", [])[:10],  # Top 10
                "asks": order_book.get("asks", [])[:10],
                "bid_volume": order_book.get("bid_volume", 0),
                "ask_volume": order_book.get("ask_volume", 0)
            },
            "trade_flow": {
                "recent_trades": trades[:10],  # Last 10
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "buy_sell_ratio": buy_volume / sell_volume if sell_volume > 0 else 0
            }
        }
    except Exception as e:
        return {"error": f"Failed to get order flow snapshot: {str(e)}", "symbol": symbol}


def stream_order_book_updates(symbol: str = "BTCUSDT", interval_seconds: int = 1) -> Generator[Dict, None, None]:
    """
    Stream order book updates at specified interval.
    Note: This is a polling-based approach. For true WebSocket streaming,
    use websocket-client library with wss://stream.binance.com:9443/ws/{symbol}@depth
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        interval_seconds: Polling interval in seconds
    
    Yields:
        Dict with order book updates
    """
    while True:
        try:
            data = get_order_book(symbol, limit=20)
            if "error" not in data:
                yield data
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            break
        except Exception as e:
            yield {"error": str(e), "symbol": symbol}
            time.sleep(interval_seconds)


def get_latest(symbol: str = "BTCUSDT") -> Dict:
    """
    Get latest order flow snapshot (alias for get_order_flow_snapshot).
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
    
    Returns:
        Dict with latest order flow data
    """
    return get_order_flow_snapshot(symbol)


def fetch_data(symbol: str = "BTCUSDT", data_type: str = "snapshot") -> Dict:
    """
    Generic data fetching function.
    
    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        data_type: Type of data to fetch (snapshot, orderbook, trades)
    
    Returns:
        Dict with requested data
    """
    if data_type == "snapshot":
        return get_order_flow_snapshot(symbol)
    elif data_type == "orderbook":
        return get_order_book(symbol)
    elif data_type == "trades":
        return {"trades": get_aggregate_trades(symbol)}
    else:
        return {"error": f"Unknown data_type: {data_type}"}


if __name__ == "__main__":
    # Test the module
    print(json.dumps({
        "module": "orderflow_free_feed",
        "status": "active",
        "source": "Binance Public API",
        "functions": [
            "get_order_book",
            "get_aggregate_trades",
            "get_order_flow_snapshot",
            "stream_order_book_updates",
            "get_latest",
            "fetch_data"
        ]
    }, indent=2))
    
    # Quick test
    print("\nTesting BTCUSDT order book...")
    result = get_order_book("BTCUSDT", limit=5)
    if "error" not in result:
        print(f"✓ Got {len(result.get('bids', []))} bids, {len(result.get('asks', []))} asks")
    else:
        print(f"✗ Error: {result.get('error')}")
