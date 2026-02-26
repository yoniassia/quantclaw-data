"""
Risk Budget Monitor — tracks portfolio risk allocation across factors and assets.

Monitors tracking error, VaR allocation, and risk contribution by position/factor.
Uses free data from Yahoo Finance and portfolio weights.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RiskBudget:
    """Risk budget allocation for a portfolio component."""
    name: str
    weight: float
    risk_contribution: float
    risk_share: float  # percentage of total risk
    var_allocation: float
    tracking_error_contribution: float
    within_budget: bool
    budget_limit: float
    utilization: float  # risk_share / budget_limit


def compute_covariance_matrix(returns: Dict[str, List[float]]) -> Tuple[np.ndarray, List[str]]:
    """Compute annualized covariance matrix from daily returns.

    Args:
        returns: Dict mapping asset names to lists of daily returns.

    Returns:
        Tuple of (covariance matrix, list of asset names).
    """
    names = sorted(returns.keys())
    n = len(names)
    min_len = min(len(returns[k]) for k in names)
    data = np.array([returns[k][:min_len] for k in names])
    cov = np.cov(data) * 252  # annualize
    if cov.ndim == 0:
        cov = cov.reshape(1, 1)
    return cov, names


def marginal_risk_contribution(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Calculate marginal risk contribution for each asset.

    Args:
        weights: Portfolio weight vector.
        cov: Covariance matrix.

    Returns:
        Array of marginal risk contributions.
    """
    port_var = weights @ cov @ weights
    port_vol = np.sqrt(port_var) if port_var > 0 else 1e-10
    mrc = (cov @ weights) / port_vol
    return mrc


def risk_contribution_decomposition(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Decompose portfolio risk into per-asset contributions.

    Args:
        weights: Portfolio weight vector.
        cov: Covariance matrix.

    Returns:
        Array of risk contributions (sum = portfolio volatility).
    """
    port_var = weights @ cov @ weights
    port_vol = np.sqrt(port_var) if port_var > 0 else 1e-10
    rc = weights * (cov @ weights) / port_vol
    return rc


def parametric_var(weights: np.ndarray, cov: np.ndarray,
                   confidence: float = 0.95, horizon_days: int = 1,
                   portfolio_value: float = 1_000_000) -> float:
    """Calculate parametric Value-at-Risk.

    Args:
        weights: Portfolio weight vector.
        cov: Annualized covariance matrix.
        confidence: Confidence level (e.g., 0.95 or 0.99).
        horizon_days: Holding period in days.
        portfolio_value: Total portfolio value in dollars.

    Returns:
        VaR in dollar terms.
    """
    from scipy.stats import norm
    port_var = weights @ cov @ weights
    port_vol_daily = np.sqrt(port_var / 252)
    z = norm.ppf(confidence)
    var = z * port_vol_daily * np.sqrt(horizon_days) * portfolio_value
    return var


def tracking_error(weights: np.ndarray, benchmark_weights: np.ndarray,
                   cov: np.ndarray) -> float:
    """Calculate ex-ante tracking error vs benchmark.

    Args:
        weights: Portfolio weight vector.
        benchmark_weights: Benchmark weight vector.
        cov: Annualized covariance matrix.

    Returns:
        Annualized tracking error as a decimal.
    """
    active = weights - benchmark_weights
    te_var = active @ cov @ active
    return np.sqrt(te_var) if te_var > 0 else 0.0


def monitor_risk_budgets(
    weights: Dict[str, float],
    returns: Dict[str, List[float]],
    budgets: Dict[str, float],
    benchmark_weights: Optional[Dict[str, float]] = None,
    portfolio_value: float = 1_000_000,
    confidence: float = 0.95
) -> List[RiskBudget]:
    """Monitor risk budget utilization across portfolio positions.

    Args:
        weights: Dict of asset name -> portfolio weight.
        returns: Dict of asset name -> daily return series.
        budgets: Dict of asset name -> max allowed risk share (0-1).
        benchmark_weights: Optional benchmark weights for TE calculation.
        portfolio_value: Portfolio value in dollars.
        confidence: VaR confidence level.

    Returns:
        List of RiskBudget objects with utilization metrics.
    """
    names = sorted(weights.keys())
    n = len(names)
    w = np.array([weights.get(k, 0) for k in names])
    cov, _ = compute_covariance_matrix({k: returns[k] for k in names if k in returns})

    rc = risk_contribution_decomposition(w, cov)
    total_rc = rc.sum() if rc.sum() > 0 else 1e-10
    total_var = parametric_var(w, cov, confidence, 1, portfolio_value)

    bw = np.array([benchmark_weights.get(k, 0) for k in names]) if benchmark_weights else np.zeros(n)

    results = []
    for i, name in enumerate(names):
        risk_share = rc[i] / total_rc
        budget_limit = budgets.get(name, 1.0)
        utilization = risk_share / budget_limit if budget_limit > 0 else float('inf')

        active_w = np.zeros(n)
        active_w[i] = w[i] - bw[i]
        te_contrib = np.sqrt(max(0, active_w @ cov @ active_w))

        results.append(RiskBudget(
            name=name,
            weight=w[i],
            risk_contribution=rc[i],
            risk_share=risk_share,
            var_allocation=total_var * risk_share,
            tracking_error_contribution=te_contrib,
            within_budget=risk_share <= budget_limit,
            budget_limit=budget_limit,
            utilization=utilization
        ))

    return sorted(results, key=lambda x: x.utilization, reverse=True)


def generate_risk_report(budgets: List[RiskBudget]) -> Dict:
    """Generate summary risk budget report.

    Args:
        budgets: List of RiskBudget objects from monitor_risk_budgets.

    Returns:
        Summary dict with total risk, breaches, and top contributors.
    """
    total_vol = sum(b.risk_contribution for b in budgets)
    breaches = [b for b in budgets if not b.within_budget]
    total_var = sum(b.var_allocation for b in budgets)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "portfolio_volatility": round(total_vol, 6),
        "total_var_95": round(total_var, 2),
        "num_positions": len(budgets),
        "num_breaches": len(breaches),
        "breaches": [{"name": b.name, "risk_share": round(b.risk_share, 4),
                       "budget": round(b.budget_limit, 4),
                       "utilization": round(b.utilization, 4)} for b in breaches],
        "top_risk_contributors": [
            {"name": b.name, "risk_share": round(b.risk_share, 4),
             "weight": round(b.weight, 4)}
            for b in budgets[:5]
        ]
    }
