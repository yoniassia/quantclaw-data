"""
Cross-Asset Correlation Dashboard — Module #220

Computes rolling correlations across asset classes (equities, bonds, commodities,
FX, crypto) to detect regime changes, diversification breakdown, and risk-on/risk-off
shifts. Uses free Yahoo Finance data via yfinance or direct download.
"""

import csv
import io
import json
import math
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


# Representative ETFs/tickers for major asset classes
DEFAULT_ASSETS = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "US_10Y": "^TNX",
    "GOLD": "GC=F",
    "OIL": "CL=F",
    "DXY": "DX-Y.NYB",
    "BTC": "BTC-USD",
    "VIX": "^VIX",
    "EM_EQUITIES": "EEM",
    "HY_BONDS": "HYG",
}


def fetch_yahoo_history(
    ticker: str,
    days: int = 252,
) -> List[Dict]:
    """
    Fetch historical daily close prices from Yahoo Finance.
    
    Args:
        ticker: Yahoo Finance ticker symbol.
        days: Number of calendar days of history.
        
    Returns:
        List of dicts with date and close price.
    """
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=days)).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
        f"?period1={start}&period2={end}&interval=1d&events=history"
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (QuantClaw/1.0)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode()
            reader = csv.DictReader(io.StringIO(text))
            results = []
            for row in reader:
                try:
                    close = float(row.get("Close", row.get("Adj Close", 0)))
                    if close > 0:
                        results.append({"date": row["Date"], "close": close})
                except (ValueError, KeyError):
                    continue
            return results
    except Exception as e:
        return []


def compute_returns(prices: List[Dict]) -> List[Dict]:
    """
    Compute daily log returns from price series.
    
    Args:
        prices: List of dicts with date and close.
        
    Returns:
        List of dicts with date and log_return.
    """
    returns = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]["close"]
        curr = prices[i]["close"]
        if prev > 0 and curr > 0:
            returns.append({
                "date": prices[i]["date"],
                "log_return": math.log(curr / prev),
            })
    return returns


def rolling_correlation(
    returns_a: List[float],
    returns_b: List[float],
    window: int = 60,
) -> List[Optional[float]]:
    """
    Compute rolling Pearson correlation between two return series.
    
    Args:
        returns_a: First return series.
        returns_b: Second return series.
        window: Rolling window size in trading days.
        
    Returns:
        List of correlation values (None for insufficient data).
    """
    n = min(len(returns_a), len(returns_b))
    correlations = []
    
    for i in range(n):
        if i < window - 1:
            correlations.append(None)
            continue
        
        a_slice = returns_a[i - window + 1: i + 1]
        b_slice = returns_b[i - window + 1: i + 1]
        
        mean_a = sum(a_slice) / window
        mean_b = sum(b_slice) / window
        
        cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(a_slice, b_slice)) / window
        std_a = math.sqrt(sum((a - mean_a) ** 2 for a in a_slice) / window)
        std_b = math.sqrt(sum((b - mean_b) ** 2 for b in b_slice) / window)
        
        if std_a > 0 and std_b > 0:
            correlations.append(round(cov / (std_a * std_b), 4))
        else:
            correlations.append(None)
    
    return correlations


def correlation_matrix(
    assets: Optional[Dict[str, str]] = None,
    days: int = 252,
) -> Dict:
    """
    Build a full cross-asset correlation matrix.
    
    Args:
        assets: Dict mapping asset labels to Yahoo tickers. Uses defaults if None.
        days: Calendar days of history to use.
        
    Returns:
        Dict with matrix, asset labels, and period info.
    """
    if assets is None:
        assets = DEFAULT_ASSETS
    
    # Fetch and compute returns
    all_returns = {}
    for label, ticker in assets.items():
        prices = fetch_yahoo_history(ticker, days)
        if prices:
            rets = compute_returns(prices)
            all_returns[label] = [r["log_return"] for r in rets]
    
    labels = list(all_returns.keys())
    matrix = {}
    
    for a in labels:
        matrix[a] = {}
        for b in labels:
            if a == b:
                matrix[a][b] = 1.0
                continue
            
            ra = all_returns[a]
            rb = all_returns[b]
            n = min(len(ra), len(rb))
            if n < 20:
                matrix[a][b] = None
                continue
            
            ra_trim = ra[-n:]
            rb_trim = rb[-n:]
            mean_a = sum(ra_trim) / n
            mean_b = sum(rb_trim) / n
            
            cov = sum((a_v - mean_a) * (b_v - mean_b) for a_v, b_v in zip(ra_trim, rb_trim)) / n
            std_a = math.sqrt(sum((v - mean_a) ** 2 for v in ra_trim) / n)
            std_b = math.sqrt(sum((v - mean_b) ** 2 for v in rb_trim) / n)
            
            if std_a > 0 and std_b > 0:
                matrix[a][b] = round(cov / (std_a * std_b), 4)
            else:
                matrix[a][b] = None
    
    return {
        "assets": labels,
        "correlation_matrix": matrix,
        "period_days": days,
        "computed_at": datetime.now().isoformat(),
    }


def detect_correlation_regime_change(
    ticker_a: str = "^GSPC",
    ticker_b: str = "^TNX",
    short_window: int = 21,
    long_window: int = 126,
    days: int = 504,
) -> Dict:
    """
    Detect regime changes by comparing short vs long-term rolling correlation.
    
    A significant divergence between short and long windows signals
    a potential regime change (e.g., stocks/bonds correlation flip).
    
    Returns:
        Dict with current short/long correlations and regime signal.
    """
    prices_a = fetch_yahoo_history(ticker_a, days)
    prices_b = fetch_yahoo_history(ticker_b, days)
    
    rets_a = [r["log_return"] for r in compute_returns(prices_a)]
    rets_b = [r["log_return"] for r in compute_returns(prices_b)]
    
    short_corr = rolling_correlation(rets_a, rets_b, short_window)
    long_corr = rolling_correlation(rets_a, rets_b, long_window)
    
    latest_short = next((v for v in reversed(short_corr) if v is not None), None)
    latest_long = next((v for v in reversed(long_corr) if v is not None), None)
    
    regime = "stable"
    if latest_short is not None and latest_long is not None:
        diff = abs(latest_short - latest_long)
        if diff > 0.3:
            regime = "regime_change_detected"
        elif diff > 0.15:
            regime = "diverging"
    
    return {
        "ticker_a": ticker_a,
        "ticker_b": ticker_b,
        "short_window": short_window,
        "long_window": long_window,
        "current_short_corr": latest_short,
        "current_long_corr": latest_long,
        "regime_signal": regime,
        "computed_at": datetime.now().isoformat(),
    }
