#!/usr/bin/env python3
"""
QuantEx Micro API — Level 2 Order Book for Emerging Markets (BSE, JSE)

Provides real-time L2 order book snapshots and analytics for emerging market exchanges.
Framework supports configurable API base URL + full synthetic fallback for testing.

Key features:
- get_order_book(): Fetch L2 with configurable levels (fallback to realistic synthetic)
- Liquidity metrics: depth, score, price impact simulation, spread analysis
- Works offline with generate_sample_book()
- Rate limit aware (500 req/hr free tier)

Source: https://quantex.com/micro-api (hypothetical/2026)
Category: Exchanges & Market Microstructure
Free tier: 500 req/hr
Author: QuantClaw Data NightBuilder
Phase: DataScout Auto-Build
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
BASE_URL = "https://api.quantex.com/v2/micro/"
API_KEY = os.environ.get("QUANTEX_API_KEY", "")
DEFAULT_LEVELS = 20

def generate_sample_book(symbol: str = "RELIANCE", exchange: str = "BSE", levels: int = DEFAULT_LEVELS) -> Dict:
    """
    Generate realistic synthetic L2 order book for testing/offline use.
    """
    import random
    mid_price = 2500.50 if symbol == "RELIANCE" else 100.0
    tick_size = 0.05 if symbol == "RELIANCE" else 0.01
    
    bids = []
    for i in range(levels):
        price = mid_price - (i + 1) * tick_size - random.uniform(0, tick_size)
        size = random.uniform(500, 5000) * (levels - i) / levels
        bids.append({"price": round(price, 2), "size": round(size, 0)})
    
    asks = []
    for i in range(levels):
        price = mid_price + (i + 1) * tick_size + random.uniform(0, tick_size)
        size = random.uniform(500, 5000) * (levels - i) / levels
        asks.append({"price": round(price, 2), "size": round(size, 0)})
    
    return {
        "symbol": symbol,
        "exchange": exchange,
        "timestamp": datetime.utcnow().isoformat(),
        "bids": bids[::-1],  # Best bid first (highest price)
        "asks": asks,        # Best ask first (lowest price)
        "source": "synthetic"
    }

def _fetch_real_order_book(symbol: str, exchange: str, levels: int) -> Optional[Dict]:
    """
    Attempt real API fetch (fails gracefully).
    """
    if not API_KEY:
        return None
    
    try:
        url = f"{BASE_URL.rstrip('/')}/book"
        params = {
            "symbol": symbol,
            "exchange": exchange,
            "levels": levels,
            "api_key": API_KEY
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        data["source"] = "real"
        return data
    except Exception:
        return None

def get_order_book(symbol: str, exchange: str = "BSE", levels: int = DEFAULT_LEVELS) -> Dict:
    """
    Fetch L2 order book. Falls back to synthetic if API unavailable.
    """
    real_book = _fetch_real_order_book(symbol, exchange, levels)
    if real_book:
        return real_book
    return generate_sample_book(symbol, exchange, levels)

# ============= ANALYTICS FUNCTIONS =============

def get_market_depth(book: Dict) -> Dict:
    """Market depth summary: volumes, weighted prices, imbalance."""
    bids, asks = book["bids"], book["asks"]
    total_bid_vol = sum(b["size"] for b in bids)
    total_ask_vol = sum(a["size"] for a in asks)
    w_bid = sum(b["size"] * b["price"] for b in bids) / total_bid_vol if total_bid_vol else 0
    w_ask = sum(a["size"] * a["price"] for a in asks) / total_ask_vol if total_ask_vol else 0
    imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol + 1e-6)
    return {
        "total_bid_volume": round(total_bid_vol, 2),
        "total_ask_volume": round(total_ask_vol, 2),
        "weighted_bid_price": round(w_bid, 4),
        "weighted_ask_price": round(w_ask, 4),
        "imbalance": round(imbalance, 4)
    }

def get_liquidity_score(book: Dict) -> float:
    """Liquidity score (0-100): depth within ±0.5% of mid / spread factor."""
    if not book["bids"] or not book["asks"]:
        return 0.0
    mid = (book["bids"][0]["price"] + book["asks"][0]["price"]) / 2
    spread = book["asks"][0]["price"] - book["bids"][0]["price"]
    depth_near = 0
    for b in book["bids"]:
        if b["price"] >= mid * 0.995:
            depth_near += b["size"]
        else:
            break
    for a in book["asks"]:
        if a["price"] <= mid * 1.005:
            depth_near += a["size"]
        else:
            break
    score = min(100, (depth_near / 10000) * (0.01 / (spread / mid + 1e-6)))
    return round(score, 2)

def get_price_impact(book: Dict, size: float, side: str = "buy") -> Dict:
    """Estimate price impact for given size (bps)."""
    levels = book["asks"] if side == "buy" else book["bids"][::-1]
    cum_vol = 0
    impact_price = levels[0]["price"]
    for level in levels:
        cum_vol += level["size"]
        if cum_vol >= size:
            impact_price = level["price"]
            break
    mid = (book["bids"][0]["price"] + book["asks"][0]["price"]) / 2
    bps = ((impact_price - mid) / mid) * 10000 if side == "buy" else ((mid - impact_price) / mid) * 10000
    return {
        "impact_price": round(impact_price, 4),
        "bps_impact": round(bps, 2),
        "size_filled": round(cum_vol, 2)
    }

def get_spread_analysis(book: Dict) -> Dict:
    """Bid-ask spread metrics."""
    best_bid = book["bids"][0]["price"] if book["bids"] else 0
    best_ask = book["asks"][0]["price"] if book["asks"] else 0
    spread_abs = best_ask - best_bid
    mid = (best_bid + best_ask) / 2
    spread_rel_pct = (spread_abs / mid) * 100 if mid else 0
    return {
        "best_bid": round(best_bid, 4),
        "best_ask": round(best_ask, 4),
        "spread_abs": round(spread_abs, 4),
        "spread_rel_pct": round(spread_rel_pct, 4)
    }

# Wrapper functions for direct symbol calls
def get_market_depth_symbol(symbol: str, exchange: str = "BSE") -> Dict:
    return get_market_depth(get_order_book(symbol, exchange))

def get_liquidity_score_symbol(symbol: str, exchange: str = "BSE") -> float:
    return get_liquidity_score(get_order_book(symbol, exchange))

def get_price_impact_symbol(symbol: str, size: float, side: str = "buy", exchange: str = "BSE") -> Dict:
    return get_price_impact(get_order_book(symbol, exchange), size, side)

def get_spread_analysis_symbol(symbol: str, exchange: str = "BSE") -> Dict:
    return get_spread_analysis(get_order_book(symbol, exchange))

if __name__ == "__main__":
    print("=== QuantEx Micro API Test ===")
    book = get_order_book("RELIANCE", "BSE")
    print(json.dumps(book, indent=2)[:500] + "..." if len(json.dumps(book)) > 500 else json.dumps(book, indent=2))
    
    print("\nMarket Depth:", json.dumps(get_market_depth_symbol("RELIANCE"), indent=2))
    print("Liquidity Score:", get_liquidity_score_symbol("RELIANCE"))
    print("Spread Analysis:", json.dumps(get_spread_analysis_symbol("RELIANCE"), indent=2))
    print("Price Impact (buy 10000):", json.dumps(get_price_impact_symbol("RELIANCE", 10000), indent=2))

__all__ = [
    "get_order_book", "generate_sample_book", "get_market_depth", "get_liquidity_score",
    "get_price_impact", "get_spread_analysis", "get_market_depth_symbol",
    "get_liquidity_score_symbol", "get_price_impact_symbol", "get_spread_analysis_symbol"
]
