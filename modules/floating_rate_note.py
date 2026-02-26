"""Floating Rate Note (FRN) Pricer — value FRNs using discount margin analysis.

Prices floating rate notes by projecting coupon cash flows from a reference rate
(SOFR, EURIBOR, etc.) plus a quoted margin, then discounting at the reference rate
plus a discount margin. Uses FRED for benchmark rate data.
"""

import datetime
import math
from typing import Dict, List, Optional


def fetch_reference_rate(rate_id: str = "SOFR") -> float:
    """Fetch current reference rate from FRED.

    Args:
        rate_id: FRED series ID — SOFR, FEDFUNDS, USD3MTD156N (3M LIBOR proxy), etc.

    Returns:
        Current annualised rate as a decimal (e.g. 0.053 for 5.3%).
    """
    import urllib.request
    import json

    series_map = {
        "SOFR": "SOFR",
        "FEDFUNDS": "FEDFUNDS",
        "EURIBOR3M": "IR3TIB01EZM156N",
        "TBILL3M": "DTB3",
    }
    series = series_map.get(rate_id.upper(), rate_id)
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series}&sort_order=desc&limit=5"
        f"&api_key=DEMO_KEY&file_type=json"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        for obs in data.get("observations", []):
            if obs["value"] != ".":
                return float(obs["value"]) / 100.0
    except Exception:
        pass
    # Fallback defaults
    defaults = {"SOFR": 0.053, "FEDFUNDS": 0.053, "EURIBOR3M": 0.038, "TBILL3M": 0.052}
    return defaults.get(rate_id.upper(), 0.05)


def price_frn(
    face: float = 100.0,
    quoted_margin_bps: float = 50.0,
    discount_margin_bps: float = 50.0,
    reference_rate: Optional[float] = None,
    maturity_years: float = 3.0,
    coupon_freq: int = 4,
    rate_id: str = "SOFR",
) -> Dict:
    """Price a floating rate note using discount margin methodology.

    Args:
        face: Par/face value.
        quoted_margin_bps: Quoted spread over reference rate in basis points.
        discount_margin_bps: Discount (required) margin in basis points.
        reference_rate: Override reference rate (decimal). If None, fetched live.
        maturity_years: Years to maturity.
        coupon_freq: Coupon payments per year (4 = quarterly).
        rate_id: Reference rate identifier for live fetch.

    Returns:
        Dict with clean_price, accrued_interest, dirty_price, current_yield,
        effective_duration, and cash_flow_schedule.
    """
    if reference_rate is None:
        reference_rate = fetch_reference_rate(rate_id)

    qm = quoted_margin_bps / 10000.0
    dm = discount_margin_bps / 10000.0
    periods = int(maturity_years * coupon_freq)
    period_rate = (reference_rate + qm) / coupon_freq
    discount_rate = (reference_rate + dm) / coupon_freq

    pv = 0.0
    cash_flows = []
    for i in range(1, periods + 1):
        coupon = face * period_rate
        cf = coupon + (face if i == periods else 0.0)
        df = 1.0 / ((1.0 + discount_rate) ** i)
        pv += cf * df
        cash_flows.append({
            "period": i,
            "time_years": round(i / coupon_freq, 4),
            "coupon": round(coupon, 4),
            "principal": face if i == periods else 0.0,
            "total_cf": round(cf, 4),
            "discount_factor": round(df, 6),
            "pv": round(cf * df, 4),
        })

    clean_price = round(pv, 4)
    annual_coupon = face * (reference_rate + qm)
    current_yield = round(annual_coupon / clean_price, 6) if clean_price > 0 else 0.0

    # Effective duration via DM shift
    shift = 0.0001
    pv_up = sum(
        cf["total_cf"] / ((1 + (reference_rate + dm + shift) / coupon_freq) ** cf["period"])
        for cf in cash_flows
    )
    pv_down = sum(
        cf["total_cf"] / ((1 + (reference_rate + dm - shift) / coupon_freq) ** cf["period"])
        for cf in cash_flows
    )
    eff_duration = round((pv_down - pv_up) / (2 * shift * pv), 4) if pv > 0 else 0.0

    return {
        "clean_price": clean_price,
        "dirty_price": clean_price,  # At reset date, no accrued
        "accrued_interest": 0.0,
        "reference_rate": round(reference_rate, 6),
        "quoted_margin_bps": quoted_margin_bps,
        "discount_margin_bps": discount_margin_bps,
        "annual_coupon_rate": round(reference_rate + qm, 6),
        "current_yield": current_yield,
        "effective_duration": eff_duration,
        "periods": periods,
        "cash_flows": cash_flows[:5],  # First 5 for brevity
    }


def discount_margin_solver(
    market_price: float,
    face: float = 100.0,
    quoted_margin_bps: float = 50.0,
    reference_rate: Optional[float] = None,
    maturity_years: float = 3.0,
    coupon_freq: int = 4,
    rate_id: str = "SOFR",
    tolerance: float = 0.0001,
    max_iter: int = 100,
) -> Dict:
    """Solve for the discount margin given a market price (Newton-Raphson).

    Returns:
        Dict with discount_margin_bps, iterations, converged flag.
    """
    if reference_rate is None:
        reference_rate = fetch_reference_rate(rate_id)

    qm = quoted_margin_bps / 10000.0
    periods = int(maturity_years * coupon_freq)
    period_coupon = face * (reference_rate + qm) / coupon_freq

    dm_guess = qm  # Start at quoted margin

    for iteration in range(max_iter):
        dr = (reference_rate + dm_guess) / coupon_freq
        pv = 0.0
        dpv = 0.0
        for i in range(1, periods + 1):
            cf = period_coupon + (face if i == periods else 0.0)
            denom = (1 + dr) ** i
            pv += cf / denom
            dpv -= i * cf / (coupon_freq * denom * (1 + dr))

        diff = pv - market_price
        if abs(diff) < tolerance:
            return {
                "discount_margin_bps": round(dm_guess * 10000, 2),
                "implied_price": round(pv, 4),
                "iterations": iteration + 1,
                "converged": True,
                "reference_rate": round(reference_rate, 6),
            }
        if abs(dpv) < 1e-12:
            break
        dm_guess -= diff / dpv

    return {
        "discount_margin_bps": round(dm_guess * 10000, 2),
        "iterations": max_iter,
        "converged": False,
        "reference_rate": round(reference_rate, 6),
    }
