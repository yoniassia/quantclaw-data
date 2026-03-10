"""
Polygon.io Options API — Real-time and Historical Options Data

Data Source: Polygon.io
Update: Real-time (delayed 15 min on free tier)
Free tier: 5 API calls per minute, delayed data, requires free API key
API Key: Set POLYGON_API_KEY env var or uses demo fallback

Provides:
- Options contracts listing and search
- Options chain for a given underlying ticker
- Last trade for an options contract
- Last quote (NBBO) for an options contract
- Options contract details (strike, expiry, type)
- Previous day OHLCV for options contracts
- Options snapshots (full chain snapshot)

Source: https://polygon.io/docs/options/getting-started
Category: Quant Tools & ML
Update frequency: real-time (15-min delay free tier)
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


API_BASE = "https://api.polygon.io"
API_KEY = os.environ.get("POLYGON_API_KEY", "demo")

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/polygon_io_options_api")
os.makedirs(CACHE_DIR, exist_ok=True)


def _request(url: str, timeout: int = 15) -> dict:
    """Internal helper to make API requests with error handling."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "QuantClaw/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:500]
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": body}
    except urllib.error.URLError as e:
        return {"error": f"URL error: {str(e.reason)}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def get_options_contracts(
    underlying_ticker: str,
    contract_type: Optional[str] = None,
    expiration_date: Optional[str] = None,
    strike_price: Optional[float] = None,
    expired: bool = False,
    limit: int = 50,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    List options contracts for an underlying ticker.

    Args:
        underlying_ticker: Underlying stock symbol (e.g., 'AAPL', 'SPY')
        contract_type: Filter by 'call' or 'put'
        expiration_date: Filter by expiry (YYYY-MM-DD)
        strike_price: Filter by exact strike price
        expired: Include expired contracts (default False)
        limit: Max results to return (max 1000)
        apikey: Polygon.io API key

    Returns:
        Dict with 'results' list of contract objects, each containing:
        - ticker: Options contract ticker (e.g., 'O:AAPL250321C00170000')
        - underlying_ticker: Underlying stock symbol
        - contract_type: 'call' or 'put'
        - strike_price: Strike price
        - expiration_date: Expiry date
        - exercise_style: 'american' or 'european'
        - shares_per_contract: Typically 100

    Example:
        >>> contracts = get_options_contracts('AAPL', contract_type='call', limit=5)
        >>> for c in contracts.get('results', []):
        ...     print(c['ticker'], c['strike_price'], c['expiration_date'])
    """
    key = apikey or API_KEY
    ticker = underlying_ticker.upper()

    params = {
        "underlying_ticker": ticker,
        "expired": str(expired).lower(),
        "limit": min(limit, 1000),
        "order": "asc",
        "sort": "expiration_date",
        "apiKey": key,
    }
    if contract_type:
        params["contract_type"] = contract_type.lower()
    if expiration_date:
        params["expiration_date"] = expiration_date
    if strike_price is not None:
        params["strike_price"] = strike_price

    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE}/v3/reference/options/contracts?{qs}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "underlying_ticker": ticker, "results": []}

    results = data.get("results", [])
    return {
        "underlying_ticker": ticker,
        "count": len(results),
        "results": results,
        "status": data.get("status", "unknown"),
    }


def get_options_chain(
    ticker: str,
    expiration_date: Optional[str] = None,
    limit: int = 50,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the full options chain (calls + puts) for a ticker.

    Fetches both call and put contracts and groups them by expiration date.

    Args:
        ticker: Underlying stock symbol (e.g., 'AAPL', 'SPY')
        expiration_date: Filter to specific expiry (YYYY-MM-DD)
        limit: Max contracts per side (calls/puts)
        apikey: Polygon.io API key

    Returns:
        Dict with:
        - ticker: Underlying symbol
        - expirations: List of unique expiration dates found
        - calls: List of call contracts
        - puts: List of put contracts
        - total_contracts: Total number of contracts

    Example:
        >>> chain = get_options_chain('AAPL')
        >>> print(f"Calls: {len(chain['calls'])}, Puts: {len(chain['puts'])}")
    """
    key = apikey or API_KEY
    ticker = ticker.upper()

    calls = get_options_contracts(
        ticker, contract_type="call", expiration_date=expiration_date,
        limit=limit, apikey=key
    )
    puts = get_options_contracts(
        ticker, contract_type="put", expiration_date=expiration_date,
        limit=limit, apikey=key
    )

    call_results = calls.get("results", [])
    put_results = puts.get("results", [])

    expirations = sorted(set(
        c.get("expiration_date", "") for c in call_results + put_results
        if c.get("expiration_date")
    ))

    return {
        "ticker": ticker,
        "expirations": expirations,
        "calls": call_results,
        "puts": put_results,
        "total_contracts": len(call_results) + len(put_results),
    }


def get_option_trade(
    options_ticker: str,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the last trade for a specific options contract.

    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00170000')
                       If no 'O:' prefix, it will be added automatically.
        apikey: Polygon.io API key

    Returns:
        Dict with last trade info:
        - symbol: Options ticker
        - price: Last trade price
        - size: Number of contracts traded
        - exchange: Exchange ID
        - timestamp: Trade timestamp (ms)
        - conditions: Trade condition codes

    Example:
        >>> trade = get_option_trade('O:AAPL250321C00170000')
        >>> print(f"Last trade: ${trade.get('price')} x {trade.get('size')}")
    """
    key = apikey or API_KEY
    symbol = options_ticker.upper()
    if not symbol.startswith("O:"):
        symbol = f"O:{symbol}"

    url = f"{API_BASE}/v2/last/trade/{symbol}?apiKey={key}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "symbol": symbol}

    if data.get("status") == "ERROR":
        return {"error": data.get("error", "Unknown API error"), "symbol": symbol}

    results = data.get("results", {})
    if not results:
        return {"error": "No trade data returned", "symbol": symbol}

    return {
        "symbol": symbol,
        "price": results.get("p"),
        "size": results.get("s"),
        "exchange": results.get("x"),
        "timestamp": results.get("t"),
        "conditions": results.get("c", []),
        "status": "ok",
    }


def get_option_quote(
    options_ticker: str,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the last NBBO quote for a specific options contract.

    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00170000')
                       If no 'O:' prefix, it will be added automatically.
        apikey: Polygon.io API key

    Returns:
        Dict with last quote info:
        - symbol: Options ticker
        - bid: Best bid price
        - bid_size: Bid size (contracts)
        - ask: Best ask price
        - ask_size: Ask size (contracts)
        - midpoint: Midpoint between bid and ask
        - spread: Ask - bid
        - timestamp: Quote timestamp (ns)

    Example:
        >>> quote = get_option_quote('O:AAPL250321C00170000')
        >>> print(f"Bid: ${quote.get('bid')} Ask: ${quote.get('ask')}")
    """
    key = apikey or API_KEY
    symbol = options_ticker.upper()
    if not symbol.startswith("O:"):
        symbol = f"O:{symbol}"

    url = f"{API_BASE}/v3/quotes/{symbol}?limit=1&order=desc&sort=timestamp&apiKey={key}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "symbol": symbol}

    results = data.get("results", [])
    if not results:
        return {"error": "No quote data returned", "symbol": symbol}

    q = results[0]
    bid = q.get("bid_price", 0)
    ask = q.get("ask_price", 0)

    return {
        "symbol": symbol,
        "bid": bid,
        "bid_size": q.get("bid_size"),
        "ask": ask,
        "ask_size": q.get("ask_size"),
        "midpoint": round((bid + ask) / 2, 4) if bid and ask else None,
        "spread": round(ask - bid, 4) if bid and ask else None,
        "timestamp": q.get("sip_timestamp") or q.get("participant_timestamp"),
        "status": "ok",
    }


def get_option_details(
    options_ticker: str,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get full contract details for a specific options contract.

    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00170000')
                       If no 'O:' prefix, it will be added automatically.
        apikey: Polygon.io API key

    Returns:
        Dict with contract details:
        - ticker: Options ticker
        - underlying_ticker: Underlying stock
        - contract_type: 'call' or 'put'
        - strike_price: Strike price
        - expiration_date: Expiry (YYYY-MM-DD)
        - exercise_style: 'american' or 'european'
        - shares_per_contract: Typically 100
        - primary_exchange: Primary exchange

    Example:
        >>> details = get_option_details('O:AAPL250321C00170000')
        >>> print(f"{details.get('contract_type')} {details.get('strike_price')}")
    """
    key = apikey or API_KEY
    symbol = options_ticker.upper()
    if not symbol.startswith("O:"):
        symbol = f"O:{symbol}"

    url = f"{API_BASE}/v3/reference/options/contracts/{symbol}?apiKey={key}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "ticker": symbol}

    results = data.get("results", {})
    if not results:
        return {"error": "No contract details returned", "ticker": symbol}

    return {
        "ticker": results.get("ticker"),
        "underlying_ticker": results.get("underlying_ticker"),
        "contract_type": results.get("contract_type"),
        "strike_price": results.get("strike_price"),
        "expiration_date": results.get("expiration_date"),
        "exercise_style": results.get("exercise_style"),
        "shares_per_contract": results.get("shares_per_contract"),
        "primary_exchange": results.get("primary_exchange"),
        "cfi": results.get("cfi"),
        "status": "ok",
    }


def get_options_snapshot(
    underlying_ticker: str,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a snapshot of all options contracts for an underlying ticker.
    Includes last trade, greeks, IV, and open interest where available.

    NOTE: Snapshot endpoint may require a paid Polygon.io plan.

    Args:
        underlying_ticker: Stock symbol (e.g., 'AAPL')
        apikey: Polygon.io API key

    Returns:
        Dict with:
        - ticker: Underlying symbol
        - results: List of option snapshots with greeks, IV, prices
        - count: Number of results

    Example:
        >>> snap = get_options_snapshot('AAPL')
        >>> for opt in snap.get('results', [])[:3]:
        ...     print(opt.get('details', {}).get('ticker'))
    """
    key = apikey or API_KEY
    ticker = underlying_ticker.upper()

    url = f"{API_BASE}/v3/snapshot/options/{ticker}?limit=50&apiKey={key}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "ticker": ticker, "results": []}

    results = data.get("results", [])
    return {
        "ticker": ticker,
        "count": len(results),
        "results": results,
        "status": data.get("status", "unknown"),
    }


def get_option_previous_close(
    options_ticker: str,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get previous day's OHLCV for an options contract.

    Args:
        options_ticker: Full options ticker (e.g., 'O:AAPL250321C00170000')
        apikey: Polygon.io API key

    Returns:
        Dict with previous day bar:
        - symbol: Options ticker
        - open, high, low, close: OHLC prices
        - volume: Trading volume
        - vwap: Volume weighted average price
        - date: Trading date

    Example:
        >>> prev = get_option_previous_close('O:AAPL250321C00170000')
        >>> print(f"Close: ${prev.get('close')}, Vol: {prev.get('volume')}")
    """
    key = apikey or API_KEY
    symbol = options_ticker.upper()
    if not symbol.startswith("O:"):
        symbol = f"O:{symbol}"

    url = f"{API_BASE}/v2/aggs/ticker/{symbol}/prev?apiKey={key}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "symbol": symbol}

    results = data.get("results", [])
    if not results:
        return {"error": "No previous close data", "symbol": symbol}

    bar = results[0]
    return {
        "symbol": symbol,
        "open": bar.get("o"),
        "high": bar.get("h"),
        "low": bar.get("l"),
        "close": bar.get("c"),
        "volume": bar.get("v"),
        "vwap": bar.get("vw"),
        "transactions": bar.get("n"),
        "date": bar.get("t"),
        "status": "ok",
    }


def search_options_contracts(
    underlying_ticker: str,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    expiration_date_gte: Optional[str] = None,
    expiration_date_lte: Optional[str] = None,
    contract_type: Optional[str] = None,
    limit: int = 50,
    apikey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search options contracts with advanced filters (strike range, date range).

    Args:
        underlying_ticker: Stock symbol (e.g., 'SPY')
        min_strike: Minimum strike price
        max_strike: Maximum strike price
        expiration_date_gte: Expiry on or after (YYYY-MM-DD)
        expiration_date_lte: Expiry on or before (YYYY-MM-DD)
        contract_type: 'call' or 'put'
        limit: Max results (up to 1000)
        apikey: Polygon.io API key

    Returns:
        Dict with filtered contract list:
        - underlying_ticker: Symbol searched
        - count: Number of results
        - results: List of matching contracts

    Example:
        >>> results = search_options_contracts('SPY', min_strike=500, max_strike=520,
        ...     contract_type='call', expiration_date_gte='2025-03-01')
        >>> print(f"Found {results['count']} contracts")
    """
    key = apikey or API_KEY
    ticker = underlying_ticker.upper()

    params = {
        "underlying_ticker": ticker,
        "expired": "false",
        "limit": min(limit, 1000),
        "order": "asc",
        "sort": "strike_price",
        "apiKey": key,
    }
    if contract_type:
        params["contract_type"] = contract_type.lower()
    if min_strike is not None:
        params["strike_price.gte"] = min_strike
    if max_strike is not None:
        params["strike_price.lte"] = max_strike
    if expiration_date_gte:
        params["expiration_date.gte"] = expiration_date_gte
    if expiration_date_lte:
        params["expiration_date.lte"] = expiration_date_lte

    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE}/v3/reference/options/contracts?{qs}"
    data = _request(url)

    if "error" in data:
        return {"error": data["error"], "underlying_ticker": ticker, "results": []}

    results = data.get("results", [])
    return {
        "underlying_ticker": ticker,
        "count": len(results),
        "results": results,
        "status": data.get("status", "unknown"),
    }
