"""Duration & Convexity Calculator — comprehensive bond risk metrics.

Computes Macaulay duration, modified duration, effective duration, dollar duration,
DV01, convexity, and price sensitivity for any fixed-coupon bond. Supports
price-change estimation under parallel yield shifts.
"""

import math
from typing import Dict, List, Optional


def bond_cash_flows(
    face: float,
    coupon_rate: float,
    maturity_years: float,
    freq: int = 2,
) -> List[Dict]:
    """Generate bond cash flow schedule.

    Args:
        face: Face/par value.
        coupon_rate: Annual coupon rate (decimal).
        maturity_years: Years to maturity.
        freq: Coupon payments per year.

    Returns:
        List of dicts with period, time, coupon, principal, total.
    """
    periods = int(maturity_years * freq)
    coupon = face * coupon_rate / freq
    flows = []
    for i in range(1, periods + 1):
        t = i / freq
        prin = face if i == periods else 0.0
        flows.append({
            "period": i,
            "time_years": round(t, 4),
            "coupon": round(coupon, 4),
            "principal": prin,
            "total": round(coupon + prin, 4),
        })
    return flows


def calculate_duration_convexity(
    face: float = 100.0,
    coupon_rate: float = 0.05,
    ytm: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
) -> Dict:
    """Calculate full suite of duration and convexity metrics.

    Args:
        face: Face value.
        coupon_rate: Annual coupon rate (decimal).
        ytm: Yield to maturity (decimal).
        maturity_years: Years to maturity.
        freq: Payments per year.

    Returns:
        Dict with macaulay_duration, modified_duration, effective_duration,
        dollar_duration, dv01, convexity, and price.
    """
    flows = bond_cash_flows(face, coupon_rate, maturity_years, freq)
    y = ytm / freq
    n = len(flows)

    price = 0.0
    mac_num = 0.0
    conv_num = 0.0

    for cf in flows:
        i = cf["period"]
        t = cf["time_years"]
        total = cf["total"]
        df = 1.0 / (1.0 + y) ** i
        pv = total * df

        price += pv
        mac_num += t * pv
        conv_num += (i * (i + 1)) * total * df

    mac_dur = mac_num / price if price > 0 else 0.0
    mod_dur = mac_dur / (1.0 + y) if (1.0 + y) != 0 else 0.0
    dollar_dur = mod_dur * price / 100.0
    dv01 = mod_dur * price / 10000.0
    convexity = conv_num / (price * freq * freq) if price > 0 else 0.0

    # Effective duration via full repricing
    shift = 0.0001
    p_up = _reprice(flows, ytm + shift, freq)
    p_down = _reprice(flows, ytm - shift, freq)
    eff_dur = (p_down - p_up) / (2.0 * shift * price) if price > 0 else 0.0

    return {
        "price": round(price, 4),
        "macaulay_duration": round(mac_dur, 4),
        "modified_duration": round(mod_dur, 4),
        "effective_duration": round(eff_dur, 4),
        "dollar_duration": round(dollar_dur, 4),
        "dv01": round(dv01, 4),
        "convexity": round(convexity, 4),
        "coupon_rate": coupon_rate,
        "ytm": ytm,
        "maturity_years": maturity_years,
        "face": face,
    }


def price_change_estimate(
    face: float = 100.0,
    coupon_rate: float = 0.05,
    ytm: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
    yield_changes_bps: Optional[List[float]] = None,
) -> Dict:
    """Estimate price changes for various yield shifts using duration + convexity.

    Args:
        yield_changes_bps: List of yield changes in basis points. Defaults to standard set.

    Returns:
        Dict with metrics and scenario table.
    """
    if yield_changes_bps is None:
        yield_changes_bps = [-100, -50, -25, -10, 10, 25, 50, 100]

    metrics = calculate_duration_convexity(face, coupon_rate, ytm, maturity_years, freq)
    price = metrics["price"]
    mod_dur = metrics["modified_duration"]
    conv = metrics["convexity"]
    flows = bond_cash_flows(face, coupon_rate, maturity_years, freq)

    scenarios = []
    for bps in yield_changes_bps:
        dy = bps / 10000.0
        # Duration-only estimate
        dur_pct = -mod_dur * dy
        # Duration + convexity estimate
        durconv_pct = -mod_dur * dy + 0.5 * conv * dy * dy
        # Exact repricing
        exact_price = _reprice(flows, ytm + dy, freq)
        exact_pct = (exact_price - price) / price

        scenarios.append({
            "yield_change_bps": bps,
            "duration_estimate_pct": round(dur_pct * 100, 4),
            "dur_convexity_estimate_pct": round(durconv_pct * 100, 4),
            "exact_change_pct": round(exact_pct * 100, 4),
            "exact_new_price": round(exact_price, 4),
            "convexity_gain": round((durconv_pct - dur_pct) * 100, 4),
        })

    return {
        **metrics,
        "scenarios": scenarios,
    }


def _reprice(flows: List[Dict], ytm: float, freq: int) -> float:
    """Reprice bond given flows and new YTM."""
    y = ytm / freq
    return sum(cf["total"] / (1.0 + y) ** cf["period"] for cf in flows)
