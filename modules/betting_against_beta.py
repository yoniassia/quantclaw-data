"""Betting Against Beta (BAB) Factor — Implements the Frazzini-Pedersen (2014) strategy
that goes long leveraged low-beta assets and short high-beta assets. Exploits the
empirical finding that the Security Market Line is too flat: low-beta stocks earn
higher risk-adjusted returns than CAPM predicts.

Data sources: Yahoo Finance (free), FRED for risk-free rate.
"""

import math
from typing import Dict, List, Optional, Tuple


def estimate_beta(
    asset_returns: List[float],
    market_returns: List[float],
    shrinkage: float = 0.6,
) -> Dict[str, float]:
    """Estimate beta with Vasicek shrinkage toward cross-sectional mean.

    Frazzini-Pedersen use shrinkage to reduce estimation error in betas.
    Beta_shrunk = shrinkage * beta_ts + (1 - shrinkage) * beta_xs_mean

    Args:
        asset_returns: Asset's excess returns (list of floats).
        market_returns: Market excess returns (same length).
        shrinkage: Weight on time-series beta vs cross-sectional mean (default 0.6).

    Returns:
        Dict with raw_beta, shrunk_beta, r_squared, vol_asset, vol_market.
    """
    if len(asset_returns) != len(market_returns):
        raise ValueError("Return series must be same length")
    n = len(asset_returns)
    if n < 3:
        return {"raw_beta": 1.0, "shrunk_beta": 1.0, "r_squared": 0, "vol_asset": 0, "vol_market": 0}

    mean_a = sum(asset_returns) / n
    mean_m = sum(market_returns) / n

    cov = sum((a - mean_a) * (m - mean_m) for a, m in zip(asset_returns, market_returns)) / n
    var_m = sum((m - mean_m) ** 2 for m in market_returns) / n
    var_a = sum((a - mean_a) ** 2 for a in asset_returns) / n

    raw_beta = cov / var_m if var_m > 0 else 1.0

    # Shrink toward 1.0 (cross-sectional mean of betas)
    shrunk_beta = shrinkage * raw_beta + (1 - shrinkage) * 1.0

    # R-squared
    ss_res = sum((a - mean_a - raw_beta * (m - mean_m)) ** 2 for a, m in zip(asset_returns, market_returns))
    ss_tot = sum((a - mean_a) ** 2 for a in asset_returns)
    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {
        "raw_beta": round(raw_beta, 6),
        "shrunk_beta": round(shrunk_beta, 6),
        "r_squared": round(max(0, r_sq), 6),
        "vol_asset": round(math.sqrt(var_a) * math.sqrt(12), 6),
        "vol_market": round(math.sqrt(var_m) * math.sqrt(12), 6),
        "correlation": round(cov / (math.sqrt(var_a) * math.sqrt(var_m)), 6) if var_a > 0 and var_m > 0 else 0,
    }


def construct_bab_portfolio(
    betas: Dict[str, float],
    n_long: int = 10,
    n_short: int = 10,
) -> Dict[str, object]:
    """Construct a Betting Against Beta portfolio.

    Long low-beta stocks (leveraged up), short high-beta stocks (deleveraged).
    Both legs are beta-weighted to be market-neutral.

    Args:
        betas: Dict of ticker -> shrunk beta.
        n_long: Number of low-beta stocks to go long.
        n_short: Number of high-beta stocks to short.

    Returns:
        Portfolio with positions and leg details.
    """
    sorted_by_beta = sorted(betas.items(), key=lambda x: x[1])

    low_beta = sorted_by_beta[:n_long]
    high_beta = sorted_by_beta[-n_short:]

    # Rank-weight within each leg
    low_beta_sum = sum(1.0 / (i + 1) for i in range(n_long))
    high_beta_sum = sum(1.0 / (i + 1) for i in range(n_short))

    long_positions = {}
    for i, (ticker, beta) in enumerate(low_beta):
        rank_weight = (1.0 / (i + 1)) / low_beta_sum
        # Leverage up to target beta = 1
        leverage = 1.0 / beta if beta > 0.1 else 10.0
        long_positions[ticker] = {
            "weight": round(rank_weight, 6),
            "beta": round(beta, 4),
            "leverage": round(min(leverage, 10.0), 4),
            "effective_weight": round(rank_weight * min(leverage, 10.0), 6),
        }

    short_positions = {}
    for i, (ticker, beta) in enumerate(reversed(high_beta)):
        rank_weight = (1.0 / (i + 1)) / high_beta_sum
        deleverage = 1.0 / beta if beta > 0.1 else 1.0
        short_positions[ticker] = {
            "weight": round(rank_weight, 6),
            "beta": round(beta, 4),
            "deleverage": round(min(deleverage, 1.0), 4),
            "effective_weight": round(rank_weight * min(deleverage, 1.0), 6),
        }

    long_beta = sum(v["beta"] * v["weight"] for v in long_positions.values())
    short_beta = sum(v["beta"] * v["weight"] for v in short_positions.values())

    return {
        "long": long_positions,
        "short": short_positions,
        "long_avg_beta": round(long_beta, 4),
        "short_avg_beta": round(short_beta, 4),
        "beta_spread": round(short_beta - long_beta, 4),
        "n_long": n_long,
        "n_short": n_short,
    }


def bab_factor_return(
    low_beta_return: float,
    high_beta_return: float,
    low_beta_avg: float,
    high_beta_avg: float,
    risk_free: float = 0.0,
) -> Dict[str, float]:
    """Calculate the BAB factor return for a single period.

    BAB = 1/beta_L * (R_L - Rf) - 1/beta_H * (R_H - Rf)

    Args:
        low_beta_return: Return of low-beta portfolio.
        high_beta_return: Return of high-beta portfolio.
        low_beta_avg: Average beta of low-beta portfolio.
        high_beta_avg: Average beta of high-beta portfolio.
        risk_free: Risk-free rate for the period.

    Returns:
        BAB factor return and components.
    """
    long_excess = low_beta_return - risk_free
    short_excess = high_beta_return - risk_free

    leveraged_long = long_excess / low_beta_avg if low_beta_avg > 0.1 else long_excess
    deleveraged_short = short_excess / high_beta_avg if high_beta_avg > 0.1 else short_excess

    bab_return = leveraged_long - deleveraged_short

    return {
        "bab_return": round(bab_return, 6),
        "long_contribution": round(leveraged_long, 6),
        "short_contribution": round(-deleveraged_short, 6),
        "long_raw_return": round(low_beta_return, 6),
        "short_raw_return": round(high_beta_return, 6),
    }
