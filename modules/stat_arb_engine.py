"""Statistical Arbitrage Engine — pairs and basket trading with cointegration, z-scores, and mean-reversion signals.

Identifies statistically cointegrated pairs/baskets, generates entry/exit signals based on
z-score thresholds, and provides risk metrics for stat-arb strategies.
Uses free data from Yahoo Finance.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def compute_spread_zscore(prices_a: List[float], prices_b: List[float], lookback: int = 60) -> Dict:
    """Compute hedge ratio, spread, and z-score for a pair of price series.

    Args:
        prices_a: Price series for asset A.
        prices_b: Price series for asset B.
        lookback: Rolling window for z-score calculation.

    Returns:
        Dict with hedge_ratio, spread, zscore, mean, std.
    """
    a = np.array(prices_a, dtype=float)
    b = np.array(prices_b, dtype=float)
    if len(a) < lookback or len(b) < lookback:
        return {"error": "Insufficient data for lookback period"}
    # OLS hedge ratio: a = beta * b + residual
    beta = np.cov(a, b)[0, 1] / np.var(b)
    spread = a - beta * b
    rolling_mean = np.convolve(spread, np.ones(lookback) / lookback, mode='valid')
    rolling_std = np.array([np.std(spread[max(0, i - lookback + 1):i + 1]) for i in range(lookback - 1, len(spread))])
    rolling_std[rolling_std == 0] = 1e-8
    zscore = (spread[lookback - 1:] - rolling_mean) / rolling_std
    return {
        "hedge_ratio": round(float(beta), 6),
        "current_spread": round(float(spread[-1]), 4),
        "current_zscore": round(float(zscore[-1]), 4),
        "spread_mean": round(float(rolling_mean[-1]), 4),
        "spread_std": round(float(rolling_std[-1]), 4),
        "spread_series": [round(float(x), 4) for x in spread[-20:]],
        "zscore_series": [round(float(x), 4) for x in zscore[-20:]],
    }


def generate_signals(zscore_series: List[float], entry_threshold: float = 2.0,
                     exit_threshold: float = 0.5) -> List[Dict]:
    """Generate stat-arb entry/exit signals from z-score series.

    Args:
        zscore_series: Z-score time series.
        entry_threshold: Absolute z-score for entry.
        exit_threshold: Absolute z-score for exit.

    Returns:
        List of signal dicts with index, zscore, and action.
    """
    signals = []
    position = 0  # 0=flat, 1=long spread, -1=short spread
    for i, z in enumerate(zscore_series):
        if position == 0:
            if z > entry_threshold:
                signals.append({"index": i, "zscore": round(z, 4), "action": "short_spread"})
                position = -1
            elif z < -entry_threshold:
                signals.append({"index": i, "zscore": round(z, 4), "action": "long_spread"})
                position = 1
        elif position == 1 and z > -exit_threshold:
            signals.append({"index": i, "zscore": round(z, 4), "action": "close_long"})
            position = 0
        elif position == -1 and z < exit_threshold:
            signals.append({"index": i, "zscore": round(z, 4), "action": "close_short"})
            position = 0
    return signals


def engle_granger_test(prices_a: List[float], prices_b: List[float]) -> Dict:
    """Simplified Engle-Granger cointegration test using ADF-like residual stationarity check.

    Returns dict with hedge_ratio, residual_adf_stat (approximate), and is_cointegrated flag.
    """
    a = np.array(prices_a, dtype=float)
    b = np.array(prices_b, dtype=float)
    beta = np.cov(a, b)[0, 1] / np.var(b)
    alpha = np.mean(a) - beta * np.mean(b)
    residuals = a - alpha - beta * b
    # Simplified ADF: regress diff(residuals) on lag(residuals)
    diff_r = np.diff(residuals)
    lag_r = residuals[:-1]
    if np.var(lag_r) == 0:
        return {"hedge_ratio": float(beta), "adf_stat": 0.0, "is_cointegrated": False}
    gamma = np.cov(diff_r, lag_r)[0, 1] / np.var(lag_r)
    se = np.std(diff_r - gamma * lag_r) / (np.std(lag_r) * np.sqrt(len(lag_r)))
    adf_stat = gamma / se if se != 0 else 0.0
    # 5% critical value for ~250 obs ≈ -3.37
    return {
        "hedge_ratio": round(float(beta), 6),
        "intercept": round(float(alpha), 6),
        "adf_stat": round(float(adf_stat), 4),
        "is_cointegrated": bool(adf_stat < -3.37),
        "half_life": round(float(-np.log(2) / gamma), 2) if gamma < 0 else None,
    }
