"""
Fallen Angel / Rising Star Predictor — Credit rating migration forecaster.

Predicts bonds likely to be downgraded from investment grade to high yield
(fallen angels) or upgraded from HY to IG (rising stars) using financial
metrics, spread behavior, and sector trends.
Free data sources: FRED, SEC EDGAR, public rating actions.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


# Credit rating numerical mapping
RATING_SCALE = {
    "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4,
    "A+": 5, "A": 6, "A-": 7,
    "BBB+": 8, "BBB": 9, "BBB-": 10,  # IG/HY boundary
    "BB+": 11, "BB": 12, "BB-": 13,
    "B+": 14, "B": 15, "B-": 16,
    "CCC+": 17, "CCC": 18, "CCC-": 19,
    "CC": 20, "C": 21, "D": 22,
}

RATING_REVERSE = {v: k for k, v in RATING_SCALE.items()}

# Historical 1-year transition probabilities (simplified Moody's/S&P style)
TRANSITION_MATRIX = {
    "BBB-": {"upgrade": 0.04, "stable": 0.88, "downgrade": 0.06, "default": 0.02},
    "BBB": {"upgrade": 0.05, "stable": 0.90, "downgrade": 0.04, "default": 0.01},
    "BBB+": {"upgrade": 0.06, "stable": 0.90, "downgrade": 0.03, "default": 0.01},
    "BB+": {"upgrade": 0.07, "stable": 0.82, "downgrade": 0.08, "default": 0.03},
    "BB": {"upgrade": 0.05, "stable": 0.80, "downgrade": 0.10, "default": 0.05},
    "BB-": {"upgrade": 0.04, "stable": 0.76, "downgrade": 0.12, "default": 0.08},
}

# Sector risk multipliers for downgrade probability
SECTOR_RISK = {
    "energy": 1.4, "retail": 1.3, "airlines": 1.5,
    "hospitality": 1.3, "real_estate": 1.2, "technology": 0.8,
    "healthcare": 0.9, "utilities": 0.7, "financials": 1.1,
    "industrials": 1.0, "consumer_staples": 0.8, "telecom": 1.1,
    "media": 1.2, "autos": 1.3, "mining": 1.4,
}


def calculate_fallen_angel_score(
    current_rating: str,
    leverage_ratio: float,
    interest_coverage: float,
    free_cash_flow_yield: float,
    spread_bps: float,
    spread_change_3m_bps: float = 0,
    sector: str = "industrials",
    negative_outlook: bool = False,
    on_creditwatch: bool = False,
) -> Dict:
    """
    Score a bond's probability of becoming a fallen angel (IG → HY downgrade).

    Args:
        current_rating: Current credit rating (must be IG: BBB- to AAA).
        leverage_ratio: Total Debt / EBITDA.
        interest_coverage: EBITDA / Interest Expense.
        free_cash_flow_yield: FCF / Market Cap.
        spread_bps: Current OAS in basis points.
        spread_change_3m_bps: 3-month spread widening in bps.
        sector: Industry sector.
        negative_outlook: Whether rating agency has negative outlook.
        on_creditwatch: Whether on CreditWatch negative.

    Returns:
        Fallen angel probability score and risk factors.
    """
    num_rating = RATING_SCALE.get(current_rating, 5)

    # Only relevant for IG bonds (BBB- and above)
    if num_rating > 10:
        return {"error": f"{current_rating} is already high yield"}

    # Base probability from transition matrix
    base_prob = TRANSITION_MATRIX.get(current_rating, {"downgrade": 0.02})["downgrade"]

    # Distance to junk (BBB- = 10)
    distance_to_junk = 10 - num_rating  # 0 for BBB-, higher = safer

    # Financial health scoring
    risk_factors = []
    score_adjustments = 0.0

    # Leverage
    if leverage_ratio > 5.0:
        score_adjustments += 0.15
        risk_factors.append(f"HIGH leverage: {leverage_ratio:.1f}x (threshold: 5.0x)")
    elif leverage_ratio > 4.0:
        score_adjustments += 0.08
        risk_factors.append(f"Elevated leverage: {leverage_ratio:.1f}x")

    # Interest coverage
    if interest_coverage < 2.0:
        score_adjustments += 0.15
        risk_factors.append(f"WEAK coverage: {interest_coverage:.1f}x (threshold: 2.0x)")
    elif interest_coverage < 3.0:
        score_adjustments += 0.07
        risk_factors.append(f"Thin coverage: {interest_coverage:.1f}x")

    # FCF yield
    if free_cash_flow_yield < 0:
        score_adjustments += 0.12
        risk_factors.append(f"NEGATIVE FCF yield: {free_cash_flow_yield:.1%}")
    elif free_cash_flow_yield < 0.02:
        score_adjustments += 0.05
        risk_factors.append(f"Low FCF yield: {free_cash_flow_yield:.1%}")

    # Spread signals
    if spread_bps > 300:
        score_adjustments += 0.10
        risk_factors.append(f"Spread at HY levels: {spread_bps}bps")
    elif spread_bps > 200:
        score_adjustments += 0.05
        risk_factors.append(f"Wide spread: {spread_bps}bps")

    if spread_change_3m_bps > 100:
        score_adjustments += 0.08
        risk_factors.append(f"Rapid spread widening: +{spread_change_3m_bps}bps in 3m")

    # Sector risk
    sector_mult = SECTOR_RISK.get(sector, 1.0)
    if sector_mult > 1.1:
        risk_factors.append(f"High-risk sector: {sector} ({sector_mult}x)")

    # Rating agency signals
    if on_creditwatch:
        score_adjustments += 0.20
        risk_factors.append("ON CREDITWATCH NEGATIVE")
    elif negative_outlook:
        score_adjustments += 0.10
        risk_factors.append("Negative outlook")

    # Final probability
    raw_prob = (base_prob + score_adjustments) * sector_mult
    # Adjust for distance to junk
    if distance_to_junk > 2:
        raw_prob *= 0.3  # Much less likely for A+ and above
    elif distance_to_junk > 0:
        raw_prob *= 0.6

    prob = min(0.95, max(0.01, raw_prob))

    return {
        "ticker_or_issuer": "input",
        "current_rating": current_rating,
        "distance_to_junk_notches": distance_to_junk,
        "fallen_angel_probability": round(prob, 4),
        "risk_level": "HIGH" if prob > 0.20 else "MEDIUM" if prob > 0.10 else "LOW",
        "risk_factors": risk_factors,
        "financial_metrics": {
            "leverage_ratio": leverage_ratio,
            "interest_coverage": interest_coverage,
            "fcf_yield": free_cash_flow_yield,
            "spread_bps": spread_bps,
        },
        "sector": sector,
        "sector_risk_multiplier": sector_mult,
        "timestamp": datetime.utcnow().isoformat(),
    }


def calculate_rising_star_score(
    current_rating: str,
    leverage_ratio: float,
    interest_coverage: float,
    revenue_growth_yoy: float,
    margin_trend: str = "stable",
    sector: str = "industrials",
    positive_outlook: bool = False,
) -> Dict:
    """
    Score a HY bond's probability of becoming a rising star (HY → IG upgrade).

    Args:
        current_rating: Current rating (must be HY: BB+ or below).
        leverage_ratio: Total Debt / EBITDA.
        interest_coverage: EBITDA / Interest Expense.
        revenue_growth_yoy: Year-over-year revenue growth rate.
        margin_trend: "improving", "stable", or "declining".
        sector: Industry sector.
        positive_outlook: Whether rating agency has positive outlook.

    Returns:
        Rising star probability score.
    """
    num_rating = RATING_SCALE.get(current_rating, 15)

    if num_rating <= 10:
        return {"error": f"{current_rating} is already investment grade"}

    # Distance from IG (BB+ = 11, one notch away)
    distance_from_ig = num_rating - 10

    # Base upgrade probability
    base_prob = TRANSITION_MATRIX.get(current_rating, {"upgrade": 0.03})["upgrade"]

    positive_factors = []
    adjustments = 0.0

    # Strong fundamentals
    if leverage_ratio < 3.0:
        adjustments += 0.10
        positive_factors.append(f"IG-quality leverage: {leverage_ratio:.1f}x")
    elif leverage_ratio < 4.0:
        adjustments += 0.05
        positive_factors.append(f"Improving leverage: {leverage_ratio:.1f}x")

    if interest_coverage > 4.0:
        adjustments += 0.08
        positive_factors.append(f"Strong coverage: {interest_coverage:.1f}x")

    if revenue_growth_yoy > 0.10:
        adjustments += 0.06
        positive_factors.append(f"Strong growth: {revenue_growth_yoy:.1%}")

    if margin_trend == "improving":
        adjustments += 0.05
        positive_factors.append("Improving margins")

    if positive_outlook:
        adjustments += 0.12
        positive_factors.append("Positive outlook from rating agency")

    # Distance penalty
    distance_mult = max(0.1, 1.0 - (distance_from_ig - 1) * 0.25)

    prob = min(0.80, max(0.01, (base_prob + adjustments) * distance_mult))

    return {
        "current_rating": current_rating,
        "distance_to_ig_notches": distance_from_ig,
        "rising_star_probability": round(prob, 4),
        "outlook": "LIKELY" if prob > 0.15 else "POSSIBLE" if prob > 0.08 else "UNLIKELY",
        "positive_factors": positive_factors,
        "timestamp": datetime.utcnow().isoformat(),
    }


def screen_fallen_angel_candidates(
    bonds: List[Dict],
    min_probability: float = 0.10,
) -> List[Dict]:
    """
    Screen a list of IG bonds for fallen angel risk.

    Args:
        bonds: List of dicts with keys: ticker, rating, leverage, coverage, fcf_yield, spread, sector.
        min_probability: Minimum probability threshold.

    Returns:
        Filtered and ranked list of fallen angel candidates.
    """
    candidates = []
    for bond in bonds:
        result = calculate_fallen_angel_score(
            current_rating=bond.get("rating", "BBB"),
            leverage_ratio=bond.get("leverage", 3.0),
            interest_coverage=bond.get("coverage", 4.0),
            free_cash_flow_yield=bond.get("fcf_yield", 0.05),
            spread_bps=bond.get("spread", 150),
            sector=bond.get("sector", "industrials"),
            negative_outlook=bond.get("negative_outlook", False),
            on_creditwatch=bond.get("on_creditwatch", False),
        )
        if "error" not in result and result["fallen_angel_probability"] >= min_probability:
            result["ticker"] = bond.get("ticker", "UNKNOWN")
            candidates.append(result)

    return sorted(candidates, key=lambda x: x["fallen_angel_probability"], reverse=True)


def get_transition_matrix() -> Dict:
    """Return the credit rating transition probability matrix."""
    return TRANSITION_MATRIX
