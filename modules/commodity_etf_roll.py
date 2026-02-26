"""
Commodity ETF Roll Yield Calculator (Roadmap #366)
Calculates roll yield, contango/backwardation costs, and total return
decomposition for commodity ETFs using free data sources.
"""

import datetime
import math
from typing import Dict, List, Optional, Tuple


# Major commodity ETFs with their underlying futures
COMMODITY_ETFS = {
    "USO": {"commodity": "WTI Crude Oil", "index": "front-month", "expense_ratio": 0.60},
    "BNO": {"commodity": "Brent Crude Oil", "index": "front-month", "expense_ratio": 0.84},
    "UNG": {"commodity": "Natural Gas", "index": "front-month", "expense_ratio": 1.06},
    "GLD": {"commodity": "Gold", "index": "spot-backed", "expense_ratio": 0.40},
    "SLV": {"commodity": "Silver", "index": "spot-backed", "expense_ratio": 0.50},
    "PDBC": {"commodity": "Diversified", "index": "DBIQ Optimum Yield", "expense_ratio": 0.59},
    "DBC": {"commodity": "Diversified", "index": "DBIQ Optimum Yield", "expense_ratio": 0.85},
    "GSG": {"commodity": "Diversified", "index": "S&P GSCI", "expense_ratio": 0.75},
    "CORN": {"commodity": "Corn", "index": "front-month", "expense_ratio": 0.76},
    "WEAT": {"commodity": "Wheat", "index": "front-month", "expense_ratio": 0.76},
    "SOYB": {"commodity": "Soybeans", "index": "front-month", "expense_ratio": 0.76},
    "CPER": {"commodity": "Copper", "index": "SummerHaven", "expense_ratio": 0.65},
    "LIT": {"commodity": "Lithium/Battery", "index": "equity-based", "expense_ratio": 0.75},
    "PPLT": {"commodity": "Platinum", "index": "spot-backed", "expense_ratio": 0.60},
    "PALL": {"commodity": "Palladium", "index": "spot-backed", "expense_ratio": 0.60},
}


def calculate_roll_yield(front_price: float, next_price: float, days_to_expiry: int) -> Dict[str, float]:
    """
    Calculate roll yield from front-month and next-month futures prices.
    
    Args:
        front_price: Front-month futures price
        next_price: Next-month (deferred) futures price
        days_to_expiry: Days until front-month expiry
        
    Returns:
        Dict with roll yield metrics
    """
    if front_price <= 0 or next_price <= 0 or days_to_expiry <= 0:
        return {"error": "Invalid inputs"}
    
    # Raw roll yield (per roll period)
    raw_roll = (front_price - next_price) / front_price
    
    # Annualized roll yield
    rolls_per_year = 365 / days_to_expiry
    annualized = raw_roll * rolls_per_year
    
    # Market structure
    if next_price > front_price:
        structure = "contango"
    elif next_price < front_price:
        structure = "backwardation"
    else:
        structure = "flat"
    
    return {
        "front_price": front_price,
        "next_price": next_price,
        "raw_roll_yield_pct": round(raw_roll * 100, 3),
        "annualized_roll_yield_pct": round(annualized * 100, 2),
        "days_to_expiry": days_to_expiry,
        "market_structure": structure,
        "premium_discount_pct": round((next_price / front_price - 1) * 100, 3),
    }


def total_return_decomposition(
    spot_return_pct: float,
    roll_yield_pct: float,
    collateral_yield_pct: float,
    expense_ratio_pct: float
) -> Dict[str, float]:
    """
    Decompose commodity ETF total return into components.
    Total Return = Spot Return + Roll Yield + Collateral Yield - Expenses
    
    Args:
        spot_return_pct: Spot price change (%)
        roll_yield_pct: Annualized roll yield (%)
        collateral_yield_pct: T-bill yield on collateral (%)
        expense_ratio_pct: ETF expense ratio (%)
        
    Returns:
        Return decomposition
    """
    total = spot_return_pct + roll_yield_pct + collateral_yield_pct - expense_ratio_pct
    
    return {
        "spot_return_pct": round(spot_return_pct, 2),
        "roll_yield_pct": round(roll_yield_pct, 2),
        "collateral_yield_pct": round(collateral_yield_pct, 2),
        "expense_ratio_pct": round(expense_ratio_pct, 2),
        "total_return_pct": round(total, 2),
        "roll_drag": roll_yield_pct < 0,
    }


def estimate_contango_cost(etf_prices: List[float], spot_prices: List[float], days: int = 252) -> Dict[str, float]:
    """
    Estimate contango/backwardation cost by comparing ETF vs spot performance.
    
    Args:
        etf_prices: Daily ETF prices (oldest first)
        spot_prices: Daily spot/index prices (oldest first)
        days: Period to analyze
        
    Returns:
        Cost analysis
    """
    if len(etf_prices) < days + 1 or len(spot_prices) < days + 1:
        return {"error": "Insufficient data"}
    
    etf_return = (etf_prices[-1] / etf_prices[-days]) - 1
    spot_return = (spot_prices[-1] / spot_prices[-days]) - 1
    
    tracking_diff = etf_return - spot_return
    
    return {
        "period_days": days,
        "etf_return_pct": round(etf_return * 100, 2),
        "spot_return_pct": round(spot_return * 100, 2),
        "tracking_difference_pct": round(tracking_diff * 100, 2),
        "estimated_roll_cost_pct": round(tracking_diff * 100, 2),
        "impact": "favorable" if tracking_diff > 0 else "unfavorable" if tracking_diff < -1 else "neutral",
    }


def rank_etfs_by_efficiency() -> List[Dict]:
    """
    Rank commodity ETFs by cost efficiency (lower expense ratio = better).
    
    Returns:
        Sorted list of ETFs by expense ratio
    """
    results = []
    for ticker, info in COMMODITY_ETFS.items():
        results.append({
            "ticker": ticker,
            "commodity": info["commodity"],
            "index_methodology": info["index"],
            "expense_ratio_pct": info["expense_ratio"],
            "has_roll_risk": info["index"] not in ["spot-backed", "equity-based"],
        })
    
    return sorted(results, key=lambda x: x["expense_ratio_pct"])


def optimal_roll_strategy_comparison(
    front_prices: List[float],
    deferred_prices: List[float],
) -> Dict[str, float]:
    """
    Compare front-month rolling vs optimum yield strategies.
    
    Args:
        front_prices: Historical front-month prices
        deferred_prices: Historical deferred-month prices
        
    Returns:
        Strategy comparison metrics
    """
    if len(front_prices) != len(deferred_prices) or len(front_prices) < 12:
        return {"error": "Need matching price series of 12+ points"}
    
    # Calculate how often backwardation occurred
    backwardation_count = sum(1 for f, d in zip(front_prices, deferred_prices) if f > d)
    total = len(front_prices)
    
    # Average roll yield
    roll_yields = []
    for f, d in zip(front_prices, deferred_prices):
        if f > 0:
            roll_yields.append((f - d) / f)
    
    avg_roll = sum(roll_yields) / len(roll_yields) if roll_yields else 0
    
    return {
        "observations": total,
        "backwardation_pct": round(backwardation_count / total * 100, 1),
        "contango_pct": round((total - backwardation_count) / total * 100, 1),
        "avg_monthly_roll_yield_pct": round(avg_roll * 100, 3),
        "avg_annual_roll_yield_pct": round(avg_roll * 12 * 100, 2),
        "recommendation": "front_month" if avg_roll > 0 else "optimum_yield",
    }
