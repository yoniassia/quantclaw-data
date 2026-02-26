"""
Distressed Debt Screener — Identifies bonds trading at distressed levels.

Screens for bonds trading below par with high yields, deteriorating credit
metrics, and potential restructuring candidates. Uses spread thresholds,
price levels, and fundamental analysis.
Free data sources: FRED spreads, SEC filings, public financial data.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime


# Distressed classification thresholds
DISTRESS_THRESHOLDS = {
    "price_distressed": 70.0,  # Below 70 cents on the dollar
    "price_stressed": 85.0,    # Stressed but not distressed
    "yield_distressed": 1000,  # 1000+ bps over treasuries
    "yield_stressed": 600,     # 600-1000 bps = stressed
    "cds_distressed": 1000,    # CDS spread indicating distress
}

# Recovery rate assumptions by seniority
RECOVERY_ASSUMPTIONS = {
    "senior_secured_first_lien": {"mean": 0.65, "range": (0.45, 0.85)},
    "senior_secured_second_lien": {"mean": 0.45, "range": (0.25, 0.65)},
    "senior_unsecured": {"mean": 0.40, "range": (0.20, 0.60)},
    "subordinated": {"mean": 0.25, "range": (0.10, 0.45)},
    "junior_subordinated": {"mean": 0.15, "range": (0.05, 0.30)},
    "preferred_equity": {"mean": 0.08, "range": (0.00, 0.20)},
}

# Altman Z-Score thresholds
ZSCORE_ZONES = {
    "safe": {"min": 2.99, "label": "Safe Zone"},
    "grey": {"min": 1.81, "label": "Grey Zone"},
    "distress": {"min": -999, "label": "Distress Zone"},
}


def calculate_altman_zscore(
    working_capital: float,
    total_assets: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    total_liabilities: float,
    revenue: float,
) -> Dict:
    """
    Calculate Altman Z-Score for bankruptcy prediction.

    Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
    A = Working Capital / Total Assets
    B = Retained Earnings / Total Assets
    C = EBIT / Total Assets
    D = Market Cap / Total Liabilities
    E = Revenue / Total Assets

    Returns:
        Z-Score with zone classification and component breakdown.
    """
    ta = max(total_assets, 1)
    tl = max(total_liabilities, 1)

    a = working_capital / ta
    b = retained_earnings / ta
    c = ebit / ta
    d = market_cap / tl
    e = revenue / ta

    z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e

    if z >= 2.99:
        zone = "safe"
        bankruptcy_prob = max(0.01, 0.05 - (z - 2.99) * 0.01)
    elif z >= 1.81:
        zone = "grey"
        bankruptcy_prob = 0.15 + (2.99 - z) * 0.10
    else:
        zone = "distress"
        bankruptcy_prob = min(0.95, 0.50 + (1.81 - z) * 0.15)

    return {
        "z_score": round(z, 3),
        "zone": zone,
        "zone_label": ZSCORE_ZONES[zone]["label"],
        "bankruptcy_probability_1yr": round(bankruptcy_prob, 3),
        "components": {
            "A_working_capital_ta": round(a, 4),
            "B_retained_earnings_ta": round(b, 4),
            "C_ebit_ta": round(c, 4),
            "D_market_cap_tl": round(d, 4),
            "E_revenue_ta": round(e, 4),
        },
        "weighted": {
            "1.2A": round(1.2 * a, 4),
            "1.4B": round(1.4 * b, 4),
            "3.3C": round(3.3 * c, 4),
            "0.6D": round(0.6 * d, 4),
            "1.0E": round(1.0 * e, 4),
        },
    }


def screen_distressed_bond(
    price: float,
    yield_spread_bps: float,
    coupon: float,
    maturity_years: float,
    seniority: str = "senior_unsecured",
    leverage_ratio: float = 5.0,
    interest_coverage: float = 2.0,
    current_rating: str = "B",
    sector: str = "industrials",
) -> Dict:
    """
    Analyze a bond for distressed debt characteristics.

    Args:
        price: Current bond price (cents on dollar, 0-100+).
        yield_spread_bps: OAS or yield spread over treasuries in bps.
        coupon: Annual coupon rate (e.g., 0.065 for 6.5%).
        maturity_years: Years to maturity.
        seniority: Bond seniority level.
        leverage_ratio: Issuer's Debt/EBITDA.
        interest_coverage: Issuer's EBITDA/Interest.
        current_rating: Current credit rating.
        sector: Industry sector.

    Returns:
        Distress analysis with recovery estimates and trade recommendation.
    """
    # Classification
    if price < DISTRESS_THRESHOLDS["price_distressed"]:
        price_status = "DISTRESSED"
    elif price < DISTRESS_THRESHOLDS["price_stressed"]:
        price_status = "STRESSED"
    else:
        price_status = "NORMAL"

    if yield_spread_bps > DISTRESS_THRESHOLDS["yield_distressed"]:
        spread_status = "DISTRESSED"
    elif yield_spread_bps > DISTRESS_THRESHOLDS["yield_stressed"]:
        spread_status = "STRESSED"
    else:
        spread_status = "NORMAL"

    # Recovery analysis
    recovery_info = RECOVERY_ASSUMPTIONS.get(
        seniority, RECOVERY_ASSUMPTIONS["senior_unsecured"]
    )
    expected_recovery = recovery_info["mean"] * 100  # cents on dollar

    # Value assessment
    discount_to_recovery = expected_recovery - price
    upside_in_recovery = (expected_recovery / max(price, 1) - 1) * 100

    # Yield to worst approximation
    ytw = (coupon * 100 + (100 - price) / max(maturity_years, 0.5)) / ((100 + price) / 2) * 100

    # Distress score (0-100, higher = more distressed)
    distress_score = 0
    risk_flags = []

    if price < 50:
        distress_score += 30
        risk_flags.append("Deep discount (below 50)")
    elif price < 70:
        distress_score += 20
        risk_flags.append("Distressed price level")
    elif price < 85:
        distress_score += 10

    if yield_spread_bps > 1500:
        distress_score += 25
        risk_flags.append(f"Extreme spread: {yield_spread_bps}bps")
    elif yield_spread_bps > 1000:
        distress_score += 15

    if leverage_ratio > 7:
        distress_score += 15
        risk_flags.append(f"Unsustainable leverage: {leverage_ratio:.1f}x")
    elif leverage_ratio > 5:
        distress_score += 8

    if interest_coverage < 1.0:
        distress_score += 20
        risk_flags.append(f"Cannot cover interest: {interest_coverage:.1f}x")
    elif interest_coverage < 1.5:
        distress_score += 10

    distress_score = min(100, distress_score)

    # Trade thesis
    if price < expected_recovery * 0.7 and interest_coverage > 1.0:
        thesis = "POTENTIAL OPPORTUNITY — trading well below recovery value with serviceable debt"
    elif price < expected_recovery and distress_score < 60:
        thesis = "WATCHLIST — discount to recovery but elevated risk"
    elif distress_score > 70:
        thesis = "AVOID/SHORT — high probability of default with limited recovery"
    else:
        thesis = "NEUTRAL — risk/reward not compelling at current levels"

    return {
        "price": price,
        "price_status": price_status,
        "spread_bps": yield_spread_bps,
        "spread_status": spread_status,
        "distress_score": distress_score,
        "distress_level": "SEVERE" if distress_score > 70 else "MODERATE" if distress_score > 40 else "MILD" if distress_score > 20 else "NONE",
        "yield_to_worst_approx": round(ytw, 2),
        "recovery_analysis": {
            "seniority": seniority,
            "expected_recovery_cents": round(expected_recovery, 1),
            "recovery_range": [round(r * 100, 1) for r in recovery_info["range"]],
            "discount_to_recovery": round(discount_to_recovery, 1),
            "upside_if_recovery_pct": round(upside_in_recovery, 1),
        },
        "risk_flags": risk_flags,
        "trade_thesis": thesis,
        "timestamp": datetime.utcnow().isoformat(),
    }


def rank_distressed_universe(
    bonds: List[Dict],
) -> List[Dict]:
    """
    Rank a universe of bonds by distressed opportunity score.

    Args:
        bonds: List of bond dicts with price, spread, coupon, maturity, seniority, etc.

    Returns:
        Sorted list with opportunity scores (best first).
    """
    results = []
    for bond in bonds:
        analysis = screen_distressed_bond(
            price=bond.get("price", 100),
            yield_spread_bps=bond.get("spread_bps", 200),
            coupon=bond.get("coupon", 0.05),
            maturity_years=bond.get("maturity_years", 5),
            seniority=bond.get("seniority", "senior_unsecured"),
            leverage_ratio=bond.get("leverage", 4.0),
            interest_coverage=bond.get("coverage", 3.0),
            current_rating=bond.get("rating", "B"),
        )
        analysis["ticker"] = bond.get("ticker", "UNKNOWN")
        # Opportunity = upside potential weighted by inverse distress (don't want the worst)
        upside = analysis["recovery_analysis"]["upside_if_recovery_pct"]
        inv_distress = max(1, 100 - analysis["distress_score"])
        analysis["opportunity_score"] = round(upside * inv_distress / 100, 2)
        results.append(analysis)

    return sorted(results, key=lambda x: x["opportunity_score"], reverse=True)
