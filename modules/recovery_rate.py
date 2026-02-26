"""
Recovery Rate Estimator — Models expected recovery in default scenarios.

Estimates recovery rates for defaulted debt based on seniority, collateral,
industry, economic conditions, and capital structure characteristics.
Uses Moody's/S&P historical recovery data and structural models.
Free data sources: Historical averages from rating agency publications.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Historical average recovery rates by seniority (Moody's LGD data)
HISTORICAL_RECOVERY = {
    "bank_loan_first_lien": {"mean": 0.69, "median": 0.77, "std": 0.24},
    "bank_loan_second_lien": {"mean": 0.43, "median": 0.42, "std": 0.28},
    "senior_secured_bond": {"mean": 0.53, "median": 0.55, "std": 0.26},
    "senior_unsecured_bond": {"mean": 0.37, "median": 0.35, "std": 0.25},
    "subordinated_bond": {"mean": 0.24, "median": 0.20, "std": 0.22},
    "junior_subordinated": {"mean": 0.14, "median": 0.10, "std": 0.18},
    "preferred_stock": {"mean": 0.06, "median": 0.02, "std": 0.12},
}

# Industry recovery adjustments (vs average)
INDUSTRY_ADJUSTMENTS = {
    "utilities": 0.10,       # Regulated assets, stable
    "telecom": 0.05,         # Infrastructure value
    "healthcare": 0.03,      # Essential services
    "technology": 0.00,      # Mixed — IP value varies
    "industrials": -0.02,    # Cyclical, asset-dependent
    "consumer_staples": 0.02,
    "consumer_discretionary": -0.05,
    "energy": -0.08,         # Commodity-dependent, volatile
    "retail": -0.10,         # Declining secular trends
    "real_estate": 0.08,     # Hard asset backing
    "financials": -0.05,     # Complex capital structures
    "media": -0.07,          # Intangible assets
    "airlines": -0.12,       # Highly cyclical, asset-heavy
    "restaurants": -0.10,    # Low recovery historically
    "mining": -0.05,         # Commodity cycles
}

# Economic cycle adjustment
CYCLE_ADJUSTMENTS = {
    "expansion": 0.08,       # Better recoveries in good times
    "late_cycle": 0.02,
    "recession": -0.12,      # Much worse in recessions
    "early_recovery": 0.00,
}

# Collateral type value retention
COLLATERAL_VALUE = {
    "cash_securities": 0.95,
    "receivables": 0.75,
    "inventory": 0.55,
    "equipment": 0.40,
    "real_property": 0.65,
    "intellectual_property": 0.20,
    "goodwill_intangibles": 0.05,
    "none_unsecured": 0.00,
}


def estimate_recovery_rate(
    seniority: str,
    industry: str = "industrials",
    economic_cycle: str = "late_cycle",
    collateral_type: Optional[str] = None,
    leverage_at_default: float = 8.0,
    asset_coverage_ratio: Optional[float] = None,
    debt_cushion_below_pct: float = 0.0,
    is_prepackaged: bool = False,
    jurisdiction: str = "us",
) -> Dict:
    """
    Estimate recovery rate for a debt instrument in a default scenario.

    Args:
        seniority: Debt seniority level (key from HISTORICAL_RECOVERY).
        industry: Industry sector.
        economic_cycle: Current economic cycle phase.
        collateral_type: Type of collateral (if secured).
        leverage_at_default: Expected leverage (Debt/EBITDA) at default.
        asset_coverage_ratio: Estimated asset value / debt at this level.
        debt_cushion_below_pct: Percentage of total debt junior to this tranche.
        is_prepackaged: Whether a prepackaged restructuring is likely.
        jurisdiction: Bankruptcy jurisdiction (us, uk, eu).

    Returns:
        Recovery rate estimate with confidence interval and factors.
    """
    # Base recovery
    base = HISTORICAL_RECOVERY.get(seniority, HISTORICAL_RECOVERY["senior_unsecured_bond"])
    recovery = base["mean"]

    adjustments = []

    # Industry adjustment
    ind_adj = INDUSTRY_ADJUSTMENTS.get(industry, 0.0)
    recovery += ind_adj
    if abs(ind_adj) > 0.03:
        adjustments.append(f"Industry ({industry}): {ind_adj:+.0%}")

    # Economic cycle
    cycle_adj = CYCLE_ADJUSTMENTS.get(economic_cycle, 0.0)
    recovery += cycle_adj
    if abs(cycle_adj) > 0.01:
        adjustments.append(f"Economic cycle ({economic_cycle}): {cycle_adj:+.0%}")

    # Collateral
    if collateral_type and collateral_type in COLLATERAL_VALUE:
        coll_value = COLLATERAL_VALUE[collateral_type]
        coll_adj = (coll_value - 0.40) * 0.15  # Adjustment relative to average
        recovery += coll_adj
        adjustments.append(f"Collateral ({collateral_type}): {coll_adj:+.1%}")

    # Leverage at default
    if leverage_at_default > 10:
        lev_adj = -0.08
        adjustments.append(f"Extreme leverage at default ({leverage_at_default:.1f}x): {lev_adj:+.0%}")
    elif leverage_at_default > 7:
        lev_adj = -0.04
    elif leverage_at_default < 5:
        lev_adj = 0.05
        adjustments.append(f"Moderate leverage ({leverage_at_default:.1f}x): {lev_adj:+.0%}")
    else:
        lev_adj = 0.0
    recovery += lev_adj

    # Debt cushion below (junior debt absorbs losses first)
    if debt_cushion_below_pct > 0.3:
        cushion_adj = 0.08
        adjustments.append(f"Strong debt cushion ({debt_cushion_below_pct:.0%} junior): {cushion_adj:+.0%}")
    elif debt_cushion_below_pct > 0.15:
        cushion_adj = 0.04
    else:
        cushion_adj = 0.0
    recovery += cushion_adj

    # Asset coverage
    if asset_coverage_ratio is not None:
        if asset_coverage_ratio > 1.5:
            acr_adj = 0.10
            adjustments.append(f"Strong asset coverage ({asset_coverage_ratio:.1f}x): {acr_adj:+.0%}")
        elif asset_coverage_ratio > 1.0:
            acr_adj = 0.04
        elif asset_coverage_ratio < 0.5:
            acr_adj = -0.10
            adjustments.append(f"Weak asset coverage ({asset_coverage_ratio:.1f}x): {acr_adj:+.0%}")
        else:
            acr_adj = -0.03
        recovery += acr_adj

    # Prepackaged restructuring (higher recovery, less value destruction)
    if is_prepackaged:
        recovery += 0.07
        adjustments.append("Prepackaged restructuring: +7%")

    # Jurisdiction
    if jurisdiction == "uk":
        recovery -= 0.03  # UK scheme slightly lower historically
    elif jurisdiction == "eu":
        recovery -= 0.05  # More complex, longer process

    # Bound recovery
    recovery = max(0.02, min(0.95, recovery))

    # Confidence interval based on historical std
    std = base["std"]
    low = max(0.0, recovery - 1.5 * std)
    high = min(1.0, recovery + 1.5 * std)

    return {
        "seniority": seniority,
        "industry": industry,
        "estimated_recovery_rate": round(recovery, 3),
        "recovery_cents_on_dollar": round(recovery * 100, 1),
        "confidence_interval": {
            "low": round(low * 100, 1),
            "mid": round(recovery * 100, 1),
            "high": round(high * 100, 1),
        },
        "historical_baseline": {
            "mean": round(base["mean"] * 100, 1),
            "median": round(base["median"] * 100, 1),
        },
        "adjustments_applied": adjustments,
        "loss_given_default": round((1 - recovery) * 100, 1),
        "inputs": {
            "economic_cycle": economic_cycle,
            "leverage_at_default": leverage_at_default,
            "debt_cushion_below": debt_cushion_below_pct,
            "prepackaged": is_prepackaged,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def waterfall_analysis(
    total_enterprise_value: float,
    capital_structure: List[Dict],
) -> List[Dict]:
    """
    Run a recovery waterfall analysis across the capital structure.

    Args:
        total_enterprise_value: Estimated enterprise value at emergence ($M).
        capital_structure: Ordered list (senior first) of dicts with:
            - name: Tranche name
            - amount: Face amount ($M)
            - seniority: Seniority key

    Returns:
        Recovery waterfall showing each tranche's recovery.
    """
    remaining_value = total_enterprise_value
    results = []

    for tranche in capital_structure:
        amount = tranche["amount"]
        if remaining_value >= amount:
            recovery_amount = amount
            recovery_rate = 1.0
        elif remaining_value > 0:
            recovery_amount = remaining_value
            recovery_rate = remaining_value / amount
        else:
            recovery_amount = 0
            recovery_rate = 0.0

        remaining_value -= recovery_amount

        results.append({
            "tranche": tranche["name"],
            "seniority": tranche.get("seniority", "unknown"),
            "face_amount_m": amount,
            "recovery_amount_m": round(recovery_amount, 2),
            "recovery_rate": round(recovery_rate, 4),
            "recovery_cents": round(recovery_rate * 100, 1),
            "impaired": recovery_rate < 1.0,
        })

    return results


def get_historical_recovery_rates() -> Dict:
    """Return historical recovery rate statistics by seniority."""
    return {
        k: {
            "mean_pct": round(v["mean"] * 100, 1),
            "median_pct": round(v["median"] * 100, 1),
            "std_pct": round(v["std"] * 100, 1),
        }
        for k, v in HISTORICAL_RECOVERY.items()
    }
