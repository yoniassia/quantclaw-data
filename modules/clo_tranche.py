"""
CLO Tranche Analyzer — Model collateralized loan obligation structures with
waterfall payments, subordination levels, and tranche-level risk metrics.

Roadmap item #343: CLO Tranche Analyzer
"""

import math
from typing import Any


# Standard CLO capital structure
DEFAULT_CLO_STRUCTURE = [
    {"tranche": "AAA", "pct": 0.62, "spread_bps": 130, "rating": "AAA"},
    {"tranche": "AA", "pct": 0.12, "spread_bps": 185, "rating": "AA"},
    {"tranche": "A", "pct": 0.07, "spread_bps": 240, "rating": "A"},
    {"tranche": "BBB", "pct": 0.05, "spread_bps": 350, "rating": "BBB"},
    {"tranche": "BB", "pct": 0.04, "spread_bps": 600, "rating": "BB"},
    {"tranche": "Equity", "pct": 0.10, "spread_bps": 0, "rating": "NR"},
]


def analyze_clo_structure(
    deal_size: float = 500_000_000,
    structure: list[dict] | None = None,
    collateral_spread_bps: float = 350,
    default_rate: float = 0.02,
    recovery_rate: float = 0.70,
    base_rate: float = 5.0,
    management_fee_bps: float = 50,
) -> dict[str, Any]:
    """
    Analyze a CLO deal structure with waterfall cash flows.

    Args:
        deal_size: Total deal size in dollars.
        structure: List of tranche dicts (tranche, pct, spread_bps, rating).
        collateral_spread_bps: Weighted average spread of underlying loans.
        default_rate: Annual default rate assumption.
        recovery_rate: Recovery rate on defaulted loans.
        base_rate: Base interest rate (SOFR/LIBOR) %.
        management_fee_bps: Annual CLO manager fee in bps.

    Returns:
        Dict with tranche details, excess spread, and coverage ratios.
    """
    tranches = structure or DEFAULT_CLO_STRUCTURE

    # Collateral income
    total_collateral_income = deal_size * (collateral_spread_bps / 10000)
    default_losses = deal_size * default_rate * (1 - recovery_rate)
    net_collateral_income = total_collateral_income - default_losses
    management_fees = deal_size * (management_fee_bps / 10000)
    available_for_tranches = net_collateral_income - management_fees

    tranche_details = []
    cumulative_sub = 0.0
    remaining = available_for_tranches

    for t in tranches:
        tranche_size = deal_size * t["pct"]
        tranche_cost = tranche_size * (t["spread_bps"] / 10000) if t["tranche"] != "Equity" else 0
        subordination = 1.0 - cumulative_sub - t["pct"]
        cumulative_sub += t["pct"]

        # Breakeven default rate: how much defaults before this tranche takes losses
        sub_below = max(0, 1.0 - cumulative_sub)
        breakeven_default = sub_below / (1 - recovery_rate) if recovery_rate < 1 else float("inf")

        paid = min(tranche_cost, remaining) if t["tranche"] != "Equity" else max(0, remaining)
        remaining = max(0, remaining - paid) if t["tranche"] != "Equity" else 0

        equity_return = (paid / tranche_size * 100) if t["tranche"] == "Equity" and tranche_size > 0 else None

        tranche_details.append({
            "tranche": t["tranche"],
            "rating": t["rating"],
            "size": round(tranche_size),
            "pct_of_deal": round(t["pct"] * 100, 1),
            "spread_bps": t["spread_bps"],
            "annual_cost": round(tranche_cost),
            "subordination_pct": round(sub_below * 100, 1),
            "breakeven_default_rate": round(breakeven_default * 100, 2),
            "fully_paid": paid >= tranche_cost if t["tranche"] != "Equity" else None,
            "equity_irr_estimate": round(equity_return, 2) if equity_return else None,
        })

    total_tranche_cost = sum(d["annual_cost"] for d in tranche_details if d["tranche"] != "Equity")
    excess_spread = net_collateral_income - management_fees - total_tranche_cost

    return {
        "deal_size": deal_size,
        "collateral_income": round(total_collateral_income),
        "default_losses": round(default_losses),
        "management_fees": round(management_fees),
        "total_tranche_costs": round(total_tranche_cost),
        "excess_spread": round(excess_spread),
        "excess_spread_bps": round(excess_spread / deal_size * 10000, 1),
        "tranches": tranche_details,
    }


def stress_test_clo(
    default_rates: list[float] | None = None,
    recovery_rates: list[float] | None = None,
    deal_size: float = 500_000_000,
) -> dict[str, Any]:
    """
    Stress test CLO tranches across various default/recovery scenarios.

    Args:
        default_rates: List of default rate scenarios to test.
        recovery_rates: List of recovery rate scenarios to test.
        deal_size: Deal size.

    Returns:
        Matrix of results showing which tranches survive each scenario.
    """
    if default_rates is None:
        default_rates = [0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15]
    if recovery_rates is None:
        recovery_rates = [0.80, 0.70, 0.60, 0.50, 0.40]

    scenarios = []
    for dr in default_rates:
        for rr in recovery_rates:
            result = analyze_clo_structure(
                deal_size=deal_size, default_rate=dr, recovery_rate=rr
            )
            impaired = [t["tranche"] for t in result["tranches"]
                        if t["tranche"] != "Equity" and not t["fully_paid"]]
            scenarios.append({
                "default_rate_pct": round(dr * 100, 1),
                "recovery_rate_pct": round(rr * 100, 1),
                "loss_pct": round(dr * (1 - rr) * 100, 2),
                "excess_spread_bps": result["excess_spread_bps"],
                "impaired_tranches": impaired,
                "equity_wiped": result["excess_spread"] <= 0,
            })

    return {"deal_size": deal_size, "scenarios": scenarios, "total_scenarios": len(scenarios)}


def compare_vintages(
    vintage_defaults: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Compare CLO performance across different vintage years by default experience.

    Args:
        vintage_defaults: Dict mapping vintage year to realized default rate.

    Returns:
        Comparison of tranche outcomes by vintage.
    """
    if vintage_defaults is None:
        vintage_defaults = {
            "2019": 0.015, "2020": 0.035, "2021": 0.01,
            "2022": 0.025, "2023": 0.02, "2024": 0.018,
        }

    comparisons = []
    for vintage, dr in vintage_defaults.items():
        result = analyze_clo_structure(default_rate=dr)
        comparisons.append({
            "vintage": vintage,
            "default_rate_pct": round(dr * 100, 1),
            "excess_spread_bps": result["excess_spread_bps"],
            "equity_return_est": next(
                (t["equity_irr_estimate"] for t in result["tranches"] if t["tranche"] == "Equity"), None
            ),
            "all_debt_paid": all(
                t["fully_paid"] for t in result["tranches"] if t["tranche"] != "Equity"
            ),
        })

    return {"vintages": comparisons}
