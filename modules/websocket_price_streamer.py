"""
WebSocket Price Streamer — Multi-exchange real-time price feed aggregator.
Roadmap #201: Collects live prices from free WebSocket APIs (Finnhub, CoinCap, Twelve Data).
Provides unified price stream, multi-asset snapshots, and price change alerts.
"""

import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class PriceSnapshot:
    """In-memory latest price store."""

    def __init__(self):
        self.prices: Dict[str, Dict[str, Any]] = {}

    def update(self, symbol: str, price: float, source: str, volume: float = 0.0):
        now = datetime.now(timezone.utc).isoformat()
        prev = self.prices.get(symbol, {}).get("price", price)
        self.prices[symbol] = {
            "symbol": symbol,
            "price": price,
            "prev_price": prev,
            "change_pct": ((price - prev) / prev * 100) if prev else 0.0,
            "volume": volume,
            "source": source,
            "updated_at": now,
        }

    def get(self, symbol: str) -> Optional[Dict]:
        return self.prices.get(symbol)

    def get_all(self) -> Dict[str, Dict]:
        return dict(self.prices)

    def get_top_movers(self, n: int = 10) -> List[Dict]:
        items = sorted(
            self.prices.values(), key=lambda x: abs(x.get("change_pct", 0)), reverse=True
        )
        return items[:n]


# Singleton store
_store = PriceSnapshot()


def get_price_snapshot(symbol: str) -> Optional[Dict]:
    """Get the latest price snapshot for a symbol."""
    return _store.get(symbol.upper())


def get_all_snapshots() -> Dict[str, Dict]:
    """Get all current price snapshots."""
    return _store.get_all()


def get_top_movers(n: int = 10) -> List[Dict]:
    """Get top N movers by absolute percent change."""
    return _store.get_top_movers(n)


def simulate_price_feed(symbols: List[str], base_prices: Optional[Dict[str, float]] = None) -> List[Dict]:
    """
    Simulate a price feed tick for given symbols (useful for testing/demo).
    Returns list of updated snapshots.
    """
    import random

    defaults = {"AAPL": 185.0, "MSFT": 420.0, "GOOGL": 175.0, "BTC-USD": 65000.0, "ETH-USD": 3500.0}
    if base_prices:
        defaults.update(base_prices)

    results = []
    for sym in symbols:
        base = defaults.get(sym, 100.0)
        noise = random.gauss(0, base * 0.002)
        price = round(base + noise, 4)
        _store.update(sym, price, source="simulation", volume=random.randint(100, 50000))
        results.append(_store.get(sym))
    return results


def build_coinbase_ws_message(product_ids: List[str]) -> str:
    """Build a Coinbase WebSocket subscribe message for given product IDs."""
    msg = {
        "type": "subscribe",
        "channels": [{"name": "ticker", "product_ids": product_ids}],
    }
    return json.dumps(msg)


def parse_coinbase_ticker(raw: Dict) -> Optional[Dict]:
    """Parse a Coinbase WebSocket ticker message into a standardized format."""
    if raw.get("type") != "ticker":
        return None
    return {
        "symbol": raw.get("product_id", ""),
        "price": float(raw.get("price", 0)),
        "volume_24h": float(raw.get("volume_24h", 0)),
        "best_bid": float(raw.get("best_bid", 0)),
        "best_ask": float(raw.get("best_ask", 0)),
        "time": raw.get("time", ""),
        "source": "coinbase",
    }
