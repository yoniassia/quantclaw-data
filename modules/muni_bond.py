"""
Municipal Bond Analyzer — Calculate tax-equivalent yields, compare muni vs
taxable bonds, and screen municipal bonds by state, maturity, and credit quality.

Roadmap item #342: Municipal Bond Analyzer (tax-equivalent yield)
"""

from typing import Any


# State income tax rates (simplified top marginal rates)
STATE_TAX_RATES = {
    "CA": 0.133, "NY": 0.109, "NJ": 0.1075, "HI": 0.11, "MN": 0.0985,
    "OR": 0.099, "VT": 0.0875, "IA": 0.06, "WI": 0.0765, "ME": 0.0715,
    "SC": 0.065, "CT": 0.0699, "ID": 0.058, "MT": 0.0675, "NE": 0.0664,
    "DE": 0.066, "WV": 0.065, "MA": 0.05, "NC": 0.0475, "IL": 0.0495,
    "GA": 0.055, "VA": 0.0575, "MD": 0.0575, "KY": 0.04, "OH": 0.04,
    "CO": 0.044, "UT": 0.0465, "MI": 0.0425, "IN": 0.0305, "PA": 0.0307,
    "AZ": 0.025, "ND": 0.0195, "FL": 0.0, "TX": 0.0, "NV": 0.0,
    "WA": 0.0, "WY": 0.0, "SD": 0.0, "AK": 0.0, "TN": 0.0, "NH": 0.0,
}


def tax_equivalent_yield(
    muni_yield: float,
    federal_rate: float = 0.37,
    state_rate: float | None = None,
    state: str | None = None,
    in_state: bool = True,
) -> dict[str, Any]:
    """
    Calculate the tax-equivalent yield of a municipal bond.

    Args:
        muni_yield: Municipal bond yield (e.g. 3.5 for 3.5%).
        federal_rate: Federal marginal tax rate (default 37%).
        state_rate: State tax rate override. If None, looked up from state.
        state: Two-letter state code.
        in_state: Whether bond is in investor's state (double tax-exempt).

    Returns:
        Dict with tax-equivalent yield, effective tax rate, and comparison.
    """
    if state_rate is None and state:
        state_rate = STATE_TAX_RATES.get(state.upper(), 0.0)
    elif state_rate is None:
        state_rate = 0.0

    # In-state munis are exempt from both federal + state
    if in_state:
        combined_rate = federal_rate + state_rate * (1 - federal_rate)
    else:
        # Out-of-state: only federal exempt
        combined_rate = federal_rate

    teq_yield = muni_yield / (1 - combined_rate)

    return {
        "muni_yield_pct": muni_yield,
        "tax_equivalent_yield_pct": round(teq_yield, 3),
        "federal_rate": federal_rate,
        "state_rate": state_rate,
        "combined_effective_rate": round(combined_rate, 4),
        "in_state": in_state,
        "state": state,
        "breakeven_taxable_yield": round(teq_yield, 3),
        "tax_savings_bps": round((teq_yield - muni_yield) * 100, 1),
    }


def muni_vs_taxable_comparison(
    muni_yield: float,
    taxable_yield: float,
    federal_rate: float = 0.37,
    state: str | None = None,
    investment: float = 100000,
    years: int = 10,
) -> dict[str, Any]:
    """
    Compare a municipal bond vs taxable bond after taxes.

    Args:
        muni_yield: Muni yield %.
        taxable_yield: Taxable bond yield %.
        federal_rate: Federal marginal rate.
        state: State code for state tax lookup.
        investment: Investment amount in dollars.
        years: Holding period in years.

    Returns:
        Dict comparing after-tax income, winner, and cumulative advantage.
    """
    state_rate = STATE_TAX_RATES.get(state.upper(), 0.0) if state else 0.0
    combined_rate = federal_rate + state_rate * (1 - federal_rate)

    annual_muni_income = investment * (muni_yield / 100)
    annual_taxable_gross = investment * (taxable_yield / 100)
    annual_taxable_net = annual_taxable_gross * (1 - combined_rate)

    total_muni = annual_muni_income * years
    total_taxable = annual_taxable_net * years

    winner = "muni" if annual_muni_income > annual_taxable_net else "taxable"
    advantage = abs(total_muni - total_taxable)

    return {
        "muni_annual_income": round(annual_muni_income, 2),
        "taxable_annual_after_tax": round(annual_taxable_net, 2),
        "taxable_annual_tax_paid": round(annual_taxable_gross - annual_taxable_net, 2),
        "winner": winner,
        "annual_advantage": round(abs(annual_muni_income - annual_taxable_net), 2),
        "cumulative_advantage_over_years": round(advantage, 2),
        "years": years,
        "investment": investment,
        "muni_ratio": round(muni_yield / taxable_yield, 4) if taxable_yield else None,
    }


def screen_muni_bonds(
    states: list[str] | None = None,
    min_yield: float | None = None,
    max_maturity_years: float | None = None,
    min_rating: str = "BBB-",
    limit: int = 20,
) -> dict[str, Any]:
    """
    Screen synthetic municipal bond universe.

    Args:
        states: Filter by issuing states.
        min_yield: Minimum coupon yield.
        max_maturity_years: Maximum years to maturity.
        min_rating: Minimum credit rating.
        limit: Max results.

    Returns:
        Filtered muni bond list with TEY calculations.
    """
    import random
    rng = random.Random(99)

    rating_order = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"]
    min_idx = rating_order.index(min_rating) if min_rating in rating_order else len(rating_order) - 1
    valid_ratings = rating_order[:min_idx + 1]

    all_states = list(STATE_TAX_RATES.keys())
    bonds = []
    for i in range(150):
        st = rng.choice(all_states)
        rating = rng.choice(valid_ratings)
        yrs = round(rng.uniform(1, 30), 1)
        coupon = round(rng.uniform(2.0, 5.5), 3)
        bonds.append({
            "issuer": f"{st}_Muni_{i:03d}",
            "state": st,
            "rating": rating,
            "coupon": coupon,
            "years_to_maturity": yrs,
            "tax_exempt": True,
        })

    if states:
        states_upper = [s.upper() for s in states]
        bonds = [b for b in bonds if b["state"] in states_upper]
    if min_yield is not None:
        bonds = [b for b in bonds if b["coupon"] >= min_yield]
    if max_maturity_years is not None:
        bonds = [b for b in bonds if b["years_to_maturity"] <= max_maturity_years]

    # Add TEY for high-tax state
    for b in bonds:
        teq = tax_equivalent_yield(b["coupon"], state=b["state"])
        b["tax_equivalent_yield"] = teq["tax_equivalent_yield_pct"]

    bonds.sort(key=lambda b: b["tax_equivalent_yield"], reverse=True)
    return {"total_matches": len(bonds), "bonds": bonds[:limit]}
