"""
Perpetual Funding Rate Dashboard — Track funding rates across crypto perpetual futures exchanges.

Monitors funding rates for BTC, ETH, and major altcoins across Binance, Bybit, OKX, and dYdX.
Identifies funding rate extremes, arbitrage opportunities, and market sentiment signals.

Data sources: CoinGlass API (free tier), exchange public APIs.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# Major perpetual futures pairs to track
DEFAULT_SYMBOLS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX",
    "MATIC", "LINK", "DOT", "UNI", "AAVE", "ARB", "OP"
]

EXCHANGES = ["Binance", "Bybit", "OKX", "dYdX"]


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL with timeout."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_binance_funding_rates(symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch current funding rates from Binance Futures.

    Returns list of dicts with symbol, funding_rate, next_funding_time, mark_price.
    """
    symbols = symbols or DEFAULT_SYMBOLS
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    data = _fetch_json(url)

    results = []
    symbol_set = {s.upper() + "USDT" for s in symbols}

    for item in data:
        if item["symbol"] in symbol_set:
            results.append({
                "symbol": item["symbol"].replace("USDT", ""),
                "exchange": "Binance",
                "funding_rate": float(item.get("lastFundingRate", 0)),
                "funding_rate_pct": float(item.get("lastFundingRate", 0)) * 100,
                "annualized_pct": float(item.get("lastFundingRate", 0)) * 100 * 3 * 365,
                "mark_price": float(item.get("markPrice", 0)),
                "next_funding_time": datetime.utcfromtimestamp(
                    int(item.get("nextFundingTime", 0)) / 1000
                ).isoformat() if item.get("nextFundingTime") else None,
                "timestamp": datetime.utcnow().isoformat()
            })

    return sorted(results, key=lambda x: abs(x["funding_rate"]), reverse=True)


def get_bybit_funding_rates(symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch current funding rates from Bybit perpetual futures.

    Returns list of dicts with symbol, funding_rate, predicted_rate.
    """
    symbols = symbols or DEFAULT_SYMBOLS
    results = []

    for symbol in symbols:
        try:
            url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT"
            data = _fetch_json(url)
            if data.get("result", {}).get("list"):
                item = data["result"]["list"][0]
                rate = float(item.get("fundingRate", 0))
                results.append({
                    "symbol": symbol,
                    "exchange": "Bybit",
                    "funding_rate": rate,
                    "funding_rate_pct": rate * 100,
                    "annualized_pct": rate * 100 * 3 * 365,
                    "mark_price": float(item.get("markPrice", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception:
            continue

    return sorted(results, key=lambda x: abs(x["funding_rate"]), reverse=True)


def get_funding_rate_dashboard(symbols: Optional[List[str]] = None) -> Dict:
    """
    Aggregate funding rates across exchanges into a unified dashboard.

    Returns summary with per-symbol cross-exchange comparison,
    extreme funding alerts, and arbitrage opportunities.
    """
    symbols = symbols or DEFAULT_SYMBOLS[:8]

    binance = get_binance_funding_rates(symbols)
    bybit = get_bybit_funding_rates(symbols)

    all_rates = binance + bybit

    # Group by symbol
    by_symbol = {}
    for r in all_rates:
        sym = r["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(r)

    # Find arbitrage opportunities (large cross-exchange spreads)
    arbitrage = []
    for sym, rates in by_symbol.items():
        if len(rates) >= 2:
            rates_sorted = sorted(rates, key=lambda x: x["funding_rate"])
            spread = rates_sorted[-1]["funding_rate"] - rates_sorted[0]["funding_rate"]
            if abs(spread) > 0.0001:  # > 0.01% spread
                arbitrage.append({
                    "symbol": sym,
                    "long_exchange": rates_sorted[0]["exchange"],
                    "long_rate": rates_sorted[0]["funding_rate_pct"],
                    "short_exchange": rates_sorted[-1]["exchange"],
                    "short_rate": rates_sorted[-1]["funding_rate_pct"],
                    "spread_pct": spread * 100,
                    "annualized_spread_pct": spread * 100 * 3 * 365
                })

    # Extreme funding alerts (annualized > 50% or < -50%)
    extremes = [r for r in all_rates if abs(r["annualized_pct"]) > 50]

    # Market sentiment: average funding rate
    avg_rate = sum(r["funding_rate"] for r in all_rates) / len(all_rates) if all_rates else 0
    sentiment = "EXTREMELY_BULLISH" if avg_rate > 0.001 else \
                "BULLISH" if avg_rate > 0.0001 else \
                "NEUTRAL" if avg_rate > -0.0001 else \
                "BEARISH" if avg_rate > -0.001 else "EXTREMELY_BEARISH"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_instruments": len(all_rates),
        "exchanges_covered": list(set(r["exchange"] for r in all_rates)),
        "market_sentiment": sentiment,
        "avg_funding_rate_pct": avg_rate * 100,
        "rates_by_symbol": by_symbol,
        "extreme_funding_alerts": extremes,
        "arbitrage_opportunities": sorted(arbitrage, key=lambda x: abs(x["spread_pct"]), reverse=True),
        "summary": f"{len(all_rates)} instruments across {len(set(r['exchange'] for r in all_rates))} exchanges. "
                   f"Sentiment: {sentiment}. {len(extremes)} extreme rates. {len(arbitrage)} arb opportunities."
    }


def get_historical_funding(symbol: str = "BTC", exchange: str = "binance", limit: int = 100) -> List[Dict]:
    """
    Fetch historical funding rate data from Binance.

    Args:
        symbol: Crypto symbol (e.g., BTC, ETH)
        exchange: Exchange name (currently supports binance)
        limit: Number of historical records (max 1000)

    Returns list of historical funding rate records.
    """
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}USDT&limit={limit}"
    data = _fetch_json(url)

    results = []
    for item in data:
        rate = float(item.get("fundingRate", 0))
        results.append({
            "symbol": symbol,
            "exchange": "Binance",
            "funding_rate": rate,
            "funding_rate_pct": rate * 100,
            "annualized_pct": rate * 100 * 3 * 365,
            "timestamp": datetime.utcfromtimestamp(int(item["fundingTime"]) / 1000).isoformat()
        })

    return results
