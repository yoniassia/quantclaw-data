"""Momentum Factor Backtest Suite — cross-sectional and time-series momentum strategy backtesting.

Implements Jegadeesh-Titman cross-sectional momentum, time-series momentum (Moskowitz),
and dual momentum (Antonacci). Uses numpy for computation, designed for free data sources.
"""

import numpy as np
from typing import Dict, List, Optional


def cross_sectional_momentum(returns_matrix: List[List[float]], lookback: int = 12,
                              holding: int = 1, top_pct: float = 0.2) -> Dict:
    """Jegadeesh-Titman cross-sectional momentum: long winners, short losers.

    Args:
        returns_matrix: List of return series per asset (rows=assets, cols=periods).
        lookback: Formation period (months).
        holding: Holding period (months).
        top_pct: Fraction of assets in long/short legs.

    Returns:
        Dict with long/short portfolio returns, spread, and Sharpe.
    """
    mat = np.array(returns_matrix, dtype=float)
    n_assets, n_periods = mat.shape
    if n_periods <= lookback + holding:
        return {"error": "Insufficient periods for lookback + holding"}

    n_select = max(1, int(n_assets * top_pct))
    spread_returns = []

    for t in range(lookback, n_periods - holding + 1):
        # Formation: cumulative return over lookback
        formation = np.prod(1 + mat[:, t - lookback:t], axis=1) - 1
        ranked = np.argsort(formation)
        winners = ranked[-n_select:]
        losers = ranked[:n_select]
        # Holding period return
        hold_ret = np.prod(1 + mat[:, t:t + holding], axis=1) - 1
        long_ret = float(np.mean(hold_ret[winners]))
        short_ret = float(np.mean(hold_ret[losers]))
        spread_returns.append(long_ret - short_ret)

    sr = np.array(spread_returns)
    sharpe = float(np.mean(sr) / np.std(sr) * np.sqrt(12 / holding)) if np.std(sr) > 0 else 0.0
    return {
        "n_periods": len(spread_returns),
        "annualized_return": round(float(np.mean(sr) * 12 / holding), 4),
        "annualized_vol": round(float(np.std(sr) * np.sqrt(12 / holding)), 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(float(_max_drawdown(sr)), 4),
        "win_rate": round(float(np.mean(sr > 0)), 4),
        "avg_spread": round(float(np.mean(sr)), 6),
        "recent_spreads": [round(float(x), 6) for x in sr[-12:]],
    }


def time_series_momentum(returns: List[float], lookback: int = 12) -> Dict:
    """Time-series momentum (TSMOM): go long if past return positive, else short.

    Args:
        returns: Monthly return series for single asset.
        lookback: Signal lookback in months.

    Returns:
        Strategy performance dict.
    """
    r = np.array(returns, dtype=float)
    if len(r) <= lookback:
        return {"error": "Insufficient data"}

    strat_returns = []
    for t in range(lookback, len(r)):
        signal = 1.0 if np.sum(r[t - lookback:t]) > 0 else -1.0
        strat_returns.append(signal * r[t])

    sr = np.array(strat_returns)
    sharpe = float(np.mean(sr) / np.std(sr) * np.sqrt(12)) if np.std(sr) > 0 else 0.0
    return {
        "annualized_return": round(float(np.mean(sr) * 12), 4),
        "annualized_vol": round(float(np.std(sr) * np.sqrt(12)), 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(float(_max_drawdown(sr)), 4),
        "hit_rate": round(float(np.mean(sr > 0)), 4),
    }


def dual_momentum(asset_returns: List[float], benchmark_returns: List[float],
                   safe_rate: float = 0.0, lookback: int = 12) -> Dict:
    """Gary Antonacci dual momentum: absolute + relative momentum.

    If asset > benchmark AND asset > 0 → long asset.
    Elif benchmark > 0 → long benchmark.
    Else → safe asset.
    """
    a = np.array(asset_returns, dtype=float)
    b = np.array(benchmark_returns, dtype=float)
    n = min(len(a), len(b))
    if n <= lookback:
        return {"error": "Insufficient data"}

    strat = []
    allocations = []
    for t in range(lookback, n):
        a_mom = np.prod(1 + a[t - lookback:t]) - 1
        b_mom = np.prod(1 + b[t - lookback:t]) - 1
        if a_mom > b_mom and a_mom > 0:
            strat.append(a[t])
            allocations.append("asset")
        elif b_mom > 0:
            strat.append(b[t])
            allocations.append("benchmark")
        else:
            strat.append(safe_rate / 12)
            allocations.append("safe")

    sr = np.array(strat)
    return {
        "annualized_return": round(float(np.mean(sr) * 12), 4),
        "sharpe_ratio": round(float(np.mean(sr) / np.std(sr) * np.sqrt(12)) if np.std(sr) > 0 else 0.0, 4),
        "max_drawdown": round(float(_max_drawdown(sr)), 4),
        "allocation_pcts": {
            "asset": round(allocations.count("asset") / len(allocations), 4),
            "benchmark": round(allocations.count("benchmark") / len(allocations), 4),
            "safe": round(allocations.count("safe") / len(allocations), 4),
        },
    }


def _max_drawdown(returns: np.ndarray) -> float:
    """Compute maximum drawdown from a return series."""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
