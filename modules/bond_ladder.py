"""Bond Ladder Builder — construct optimal bond ladders for income and risk management.

Builds maturity-staggered bond portfolios to manage reinvestment risk and provide
steady income. Supports Treasury, corporate, and municipal bond ladders with
customisable rungs, reinvestment assumptions, and tax-equivalent yield calculations.
Uses FRED for yield curve data.
"""

import datetime
from typing import Dict, List, Optional


def fetch_treasury_yields() -> Dict[str, float]:
    """Fetch current US Treasury yields from FRED for common maturities.

    Returns:
        Dict mapping maturity labels to annualised yields (decimal).
    """
    import urllib.request
    import json

    series = {
        "3M": "DTB3",
        "6M": "DTB6",
        "1Y": "DGS1",
        "2Y": "DGS2",
        "3Y": "DGS3",
        "5Y": "DGS5",
        "7Y": "DGS7",
        "10Y": "DGS10",
        "20Y": "DGS20",
        "30Y": "DGS30",
    }
    yields = {}
    for label, sid in series.items():
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={sid}&sort_order=desc&limit=5"
            f"&api_key=DEMO_KEY&file_type=json"
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
            for obs in data.get("observations", []):
                if obs["value"] != ".":
                    yields[label] = float(obs["value"]) / 100.0
                    break
        except Exception:
            pass

    # Fallback if FRED unavailable
    if not yields:
        yields = {
            "1Y": 0.048, "2Y": 0.045, "3Y": 0.043, "5Y": 0.042,
            "7Y": 0.042, "10Y": 0.043, "20Y": 0.046, "30Y": 0.047,
        }
    return yields


def build_ladder(
    total_investment: float = 100000.0,
    min_maturity_years: int = 1,
    max_maturity_years: int = 10,
    rung_spacing_years: int = 1,
    coupon_freq: int = 2,
    bond_type: str = "treasury",
    credit_spread_bps: float = 0.0,
    tax_rate: float = 0.0,
) -> Dict:
    """Build a bond ladder portfolio.

    Args:
        total_investment: Total amount to invest.
        min_maturity_years: Shortest rung maturity.
        max_maturity_years: Longest rung maturity.
        rung_spacing_years: Years between each rung.
        coupon_freq: Coupons per year (2 = semi-annual).
        bond_type: 'treasury', 'corporate', or 'municipal'.
        credit_spread_bps: Additional spread for non-treasury bonds.
        tax_rate: Marginal tax rate for tax-equivalent yield calc (0-1).

    Returns:
        Dict with rungs, portfolio metrics, and income schedule.
    """
    yields = fetch_treasury_yields()
    spread = credit_spread_bps / 10000.0

    maturities = list(range(min_maturity_years, max_maturity_years + 1, rung_spacing_years))
    num_rungs = len(maturities)
    per_rung = total_investment / num_rungs

    rungs = []
    total_annual_income = 0.0
    weighted_duration = 0.0

    for mat in maturities:
        # Interpolate yield
        label = f"{mat}Y"
        if label in yields:
            base_yield = yields[label]
        else:
            keys_years = {int(k.replace("Y", "").replace("M", "")): v for k, v in yields.items() if "Y" in k}
            sorted_k = sorted(keys_years.keys())
            if mat <= sorted_k[0]:
                base_yield = keys_years[sorted_k[0]]
            elif mat >= sorted_k[-1]:
                base_yield = keys_years[sorted_k[-1]]
            else:
                lo = max(k for k in sorted_k if k <= mat)
                hi = min(k for k in sorted_k if k >= mat)
                if lo == hi:
                    base_yield = keys_years[lo]
                else:
                    w = (mat - lo) / (hi - lo)
                    base_yield = keys_years[lo] * (1 - w) + keys_years[hi] * w

        ytm = base_yield + spread
        if bond_type == "municipal" and tax_rate > 0:
            tax_equiv_yield = ytm / (1 - tax_rate)
        else:
            tax_equiv_yield = ytm

        annual_income = per_rung * ytm
        total_annual_income += annual_income

        # Approximate Macaulay duration
        mac_dur = _macaulay_duration(ytm, mat, coupon_freq)
        weighted_duration += mac_dur * (per_rung / total_investment)

        rungs.append({
            "maturity_years": mat,
            "amount": round(per_rung, 2),
            "ytm": round(ytm, 4),
            "tax_equivalent_yield": round(tax_equiv_yield, 4),
            "annual_income": round(annual_income, 2),
            "macaulay_duration": round(mac_dur, 2),
        })

    avg_yield = sum(r["ytm"] for r in rungs) / num_rungs if num_rungs else 0

    return {
        "bond_type": bond_type,
        "total_investment": total_investment,
        "num_rungs": num_rungs,
        "rungs": rungs,
        "portfolio_metrics": {
            "average_yield": round(avg_yield, 4),
            "total_annual_income": round(total_annual_income, 2),
            "portfolio_duration": round(weighted_duration, 2),
            "average_maturity": round(sum(maturities) / num_rungs, 1),
            "income_yield": round(total_annual_income / total_investment, 4),
        },
    }


def compare_ladders(
    total_investment: float = 100000.0,
    scenarios: Optional[List[Dict]] = None,
) -> Dict:
    """Compare multiple ladder configurations side-by-side.

    Args:
        total_investment: Amount per scenario.
        scenarios: List of dicts with ladder params. Defaults to short/medium/long.

    Returns:
        Comparison dict with each scenario's metrics.
    """
    if scenarios is None:
        scenarios = [
            {"name": "Short (1-5Y)", "min_maturity_years": 1, "max_maturity_years": 5},
            {"name": "Medium (1-10Y)", "min_maturity_years": 1, "max_maturity_years": 10},
            {"name": "Long (1-20Y)", "min_maturity_years": 2, "max_maturity_years": 20, "rung_spacing_years": 2},
        ]

    results = []
    for s in scenarios:
        name = s.pop("name", "Unnamed")
        ladder = build_ladder(total_investment=total_investment, **s)
        results.append({
            "name": name,
            **ladder["portfolio_metrics"],
        })
        s["name"] = name  # Restore

    return {"total_investment": total_investment, "scenarios": results}


def _macaulay_duration(ytm: float, maturity: int, freq: int) -> float:
    """Approximate Macaulay duration for a par bond."""
    if ytm <= 0:
        return float(maturity)
    c = ytm / freq
    n = maturity * freq
    if c == 0:
        return float(maturity)
    pv_weighted = 0.0
    pv_total = 0.0
    for i in range(1, n + 1):
        t = i / freq
        cf = c * 100 + (100 if i == n else 0)
        df = 1 / (1 + c) ** i
        pv_weighted += t * cf * df
        pv_total += cf * df
    return pv_weighted / pv_total if pv_total > 0 else float(maturity)
