"""
Liquidity Score Calculator — Amihud illiquidity, bid-ask spread, volume-based scoring.

Computes composite liquidity scores for equities using multiple free data sources.
Supports Amihud (2002) illiquidity ratio, relative spread estimation, and turnover metrics.
"""

import math
from typing import Dict, List, Optional
from datetime import datetime, timedelta


def amihud_illiquidity(daily_returns: List[float], daily_volumes_usd: List[float]) -> float:
    """
    Compute Amihud (2002) illiquidity ratio: average |return| / dollar volume.
    
    Lower values = more liquid. Typically computed over 20-60 trading days.
    
    Args:
        daily_returns: List of daily returns (as decimals, e.g. 0.01 = 1%)
        daily_volumes_usd: List of daily dollar volumes
    
    Returns:
        Amihud illiquidity ratio (scaled by 1e6 for readability)
    """
    if len(daily_returns) != len(daily_volumes_usd):
        raise ValueError("Returns and volumes must have same length")
    
    valid_pairs = [
        (abs(r), v) for r, v in zip(daily_returns, daily_volumes_usd)
        if v > 0
    ]
    
    if not valid_pairs:
        return float('inf')
    
    illiq = sum(ar / dv for ar, dv in valid_pairs) / len(valid_pairs)
    return illiq * 1e6  # Scale for readability


def bid_ask_spread_estimate(high_prices: List[float], low_prices: List[float]) -> float:
    """
    Estimate effective bid-ask spread using Corwin-Schultz (2012) high-low estimator.
    
    Uses consecutive daily high/low prices to estimate the spread component
    separate from volatility.
    
    Args:
        high_prices: Daily high prices (at least 2 days)
        low_prices: Daily low prices (at least 2 days)
    
    Returns:
        Estimated proportional bid-ask spread
    """
    if len(high_prices) < 2 or len(low_prices) < 2:
        raise ValueError("Need at least 2 days of data")
    
    n = min(len(high_prices), len(low_prices))
    spreads = []
    
    for i in range(n - 1):
        # Single-day log range
        gamma_1 = math.log(high_prices[i] / low_prices[i]) ** 2
        gamma_2 = math.log(high_prices[i + 1] / low_prices[i + 1]) ** 2
        
        # Two-day log range
        h2 = max(high_prices[i], high_prices[i + 1])
        l2 = min(low_prices[i], low_prices[i + 1])
        beta = math.log(h2 / l2) ** 2
        
        gamma = gamma_1 + gamma_2
        
        # Corwin-Schultz formula
        alpha_num = (math.sqrt(2) - 1) * math.sqrt(beta) - math.sqrt(gamma)
        denom = 3 - 2 * math.sqrt(2)
        
        if denom != 0:
            alpha = max(0, alpha_num / denom)
            spread = 2 * (math.exp(alpha) - 1) / (1 + math.exp(alpha))
            spreads.append(max(0, spread))
    
    return sum(spreads) / len(spreads) if spreads else 0.0


def turnover_ratio(volume_shares: List[float], shares_outstanding: float) -> float:
    """
    Compute average daily turnover ratio.
    
    Args:
        volume_shares: Daily share volumes
        shares_outstanding: Total shares outstanding
    
    Returns:
        Average daily turnover ratio
    """
    if shares_outstanding <= 0:
        return 0.0
    avg_vol = sum(volume_shares) / len(volume_shares) if volume_shares else 0
    return avg_vol / shares_outstanding


def composite_liquidity_score(
    amihud: float,
    spread: float,
    turnover: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute composite liquidity score (0-100, higher = more liquid).
    
    Normalizes each component using sigmoid-like transforms and combines
    with configurable weights.
    
    Args:
        amihud: Amihud illiquidity ratio (scaled 1e6)
        spread: Estimated bid-ask spread (proportional)
        turnover: Daily turnover ratio
        weights: Optional dict with keys 'amihud', 'spread', 'turnover'
    
    Returns:
        Composite score 0-100
    """
    if weights is None:
        weights = {'amihud': 0.4, 'spread': 0.35, 'turnover': 0.25}
    
    # Transform each metric to 0-100 (higher = more liquid)
    # Amihud: lower is better, use inverse sigmoid
    amihud_score = 100 / (1 + amihud / 10)
    
    # Spread: lower is better
    spread_score = 100 * max(0, 1 - spread * 100)
    
    # Turnover: higher is better, sigmoid
    turnover_score = 100 * (1 - 1 / (1 + turnover * 1000))
    
    composite = (
        weights.get('amihud', 0.4) * amihud_score +
        weights.get('spread', 0.35) * spread_score +
        weights.get('turnover', 0.25) * turnover_score
    )
    
    return round(max(0, min(100, composite)), 2)


def liquidity_percentile_rank(scores: Dict[str, float]) -> Dict[str, int]:
    """
    Rank tickers by liquidity score percentile.
    
    Args:
        scores: Dict of {ticker: composite_liquidity_score}
    
    Returns:
        Dict of {ticker: percentile_rank (0-100)}
    """
    sorted_tickers = sorted(scores.keys(), key=lambda t: scores[t])
    n = len(sorted_tickers)
    if n == 0:
        return {}
    return {
        ticker: round(100 * idx / max(1, n - 1))
        for idx, ticker in enumerate(sorted_tickers)
    }
