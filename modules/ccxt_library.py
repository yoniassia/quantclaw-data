"""
CCXT Library — Unified Crypto Exchange API (400+ Exchanges)

Data Source: CCXT library (pip install ccxt)
Update: Real-time (exchange API calls)
History: Varies by exchange (some offer years of OHLCV)
Free: Yes (no API key needed for public endpoints)

Provides:
- Ticker data (bid/ask/last/volume) from any exchange
- OHLCV candlestick data (1m to 1M timeframes)
- Order book depth (bids/asks)
- Exchange listing & market info
- Multi-exchange price comparison / arbitrage detection
- Funding rates for perpetual futures

Usage:
- Real-time crypto prices from 400+ exchanges
- Historical candlestick data for backtesting
- Cross-exchange arbitrage detection
- Market structure analysis (spreads, depth, volume)
"""

import ccxt
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/ccxt")
os.makedirs(CACHE_DIR, exist_ok=True)

# Default exchanges for multi-exchange queries
DEFAULT_EXCHANGES = ["binance", "coinbasepro", "kraken", "bybit", "okx"]


def list_exchanges() -> List[str]:
    """
    List all supported exchange IDs.

    Returns:
        List of exchange ID strings (e.g. ['binance', 'kraken', ...])
    """
    return ccxt.exchanges


def get_exchange(exchange_id: str = "binance") -> ccxt.Exchange:
    """
    Instantiate a CCXT exchange object.

    Args:
        exchange_id: Exchange identifier (e.g. 'binance', 'kraken')

    Returns:
        ccxt.Exchange instance

    Raises:
        ValueError: If exchange_id is not supported
    """
    exchange_id = exchange_id.lower()
    if exchange_id not in ccxt.exchanges:
        raise ValueError(f"Unknown exchange: {exchange_id}. Use list_exchanges() to see available.")
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({"enableRateLimit": True})


def fetch_ticker(symbol: str = "BTC/USDT", exchange_id: str = "binance") -> Dict:
    """
    Fetch current ticker for a trading pair.

    Args:
        symbol: Trading pair (e.g. 'BTC/USDT', 'ETH/BTC')
        exchange_id: Exchange to query

    Returns:
        Dict with keys: symbol, last, bid, ask, high, low, volume,
        change_pct, vwap, timestamp, exchange
    """
    try:
        exchange = get_exchange(exchange_id)
        ticker = exchange.fetch_ticker(symbol)
        return {
            "symbol": ticker.get("symbol"),
            "last": ticker.get("last"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
            "high": ticker.get("high"),
            "low": ticker.get("low"),
            "volume": ticker.get("baseVolume"),
            "quote_volume": ticker.get("quoteVolume"),
            "change_pct": ticker.get("percentage"),
            "vwap": ticker.get("vwap"),
            "timestamp": ticker.get("datetime"),
            "exchange": exchange_id,
        }
    except ccxt.BadSymbol as e:
        return {"error": f"Bad symbol '{symbol}' on {exchange_id}", "detail": str(e)}
    except ccxt.NetworkError as e:
        return {"error": f"Network error on {exchange_id}", "detail": str(e)}
    except Exception as e:
        return {"error": str(e), "exchange": exchange_id}


def fetch_tickers(symbols: Optional[List[str]] = None, exchange_id: str = "binance") -> List[Dict]:
    """
    Fetch tickers for multiple symbols at once.

    Args:
        symbols: List of trading pairs. None = all available.
        exchange_id: Exchange to query

    Returns:
        List of ticker dicts
    """
    try:
        exchange = get_exchange(exchange_id)
        tickers = exchange.fetch_tickers(symbols)
        results = []
        for sym, t in tickers.items():
            results.append({
                "symbol": t.get("symbol"),
                "last": t.get("last"),
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "volume": t.get("baseVolume"),
                "change_pct": t.get("percentage"),
                "exchange": exchange_id,
            })
        return results
    except Exception as e:
        return [{"error": str(e), "exchange": exchange_id}]


def fetch_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "1d",
    limit: int = 100,
    exchange_id: str = "binance",
    since: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch OHLCV candlestick data.

    Args:
        symbol: Trading pair
        timeframe: Candle period ('1m','5m','15m','1h','4h','1d','1w','1M')
        limit: Number of candles (max varies by exchange, typically 500-1000)
        exchange_id: Exchange to query
        since: Start date string 'YYYY-MM-DD' (optional)

    Returns:
        List of dicts with: timestamp, open, high, low, close, volume
    """
    try:
        exchange = get_exchange(exchange_id)
        since_ms = None
        if since:
            since_ms = exchange.parse8601(since + "T00:00:00Z")

        raw = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
        candles = []
        for c in raw:
            candles.append({
                "timestamp": exchange.iso8601(c[0]),
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5],
            })
        return candles
    except Exception as e:
        return [{"error": str(e), "exchange": exchange_id}]


def fetch_order_book(symbol: str = "BTC/USDT", exchange_id: str = "binance", depth: int = 10) -> Dict:
    """
    Fetch order book (bids and asks).

    Args:
        symbol: Trading pair
        exchange_id: Exchange to query
        depth: Number of price levels per side

    Returns:
        Dict with bids, asks (each a list of [price, amount]),
        spread, spread_pct, mid_price, timestamp
    """
    try:
        exchange = get_exchange(exchange_id)
        book = exchange.fetch_order_book(symbol, limit=depth)
        bids = book.get("bids", [])[:depth]
        asks = book.get("asks", [])[:depth]

        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = best_ask - best_bid if best_bid and best_ask else 0
        mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
        spread_pct = (spread / mid * 100) if mid else 0

        return {
            "symbol": symbol,
            "exchange": exchange_id,
            "bids": bids,
            "asks": asks,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": round(spread, 8),
            "spread_pct": round(spread_pct, 4),
            "mid_price": round(mid, 8),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "exchange": exchange_id}


def fetch_markets(exchange_id: str = "binance") -> List[Dict]:
    """
    List all markets/trading pairs on an exchange.

    Args:
        exchange_id: Exchange to query

    Returns:
        List of dicts with: symbol, base, quote, type, active
    """
    try:
        exchange = get_exchange(exchange_id)
        exchange.load_markets()
        markets = []
        for sym, m in exchange.markets.items():
            markets.append({
                "symbol": m.get("symbol"),
                "base": m.get("base"),
                "quote": m.get("quote"),
                "type": m.get("type"),
                "active": m.get("active"),
            })
        return markets
    except Exception as e:
        return [{"error": str(e), "exchange": exchange_id}]


def compare_price(symbol: str = "BTC/USDT", exchanges: Optional[List[str]] = None) -> Dict:
    """
    Compare price of a symbol across multiple exchanges for arbitrage detection.

    Args:
        symbol: Trading pair to compare
        exchanges: List of exchange IDs (defaults to DEFAULT_EXCHANGES)

    Returns:
        Dict with per-exchange prices, best_bid, best_ask,
        arbitrage spread, and signal
    """
    if exchanges is None:
        exchanges = DEFAULT_EXCHANGES

    results = {}
    for eid in exchanges:
        try:
            t = fetch_ticker(symbol, eid)
            if "error" not in t:
                results[eid] = {
                    "bid": t["bid"],
                    "ask": t["ask"],
                    "last": t["last"],
                    "volume": t["volume"],
                }
        except Exception:
            continue

    if len(results) < 2:
        return {"error": "Need at least 2 exchanges for comparison", "found": list(results.keys())}

    best_bid_exchange = max(results, key=lambda x: results[x]["bid"] or 0)
    best_ask_exchange = min(results, key=lambda x: results[x]["ask"] or float("inf"))

    best_bid = results[best_bid_exchange]["bid"]
    best_ask = results[best_ask_exchange]["ask"]
    arb_spread = best_bid - best_ask if best_bid and best_ask else 0
    arb_pct = (arb_spread / best_ask * 100) if best_ask else 0

    return {
        "symbol": symbol,
        "prices": results,
        "best_bid": {"exchange": best_bid_exchange, "price": best_bid},
        "best_ask": {"exchange": best_ask_exchange, "price": best_ask},
        "arb_spread": round(arb_spread, 8),
        "arb_pct": round(arb_pct, 4),
        "signal": "ARBITRAGE" if arb_pct > 0.1 else "NO_ARB",
        "timestamp": datetime.utcnow().isoformat(),
    }


def fetch_funding_rate(symbol: str = "BTC/USDT", exchange_id: str = "binance") -> Dict:
    """
    Fetch funding rate for perpetual futures contracts.

    Args:
        symbol: Perpetual contract symbol (e.g. 'BTC/USDT')
        exchange_id: Exchange supporting futures (binance, bybit, okx)

    Returns:
        Dict with funding_rate, next_funding_time, mark_price
    """
    try:
        exchange = get_exchange(exchange_id)
        # Some exchanges need linear swap market symbol
        # Try to fetch funding rate from the exchange
        if hasattr(exchange, "fetch_funding_rate"):
            fr = exchange.fetch_funding_rate(symbol)
            return {
                "symbol": fr.get("symbol", symbol),
                "funding_rate": fr.get("fundingRate"),
                "funding_timestamp": fr.get("fundingDatetime"),
                "mark_price": fr.get("markPrice"),
                "index_price": fr.get("indexPrice"),
                "exchange": exchange_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            return {"error": f"{exchange_id} does not support fetch_funding_rate", "exchange": exchange_id}
    except Exception as e:
        return {"error": str(e), "exchange": exchange_id}


def get_exchange_status(exchange_id: str = "binance") -> Dict:
    """
    Check if an exchange API is operational.

    Args:
        exchange_id: Exchange to check

    Returns:
        Dict with status, url, rate_limit info
    """
    try:
        exchange = get_exchange(exchange_id)
        status = exchange.fetch_status() if hasattr(exchange, "fetch_status") else {}
        return {
            "exchange": exchange_id,
            "status": status.get("status", "ok"),
            "message": status.get("msg", ""),
            "url": exchange.urls.get("www", ""),
            "rate_limit": exchange.rateLimit,
            "has_ohlcv": exchange.has.get("fetchOHLCV", False),
            "has_order_book": exchange.has.get("fetchOrderBook", False),
            "has_funding_rate": exchange.has.get("fetchFundingRate", False),
            "timeframes": list(exchange.timeframes.keys()) if hasattr(exchange, "timeframes") and exchange.timeframes else [],
        }
    except Exception as e:
        return {"error": str(e), "exchange": exchange_id}


def fetch_top_volume(exchange_id: str = "binance", quote: str = "USDT", top_n: int = 20) -> List[Dict]:
    """
    Get top traded pairs by volume on an exchange.

    Args:
        exchange_id: Exchange to query
        quote: Quote currency filter (e.g. 'USDT', 'BTC')
        top_n: Number of top pairs to return

    Returns:
        Sorted list of dicts with symbol, volume, last price
    """
    try:
        exchange = get_exchange(exchange_id)
        tickers = exchange.fetch_tickers()
        filtered = []
        for sym, t in tickers.items():
            if quote and f"/{quote}" not in sym:
                continue
            vol = t.get("quoteVolume") or 0
            if vol > 0:
                filtered.append({
                    "symbol": t.get("symbol"),
                    "last": t.get("last"),
                    "volume_quote": round(vol, 2),
                    "change_pct": t.get("percentage"),
                })
        filtered.sort(key=lambda x: x["volume_quote"], reverse=True)
        return filtered[:top_n]
    except Exception as e:
        return [{"error": str(e), "exchange": exchange_id}]


# === CLI Commands ===

def cli_ticker(symbol: str = "BTC/USDT", exchange_id: str = "binance"):
    """Show current ticker"""
    data = fetch_ticker(symbol, exchange_id)
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    print(f"\n📊 {data['symbol']} on {data['exchange']}")
    print("=" * 50)
    print(f"💰 Last:    ${data['last']:,.2f}")
    print(f"📈 High:    ${data['high']:,.2f}")
    print(f"📉 Low:     ${data['low']:,.2f}")
    print(f"🔀 Bid/Ask: ${data['bid']:,.2f} / ${data['ask']:,.2f}")
    pct = data.get('change_pct')
    if pct is not None:
        emoji = "🟢" if pct >= 0 else "🔴"
        print(f"{emoji} 24h:    {pct:+.2f}%")
    print(f"📦 Volume:  {data['volume']:,.2f}")
    print(f"🕐 Time:    {data['timestamp']}")


def cli_arb(symbol: str = "BTC/USDT"):
    """Show cross-exchange arbitrage"""
    data = compare_price(symbol)
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    print(f"\n🔄 Arbitrage Check: {data['symbol']}")
    print("=" * 50)
    for eid, p in data["prices"].items():
        print(f"  {eid:15s}  bid: ${p['bid']:,.2f}  ask: ${p['ask']:,.2f}")
    print(f"\n✅ Best Bid: {data['best_bid']['exchange']} @ ${data['best_bid']['price']:,.2f}")
    print(f"✅ Best Ask: {data['best_ask']['exchange']} @ ${data['best_ask']['price']:,.2f}")
    print(f"📊 Arb Spread: ${data['arb_spread']:,.2f} ({data['arb_pct']:+.4f}%)")
    print(f"🚦 Signal: {data['signal']}")


def cli_top(exchange_id: str = "binance", quote: str = "USDT"):
    """Show top volume pairs"""
    data = fetch_top_volume(exchange_id, quote, top_n=15)
    if data and "error" in data[0]:
        print(f"❌ {data[0]['error']}")
        return
    print(f"\n📊 Top Volume ({quote}) on {exchange_id}")
    print("=" * 60)
    for i, d in enumerate(data, 1):
        pct = d.get("change_pct")
        pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
        print(f"  {i:2d}. {d['symbol']:15s}  ${d['last']:>12,.2f}  Vol: ${d['volume_quote']:>15,.0f}  {pct_str}")


if __name__ == "__main__":
    cli_ticker()
