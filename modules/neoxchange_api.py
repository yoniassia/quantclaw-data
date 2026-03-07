"""
Market Microstructure Data — Order Book, Spreads, and Depth Analysis

Provides real-time market microstructure metrics using free public data sources.
Data: IEX Cloud API (free tier), Yahoo Finance quotes

Use cases:
- Bid-ask spread analysis
- Market depth monitoring
- Order book snapshots
- Trade imbalance detection
- Liquidity metrics for high-frequency strategies
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "neoxchange_api"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# IEX Cloud free tier - no API key required for basic quotes
BASE_URL = "https://api.iex.cloud/v1"
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"


def get_quote_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Fetch real-time quote data from Yahoo Finance."""
    cache_path = CACHE_DIR / f"quote_{ticker}.json"
    
    # Check cache (5-minute expiry for real-time data)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(minutes=5):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from Yahoo Finance
    url = f"{YAHOO_BASE}/{ticker}"
    params = {
        'range': '1d',
        'interval': '1m',
        'indicators': 'quote',
        'includePrePost': 'false'
    }
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            return None
        
        result = data['chart']['result'][0]
        meta = result.get('meta', {})
        
        quote_data = {
            'symbol': ticker,
            'price': meta.get('regularMarketPrice'),
            'bid': meta.get('bid'),
            'ask': meta.get('ask'),
            'bid_size': meta.get('bidSize'),
            'ask_size': meta.get('askSize'),
            'volume': meta.get('regularMarketVolume'),
            'timestamp': datetime.fromtimestamp(meta.get('regularMarketTime', 0)).isoformat() if meta.get('regularMarketTime') else None,
            'exchange': meta.get('exchangeName', 'N/A')
        }
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(quote_data, f, indent=2)
        
        return quote_data
    except Exception as e:
        print(f"Error fetching quote for {ticker}: {e}")
        return None


def get_bid_ask_spread(ticker: str) -> Optional[Dict]:
    """
    Calculate bid-ask spread metrics for a ticker.
    
    Returns:
        - absolute_spread: Ask - Bid
        - relative_spread: (Ask - Bid) / Midpoint
        - percentage_spread: Relative spread as percentage
    """
    quote = get_quote_data(ticker)
    if not quote or not quote.get('bid') or not quote.get('ask'):
        return None
    
    bid = float(quote['bid'])
    ask = float(quote['ask'])
    midpoint = (bid + ask) / 2
    
    absolute_spread = ask - bid
    relative_spread = absolute_spread / midpoint if midpoint > 0 else 0
    percentage_spread = relative_spread * 100
    
    return {
        'symbol': ticker,
        'bid': bid,
        'ask': ask,
        'midpoint': round(midpoint, 4),
        'absolute_spread': round(absolute_spread, 4),
        'relative_spread': round(relative_spread, 6),
        'percentage_spread': round(percentage_spread, 4),
        'timestamp': quote.get('timestamp'),
        'liquidity_quality': 'tight' if percentage_spread < 0.1 else 'normal' if percentage_spread < 0.5 else 'wide'
    }


def get_market_depth(ticker: str) -> Optional[Dict]:
    """
    Estimate market depth from bid/ask sizes.
    
    Returns depth metrics including:
        - bid_depth: Shares available at bid
        - ask_depth: Shares available at ask
        - depth_imbalance: Ratio of bid to ask depth
    """
    quote = get_quote_data(ticker)
    if not quote or not quote.get('bid_size') or not quote.get('ask_size'):
        return None
    
    bid_size = int(quote['bid_size'])
    ask_size = int(quote['ask_size'])
    total_depth = bid_size + ask_size
    
    # Depth imbalance: > 1 means more buying pressure, < 1 means more selling
    depth_imbalance = bid_size / ask_size if ask_size > 0 else 0
    
    return {
        'symbol': ticker,
        'bid_depth': bid_size,
        'ask_depth': ask_size,
        'total_depth': total_depth,
        'depth_imbalance': round(depth_imbalance, 3),
        'pressure': 'buy' if depth_imbalance > 1.2 else 'sell' if depth_imbalance < 0.8 else 'balanced',
        'timestamp': quote.get('timestamp')
    }


def get_trade_imbalance(ticker: str) -> Optional[Dict]:
    """
    Calculate trade imbalance from order book depth.
    
    Imbalance = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
    Positive = buying pressure, Negative = selling pressure
    """
    depth = get_market_depth(ticker)
    if not depth:
        return None
    
    bid_vol = depth['bid_depth']
    ask_vol = depth['ask_depth']
    total_vol = bid_vol + ask_vol
    
    imbalance = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0
    
    return {
        'symbol': ticker,
        'imbalance': round(imbalance, 4),
        'imbalance_pct': round(imbalance * 100, 2),
        'signal': 'strong_buy' if imbalance > 0.3 else 'buy' if imbalance > 0.1 else 'strong_sell' if imbalance < -0.3 else 'sell' if imbalance < -0.1 else 'neutral',
        'bid_volume': bid_vol,
        'ask_volume': ask_vol,
        'timestamp': depth.get('timestamp')
    }


def get_order_book_snapshot(ticker: str) -> Optional[Dict]:
    """
    Get a snapshot of the order book including best bid/ask and depth.
    
    Combines spread, depth, and imbalance metrics.
    """
    quote = get_quote_data(ticker)
    if not quote:
        return None
    
    spread = get_bid_ask_spread(ticker)
    depth = get_market_depth(ticker)
    imbalance = get_trade_imbalance(ticker)
    
    return {
        'symbol': ticker,
        'timestamp': quote.get('timestamp'),
        'price': quote.get('price'),
        'volume': quote.get('volume'),
        'exchange': quote.get('exchange'),
        'best_bid': quote.get('bid'),
        'best_ask': quote.get('ask'),
        'spread': spread.get('absolute_spread') if spread else None,
        'spread_pct': spread.get('percentage_spread') if spread else None,
        'bid_depth': depth.get('bid_depth') if depth else None,
        'ask_depth': depth.get('ask_depth') if depth else None,
        'imbalance': imbalance.get('imbalance') if imbalance else None,
        'liquidity_quality': spread.get('liquidity_quality') if spread else None,
        'pressure': depth.get('pressure') if depth else None
    }


def get_microstructure_summary(ticker: str) -> pd.DataFrame:
    """
    Get comprehensive microstructure summary as DataFrame.
    
    Returns all key metrics in a formatted table.
    """
    snapshot = get_order_book_snapshot(ticker)
    if not snapshot:
        return pd.DataFrame()
    
    def fmt_price(val):
        return f"${val:.2f}" if val is not None else "N/A"
    
    def fmt_num(val, decimals=4):
        return f"{val:.{decimals}f}" if val is not None else "N/A"
    
    def fmt_int(val):
        return f"{val:,}" if val is not None else "N/A"
    
    records = [
        {'metric': 'Symbol', 'value': snapshot.get('symbol')},
        {'metric': 'Price', 'value': fmt_price(snapshot.get('price'))},
        {'metric': 'Best Bid', 'value': fmt_price(snapshot.get('best_bid'))},
        {'metric': 'Best Ask', 'value': fmt_price(snapshot.get('best_ask'))},
        {'metric': 'Spread', 'value': fmt_price(snapshot.get('spread'))},
        {'metric': 'Spread %', 'value': f"{fmt_num(snapshot.get('spread_pct'), 3)}%" if snapshot.get('spread_pct') is not None else "N/A"},
        {'metric': 'Bid Depth', 'value': f"{fmt_int(snapshot.get('bid_depth'))} shares" if snapshot.get('bid_depth') is not None else "N/A"},
        {'metric': 'Ask Depth', 'value': f"{fmt_int(snapshot.get('ask_depth'))} shares" if snapshot.get('ask_depth') is not None else "N/A"},
        {'metric': 'Imbalance', 'value': fmt_num(snapshot.get('imbalance'))},
        {'metric': 'Liquidity', 'value': snapshot.get('liquidity_quality', 'N/A')},
        {'metric': 'Pressure', 'value': snapshot.get('pressure', 'N/A')},
        {'metric': 'Volume', 'value': fmt_int(snapshot.get('volume'))},
        {'metric': 'Exchange', 'value': snapshot.get('exchange', 'N/A')},
        {'metric': 'Timestamp', 'value': snapshot.get('timestamp', 'N/A')}
    ]
    
    return pd.DataFrame(records)


def cli_snapshot(ticker: str):
    """CLI: Display order book snapshot."""
    snapshot = get_order_book_snapshot(ticker.upper())
    if not snapshot:
        print(f"No data available for {ticker}")
        return
    
    print(f"\n=== Order Book Snapshot: {ticker.upper()} ===")
    print(f"Time: {snapshot.get('timestamp', 'N/A')}")
    print(f"Exchange: {snapshot.get('exchange', 'N/A')}")
    print(f"\nPrice: ${snapshot.get('price', 0):.2f}")
    print(f"Best Bid: ${snapshot.get('best_bid', 0):.2f} ({snapshot.get('bid_depth', 0):,} shares)")
    print(f"Best Ask: ${snapshot.get('best_ask', 0):.2f} ({snapshot.get('ask_depth', 0):,} shares)")
    print(f"Spread: ${snapshot.get('spread', 0):.4f} ({snapshot.get('spread_pct', 0):.3f}%)")
    print(f"Imbalance: {snapshot.get('imbalance', 0):.4f}")
    print(f"Liquidity: {snapshot.get('liquidity_quality', 'N/A')}")
    print(f"Pressure: {snapshot.get('pressure', 'N/A')}")
    print(f"Volume: {snapshot.get('volume', 0):,}")


def cli_spread(ticker: str):
    """CLI: Display bid-ask spread analysis."""
    spread = get_bid_ask_spread(ticker.upper())
    if not spread:
        print(f"No spread data available for {ticker}")
        return
    
    print(f"\n=== Bid-Ask Spread: {ticker.upper()} ===")
    print(f"Bid: ${spread.get('bid', 0):.2f}")
    print(f"Ask: ${spread.get('ask', 0):.2f}")
    print(f"Midpoint: ${spread.get('midpoint', 0):.4f}")
    print(f"Absolute Spread: ${spread.get('absolute_spread', 0):.4f}")
    print(f"Percentage Spread: {spread.get('percentage_spread', 0):.4f}%")
    print(f"Quality: {spread.get('liquidity_quality', 'N/A')}")


def cli_depth(ticker: str):
    """CLI: Display market depth analysis."""
    depth = get_market_depth(ticker.upper())
    if not depth:
        print(f"No depth data available for {ticker}")
        return
    
    print(f"\n=== Market Depth: {ticker.upper()} ===")
    print(f"Bid Depth: {depth.get('bid_depth', 0):,} shares")
    print(f"Ask Depth: {depth.get('ask_depth', 0):,} shares")
    print(f"Total Depth: {depth.get('total_depth', 0):,} shares")
    print(f"Depth Imbalance: {depth.get('depth_imbalance', 0):.3f}")
    print(f"Pressure: {depth.get('pressure', 'N/A')}")


def cli_imbalance(ticker: str):
    """CLI: Display trade imbalance."""
    imbalance = get_trade_imbalance(ticker.upper())
    if not imbalance:
        print(f"No imbalance data available for {ticker}")
        return
    
    print(f"\n=== Trade Imbalance: {ticker.upper()} ===")
    print(f"Imbalance: {imbalance.get('imbalance', 0):.4f} ({imbalance.get('imbalance_pct', 0):.2f}%)")
    print(f"Signal: {imbalance.get('signal', 'N/A')}")
    print(f"Bid Volume: {imbalance.get('bid_volume', 0):,} shares")
    print(f"Ask Volume: {imbalance.get('ask_volume', 0):,} shares")


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python neoxchange_api.py <command> <ticker>")
        print("Commands: snapshot, spread, depth, imbalance")
        print("Example: python neoxchange_api.py snapshot AAPL")
        sys.exit(0)
    
    command = args[0].lower()
    ticker = args[1] if len(args) > 1 else "AAPL"
    
    if command == "snapshot":
        cli_snapshot(ticker)
    elif command == "spread":
        cli_spread(ticker)
    elif command == "depth":
        cli_depth(ticker)
    elif command == "imbalance":
        cli_imbalance(ticker)
    else:
        print(f"Unknown command: {command}")
        print("Available: snapshot, spread, depth, imbalance")
        sys.exit(1)
