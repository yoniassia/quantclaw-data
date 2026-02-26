"""
Slippage Tracker & Analyzer — Measure and analyze execution slippage.

Tracks the difference between intended and actual execution prices,
decomposes slippage into market impact, timing, and spread components,
and provides statistical analysis of execution quality.
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def calculate_slippage(
    decision_price: float,
    execution_price: float,
    side: str = 'buy'
) -> Dict[str, float]:
    """
    Calculate slippage between decision and execution price.
    
    Args:
        decision_price: Price when trade decision was made
        execution_price: Actual fill price
        side: 'buy' or 'sell'
    
    Returns:
        Dict with slippage in price, bps, and direction
    """
    if decision_price <= 0:
        raise ValueError("Decision price must be positive")
    
    price_diff = execution_price - decision_price
    slippage_bps = (price_diff / decision_price) * 10000
    
    # For buys, positive slippage = adverse (paid more)
    # For sells, negative slippage = adverse (received less)
    if side.lower() == 'buy':
        adverse_bps = slippage_bps
    else:
        adverse_bps = -slippage_bps
    
    return {
        'decision_price': decision_price,
        'execution_price': execution_price,
        'slippage_price': round(price_diff, 6),
        'slippage_bps': round(slippage_bps, 2),
        'adverse_bps': round(adverse_bps, 2),
        'favorable': adverse_bps < 0
    }


def implementation_shortfall(
    decision_price: float,
    arrival_price: float,
    execution_price: float,
    benchmark_close: float,
    shares_executed: float,
    shares_intended: float,
    side: str = 'buy'
) -> Dict[str, float]:
    """
    Full implementation shortfall decomposition (Perold, 1988).
    
    Decomposes total cost into: delay cost, market impact, timing cost,
    and opportunity cost.
    
    Args:
        decision_price: Price at investment decision
        arrival_price: Price when order hits market
        execution_price: Volume-weighted avg execution price
        benchmark_close: Closing price on execution day
        shares_executed: Shares actually filled
        shares_intended: Shares originally intended
        side: 'buy' or 'sell'
    
    Returns:
        Dict with IS components in basis points
    """
    sign = 1 if side.lower() == 'buy' else -1
    
    # Delay cost: slippage between decision and arrival
    delay_bps = sign * (arrival_price - decision_price) / decision_price * 10000
    
    # Market impact: execution vs arrival
    impact_bps = sign * (execution_price - arrival_price) / decision_price * 10000
    
    # Timing cost: close vs execution (for executed shares)
    timing_bps = sign * (benchmark_close - execution_price) / decision_price * 10000
    
    # Opportunity cost: unfilled shares × price movement
    unfilled = shares_intended - shares_executed
    fill_rate = shares_executed / shares_intended if shares_intended > 0 else 1
    opp_cost_bps = (1 - fill_rate) * sign * (benchmark_close - decision_price) / decision_price * 10000
    
    total_is = delay_bps + impact_bps + timing_bps + opp_cost_bps
    
    return {
        'delay_cost_bps': round(delay_bps, 2),
        'market_impact_bps': round(impact_bps, 2),
        'timing_cost_bps': round(timing_bps, 2),
        'opportunity_cost_bps': round(opp_cost_bps, 2),
        'total_is_bps': round(total_is, 2),
        'fill_rate': round(fill_rate * 100, 2),
        'executed_cost_bps': round(delay_bps + impact_bps, 2)
    }


def analyze_slippage_history(
    trades: List[Dict[str, float]]
) -> Dict[str, float]:
    """
    Statistical analysis of historical slippage across trades.
    
    Args:
        trades: List of dicts with 'adverse_bps' from calculate_slippage
    
    Returns:
        Summary statistics
    """
    if not trades:
        return {}
    
    slippages = [t['adverse_bps'] for t in trades if 'adverse_bps' in t]
    
    if not slippages:
        return {}
    
    adverse = [s for s in slippages if s > 0]
    favorable = [s for s in slippages if s < 0]
    
    return {
        'count': len(slippages),
        'mean_bps': round(statistics.mean(slippages), 2),
        'median_bps': round(statistics.median(slippages), 2),
        'std_bps': round(statistics.stdev(slippages), 2) if len(slippages) > 1 else 0,
        'max_adverse_bps': round(max(slippages), 2),
        'max_favorable_bps': round(min(slippages), 2),
        'pct_adverse': round(100 * len(adverse) / len(slippages), 1),
        'avg_adverse_bps': round(statistics.mean(adverse), 2) if adverse else 0,
        'avg_favorable_bps': round(statistics.mean(favorable), 2) if favorable else 0,
        'total_cost_bps': round(sum(slippages), 2)
    }


def vwap_slippage(
    execution_price: float,
    vwap: float,
    side: str = 'buy'
) -> Dict[str, float]:
    """
    Calculate slippage relative to VWAP benchmark.
    
    Args:
        execution_price: Actual fill price
        vwap: Volume-weighted average price for the period
        side: 'buy' or 'sell'
    
    Returns:
        VWAP slippage metrics
    """
    if vwap <= 0:
        raise ValueError("VWAP must be positive")
    
    diff_bps = (execution_price - vwap) / vwap * 10000
    sign = 1 if side.lower() == 'buy' else -1
    adverse = sign * diff_bps
    
    return {
        'execution_price': execution_price,
        'vwap': vwap,
        'slippage_bps': round(diff_bps, 2),
        'adverse_bps': round(adverse, 2),
        'beat_vwap': adverse < 0
    }
