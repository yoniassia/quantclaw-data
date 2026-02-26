"""
Tick-by-Tick Trade Tape — Time & sales data aggregation and analysis.

Provides trade tape analysis using free market data sources including
SEC MIDAS data, aggregated trade statistics, and tick-level analytics.
"""

import json
import math
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def get_trade_tape_summary(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get aggregated trade tape summary for a symbol using Polygon.io or Alpha Vantage.

    Falls back to Yahoo Finance intraday data if no API key provided.

    Args:
        symbol: Stock ticker symbol
        api_key: Optional Polygon.io API key

    Returns:
        Dict with trade tape summary including volume, VWAP, trade count
    """
    # Try Polygon.io grouped daily bars (free tier)
    if api_key:
        try:
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{date_str}/{date_str}?apiKey={api_key}&limit=500"
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            results = data.get("results", [])
            if results:
                total_volume = sum(bar.get("v", 0) for bar in results)
                total_trades = sum(bar.get("n", 0) for bar in results)
                vwap = sum(bar.get("vw", 0) * bar.get("v", 0) for bar in results)
                vwap = vwap / total_volume if total_volume > 0 else 0

                # Classify bars by volume intensity
                avg_vol = total_volume / len(results) if results else 0
                high_vol_bars = [b for b in results if b.get("v", 0) > avg_vol * 2]

                return {
                    "symbol": symbol,
                    "date": date_str,
                    "total_volume": total_volume,
                    "total_trades": total_trades,
                    "vwap": round(vwap, 4),
                    "bar_count": len(results),
                    "avg_volume_per_bar": round(avg_vol, 0),
                    "high_volume_bars": len(high_vol_bars),
                    "open": results[0].get("o"),
                    "close": results[-1].get("c"),
                    "high": max(b.get("h", 0) for b in results),
                    "low": min(b.get("l", float("inf")) for b in results),
                    "source": "polygon.io",
                }
        except Exception as e:
            pass  # Fall through to alternative

    # Fallback: SEC MIDAS aggregate data
    return _get_sec_midas_summary(symbol)


def _get_sec_midas_summary(symbol: str) -> Dict:
    """Fetch SEC MIDAS market structure data as fallback."""
    try:
        url = "https://www.sec.gov/files/data/midas/midas_metrics.json"
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        return {
            "symbol": symbol,
            "source": "SEC MIDAS (aggregate market)",
            "note": "Individual stock MIDAS data requires SEC EDGAR filing lookup",
            "market_metrics": data if isinstance(data, dict) else {"raw_count": len(data)},
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "source": "sec_midas"}


def analyze_trade_distribution(trades: List[Dict]) -> Dict:
    """
    Analyze trade size distribution from a list of trades.

    Classifies trades into odd lot, round lot, and block trade categories
    and computes distribution statistics.

    Args:
        trades: List of dicts with 'size' and optionally 'price', 'timestamp'

    Returns:
        Dict with trade distribution analysis
    """
    if not trades:
        return {"error": "No trades provided"}

    sizes = [t.get("size", 0) for t in trades]
    total_volume = sum(sizes)
    total_trades = len(sizes)

    # Classification
    odd_lots = [s for s in sizes if s < 100]
    round_lots = [s for s in sizes if 100 <= s < 10000]
    block_trades = [s for s in sizes if s >= 10000]

    # Statistics
    avg_size = total_volume / total_trades if total_trades > 0 else 0
    median_size = sorted(sizes)[len(sizes) // 2] if sizes else 0
    std_dev = math.sqrt(sum((s - avg_size) ** 2 for s in sizes) / len(sizes)) if sizes else 0

    # Price-weighted if available
    dollar_volume = sum(
        t.get("size", 0) * t.get("price", 0) for t in trades if t.get("price")
    )

    return {
        "total_trades": total_trades,
        "total_volume": total_volume,
        "dollar_volume": round(dollar_volume, 2) if dollar_volume else None,
        "avg_trade_size": round(avg_size, 2),
        "median_trade_size": median_size,
        "std_dev_size": round(std_dev, 2),
        "distribution": {
            "odd_lots": {
                "count": len(odd_lots),
                "pct_trades": round(len(odd_lots) / total_trades * 100, 2),
                "volume": sum(odd_lots),
                "pct_volume": round(sum(odd_lots) / total_volume * 100, 2) if total_volume else 0,
            },
            "round_lots": {
                "count": len(round_lots),
                "pct_trades": round(len(round_lots) / total_trades * 100, 2),
                "volume": sum(round_lots),
                "pct_volume": round(sum(round_lots) / total_volume * 100, 2) if total_volume else 0,
            },
            "block_trades": {
                "count": len(block_trades),
                "pct_trades": round(len(block_trades) / total_trades * 100, 2),
                "volume": sum(block_trades),
                "pct_volume": round(sum(block_trades) / total_volume * 100, 2) if total_volume else 0,
            },
        },
    }


def compute_tick_statistics(prices: List[float]) -> Dict:
    """
    Compute tick-level statistics from a sequence of trade prices.

    Calculates uptick/downtick ratios, tick runs, and microstructure metrics.

    Args:
        prices: Ordered list of trade prices

    Returns:
        Dict with tick statistics and microstructure metrics
    """
    if len(prices) < 2:
        return {"error": "Need at least 2 prices"}

    upticks = 0
    downticks = 0
    zero_ticks = 0
    max_uptick_run = 0
    max_downtick_run = 0
    current_run = 0
    current_direction = 0

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            upticks += 1
            if current_direction == 1:
                current_run += 1
            else:
                current_run = 1
                current_direction = 1
            max_uptick_run = max(max_uptick_run, current_run)
        elif diff < 0:
            downticks += 1
            if current_direction == -1:
                current_run += 1
            else:
                current_run = 1
                current_direction = -1
            max_downtick_run = max(max_downtick_run, current_run)
        else:
            zero_ticks += 1

    total_ticks = len(prices) - 1
    tick_imbalance = (upticks - downticks) / total_ticks if total_ticks else 0

    return {
        "total_ticks": total_ticks,
        "upticks": upticks,
        "downticks": downticks,
        "zero_ticks": zero_ticks,
        "uptick_pct": round(upticks / total_ticks * 100, 2),
        "downtick_pct": round(downticks / total_ticks * 100, 2),
        "tick_imbalance": round(tick_imbalance, 4),
        "max_uptick_run": max_uptick_run,
        "max_downtick_run": max_downtick_run,
        "price_range": round(max(prices) - min(prices), 6),
        "net_change": round(prices[-1] - prices[0], 6),
        "direction_bias": "BULLISH" if tick_imbalance > 0.05 else (
            "BEARISH" if tick_imbalance < -0.05 else "NEUTRAL"
        ),
    }
