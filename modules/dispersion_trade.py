"""Dispersion Trade Analyzer — Identifies dispersion trading opportunities by comparing
index implied volatility against constituent implied volatilities. Dispersion trades
profit when the correlation between index components is overpriced (short index vol,
long single-stock vol) or underpriced.

Data sources: Yahoo Finance (free), CBOE (public indices).
"""

import math
from typing import Dict, List, Optional, Tuple


def calculate_implied_correlation(
    index_iv: float,
    constituent_ivs: List[float],
    weights: List[float],
) -> float:
    """Calculate implied correlation from index IV and constituent IVs.

    Uses the formula: rho_implied = (sigma_index^2 - sum(w_i^2 * sigma_i^2)) /
                                     (sum over i!=j of w_i * w_j * sigma_i * sigma_j)

    Args:
        index_iv: Index implied volatility (annualized, decimal e.g. 0.20 for 20%).
        constituent_ivs: List of constituent implied volatilities.
        weights: Portfolio weights of each constituent in the index.

    Returns:
        Implied correlation coefficient.
    """
    if len(constituent_ivs) != len(weights):
        raise ValueError("constituent_ivs and weights must have same length")

    n = len(weights)
    var_index = index_iv ** 2
    weighted_var_sum = sum(w ** 2 * s ** 2 for w, s in zip(weights, constituent_ivs))

    cross_term = 0.0
    for i in range(n):
        for j in range(n):
            if i != j:
                cross_term += weights[i] * weights[j] * constituent_ivs[i] * constituent_ivs[j]

    if cross_term == 0:
        return 0.0

    implied_corr = (var_index - weighted_var_sum) / cross_term
    return max(-1.0, min(1.0, implied_corr))


def dispersion_trade_pnl(
    index_iv_entry: float,
    constituent_ivs_entry: List[float],
    weights: List[float],
    index_rv: float,
    constituent_rvs: List[float],
    notional: float = 1_000_000,
    vega_per_vol_point: float = 1000,
) -> Dict[str, float]:
    """Estimate P&L of a dispersion trade (short index variance, long single-stock variance).

    Args:
        index_iv_entry: Index IV at trade entry.
        constituent_ivs_entry: Constituent IVs at entry.
        weights: Index weights.
        index_rv: Realized volatility of index over holding period.
        constituent_rvs: Realized volatilities of constituents.
        notional: Trade notional.
        vega_per_vol_point: Vega exposure per vol point.

    Returns:
        Dict with index_pnl, constituent_pnl, net_pnl, realized_correlation.
    """
    # Short index vol: profit when RV < IV
    index_pnl = (index_iv_entry - index_rv) * 100 * vega_per_vol_point

    # Long constituent vol: profit when RV > IV
    constituent_pnl = sum(
        w * (rv - iv) * 100 * vega_per_vol_point
        for w, rv, iv in zip(weights, constituent_rvs, constituent_ivs_entry)
    )

    # Realized correlation
    weighted_rv_sum = sum(w ** 2 * rv ** 2 for w, rv in zip(weights, constituent_rvs))
    cross_rv = 0.0
    n = len(weights)
    for i in range(n):
        for j in range(n):
            if i != j:
                cross_rv += weights[i] * weights[j] * constituent_rvs[i] * constituent_rvs[j]

    realized_corr = (index_rv ** 2 - weighted_rv_sum) / cross_rv if cross_rv != 0 else 0.0

    return {
        "index_pnl": round(index_pnl, 2),
        "constituent_pnl": round(constituent_pnl, 2),
        "net_pnl": round(index_pnl + constituent_pnl, 2),
        "realized_correlation": round(max(-1.0, min(1.0, realized_corr)), 4),
        "implied_correlation": round(
            calculate_implied_correlation(index_iv_entry, constituent_ivs_entry, weights), 4
        ),
    }


def scan_dispersion_opportunities(
    index_iv: float,
    constituent_ivs: List[float],
    weights: List[float],
    tickers: List[str],
    correlation_threshold: float = 0.7,
) -> List[Dict]:
    """Scan for dispersion trade opportunities based on implied correlation extremes.

    Args:
        index_iv: Current index implied volatility.
        constituent_ivs: Current constituent IVs.
        weights: Index weights.
        tickers: Constituent ticker symbols.
        correlation_threshold: Flag opportunities when implied corr exceeds this.

    Returns:
        List of opportunity dicts with signal direction and strength.
    """
    implied_corr = calculate_implied_correlation(index_iv, constituent_ivs, weights)
    opportunities = []

    if implied_corr > correlation_threshold:
        # Correlation is high → sell correlation (classic dispersion)
        strength = min((implied_corr - correlation_threshold) / (1 - correlation_threshold), 1.0)
        opportunities.append({
            "signal": "SELL_CORRELATION",
            "implied_correlation": round(implied_corr, 4),
            "strength": round(strength, 4),
            "trade": "Short index vol, long constituent vol",
            "constituents": len(tickers),
        })
    elif implied_corr < 1 - correlation_threshold:
        # Correlation is low → buy correlation (reverse dispersion)
        strength = min(((1 - correlation_threshold) - implied_corr) / (1 - correlation_threshold), 1.0)
        opportunities.append({
            "signal": "BUY_CORRELATION",
            "implied_correlation": round(implied_corr, 4),
            "strength": round(strength, 4),
            "trade": "Long index vol, short constituent vol",
            "constituents": len(tickers),
        })

    # Per-constituent relative value
    avg_iv = sum(iv for iv in constituent_ivs) / len(constituent_ivs) if constituent_ivs else 0
    for ticker, iv, w in zip(tickers, constituent_ivs, weights):
        z = (iv - avg_iv) / avg_iv if avg_iv > 0 else 0
        if abs(z) > 0.5:
            opportunities.append({
                "signal": "RICH" if z > 0 else "CHEAP",
                "ticker": ticker,
                "iv": round(iv, 4),
                "z_score_vs_peers": round(z, 4),
                "weight": round(w, 4),
            })

    return opportunities
