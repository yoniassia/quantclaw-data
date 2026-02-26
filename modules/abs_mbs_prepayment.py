"""
ABS/MBS Prepayment Model — Model mortgage-backed and asset-backed securities
prepayment behavior using PSA, CPR, and SMM methodologies.

Roadmap item #344: ABS/MBS Prepayment Model
"""

import math
from typing import Any


def psa_to_cpr(month: int, psa_speed: float = 100) -> float:
    """
    Convert PSA speed to CPR (Conditional Prepayment Rate) for a given month.

    PSA 100% assumes CPR ramps from 0.2% to 6% over 30 months, then stays at 6%.
    PSA speed scales linearly (e.g. PSA 200 = 2x).

    Args:
        month: Loan age in months.
        psa_speed: PSA speed as percentage (100 = standard).

    Returns:
        Annual CPR as decimal.
    """
    base_cpr = min(month * 0.002, 0.06)
    return base_cpr * (psa_speed / 100)


def cpr_to_smm(cpr: float) -> float:
    """
    Convert annual CPR to monthly SMM (Single Monthly Mortality).

    Args:
        cpr: Conditional Prepayment Rate (annual, decimal).

    Returns:
        SMM as decimal.
    """
    return 1 - (1 - cpr) ** (1 / 12)


def project_cashflows(
    original_balance: float = 1_000_000,
    coupon_rate: float = 6.0,
    term_months: int = 360,
    psa_speed: float = 100,
    current_month: int = 0,
    projection_months: int = 60,
) -> dict[str, Any]:
    """
    Project MBS cash flows with prepayment modeling.

    Args:
        original_balance: Original pool balance.
        coupon_rate: Annual coupon rate %.
        term_months: Original loan term in months.
        psa_speed: PSA prepayment speed.
        current_month: Current loan age in months.
        projection_months: Number of months to project.

    Returns:
        Dict with monthly cash flows, WAL, and total prepayments.
    """
    monthly_rate = coupon_rate / 100 / 12
    balance = original_balance
    flows = []
    total_principal = 0
    total_interest = 0
    total_prepayment = 0
    wal_numerator = 0

    for m in range(1, projection_months + 1):
        age = current_month + m
        remaining = term_months - age + 1
        if remaining <= 0 or balance <= 0.01:
            break

        # Scheduled payment
        if monthly_rate > 0:
            scheduled_pmt = balance * monthly_rate / (1 - (1 + monthly_rate) ** (-remaining))
        else:
            scheduled_pmt = balance / remaining

        interest = balance * monthly_rate
        scheduled_principal = scheduled_pmt - interest

        # Prepayment
        cpr = psa_to_cpr(age, psa_speed)
        smm = cpr_to_smm(cpr)
        prepayment = (balance - scheduled_principal) * smm

        total_pmt = scheduled_principal + prepayment + interest
        wal_numerator += (scheduled_principal + prepayment) * m

        flows.append({
            "month": m,
            "age": age,
            "balance": round(balance, 2),
            "interest": round(interest, 2),
            "scheduled_principal": round(scheduled_principal, 2),
            "prepayment": round(prepayment, 2),
            "total_principal": round(scheduled_principal + prepayment, 2),
            "cpr_pct": round(cpr * 100, 3),
            "smm_pct": round(smm * 100, 4),
        })

        total_interest += interest
        total_principal += scheduled_principal
        total_prepayment += prepayment
        balance -= (scheduled_principal + prepayment)

    wal = (wal_numerator / original_balance / 12) if original_balance > 0 else 0

    return {
        "original_balance": original_balance,
        "psa_speed": psa_speed,
        "coupon_rate": coupon_rate,
        "projected_months": len(flows),
        "ending_balance": round(max(balance, 0), 2),
        "total_interest": round(total_interest, 2),
        "total_scheduled_principal": round(total_principal, 2),
        "total_prepayments": round(total_prepayment, 2),
        "weighted_average_life_years": round(wal, 2),
        "cashflows": flows[:24],  # First 24 months for brevity
        "cashflows_note": f"Showing 24 of {len(flows)} months",
    }


def prepayment_sensitivity(
    original_balance: float = 1_000_000,
    coupon_rate: float = 6.0,
    psa_speeds: list[float] | None = None,
) -> dict[str, Any]:
    """
    Analyze sensitivity of WAL and cash flows to different prepayment speeds.

    Args:
        original_balance: Pool balance.
        coupon_rate: Coupon rate %.
        psa_speeds: List of PSA speeds to test.

    Returns:
        Dict with WAL, ending balance, and total prepayments per speed.
    """
    if psa_speeds is None:
        psa_speeds = [0, 50, 100, 150, 200, 300, 400, 500]

    results = []
    for speed in psa_speeds:
        proj = project_cashflows(
            original_balance=original_balance,
            coupon_rate=coupon_rate,
            psa_speed=speed,
            projection_months=360,
        )
        results.append({
            "psa_speed": speed,
            "wal_years": proj["weighted_average_life_years"],
            "ending_balance_pct": round(proj["ending_balance"] / original_balance * 100, 1),
            "total_prepayments": proj["total_prepayments"],
            "total_interest": proj["total_interest"],
        })

    return {
        "original_balance": original_balance,
        "coupon_rate": coupon_rate,
        "scenarios": results,
    }


def refinance_incentive(
    pool_coupon: float,
    current_market_rate: float,
    burnout_factor: float = 0.0,
) -> dict[str, Any]:
    """
    Estimate refinancing incentive and implied prepayment speed.

    Args:
        pool_coupon: Weighted average coupon of the pool %.
        current_market_rate: Current market mortgage rate %.
        burnout_factor: Burnout adjustment (0-1, higher = more burned out).

    Returns:
        Dict with incentive, implied PSA speed, and refinance probability.
    """
    incentive_bps = (pool_coupon - current_market_rate) * 100

    # S-curve model for prepayment response
    if incentive_bps <= 0:
        base_psa = max(50, 100 + incentive_bps * 0.3)
    elif incentive_bps <= 100:
        base_psa = 100 + incentive_bps * 1.5
    elif incentive_bps <= 200:
        base_psa = 250 + (incentive_bps - 100) * 2.0
    else:
        base_psa = min(700, 450 + (incentive_bps - 200) * 1.0)

    # Apply burnout
    adjusted_psa = base_psa * (1 - burnout_factor * 0.5)

    refi_probability = min(0.95, max(0.05, 1 / (1 + math.exp(-0.02 * (incentive_bps - 50)))))

    return {
        "pool_coupon_pct": pool_coupon,
        "market_rate_pct": current_market_rate,
        "incentive_bps": round(incentive_bps, 1),
        "base_psa_speed": round(base_psa, 0),
        "burnout_factor": burnout_factor,
        "adjusted_psa_speed": round(adjusted_psa, 0),
        "refinance_probability": round(refi_probability, 3),
        "direction": "In the money" if incentive_bps > 0 else "Out of the money",
    }
