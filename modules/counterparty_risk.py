"""Counterparty Risk Scorer — CDS-implied default probability and exposure.

Calculates counterparty credit risk using CDS spreads, credit ratings,
and exposure metrics. Provides probability of default (PD), loss given
default (LGD), expected loss, and risk scores for counterparty management.

Roadmap #249: Counterparty Risk Scorer (CDS-implied)
"""

import math
import datetime
from typing import Any


# S&P credit rating to 1-year default probability (historical averages)
RATING_PD_MAP = {
    "AAA": 0.0001, "AA+": 0.0002, "AA": 0.0003, "AA-": 0.0005,
    "A+": 0.0007, "A": 0.0009, "A-": 0.0013,
    "BBB+": 0.0020, "BBB": 0.0030, "BBB-": 0.0050,
    "BB+": 0.0080, "BB": 0.0120, "BB-": 0.0200,
    "B+": 0.0350, "B": 0.0500, "B-": 0.0800,
    "CCC+": 0.1200, "CCC": 0.1800, "CCC-": 0.2500,
    "CC": 0.3500, "C": 0.5000, "D": 1.0000,
}

# Standard LGD assumptions by seniority
LGD_BY_SENIORITY = {
    "senior_secured": 0.25,
    "senior_unsecured": 0.40,
    "subordinated": 0.60,
    "junior_subordinated": 0.75,
    "equity": 1.00,
}


def cds_implied_pd(
    cds_spread_bps: float,
    recovery_rate: float = 0.40,
    maturity_years: float = 5.0,
) -> dict[str, Any]:
    """Calculate implied probability of default from CDS spread.

    Uses the simplified hazard rate model:
        hazard_rate = spread / (1 - recovery_rate)
        cumulative_PD = 1 - exp(-hazard_rate * T)

    Args:
        cds_spread_bps: CDS spread in basis points.
        recovery_rate: Assumed recovery rate (default 40%).
        maturity_years: CDS maturity in years.

    Returns:
        Dict with hazard rate, annualized PD, cumulative PD.
    """
    spread_decimal = cds_spread_bps / 10000
    lgd = 1 - recovery_rate

    if lgd <= 0:
        return {"error": "Recovery rate must be < 1"}

    hazard_rate = spread_decimal / lgd
    annual_pd = 1 - math.exp(-hazard_rate)
    cumulative_pd = 1 - math.exp(-hazard_rate * maturity_years)

    return {
        "cds_spread_bps": cds_spread_bps,
        "recovery_rate": recovery_rate,
        "hazard_rate": round(hazard_rate, 6),
        "annual_pd": round(annual_pd, 6),
        "annual_pd_pct": round(annual_pd * 100, 4),
        "cumulative_pd": round(cumulative_pd, 6),
        "cumulative_pd_pct": round(cumulative_pd * 100, 4),
        "maturity_years": maturity_years,
    }


def rating_implied_pd(rating: str) -> dict[str, Any]:
    """Get historical default probability for a credit rating.

    Args:
        rating: S&P credit rating string (e.g., 'BBB+').

    Returns:
        Dict with rating and associated 1-year PD.
    """
    pd = RATING_PD_MAP.get(rating.upper())
    if pd is None:
        return {"rating": rating, "error": "Unknown rating"}
    return {
        "rating": rating.upper(),
        "one_year_pd": pd,
        "one_year_pd_pct": round(pd * 100, 4),
    }


def calculate_expected_loss(
    exposure_usd: float,
    pd: float,
    lgd: float = 0.40,
) -> dict[str, Any]:
    """Calculate expected loss from exposure, PD, and LGD.

    Expected Loss = Exposure × PD × LGD

    Args:
        exposure_usd: Current exposure in USD.
        pd: Probability of default (0-1).
        lgd: Loss given default (0-1).

    Returns:
        Dict with expected loss calculation.
    """
    el = exposure_usd * pd * lgd
    return {
        "exposure_usd": round(exposure_usd, 2),
        "pd": round(pd, 6),
        "lgd": round(lgd, 4),
        "expected_loss_usd": round(el, 2),
        "expected_loss_bps": round(el / exposure_usd * 10000, 2) if exposure_usd > 0 else 0,
    }


def score_counterparty(
    name: str,
    cds_spread_bps: float | None = None,
    credit_rating: str | None = None,
    exposure_usd: float = 0,
    seniority: str = "senior_unsecured",
    netting_benefit_pct: float = 0.0,
    collateral_usd: float = 0.0,
) -> dict[str, Any]:
    """Comprehensive counterparty risk score.

    Combines CDS-implied and rating-implied PD, calculates net exposure
    after netting and collateral, and assigns a risk tier.

    Args:
        name: Counterparty name.
        cds_spread_bps: CDS spread (optional).
        credit_rating: S&P rating (optional).
        exposure_usd: Gross exposure.
        seniority: Claim seniority for LGD.
        netting_benefit_pct: Netting benefit as percentage (0-1).
        collateral_usd: Collateral held.

    Returns:
        Comprehensive risk assessment dict.
    """
    # Determine PD
    pd_cds = None
    pd_rating = None

    if cds_spread_bps is not None:
        cds_result = cds_implied_pd(cds_spread_bps)
        pd_cds = cds_result.get("annual_pd", 0)

    if credit_rating:
        rating_result = rating_implied_pd(credit_rating)
        pd_rating = rating_result.get("one_year_pd", 0)

    # Use CDS-implied PD if available (market-based), else rating
    if pd_cds is not None and pd_rating is not None:
        pd_final = max(pd_cds, pd_rating)  # Conservative: take higher
        pd_source = "max(CDS, rating)"
    elif pd_cds is not None:
        pd_final = pd_cds
        pd_source = "CDS-implied"
    elif pd_rating is not None:
        pd_final = pd_rating
        pd_source = "rating-implied"
    else:
        pd_final = 0.01  # Default assumption
        pd_source = "default"

    lgd = LGD_BY_SENIORITY.get(seniority, 0.40)

    # Net exposure
    net_exposure = exposure_usd * (1 - netting_benefit_pct) - collateral_usd
    net_exposure = max(net_exposure, 0)

    el = calculate_expected_loss(net_exposure, pd_final, lgd)

    # Risk score (0-100, higher = more risky)
    risk_score = min(100, pd_final * 1000 + (net_exposure / 1_000_000) * 5)

    if risk_score < 10:
        tier = "Low"
    elif risk_score < 30:
        tier = "Medium"
    elif risk_score < 60:
        tier = "High"
    else:
        tier = "Critical"

    return {
        "counterparty": name,
        "credit_rating": credit_rating,
        "cds_spread_bps": cds_spread_bps,
        "pd_final": round(pd_final, 6),
        "pd_source": pd_source,
        "lgd": lgd,
        "seniority": seniority,
        "gross_exposure_usd": round(exposure_usd, 2),
        "netting_benefit_pct": netting_benefit_pct,
        "collateral_usd": collateral_usd,
        "net_exposure_usd": round(net_exposure, 2),
        "expected_loss_usd": el["expected_loss_usd"],
        "risk_score": round(risk_score, 1),
        "risk_tier": tier,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
