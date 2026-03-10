#!/usr/bin/env python3
"""
Alpaca Market Data API — US Stocks, Crypto, Options Market Data

Data Source: Alpaca Markets (https://alpaca.markets)
Update: Real-time (IEX free tier) / 15-min delayed
History: 5+ years of bars, trades, quotes
Free: Yes (free tier with paper trading API keys — no payment required)

Provides:
- Historical OHLCV bars (minute, hour, day, week, month)
- Latest trade / quote / snapshot per symbol
- Multi-symbol snapshots for screening
- Crypto bars and snapshots (BTC, ETH, etc.)
- Trade and quote history

Setup:
  1. Create free account at https://app.alpaca.markets/signup
  2. Generate paper trading API keys (no payment needed)
  3. Export: APCA_API_KEY_ID and APCA_API_SECRET_KEY

Usage as Signal:
- Bar data for technical analysis (SMA, RSI, MACD)
- Quote spread analysis for liquidity assessment
- Snapshot data for real-time screening
- Crypto data for cross-asset correlation
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/alpaca")
os.makedirs(CACHE_DIR, exist_ok=True)

# Alpaca data API base URLs
STOCK_BASE = "https://data.alpaca.markets/v2/stocks"
CRYPTO_BASE = "https://data.alpaca.markets/v1beta3/crypto/us"

# Auth from environment (free paper-trading keys)
_KEY_ID = os.environ.get("APCA_API_KEY_ID", "")
_SECRET_KEY = os.environ.get("APCA_API_SECRET_KEY", "")

_HEADERS = {
    "APCA-API-KEY-ID": _KEY_ID,
    "APCA-API-SECRET-KEY": _SECRET_KEY,
    "Accept": "application/json",
}

_TIMEFRAMES = ("1Min", "5Min", "15Min", "30Min", "1Hour", "4Hour", "1Day", "1Week", "1Month")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_keys() -> None:
    """Raise if API keys are not configured."""
    if not _KEY_ID or not _SECRET_KEY:
        raise EnvironmentError(
            "Alpaca API keys not set. Export APCA_API_KEY_ID and "
            "APCA_API_SECRET_KEY (free paper-trading keys from https://app.alpaca.markets)."
        )


def _get(url: str, params: Optional[dict] = None, timeout: int = 15) -> dict:
    """Execute authenticated GET request and return JSON."""
    _check_keys()
    resp = requests.get(url, headers=_HEADERS, params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _cache_get(key: str, max_age_seconds: int = 300) -> Optional[dict]:
    """Return cached JSON if fresh enough, else None."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age.total_seconds() < max_age_seconds:
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data) -> None:
    """Write data to cache file."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f)


# ===================================================================
# STOCK FUNCTIONS
# ===================================================================

def get_stock_bars(
    symbol: str,
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    adjustment: str = "split",
) -> List[Dict]:
    """
    Fetch historical OHLCV bars for a US stock.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL', 'SPY').
        timeframe: Bar size — one of 1Min, 5Min, 15Min, 30Min,
                   1Hour, 4Hour, 1Day, 1Week, 1Month.
        start: Start date (RFC-3339 or YYYY-MM-DD). Default: 30 days ago.
        end: End date. Default: now.
        limit: Max bars to return (1-10000). Default 100.
        adjustment: Price adjustment — raw, split, dividend, all. Default split.

    Returns:
        List of bar dicts with keys: t, o, h, l, c, v, n, vw
        (timestamp, open, high, low, close, volume, trade_count, vwap)
    """
    if timeframe not in _TIMEFRAMES:
        raise ValueError(f"Invalid timeframe '{timeframe}'. Must be one of {_TIMEFRAMES}")

    if not start:
        start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "timeframe": timeframe,
        "start": start,
        "limit": min(limit, 10000),
        "adjustment": adjustment,
    }
    if end:
        params["end"] = end

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/bars", params)
    return data.get("bars", [])


def get_stock_latest_trade(symbol: str) -> Dict:
    """
    Get the latest trade for a stock symbol.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL').

    Returns:
        Dict with keys: t (timestamp), x (exchange), p (price),
        s (size), c (conditions), i (id), z (tape).
    """
    cache_key = f"latest_trade_{symbol.upper()}"
    cached = _cache_get(cache_key, max_age_seconds=60)
    if cached:
        return cached

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/trades/latest")
    result = data.get("trade", data)
    _cache_set(cache_key, result)
    return result


def get_stock_latest_quote(symbol: str) -> Dict:
    """
    Get the latest NBBO quote for a stock symbol.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL').

    Returns:
        Dict with keys: t, ax, ap, as, bx, bp, bs, c, z
        (timestamp, ask exchange/price/size, bid exchange/price/size, conditions, tape)
    """
    cache_key = f"latest_quote_{symbol.upper()}"
    cached = _cache_get(cache_key, max_age_seconds=30)
    if cached:
        return cached

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/quotes/latest")
    result = data.get("quote", data)
    _cache_set(cache_key, result)
    return result


def get_stock_snapshot(symbol: str) -> Dict:
    """
    Get a comprehensive snapshot for a stock: latest trade, quote,
    minute bar, daily bar, and previous daily bar.

    Args:
        symbol: Ticker symbol (e.g. 'SPY').

    Returns:
        Dict with keys: latestTrade, latestQuote, minuteBar,
        dailyBar, prevDailyBar.
    """
    cache_key = f"snapshot_{symbol.upper()}"
    cached = _cache_get(cache_key, max_age_seconds=60)
    if cached:
        return cached

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/snapshot")
    _cache_set(cache_key, data)
    return data


def get_multi_stock_snapshots(symbols: List[str]) -> Dict:
    """
    Get snapshots for multiple stocks in a single request.

    Args:
        symbols: List of ticker symbols (e.g. ['AAPL', 'MSFT', 'SPY']).

    Returns:
        Dict mapping symbol -> snapshot dict.
    """
    sym_str = ",".join(s.upper() for s in symbols)
    data = _get(f"{STOCK_BASE}/snapshots", {"symbols": sym_str})
    return data


def get_stock_trades(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """
    Fetch historical trades for a stock.

    Args:
        symbol: Ticker symbol.
        start: Start timestamp (RFC-3339 or YYYY-MM-DD).
        end: End timestamp.
        limit: Max trades (1-10000).

    Returns:
        List of trade dicts with keys: t, x, p, s, c, i, z.
    """
    params = {"limit": min(limit, 10000)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/trades", params)
    return data.get("trades", [])


def get_stock_quotes(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """
    Fetch historical quotes (NBBO) for a stock.

    Args:
        symbol: Ticker symbol.
        start: Start timestamp (RFC-3339 or YYYY-MM-DD).
        end: End timestamp.
        limit: Max quotes (1-10000).

    Returns:
        List of quote dicts.
    """
    params = {"limit": min(limit, 10000)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    data = _get(f"{STOCK_BASE}/{symbol.upper()}/quotes", params)
    return data.get("quotes", [])


# ===================================================================
# CRYPTO FUNCTIONS
# ===================================================================

def get_crypto_bars(
    symbol: str = "BTC/USD",
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """
    Fetch historical OHLCV bars for a crypto pair.

    Args:
        symbol: Crypto pair (e.g. 'BTC/USD', 'ETH/USD').
        timeframe: Bar size (1Min through 1Month).
        start: Start date (RFC-3339 or YYYY-MM-DD). Default: 30 days ago.
        end: End date.
        limit: Max bars (1-10000).

    Returns:
        List of bar dicts with keys: t, o, h, l, c, v, n, vw.
    """
    if timeframe not in _TIMEFRAMES:
        raise ValueError(f"Invalid timeframe '{timeframe}'. Must be one of {_TIMEFRAMES}")

    if not start:
        start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "timeframe": timeframe,
        "start": start,
        "limit": min(limit, 10000),
    }
    if end:
        params["end"] = end

    data = _get(f"{CRYPTO_BASE}/{symbol}/bars", params)
    return data.get("bars", [])


def get_crypto_latest_trade(symbol: str = "BTC/USD") -> Dict:
    """
    Get the latest trade for a crypto pair.

    Args:
        symbol: Crypto pair (e.g. 'BTC/USD').

    Returns:
        Dict with keys: t (timestamp), p (price), s (size), tks (taker side).
    """
    data = _get(f"{CRYPTO_BASE}/{symbol}/trades/latest")
    return data.get("trade", data)


def get_crypto_latest_quote(symbol: str = "BTC/USD") -> Dict:
    """
    Get the latest quote for a crypto pair.

    Args:
        symbol: Crypto pair (e.g. 'BTC/USD').

    Returns:
        Dict with keys: t, bp, bs, ap, as (bid/ask price/size).
    """
    data = _get(f"{CRYPTO_BASE}/{symbol}/quotes/latest")
    return data.get("quote", data)


def get_crypto_snapshot(symbol: str = "BTC/USD") -> Dict:
    """
    Get a snapshot for a crypto pair: latest trade, quote,
    minute bar, daily bar, previous daily bar.

    Args:
        symbol: Crypto pair (e.g. 'BTC/USD').

    Returns:
        Dict with snapshot data.
    """
    data = _get(f"{CRYPTO_BASE}/{symbol}/snapshot")
    return data


# ===================================================================
# UTILITY FUNCTIONS
# ===================================================================

def get_most_active_stocks(top: int = 20) -> List[Dict]:
    """
    Get snapshots of the most active US stocks by volume.
    Uses the /screener/stocks/most-actives endpoint.

    Args:
        top: Number of results (max 50).

    Returns:
        List of dicts with symbol, trade_count, volume, etc.
    """
    _check_keys()
    url = "https://data.alpaca.markets/v1beta1/screener/stocks/most-actives"
    params = {"top": min(top, 50)}
    resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("most_actives", [])


def get_market_movers(market_type: str = "stocks", top: int = 20) -> Dict:
    """
    Get top gainers and losers.

    Args:
        market_type: 'stocks' or 'crypto'.
        top: Number per category (max 50).

    Returns:
        Dict with 'gainers' and 'losers' lists.
    """
    _check_keys()
    base = "https://data.alpaca.markets/v1beta1/screener"
    url = f"{base}/{market_type}/movers"
    params = {"top": min(top, 50)}
    resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def check_api_status() -> Dict:
    """
    Quick health check — verifies API keys work by fetching AAPL latest trade.

    Returns:
        Dict with status, symbol, price, timestamp.
    """
    try:
        trade = get_stock_latest_trade("AAPL")
        return {
            "status": "ok",
            "symbol": "AAPL",
            "price": trade.get("p"),
            "timestamp": trade.get("t"),
            "api_keys_configured": bool(_KEY_ID and _SECRET_KEY),
        }
    except EnvironmentError:
        return {
            "status": "error",
            "error": "API keys not configured",
            "api_keys_configured": False,
            "setup": "Export APCA_API_KEY_ID and APCA_API_SECRET_KEY",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_keys_configured": bool(_KEY_ID and _SECRET_KEY),
        }


# ===================================================================
# MODULE INFO
# ===================================================================

MODULE_INFO = {
    "name": "alpaca_market_data_api",
    "description": "Alpaca Market Data — US stocks, crypto OHLCV, quotes, trades, snapshots",
    "source": "https://alpaca.markets",
    "category": "Exchanges & Market Microstructure",
    "free_tier": True,
    "requires_key": True,
    "key_env_vars": ["APCA_API_KEY_ID", "APCA_API_SECRET_KEY"],
    "update_frequency": "real-time",
    "functions": [
        "get_stock_bars",
        "get_stock_latest_trade",
        "get_stock_latest_quote",
        "get_stock_snapshot",
        "get_multi_stock_snapshots",
        "get_stock_trades",
        "get_stock_quotes",
        "get_crypto_bars",
        "get_crypto_latest_trade",
        "get_crypto_latest_quote",
        "get_crypto_snapshot",
        "get_most_active_stocks",
        "get_market_movers",
        "check_api_status",
    ],
}

if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))
    print("\n--- API Status ---")
    print(json.dumps(check_api_status(), indent=2))
