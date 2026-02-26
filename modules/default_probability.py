"""
Default Probability Term Structure (Roadmap #357)
Models the term structure of default probabilities for corporate bonds
using credit spreads, ratings, and structural models. Free data sources.
"""

import math
from typing import Dict, List, Optional, Tuple


# Moody's historical average annual default rates by rating (%)
HISTORICAL_DEFAULT_RATES = {
    "Aaa": 0.00,
    "Aa1": 0.02, "Aa2": 0.03, "Aa3": 0.05,
    "A1": 0.06, "A2": 0.08, "A3": 0.10,
    "Baa1": 0.15, "Baa2": 0.20, "Baa3": 0.35,
    "Ba1": 0.60, "Ba2": 0.95, "Ba3": 1.50,
    "B1": 2.50, "B2": 4.00, "B3": 6.50,
    "Caa1": 10.00, "Caa2": 15.00, "Caa3": 25.00,
    "Ca": 35.00, "C": 50.00,
}

# S&P equivalent mapping
SP_TO_MOODYS = {
    "AAA": "Aaa", "AA+": "Aa1", "AA": "Aa2", "AA-": "Aa3",
    "A+": "A1", "A": "A2", "A-": "A3",
    "BBB+": "Baa1", "BBB": "Baa2", "BBB-": "Baa3",
    "BB+": "Ba1", "BB": "Ba2", "BB-": "Ba3",
    "B+": "B1", "B": "B2", "B-": "B3",
    "CCC+": "Caa1", "CCC": "Caa2", "CCC-": "Caa3",
    "CC": "Ca", "C": "C", "D": "C",
}


def annual_default_probability_from_rating(rating: str) -> float:
    """
    Get historical average annual default probability from credit rating.
    
    Args:
        rating: Moody's or S&P rating string
        
    Returns:
        Annual default probability as percentage
    """
    # Try Moody's first
    if rating in HISTORICAL_DEFAULT_RATES:
        return HISTORICAL_DEFAULT_RATES[rating]
    
    # Try S&P mapping
    moody = SP_TO_MOODYS.get(rating.upper())
    if moody and moody in HISTORICAL_DEFAULT_RATES:
        return HISTORICAL_DEFAULT_RATES[moody]
    
    return -1.0  # unknown rating


def cumulative_default_probability(annual_pd: float, years: int) -> float:
    """
    Calculate cumulative default probability over multiple years.
    Assumes constant hazard rate.
    
    Args:
        annual_pd: Annual default probability (as decimal, e.g., 0.02 for 2%)
        years: Time horizon in years
        
    Returns:
        Cumulative default probability (decimal)
    """
    if annual_pd <= 0 or years <= 0:
        return 0.0
    survival = (1 - annual_pd) ** years
    return round(1 - survival, 6)


def default_probability_term_structure(
    rating: str,
    horizons: Optional[List[int]] = None
) -> List[Dict[str, float]]:
    """
    Build default probability term structure for a given rating.
    
    Args:
        rating: Credit rating (Moody's or S&P)
        horizons: List of year horizons (default: 1-10)
        
    Returns:
        List of dicts with year, cumulative PD, marginal PD, survival probability
    """
    if horizons is None:
        horizons = list(range(1, 11))
    
    annual_pct = annual_default_probability_from_rating(rating)
    if annual_pct < 0:
        return [{"error": f"Unknown rating: {rating}"}]
    
    annual_pd = annual_pct / 100.0
    results = []
    prev_cum = 0.0
    
    for yr in horizons:
        cum_pd = cumulative_default_probability(annual_pd, yr)
        survival = 1 - cum_pd
        marginal = cum_pd - prev_cum
        
        results.append({
            "year": yr,
            "cumulative_pd_pct": round(cum_pd * 100, 4),
            "marginal_pd_pct": round(marginal * 100, 4),
            "survival_probability_pct": round(survival * 100, 4),
        })
        prev_cum = cum_pd
    
    return results


def implied_pd_from_spread(
    credit_spread_bps: float,
    recovery_rate: float = 0.40,
    maturity_years: int = 5
) -> Dict[str, float]:
    """
    Extract implied default probability from credit spread.
    Uses the simplified relationship: spread ≈ PD × (1 - Recovery)
    
    Args:
        credit_spread_bps: Credit spread in basis points
        recovery_rate: Expected recovery rate (0-1)
        maturity_years: Bond maturity in years
        
    Returns:
        Implied default probabilities
    """
    spread_decimal = credit_spread_bps / 10000
    lgd = 1 - recovery_rate
    
    if lgd <= 0:
        return {"error": "Recovery rate must be < 1"}
    
    # Annual hazard rate
    hazard_rate = spread_decimal / lgd
    
    # Annual PD
    annual_pd = 1 - math.exp(-hazard_rate)
    
    # Cumulative PD over maturity
    cum_pd = 1 - math.exp(-hazard_rate * maturity_years)
    
    return {
        "credit_spread_bps": credit_spread_bps,
        "recovery_rate": recovery_rate,
        "loss_given_default": lgd,
        "implied_hazard_rate": round(hazard_rate, 6),
        "implied_annual_pd_pct": round(annual_pd * 100, 4),
        "implied_cumulative_pd_pct": round(cum_pd * 100, 4),
        "maturity_years": maturity_years,
    }


def merton_model_pd(
    asset_value: float,
    debt_face: float,
    asset_volatility: float,
    risk_free_rate: float,
    time_years: float = 1.0
) -> Dict[str, float]:
    """
    Calculate default probability using Merton's structural model.
    
    Args:
        asset_value: Current firm asset value
        debt_face: Face value of debt (default barrier)
        asset_volatility: Annual asset volatility (decimal)
        risk_free_rate: Risk-free rate (decimal)
        time_years: Time horizon in years
        
    Returns:
        Distance to default and default probability
    """
    if asset_value <= 0 or debt_face <= 0 or asset_volatility <= 0 or time_years <= 0:
        return {"error": "Invalid inputs"}
    
    # Distance to default (DD)
    d2 = (math.log(asset_value / debt_face) +
          (risk_free_rate - 0.5 * asset_volatility ** 2) * time_years) / \
         (asset_volatility * math.sqrt(time_years))
    
    # PD using normal CDF approximation
    pd = _norm_cdf(-d2)
    
    return {
        "asset_value": asset_value,
        "debt_face_value": debt_face,
        "leverage_ratio": round(debt_face / asset_value, 4),
        "distance_to_default": round(d2, 4),
        "default_probability_pct": round(pd * 100, 4),
        "interpretation": "safe" if d2 > 3 else "stable" if d2 > 2 else "watch" if d2 > 1 else "distressed",
    }


def compare_ratings_pd(ratings: List[str], horizon_years: int = 5) -> List[Dict]:
    """
    Compare default probabilities across multiple ratings.
    
    Args:
        ratings: List of credit ratings to compare
        horizon_years: Time horizon
        
    Returns:
        Sorted list by default probability
    """
    results = []
    for rating in ratings:
        annual_pct = annual_default_probability_from_rating(rating)
        if annual_pct >= 0:
            annual_pd = annual_pct / 100.0
            cum_pd = cumulative_default_probability(annual_pd, horizon_years)
            results.append({
                "rating": rating,
                "annual_pd_pct": annual_pct,
                "cumulative_pd_pct": round(cum_pd * 100, 4),
                "horizon_years": horizon_years,
            })
    
    return sorted(results, key=lambda x: x["annual_pd_pct"])


def _norm_cdf(x: float) -> float:
    """Approximate standard normal CDF using Abramowitz & Stegun."""
    if x < -8:
        return 0.0
    if x > 8:
        return 1.0
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)
