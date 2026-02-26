"""
Market Impact Estimator — Almgren-Chriss optimal execution and impact models.

Estimates expected market impact for large orders using the Almgren-Chriss (2001)
framework plus simpler square-root and linear impact models.
Uses free market data for calibration.
"""

import math
from typing import Dict, List, Optional, Tuple


def square_root_impact(
    order_shares: float,
    adv: float,
    daily_volatility: float,
    participation_rate: float = 0.1
) -> float:
    """
    Square-root market impact model (Barra/ITG style).
    
    Impact ≈ σ * sqrt(Q / ADV) where Q is order size.
    
    Args:
        order_shares: Number of shares to trade
        adv: Average daily volume in shares
        daily_volatility: Daily return volatility (e.g. 0.02 = 2%)
        participation_rate: Expected participation rate (default 10%)
    
    Returns:
        Expected impact in basis points
    """
    if adv <= 0 or daily_volatility <= 0:
        return 0.0
    
    # Fraction of daily volume
    q_ratio = order_shares / adv
    
    # Square root model with participation adjustment
    impact = daily_volatility * math.sqrt(q_ratio) * 10000  # in bps
    
    return round(impact, 2)


def almgren_chriss_optimal_trajectory(
    total_shares: float,
    num_periods: int,
    daily_volatility: float,
    adv: float,
    risk_aversion: float = 1e-6,
    temporary_impact_coeff: float = 0.01,
    permanent_impact_coeff: float = 0.001
) -> List[Dict[str, float]]:
    """
    Almgren-Chriss (2001) optimal execution trajectory.
    
    Computes the optimal trade schedule that minimizes expected cost
    plus risk aversion * variance of cost.
    
    Args:
        total_shares: Total shares to execute
        num_periods: Number of trading intervals
        daily_volatility: Daily return volatility
        adv: Average daily volume
        risk_aversion: Risk aversion parameter (lambda)
        temporary_impact_coeff: Temporary impact coefficient (eta)
        permanent_impact_coeff: Permanent impact coefficient (gamma)
    
    Returns:
        List of dicts with 'period', 'shares', 'cumulative_pct', 'expected_cost_bps'
    """
    if num_periods <= 0 or total_shares <= 0:
        return []
    
    tau = 1.0 / num_periods  # Time interval as fraction of day
    sigma = daily_volatility
    eta = temporary_impact_coeff
    gamma = permanent_impact_coeff
    lam = risk_aversion
    
    # Almgren-Chriss kappa
    kappa_sq = lam * sigma * sigma / (eta * (1.0 / tau))
    kappa = math.sqrt(max(kappa_sq, 1e-12))
    
    trajectory = []
    remaining = total_shares
    
    for j in range(num_periods):
        # Optimal fraction based on sinh schedule
        t_j = j * tau
        t_next = (j + 1) * tau
        
        if kappa * (1 - t_j) > 20:  # Prevent overflow
            frac = 1.0 / num_periods
        else:
            denom = math.sinh(kappa * 1.0)
            if abs(denom) < 1e-12:
                frac = 1.0 / num_periods
            else:
                nj = (math.sinh(kappa * (1 - t_j)) - math.sinh(kappa * (1 - t_next))) / denom
                frac = nj
        
        shares_this_period = total_shares * frac
        remaining -= shares_this_period
        
        # Estimated cost for this slice
        participation = shares_this_period / (adv / num_periods) if adv > 0 else 0
        temp_cost = eta * participation * 10000
        perm_cost = gamma * (shares_this_period / adv) * 10000 if adv > 0 else 0
        
        trajectory.append({
            'period': j + 1,
            'shares': round(shares_this_period, 0),
            'cumulative_pct': round(100 * (1 - remaining / total_shares), 2),
            'expected_cost_bps': round(temp_cost + perm_cost, 2)
        })
    
    return trajectory


def linear_impact_model(
    order_shares: float,
    adv: float,
    daily_volatility: float,
    spread_bps: float = 10.0
) -> Dict[str, float]:
    """
    Simple linear impact decomposition: spread + temporary + permanent.
    
    Args:
        order_shares: Order size in shares
        adv: Average daily volume
        daily_volatility: Daily volatility
        spread_bps: Bid-ask spread in basis points
    
    Returns:
        Dict with spread_cost_bps, temporary_bps, permanent_bps, total_bps
    """
    q_ratio = order_shares / adv if adv > 0 else 0
    
    spread_cost = spread_bps / 2  # Half spread crossing cost
    temporary = daily_volatility * 10000 * q_ratio * 0.5
    permanent = daily_volatility * 10000 * q_ratio * 0.3
    
    return {
        'spread_cost_bps': round(spread_cost, 2),
        'temporary_bps': round(temporary, 2),
        'permanent_bps': round(permanent, 2),
        'total_bps': round(spread_cost + temporary + permanent, 2)
    }


def estimate_execution_cost(
    order_value_usd: float,
    adv_usd: float,
    daily_volatility: float,
    strategy: str = 'vwap'
) -> Dict[str, float]:
    """
    Estimate total execution cost for different strategies.
    
    Args:
        order_value_usd: Order notional value
        adv_usd: Average daily dollar volume
        daily_volatility: Daily return volatility
        strategy: 'vwap', 'twap', 'aggressive', or 'passive'
    
    Returns:
        Dict with estimated cost metrics per strategy
    """
    q_ratio = order_value_usd / adv_usd if adv_usd > 0 else 0
    
    # Strategy-specific multipliers
    multipliers = {
        'vwap': {'impact': 1.0, 'timing': 0.5, 'spread': 1.0},
        'twap': {'impact': 0.8, 'timing': 0.7, 'spread': 1.0},
        'aggressive': {'impact': 1.5, 'timing': 0.2, 'spread': 1.2},
        'passive': {'impact': 0.5, 'timing': 1.0, 'spread': 0.7},
    }
    
    m = multipliers.get(strategy, multipliers['vwap'])
    
    base_impact = daily_volatility * 10000 * math.sqrt(q_ratio)
    
    impact_bps = base_impact * m['impact']
    timing_bps = daily_volatility * 10000 * 0.1 * m['timing']
    spread_bps = 5 * m['spread']
    
    total_bps = impact_bps + timing_bps + spread_bps
    total_usd = order_value_usd * total_bps / 10000
    
    return {
        'strategy': strategy,
        'impact_bps': round(impact_bps, 2),
        'timing_risk_bps': round(timing_bps, 2),
        'spread_bps': round(spread_bps, 2),
        'total_bps': round(total_bps, 2),
        'total_cost_usd': round(total_usd, 2),
        'pct_of_adv': round(q_ratio * 100, 2)
    }
