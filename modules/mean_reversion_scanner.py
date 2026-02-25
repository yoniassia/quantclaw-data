"""Mean Reversion Z-Score Scanner — multi-timeframe mean reversion signal detector.

Scans stocks for extreme z-score deviations from their moving averages across
multiple timeframes, identifying potential mean reversion opportunities.
"""

import datetime
import json
import math
import urllib.request
from typing import Dict, List, Optional, Tuple


def fetch_price_history(symbol: str, days: int = 252) -> List[float]:
    """Fetch closing prices for a symbol from Yahoo Finance.

    Args:
        symbol: Ticker symbol.
        days: Number of days of history.

    Returns:
        List of closing prices (oldest first).
    """
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?range={days}d&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    return [c for c in closes if c is not None]


def compute_z_score(prices: List[float], lookback: int) -> Optional[float]:
    """Compute z-score of current price vs rolling mean/std.

    Args:
        prices: List of closing prices.
        lookback: Rolling window size.

    Returns:
        Z-score or None if insufficient data.
    """
    if len(prices) < lookback + 1:
        return None

    window = prices[-lookback:]
    mean = sum(window) / len(window)
    variance = sum((p - mean) ** 2 for p in window) / len(window)
    std = math.sqrt(variance) if variance > 0 else 0

    if std == 0:
        return None

    current = prices[-1]
    return (current - mean) / std


def multi_timeframe_zscore(symbol: str) -> Dict:
    """Compute z-scores across multiple timeframes for a symbol.

    Timeframes: 20-day, 50-day, 100-day, 200-day.

    Args:
        symbol: Ticker symbol.

    Returns:
        Dict with z-scores per timeframe and composite signal.
    """
    prices = fetch_price_history(symbol, 300)
    timeframes = [20, 50, 100, 200]
    scores = {}

    for tf in timeframes:
        z = compute_z_score(prices, tf)
        if z is not None:
            scores[f"z_{tf}d"] = round(z, 3)

    if not scores:
        return {"symbol": symbol, "error": "Insufficient data"}

    # Composite: weighted average (shorter = higher weight)
    weights = {20: 0.4, 50: 0.3, 100: 0.2, 200: 0.1}
    weighted_sum = 0
    total_weight = 0
    for tf in timeframes:
        key = f"z_{tf}d"
        if key in scores:
            weighted_sum += scores[key] * weights[tf]
            total_weight += weights[tf]

    composite = weighted_sum / total_weight if total_weight > 0 else 0

    # Signal
    if composite < -2:
        signal = "STRONG_BUY"
    elif composite < -1:
        signal = "BUY"
    elif composite > 2:
        signal = "STRONG_SELL"
    elif composite > 1:
        signal = "SELL"
    else:
        signal = "NEUTRAL"

    return {
        "symbol": symbol,
        "current_price": round(prices[-1], 2) if prices else None,
        **scores,
        "composite_z": round(composite, 3),
        "signal": signal,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


def scan_universe(
    symbols: Optional[List[str]] = None, min_abs_z: float = 1.5
) -> List[Dict]:
    """Scan a universe of symbols for mean reversion candidates.

    Args:
        symbols: List of tickers to scan. Defaults to major stocks.
        min_abs_z: Minimum absolute composite z-score to include.

    Returns:
        Sorted list of candidates with strongest signals first.
    """
    if symbols is None:
        symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            "JPM", "BAC", "GS", "XOM", "CVX", "JNJ", "PFE", "UNH",
            "HD", "WMT", "KO", "PEP", "DIS", "NFLX", "CRM", "ORCL",
        ]

    results = []
    for sym in symbols:
        try:
            analysis = multi_timeframe_zscore(sym)
            if "error" not in analysis and abs(analysis.get("composite_z", 0)) >= min_abs_z:
                results.append(analysis)
        except Exception:
            continue

    return sorted(results, key=lambda x: abs(x.get("composite_z", 0)), reverse=True)


def bollinger_band_analysis(symbol: str, lookback: int = 20, num_std: float = 2.0) -> Dict:
    """Bollinger Band analysis for mean reversion signals.

    Args:
        symbol: Ticker symbol.
        lookback: BB period.
        num_std: Number of standard deviations.

    Returns:
        Dict with BB levels, %B, bandwidth, and signal.
    """
    prices = fetch_price_history(symbol, lookback + 50)
    if len(prices) < lookback:
        return {"symbol": symbol, "error": "Insufficient data"}

    window = prices[-lookback:]
    sma = sum(window) / len(window)
    std = math.sqrt(sum((p - sma) ** 2 for p in window) / len(window))

    upper = sma + num_std * std
    lower = sma - num_std * std
    current = prices[-1]

    pct_b = (current - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    bandwidth = (upper - lower) / sma * 100 if sma > 0 else 0

    if pct_b < 0:
        signal = "OVERSOLD_BELOW_BB"
    elif pct_b < 0.2:
        signal = "OVERSOLD"
    elif pct_b > 1:
        signal = "OVERBOUGHT_ABOVE_BB"
    elif pct_b > 0.8:
        signal = "OVERBOUGHT"
    else:
        signal = "NEUTRAL"

    return {
        "symbol": symbol,
        "price": round(current, 2),
        "sma": round(sma, 2),
        "upper_bb": round(upper, 2),
        "lower_bb": round(lower, 2),
        "pct_b": round(pct_b, 4),
        "bandwidth": round(bandwidth, 2),
        "signal": signal,
    }
