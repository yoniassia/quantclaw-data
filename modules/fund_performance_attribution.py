"""Fund Performance Attribution — Brinson-Hood-Beebower (BHB) and factor-based
attribution for fund returns. Decomposes alpha into allocation, selection, and
interaction effects. Supports multi-period linking and factor regression."""

import json
import statistics
from typing import Dict, List, Optional, Tuple


def brinson_single_period(portfolio_weights: Dict[str, float],
                            benchmark_weights: Dict[str, float],
                            portfolio_returns: Dict[str, float],
                            benchmark_returns: Dict[str, float]) -> Dict:
    """Brinson-Hood-Beebower single-period attribution.
    
    Args:
        portfolio_weights: Sector -> portfolio weight
        benchmark_weights: Sector -> benchmark weight
        portfolio_returns: Sector -> portfolio return
        benchmark_returns: Sector -> benchmark return
    
    Returns:
        Attribution breakdown by sector with allocation, selection, interaction effects
    """
    sectors = set(portfolio_weights) | set(benchmark_weights)
    
    total_port_ret = sum(portfolio_weights.get(s, 0) * portfolio_returns.get(s, 0) for s in sectors)
    total_bm_ret = sum(benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0) for s in sectors)
    
    sector_details = []
    total_allocation = 0
    total_selection = 0
    total_interaction = 0
    
    for sector in sorted(sectors):
        wp = portfolio_weights.get(sector, 0)
        wb = benchmark_weights.get(sector, 0)
        rp = portfolio_returns.get(sector, 0)
        rb = benchmark_returns.get(sector, 0)
        
        allocation = (wp - wb) * rb
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)
        
        total_allocation += allocation
        total_selection += selection
        total_interaction += interaction
        
        sector_details.append({
            "sector": sector,
            "port_weight": round(wp, 4),
            "bench_weight": round(wb, 4),
            "port_return": round(rp, 4),
            "bench_return": round(rb, 4),
            "allocation_effect": round(allocation, 6),
            "selection_effect": round(selection, 6),
            "interaction_effect": round(interaction, 6),
            "total_effect": round(allocation + selection + interaction, 6)
        })
    
    active_return = total_port_ret - total_bm_ret
    
    return {
        "portfolio_return": round(total_port_ret, 6),
        "benchmark_return": round(total_bm_ret, 6),
        "active_return": round(active_return, 6),
        "allocation_effect": round(total_allocation, 6),
        "selection_effect": round(total_selection, 6),
        "interaction_effect": round(total_interaction, 6),
        "sum_of_effects": round(total_allocation + total_selection + total_interaction, 6),
        "sectors": sector_details
    }


def multi_period_attribution(periods: List[Dict]) -> Dict:
    """Link single-period attributions across multiple periods using geometric linking.
    
    Args:
        periods: List of dicts, each with 'date', 'portfolio_return', 'benchmark_return',
                'allocation', 'selection', 'interaction'
    
    Returns:
        Multi-period linked attribution
    """
    if not periods:
        return {"error": "No periods provided"}
    
    cum_port = 1.0
    cum_bm = 1.0
    
    linked_alloc = 0
    linked_select = 0
    linked_inter = 0
    
    for p in periods:
        pr = p["portfolio_return"]
        br = p["benchmark_return"]
        
        # Carino smoothing factor for geometric linking
        cum_port *= (1 + pr)
        cum_bm *= (1 + br)
        
        # Simple additive (Frongello method approximation)
        scale = cum_bm  # accumulated benchmark
        linked_alloc += p.get("allocation", 0) * scale
        linked_select += p.get("selection", 0) * scale
        linked_inter += p.get("interaction", 0) * scale
    
    total_active = cum_port - cum_bm
    sum_effects = linked_alloc + linked_select + linked_inter
    
    # Rescale to match geometric active return
    if abs(sum_effects) > 1e-10:
        scale_factor = total_active / sum_effects
        linked_alloc *= scale_factor
        linked_select *= scale_factor
        linked_inter *= scale_factor
    
    return {
        "cumulative_portfolio_return": round(cum_port - 1, 6),
        "cumulative_benchmark_return": round(cum_bm - 1, 6),
        "cumulative_active_return": round(total_active, 6),
        "linked_allocation": round(linked_alloc, 6),
        "linked_selection": round(linked_select, 6),
        "linked_interaction": round(linked_inter, 6),
        "num_periods": len(periods)
    }


def factor_attribution(returns: List[float], factor_returns: Dict[str, List[float]],
                         risk_free: List[float] = None) -> Dict:
    """Factor-based regression attribution (Fama-French style).
    
    Args:
        returns: Portfolio excess returns per period
        factor_returns: Factor name -> list of factor returns per period
        risk_free: Risk-free rates per period (optional)
    
    Returns:
        Factor exposures (betas), alpha, R-squared
    """
    n = len(returns)
    if n < 5:
        return {"error": "Need at least 5 periods for regression"}
    
    rf = risk_free or [0.0] * n
    excess_returns = [r - f for r, f in zip(returns, rf)]
    
    factors = list(factor_returns.keys())
    k = len(factors)
    
    # Simple OLS via normal equations (X'X)^-1 X'y
    # Build X matrix (with intercept)
    X = []
    for i in range(n):
        row = [1.0]  # intercept (alpha)
        for f in factors:
            row.append(factor_returns[f][i])
        X.append(row)
    
    # X'X
    XtX = [[sum(X[i][j] * X[i][l] for i in range(n)) for l in range(k + 1)] for j in range(k + 1)]
    # X'y
    Xty = [sum(X[i][j] * excess_returns[i] for i in range(n)) for j in range(k + 1)]
    
    # Solve via Gaussian elimination
    aug = [XtX[i][:] + [Xty[i]] for i in range(k + 1)]
    for col in range(k + 1):
        max_row = max(range(col, k + 1), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        if abs(aug[col][col]) < 1e-12:
            continue
        for row in range(k + 1):
            if row != col:
                factor = aug[row][col] / aug[col][col]
                for j in range(k + 2):
                    aug[row][j] -= factor * aug[col][j]
    
    coeffs = [aug[i][k + 1] / aug[i][i] if abs(aug[i][i]) > 1e-12 else 0 for i in range(k + 1)]
    
    alpha = coeffs[0]
    betas = {factors[i]: round(coeffs[i + 1], 4) for i in range(k)}
    
    # R-squared
    y_mean = statistics.mean(excess_returns)
    ss_tot = sum((y - y_mean) ** 2 for y in excess_returns)
    y_pred = [sum(X[i][j] * coeffs[j] for j in range(k + 1)) for i in range(n)]
    ss_res = sum((excess_returns[i] - y_pred[i]) ** 2 for i in range(n))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    # Factor contributions
    factor_contrib = {}
    for i, f in enumerate(factors):
        avg_factor = statistics.mean(factor_returns[f])
        factor_contrib[f] = round(coeffs[i + 1] * avg_factor, 6)
    
    return {
        "alpha_annualized_pct": round(alpha * 12 * 100, 2),  # assuming monthly
        "alpha_monthly": round(alpha, 6),
        "betas": betas,
        "r_squared": round(r_squared, 4),
        "factor_contributions": factor_contrib,
        "residual_return": round(alpha, 6),
        "periods": n,
        "factors_used": factors
    }


def holdings_based_attribution(holdings: List[Dict], benchmark_holdings: List[Dict]) -> Dict:
    """Holdings-based attribution comparing portfolio to benchmark at security level.
    
    Args:
        holdings: List of {'ticker': str, 'weight': float, 'return': float, 'sector': str}
        benchmark_holdings: Same format for benchmark
    
    Returns:
        Security and sector level attribution
    """
    bm_map = {h["ticker"]: h for h in benchmark_holdings}
    sectors = set(h.get("sector", "Other") for h in holdings + benchmark_holdings)
    
    security_effects = []
    sector_agg = {s: {"alloc": 0, "select": 0, "port_w": 0, "bm_w": 0} for s in sectors}
    
    all_tickers = set(h["ticker"] for h in holdings) | set(h["ticker"] for h in benchmark_holdings)
    port_map = {h["ticker"]: h for h in holdings}
    
    for ticker in all_tickers:
        ph = port_map.get(ticker, {"weight": 0, "return": 0, "sector": "Other"})
        bh = bm_map.get(ticker, {"weight": 0, "return": 0, "sector": "Other"})
        
        wp = ph["weight"]
        wb = bh["weight"]
        rp = ph["return"]
        rb = bh["return"]
        sector = ph.get("sector") or bh.get("sector", "Other")
        
        effect = wp * rp - wb * rb
        
        security_effects.append({
            "ticker": ticker,
            "sector": sector,
            "port_weight": wp,
            "bench_weight": wb,
            "active_weight": round(wp - wb, 4),
            "port_return": rp,
            "bench_return": rb,
            "total_effect": round(effect, 6)
        })
        
        if sector in sector_agg:
            sector_agg[sector]["port_w"] += wp
            sector_agg[sector]["bm_w"] += wb
    
    # Sort by absolute effect
    security_effects.sort(key=lambda x: abs(x["total_effect"]), reverse=True)
    
    return {
        "top_contributors": [s for s in security_effects if s["total_effect"] > 0][:10],
        "top_detractors": [s for s in security_effects if s["total_effect"] < 0][:10],
        "total_securities": len(security_effects),
        "active_positions": sum(1 for s in security_effects if abs(s["active_weight"]) > 0.001)
    }
