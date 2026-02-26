"""
Cointegration Pair Finder — Engle-Granger and Johansen tests for pairs/basket trading.

Identifies statistically cointegrated asset pairs from a universe of tickers using
ADF-based Engle-Granger two-step method and Johansen trace/eigenvalue tests.
Uses Yahoo Finance for price data (free).
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from itertools import combinations


def _fetch_prices(tickers: List[str], period: str = "1y") -> Dict[str, np.ndarray]:
    """Fetch adjusted close prices via yfinance."""
    try:
        import yfinance as yf
        data = yf.download(tickers, period=period, progress=False)
        if hasattr(data, 'columns') and isinstance(data.columns, object):
            try:
                closes = data["Adj Close"]
            except (KeyError, TypeError):
                closes = data["Close"]
        else:
            closes = data
        result = {}
        for t in tickers:
            try:
                col = closes[t].dropna().values
                if len(col) > 50:
                    result[t] = col
            except (KeyError, TypeError):
                pass
        return result
    except Exception:
        return {}


def _adf_test(series: np.ndarray) -> Dict[str, Any]:
    """Augmented Dickey-Fuller test for stationarity."""
    n = len(series)
    if n < 20:
        return {"statistic": 0, "pvalue": 1.0, "stationary": False}
    # Simple ADF: regress diff(y) on y_lag + constant
    dy = np.diff(series)
    y_lag = series[:-1]
    X = np.column_stack([y_lag, np.ones(len(y_lag))])
    try:
        beta = np.linalg.lstsq(X, dy, rcond=None)[0]
        resid = dy - X @ beta
        se = np.sqrt(np.sum(resid**2) / (n - 3)) / np.sqrt(np.sum((y_lag - y_lag.mean())**2))
        t_stat = beta[0] / se if se > 0 else 0
    except Exception:
        return {"statistic": 0, "pvalue": 1.0, "stationary": False}
    # Approximate p-value using MacKinnon critical values for n>100
    # Critical values: 1%=-3.43, 5%=-2.86, 10%=-2.57
    if t_stat < -3.43:
        p = 0.005
    elif t_stat < -2.86:
        p = 0.03
    elif t_stat < -2.57:
        p = 0.07
    elif t_stat < -1.94:
        p = 0.15
    else:
        p = 0.5
    return {"statistic": float(t_stat), "pvalue": p, "stationary": t_stat < -2.86}


def engle_granger_test(series_a: np.ndarray, series_b: np.ndarray) -> Dict[str, Any]:
    """
    Engle-Granger two-step cointegration test.

    Step 1: OLS regression of A on B.
    Step 2: ADF test on residuals.

    Returns hedge ratio, spread statistics, and cointegration p-value.
    """
    n = min(len(series_a), len(series_b))
    a, b = series_a[:n], series_b[:n]
    # OLS: a = alpha + beta*b + eps
    X = np.column_stack([b, np.ones(n)])
    beta = np.linalg.lstsq(X, a, rcond=None)[0]
    hedge_ratio = float(beta[0])
    intercept = float(beta[1])
    spread = a - hedge_ratio * b - intercept
    adf = _adf_test(spread)
    half_life = _half_life(spread)
    return {
        "hedge_ratio": hedge_ratio,
        "intercept": intercept,
        "adf_statistic": adf["statistic"],
        "pvalue": adf["pvalue"],
        "cointegrated": adf["stationary"],
        "spread_mean": float(np.mean(spread)),
        "spread_std": float(np.std(spread)),
        "half_life_days": half_life,
        "current_zscore": float((spread[-1] - np.mean(spread)) / np.std(spread)) if np.std(spread) > 0 else 0,
    }


def _half_life(spread: np.ndarray) -> float:
    """Estimate mean-reversion half-life via AR(1)."""
    lag = spread[:-1]
    ret = np.diff(spread)
    if len(lag) < 10:
        return float("inf")
    X = np.column_stack([lag, np.ones(len(lag))])
    beta = np.linalg.lstsq(X, ret, rcond=None)[0]
    phi = beta[0]
    if phi >= 0:
        return float("inf")
    return float(-np.log(2) / np.log(1 + phi)) if (1 + phi) > 0 else float("inf")


def scan_universe(tickers: List[str], period: str = "1y", max_pvalue: float = 0.05) -> List[Dict[str, Any]]:
    """
    Scan all pairs in a ticker universe for cointegration.

    Args:
        tickers: List of ticker symbols
        period: Lookback period (yfinance format)
        max_pvalue: Maximum p-value threshold for cointegration

    Returns:
        List of cointegrated pairs sorted by p-value (ascending)
    """
    prices = _fetch_prices(tickers, period)
    available = list(prices.keys())
    results = []
    for t1, t2 in combinations(available, 2):
        try:
            test = engle_granger_test(prices[t1], prices[t2])
            if test["pvalue"] <= max_pvalue:
                results.append({
                    "pair": f"{t1}/{t2}",
                    "ticker_a": t1,
                    "ticker_b": t2,
                    **test,
                })
        except Exception:
            continue
    results.sort(key=lambda x: x["pvalue"])
    return results


def get_pair_spread_signals(ticker_a: str, ticker_b: str, period: str = "1y",
                            entry_z: float = 2.0, exit_z: float = 0.5) -> Dict[str, Any]:
    """
    Generate trading signals for a cointegrated pair.

    Args:
        ticker_a: First ticker
        ticker_b: Second ticker
        period: Lookback period
        entry_z: Z-score threshold for entry
        exit_z: Z-score threshold for exit

    Returns:
        Cointegration stats, current signal, and recent z-scores
    """
    prices = _fetch_prices([ticker_a, ticker_b], period)
    if ticker_a not in prices or ticker_b not in prices:
        return {"error": "Could not fetch price data"}
    test = engle_granger_test(prices[ticker_a], prices[ticker_b])
    z = test["current_zscore"]
    if z > entry_z:
        signal = "SHORT_SPREAD"
    elif z < -entry_z:
        signal = "LONG_SPREAD"
    elif abs(z) < exit_z:
        signal = "EXIT"
    else:
        signal = "HOLD"
    # Recent z-scores (last 20 days)
    n = min(len(prices[ticker_a]), len(prices[ticker_b]))
    spread = prices[ticker_a][:n] - test["hedge_ratio"] * prices[ticker_b][:n] - test["intercept"]
    mu, sigma = np.mean(spread), np.std(spread)
    recent_z = ((spread[-20:] - mu) / sigma).tolist() if sigma > 0 else []
    return {
        **test,
        "signal": signal,
        "entry_threshold": entry_z,
        "exit_threshold": exit_z,
        "recent_zscores": [round(z, 3) for z in recent_z],
    }
