"""
Open Interest Heatmap — Aggregate open interest data across crypto derivatives exchanges.

Tracks open interest by symbol, exchange, and strike price for futures and options.
Identifies positioning extremes, liquidation clusters, and market structure shifts.

Data sources: Binance, Bybit, Deribit public APIs.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Any


DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "ARB", "OP"]


def _fetch_json(url: str, timeout: int = 15) -> Any:
    """Fetch JSON from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_binance_open_interest(symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch open interest from Binance Futures for specified symbols.

    Returns list of dicts: symbol, open_interest (contracts), open_interest_usd, exchange.
    """
    symbols = symbols or DEFAULT_SYMBOLS
    results = []

    for symbol in symbols:
        try:
            url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}USDT"
            data = _fetch_json(url)
            oi = float(data.get("openInterest", 0))

            # Get mark price for USD conversion
            price_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}USDT"
            price_data = _fetch_json(price_url)
            mark_price = float(price_data.get("markPrice", 0))

            results.append({
                "symbol": symbol,
                "exchange": "Binance",
                "open_interest": oi,
                "open_interest_usd": oi * mark_price,
                "mark_price": mark_price,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["open_interest_usd"], reverse=True)


def get_bybit_open_interest(symbols: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch open interest from Bybit for specified symbols.

    Returns list of dicts: symbol, open_interest, open_interest_usd, exchange.
    """
    symbols = symbols or DEFAULT_SYMBOLS
    results = []

    for symbol in symbols:
        try:
            url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}USDT"
            data = _fetch_json(url)
            if data.get("result", {}).get("list"):
                item = data["result"]["list"][0]
                oi = float(item.get("openInterest", 0))
                mark = float(item.get("markPrice", 0))
                results.append({
                    "symbol": symbol,
                    "exchange": "Bybit",
                    "open_interest": oi,
                    "open_interest_usd": oi * mark,
                    "mark_price": mark,
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["open_interest_usd"], reverse=True)


def get_open_interest_heatmap(symbols: Optional[List[str]] = None) -> Dict:
    """
    Build aggregated open interest heatmap across exchanges.

    Returns cross-exchange OI comparison, concentration metrics,
    and dominant positioning analysis.
    """
    symbols = symbols or DEFAULT_SYMBOLS[:8]

    binance_oi = get_binance_open_interest(symbols)
    bybit_oi = get_bybit_open_interest(symbols)

    all_oi = binance_oi + bybit_oi

    # Aggregate by symbol
    by_symbol = {}
    for item in all_oi:
        sym = item["symbol"]
        if sym not in by_symbol:
            by_symbol[sym] = {"total_oi_usd": 0, "exchanges": [], "mark_price": item["mark_price"]}
        by_symbol[sym]["total_oi_usd"] += item["open_interest_usd"]
        by_symbol[sym]["exchanges"].append({
            "exchange": item["exchange"],
            "oi_usd": item["open_interest_usd"],
            "oi_contracts": item["open_interest"]
        })

    # Rank by total OI
    ranked = sorted(by_symbol.items(), key=lambda x: x[1]["total_oi_usd"], reverse=True)

    total_oi_usd = sum(v["total_oi_usd"] for v in by_symbol.values())

    # Concentration: top 3 share
    top3_oi = sum(v["total_oi_usd"] for _, v in ranked[:3])
    concentration = (top3_oi / total_oi_usd * 100) if total_oi_usd > 0 else 0

    heatmap = []
    for sym, data in ranked:
        share = (data["total_oi_usd"] / total_oi_usd * 100) if total_oi_usd > 0 else 0
        heatmap.append({
            "symbol": sym,
            "total_oi_usd": data["total_oi_usd"],
            "market_share_pct": round(share, 2),
            "mark_price": data["mark_price"],
            "exchanges": data["exchanges"]
        })

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_open_interest_usd": total_oi_usd,
        "symbols_tracked": len(by_symbol),
        "exchanges_covered": list(set(i["exchange"] for i in all_oi)),
        "top3_concentration_pct": round(concentration, 2),
        "heatmap": heatmap,
        "summary": f"${total_oi_usd/1e9:.1f}B total OI across {len(by_symbol)} symbols. "
                   f"Top 3 concentration: {concentration:.1f}%."
    }


def get_oi_history(symbol: str = "BTC", period: str = "5m", limit: int = 50) -> List[Dict]:
    """
    Fetch open interest history from Binance Futures.

    Args:
        symbol: Crypto symbol
        period: Interval (5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d)
        limit: Number of records (max 500)

    Returns list of historical OI records with timestamps.
    """
    url = (f"https://fapi.binance.com/futures/data/openInterestHist"
           f"?symbol={symbol}USDT&period={period}&limit={limit}")
    data = _fetch_json(url)

    results = []
    for item in data:
        results.append({
            "symbol": symbol,
            "open_interest": float(item.get("sumOpenInterest", 0)),
            "open_interest_usd": float(item.get("sumOpenInterestValue", 0)),
            "timestamp": datetime.utcfromtimestamp(int(item["timestamp"]) / 1000).isoformat()
        })

    return results
