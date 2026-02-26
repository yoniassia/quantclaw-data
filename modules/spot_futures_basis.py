"""
Commodity Spot vs Futures Basis Monitor.

Tracks the basis (spot - futures) across major commodity markets,
identifies contango/backwardation, calculates annualized basis,
and detects basis trading opportunities.

Free data: Yahoo Finance futures chains, FRED commodity prices.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math


# Common commodity futures tickers (Yahoo format)
COMMODITY_CONTRACTS = {
    "crude_oil": {"spot": "CL=F", "front": "CL=F", "name": "WTI Crude Oil", "unit": "$/barrel"},
    "gold": {"spot": "GC=F", "front": "GC=F", "name": "Gold", "unit": "$/oz"},
    "silver": {"spot": "SI=F", "front": "SI=F", "name": "Silver", "unit": "$/oz"},
    "natural_gas": {"spot": "NG=F", "front": "NG=F", "name": "Natural Gas", "unit": "$/MMBtu"},
    "copper": {"spot": "HG=F", "front": "HG=F", "name": "Copper", "unit": "$/lb"},
    "corn": {"spot": "ZC=F", "front": "ZC=F", "name": "Corn", "unit": "c/bushel"},
    "soybeans": {"spot": "ZS=F", "front": "ZS=F", "name": "Soybeans", "unit": "c/bushel"},
    "wheat": {"spot": "ZW=F", "front": "ZW=F", "name": "Wheat", "unit": "c/bushel"},
}


def calculate_basis(
    spot_price: float,
    futures_price: float,
    days_to_expiry: int,
    commodity_name: str = "Unknown"
) -> Dict:
    """
    Calculate basis and annualized basis between spot and futures.

    Args:
        spot_price: Current spot price
        futures_price: Futures contract price
        days_to_expiry: Days until futures expiration
        commodity_name: Name for labeling

    Returns:
        Dict with basis metrics and market structure
    """
    basis = spot_price - futures_price
    basis_pct = (basis / spot_price * 100) if spot_price != 0 else 0

    # Annualized basis (carry)
    if days_to_expiry > 0 and futures_price > 0:
        annualized = ((spot_price / futures_price) ** (365 / days_to_expiry) - 1) * 100
    else:
        annualized = 0

    # Market structure
    if basis > 0:
        structure = "BACKWARDATION"
        interpretation = "Spot premium — supply tightness or strong near-term demand"
    elif basis < 0:
        structure = "CONTANGO"
        interpretation = "Futures premium — normal carry cost (storage + financing)"
    else:
        structure = "FLAT"
        interpretation = "No basis — spot equals futures"

    return {
        "commodity": commodity_name,
        "spot_price": round(spot_price, 4),
        "futures_price": round(futures_price, 4),
        "basis": round(basis, 4),
        "basis_pct": round(basis_pct, 4),
        "annualized_basis_pct": round(annualized, 4),
        "days_to_expiry": days_to_expiry,
        "market_structure": structure,
        "interpretation": interpretation
    }


def monitor_basis_curve(
    spot_price: float,
    futures_chain: List[Dict],
    commodity_name: str = "Unknown"
) -> Dict:
    """
    Analyze full futures curve basis structure.

    Args:
        spot_price: Current spot price
        futures_chain: List of dicts with keys: price, days_to_expiry, contract_month
        commodity_name: Commodity label

    Returns:
        Dict with curve analysis, roll yield, and term structure
    """
    if not futures_chain:
        return {"error": "No futures chain data provided"}

    chain = sorted(futures_chain, key=lambda x: x["days_to_expiry"])

    term_structure = []
    prev_price = spot_price

    for contract in chain:
        fp = contract["price"]
        dte = contract["days_to_expiry"]
        month = contract.get("contract_month", "")

        basis_info = calculate_basis(spot_price, fp, dte, commodity_name)

        # Calendar spread (roll yield between consecutive contracts)
        calendar_spread = prev_price - fp
        roll_yield_ann = 0
        if fp > 0 and dte > 0:
            roll_yield_ann = (calendar_spread / fp) * (365 / max(dte, 30)) * 100

        term_structure.append({
            "contract_month": month,
            "futures_price": round(fp, 4),
            "days_to_expiry": dte,
            "basis": round(spot_price - fp, 4),
            "basis_pct": round((spot_price - fp) / spot_price * 100, 4) if spot_price else 0,
            "calendar_spread": round(calendar_spread, 4),
            "roll_yield_annualized": round(roll_yield_ann, 4)
        })

        prev_price = fp

    # Overall curve shape
    front = chain[0]["price"]
    back = chain[-1]["price"]
    curve_slope = (back - front) / front * 100 if front > 0 else 0

    if curve_slope > 2:
        curve_shape = "STEEP_CONTANGO"
    elif curve_slope > 0:
        curve_shape = "MILD_CONTANGO"
    elif curve_slope > -2:
        curve_shape = "MILD_BACKWARDATION"
    else:
        curve_shape = "STEEP_BACKWARDATION"

    return {
        "commodity": commodity_name,
        "spot_price": round(spot_price, 4),
        "front_month_price": round(front, 4),
        "back_month_price": round(back, 4),
        "curve_slope_pct": round(curve_slope, 4),
        "curve_shape": curve_shape,
        "n_contracts": len(chain),
        "term_structure": term_structure
    }


def detect_basis_opportunities(
    commodities: List[Dict],
    threshold_annualized: float = 10.0
) -> Dict:
    """
    Screen multiple commodities for basis trading opportunities.

    Args:
        commodities: List of dicts with spot_price, futures_price,
                     days_to_expiry, name
        threshold_annualized: Min annualized basis % to flag

    Returns:
        Dict with ranked opportunities
    """
    opportunities = []

    for c in commodities:
        basis = calculate_basis(
            c["spot_price"],
            c["futures_price"],
            c["days_to_expiry"],
            c.get("name", "Unknown")
        )

        ann = abs(basis["annualized_basis_pct"])
        if ann >= threshold_annualized:
            trade_type = (
                "CASH_AND_CARRY" if basis["market_structure"] == "CONTANGO"
                else "REVERSE_CASH_AND_CARRY"
            )
            opportunities.append({
                **basis,
                "trade_type": trade_type,
                "opportunity_score": round(ann / threshold_annualized, 2)
            })

    opportunities.sort(key=lambda x: abs(x["annualized_basis_pct"]), reverse=True)

    return {
        "n_screened": len(commodities),
        "n_opportunities": len(opportunities),
        "threshold_annualized_pct": threshold_annualized,
        "opportunities": opportunities,
        "best_opportunity": opportunities[0] if opportunities else None
    }


def basis_risk_calculator(
    hedge_ratio: float,
    spot_volatility: float,
    futures_volatility: float,
    correlation: float
) -> Dict:
    """
    Calculate basis risk for a hedged position.

    Args:
        hedge_ratio: Futures position / spot position
        spot_volatility: Annualized spot price volatility
        futures_volatility: Annualized futures price volatility
        correlation: Spot-futures price correlation

    Returns:
        Dict with basis risk metrics and optimal hedge ratio
    """
    # Portfolio variance: var(S) + h^2*var(F) - 2*h*cov(S,F)
    cov = correlation * spot_volatility * futures_volatility
    hedged_var = (
        spot_volatility ** 2
        + hedge_ratio ** 2 * futures_volatility ** 2
        - 2 * hedge_ratio * cov
    )
    hedged_vol = math.sqrt(max(hedged_var, 0))

    # Optimal hedge ratio (minimum variance)
    optimal_h = cov / (futures_volatility ** 2) if futures_volatility > 0 else 1.0

    # Hedge effectiveness
    unhedged_var = spot_volatility ** 2
    effectiveness = 1 - hedged_var / unhedged_var if unhedged_var > 0 else 0

    return {
        "hedge_ratio": round(hedge_ratio, 4),
        "optimal_hedge_ratio": round(optimal_h, 4),
        "unhedged_volatility": round(spot_volatility, 4),
        "hedged_volatility": round(hedged_vol, 4),
        "volatility_reduction_pct": round((1 - hedged_vol / spot_volatility) * 100, 2) if spot_volatility > 0 else 0,
        "hedge_effectiveness": round(effectiveness, 4),
        "basis_risk": round(hedged_vol, 4),
        "correlation": round(correlation, 4)
    }
