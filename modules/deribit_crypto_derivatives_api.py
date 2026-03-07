"""Deribit Crypto Derivatives API — Options, futures, volatility, and funding data.

Public endpoints for crypto derivatives analysis: options/futures book summaries,
index prices, historical volatility, perpetual swap tickers, and instrument listings.

Data source: Deribit public REST API (no authentication required).
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

BASE_URL = "https://www.deribit.com/api/v2/public"
HEADERS = {"User-Agent": "QuantClaw/1.0"}


def _fetch(endpoint: str, params: dict | None = None) -> Any:
    """Fetch JSON from Deribit public API.

    Args:
        endpoint: API endpoint path (e.g. 'get_index_price').
        params: Query parameters dict.

    Returns:
        Parsed 'result' field from API response.

    Raises:
        ValueError: If API returns an error.
    """
    url = f"{BASE_URL}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if "error" in data:
            raise ValueError(f"Deribit API error: {data['error']}")
        return data.get("result", data)
    except Exception as e:
        raise ValueError(f"Deribit fetch failed ({endpoint}): {e}")


def get_options_summary(currency: str = "BTC") -> list[dict[str, Any]]:
    """Get options book summary for a currency.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        List of option instrument summaries with bid/ask, volume, open interest, etc.
    """
    try:
        result = _fetch("get_book_summary_by_currency", {"currency": currency, "kind": "option"})
        return [
            {
                "instrument": item.get("instrument_name"),
                "bid_price": item.get("bid_price"),
                "ask_price": item.get("ask_price"),
                "mark_price": item.get("mark_price"),
                "volume": item.get("volume"),
                "open_interest": item.get("open_interest"),
                "underlying_price": item.get("underlying_price"),
                "mid_price": item.get("mid_price"),
            }
            for item in result
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_futures_summary(currency: str = "BTC") -> list[dict[str, Any]]:
    """Get futures book summary for a currency.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        List of futures instrument summaries with pricing and volume data.
    """
    try:
        result = _fetch("get_book_summary_by_currency", {"currency": currency, "kind": "future"})
        return [
            {
                "instrument": item.get("instrument_name"),
                "bid_price": item.get("bid_price"),
                "ask_price": item.get("ask_price"),
                "mark_price": item.get("mark_price"),
                "volume": item.get("volume"),
                "open_interest": item.get("open_interest"),
                "underlying_price": item.get("underlying_price"),
                "last": item.get("last"),
                "low": item.get("low"),
                "high": item.get("high"),
            }
            for item in result
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_index_price(currency: str = "BTC") -> dict[str, Any]:
    """Get current index price for a currency.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        Dict with index price and estimated delivery price.
    """
    try:
        index_name = f"{currency.lower()}_usd"
        result = _fetch("get_index_price", {"index_name": index_name})
        return {
            "currency": currency,
            "index_price": result.get("index_price"),
            "estimated_delivery_price": result.get("estimated_delivery_price"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_historical_volatility(currency: str = "BTC") -> list[list]:
    """Get historical volatility data for a currency.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        List of [timestamp, volatility] pairs.
    """
    try:
        result = _fetch("get_historical_volatility", {"currency": currency})
        return result
    except Exception as e:
        return [{"error": str(e)}]


def get_perpetual_ticker(currency: str = "BTC") -> dict[str, Any]:
    """Get perpetual swap ticker data including funding rate and mark price.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        Dict with mark price, index price, funding rate, open interest, volume.
    """
    try:
        instrument = f"{currency}-PERPETUAL"
        result = _fetch("ticker", {"instrument_name": instrument})
        return {
            "instrument": result.get("instrument_name"),
            "mark_price": result.get("mark_price"),
            "index_price": result.get("index_price"),
            "last_price": result.get("last_price"),
            "best_bid": result.get("best_bid_price"),
            "best_ask": result.get("best_ask_price"),
            "funding_8h": result.get("funding_8h"),
            "current_funding": result.get("current_funding"),
            "open_interest": result.get("open_interest"),
            "volume_24h": result.get("stats", {}).get("volume"),
            "price_change_24h": result.get("stats", {}).get("price_change"),
            "high_24h": result.get("stats", {}).get("high"),
            "low_24h": result.get("stats", {}).get("low"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_instruments(currency: str = "BTC", kind: str = "option") -> list[dict[str, Any]]:
    """List available instruments for a currency and kind.

    Args:
        currency: Currency code (BTC, ETH).
        kind: Instrument kind (option, future, spot, future_combo, option_combo).

    Returns:
        List of instrument dicts with name, expiry, strike, type info.
    """
    try:
        result = _fetch("get_instruments", {"currency": currency, "kind": kind})
        return [
            {
                "name": item.get("instrument_name"),
                "kind": item.get("kind"),
                "expiration": datetime.fromtimestamp(
                    item.get("expiration_timestamp", 0) / 1000, tz=timezone.utc
                ).isoformat() if item.get("expiration_timestamp") else None,
                "strike": item.get("strike"),
                "option_type": item.get("option_type"),
                "is_active": item.get("is_active"),
                "tick_size": item.get("tick_size"),
                "min_trade_amount": item.get("min_trade_amount"),
                "contract_size": item.get("contract_size"),
            }
            for item in result
        ]
    except Exception as e:
        return [{"error": str(e)}]


def crypto_derivatives_analysis(currency: str = "BTC") -> dict[str, Any]:
    """Comprehensive crypto derivatives analysis with put/call ratio, volatility, and funding.

    Args:
        currency: Currency code (BTC, ETH).

    Returns:
        Analysis dict with market overview, options metrics, futures data, and signals.
    """
    analysis = {"currency": currency, "fetched_at": datetime.now(timezone.utc).isoformat()}

    # Index price
    idx = get_index_price(currency)
    analysis["index_price"] = idx.get("index_price")

    # Perpetual data
    perp = get_perpetual_ticker(currency)
    if "error" not in perp:
        analysis["perpetual"] = {
            "mark_price": perp.get("mark_price"),
            "funding_8h": perp.get("funding_8h"),
            "current_funding": perp.get("current_funding"),
            "open_interest": perp.get("open_interest"),
            "volume_24h": perp.get("volume_24h"),
            "price_change_24h": perp.get("price_change_24h"),
        }
        # Funding signal
        funding = perp.get("current_funding") or 0
        if funding > 0.0005:
            analysis["funding_signal"] = "overbought_longs_pay"
        elif funding < -0.0005:
            analysis["funding_signal"] = "oversold_shorts_pay"
        else:
            analysis["funding_signal"] = "neutral"

    # Options put/call analysis
    options = get_options_summary(currency)
    if options and "error" not in options[0]:
        puts = [o for o in options if o.get("instrument", "").endswith("-P")]
        calls = [o for o in options if o.get("instrument", "").endswith("-C")]

        put_oi = sum(o.get("open_interest", 0) or 0 for o in puts)
        call_oi = sum(o.get("open_interest", 0) or 0 for o in calls)
        put_vol = sum(o.get("volume", 0) or 0 for o in puts)
        call_vol = sum(o.get("volume", 0) or 0 for o in calls)

        pc_ratio_oi = round(put_oi / call_oi, 4) if call_oi > 0 else None
        pc_ratio_vol = round(put_vol / call_vol, 4) if call_vol > 0 else None

        analysis["options"] = {
            "total_instruments": len(options),
            "puts_count": len(puts),
            "calls_count": len(calls),
            "put_open_interest": put_oi,
            "call_open_interest": call_oi,
            "put_call_ratio_oi": pc_ratio_oi,
            "put_volume": put_vol,
            "call_volume": call_vol,
            "put_call_ratio_volume": pc_ratio_vol,
        }

        # Sentiment from P/C ratio
        if pc_ratio_oi:
            if pc_ratio_oi > 1.2:
                analysis["options_sentiment"] = "bearish_hedging"
            elif pc_ratio_oi < 0.7:
                analysis["options_sentiment"] = "bullish_speculation"
            else:
                analysis["options_sentiment"] = "neutral"

    # Historical volatility
    hvol = get_historical_volatility(currency)
    if hvol and isinstance(hvol, list) and len(hvol) > 0 and not isinstance(hvol[0], dict):
        latest_vol = hvol[-1] if hvol else None
        analysis["historical_volatility"] = {
            "data_points": len(hvol),
            "latest": latest_vol,
        }

    # Futures summary
    futures = get_futures_summary(currency)
    if futures and "error" not in futures[0]:
        analysis["futures"] = {
            "total_instruments": len(futures),
            "instruments": [
                {
                    "name": f.get("instrument"),
                    "mark_price": f.get("mark_price"),
                    "volume": f.get("volume"),
                    "open_interest": f.get("open_interest"),
                }
                for f in futures[:5]
            ],
        }

    return analysis


# Aliases for stub compatibility
fetch_data = crypto_derivatives_analysis
get_latest = get_index_price


if __name__ == "__main__":
    import sys
    result = crypto_derivatives_analysis("BTC")
    print(json.dumps(result, indent=2, default=str))
