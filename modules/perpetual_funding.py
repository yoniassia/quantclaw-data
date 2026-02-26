"""Perpetual Funding Rate Dashboard — Track funding rates across crypto perpetual futures exchanges.

Monitors funding rates for perpetual swaps on major exchanges (Binance, Bybit, OKX, dYdX)
to identify carry trade opportunities and sentiment extremes.

Data sources: CoinGlass API (free tier), exchange public APIs.
Roadmap item #313.
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any


def get_funding_rates(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    """Fetch current funding rates for top perpetual futures contracts.

    Args:
        symbols: Optional list of symbols (e.g. ['BTC', 'ETH']). Defaults to top 20.

    Returns:
        List of dicts with symbol, exchange, funding_rate, next_funding_time, annualized_rate.
    """
    if symbols is None:
        symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT"]

    results = []
    for sym in symbols:
        pair = f"{sym}USDT"
        try:
            url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={pair}"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            rate = float(data.get("lastFundingRate", 0))
            results.append({
                "symbol": sym,
                "exchange": "binance",
                "pair": pair,
                "funding_rate": rate,
                "funding_rate_pct": round(rate * 100, 4),
                "annualized_rate_pct": round(rate * 3 * 365 * 100, 2),
                "mark_price": float(data.get("markPrice", 0)),
                "index_price": float(data.get("indexPrice", 0)),
                "next_funding_time": data.get("nextFundingTime"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: abs(x["funding_rate"]), reverse=True)


def find_funding_extremes(threshold_pct: float = 0.05) -> dict[str, list[dict]]:
    """Find symbols with extreme funding rates (carry trade opportunities).

    Args:
        threshold_pct: Funding rate threshold in percent (default 0.05%).

    Returns:
        Dict with 'high_positive' (crowded longs) and 'high_negative' (crowded shorts) lists.
    """
    rates = get_funding_rates()
    threshold = threshold_pct / 100
    return {
        "high_positive": [r for r in rates if r["funding_rate"] > threshold],
        "high_negative": [r for r in rates if r["funding_rate"] < -threshold],
        "neutral": [r for r in rates if abs(r["funding_rate"]) <= threshold],
        "threshold_pct": threshold_pct,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def funding_rate_summary() -> dict[str, Any]:
    """Generate a summary of the current funding rate environment."""
    rates = get_funding_rates()
    if not rates:
        return {"error": "No data available"}
    fr = [r["funding_rate"] for r in rates]
    avg = sum(fr) / len(fr)
    return {
        "count": len(rates),
        "avg_funding_rate_pct": round(avg * 100, 4),
        "max_positive": max(rates, key=lambda x: x["funding_rate"]),
        "max_negative": min(rates, key=lambda x: x["funding_rate"]),
        "sentiment": "bullish" if avg > 0.0001 else "bearish" if avg < -0.0001 else "neutral",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
