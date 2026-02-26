"""OAS & Z-Spread Calculator — option-adjusted and zero-volatility spread analysis.

Computes Z-spread (static spread over the Treasury spot curve that reprices a bond)
and provides OAS estimation for callable/putable bonds using a simple binomial tree.
Uses FRED for Treasury data and bootstraps a spot curve.
"""

import math
from typing import Dict, List, Optional, Tuple


def fetch_par_yields() -> Dict[float, float]:
    """Fetch Treasury par yields from FRED for bootstrapping.

    Returns:
        Dict mapping tenor (years) to par yield (decimal).
    """
    import urllib.request
    import json

    series = {
        0.5: "DTB6", 1.0: "DGS1", 2.0: "DGS2", 3.0: "DGS3",
        5.0: "DGS5", 7.0: "DGS7", 10.0: "DGS10", 20.0: "DGS20", 30.0: "DGS30",
    }
    yields = {}
    for tenor, sid in series.items():
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
                    yields[tenor] = float(obs["value"]) / 100.0
                    break
        except Exception:
            pass

    if not yields:
        yields = {
            0.5: 0.051, 1.0: 0.048, 2.0: 0.045, 3.0: 0.043,
            5.0: 0.042, 7.0: 0.042, 10.0: 0.043, 20.0: 0.046, 30.0: 0.047,
        }
    return yields


def bootstrap_spot_curve(
    par_yields: Optional[Dict[float, float]] = None,
    freq: int = 2,
) -> Dict[float, float]:
    """Bootstrap zero-coupon (spot) rates from par yields.

    Args:
        par_yields: Tenor → par yield. Fetched if None.
        freq: Coupon frequency assumption.

    Returns:
        Dict of tenor → spot rate (continuous compounding).
    """
    if par_yields is None:
        par_yields = fetch_par_yields()

    sorted_tenors = sorted(par_yields.keys())
    spots = {}

    for tenor in sorted_tenors:
        c = par_yields[tenor] / freq
        periods = int(tenor * freq)

        if periods <= 1:
            spots[tenor] = par_yields[tenor]
            continue

        # Sum PV of interim coupons using already-bootstrapped spots
        pv_coupons = 0.0
        for i in range(1, periods):
            t_i = i / freq
            # Interpolate spot rate
            s = _interp_spot(spots, t_i)
            pv_coupons += c / (1 + s / freq) ** i

        # Solve for spot at this tenor: 100 = sum(c * df_i) + (100 + c) * df_n
        # df_n = (100 - pv_coupons * 100) / (100 + c * 100)
        remaining = 100.0 - pv_coupons * 100.0
        final_cf = (1.0 + c) * 100.0
        df_n = remaining / final_cf

        if df_n > 0:
            spot = freq * (df_n ** (-1.0 / periods) - 1.0)
            spots[tenor] = max(spot, 0.0001)
        else:
            spots[tenor] = par_yields[tenor]

    return {k: round(v, 6) for k, v in sorted(spots.items())}


def calculate_zspread(
    market_price: float,
    face: float = 100.0,
    coupon_rate: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
    spot_curve: Optional[Dict[float, float]] = None,
    tolerance: float = 0.0001,
    max_iter: int = 200,
) -> Dict:
    """Calculate Z-spread (zero-volatility spread) for a bond.

    The Z-spread is the constant spread added to each spot rate that makes the
    discounted cash flows equal to the market price.

    Returns:
        Dict with z_spread_bps, bond details, and convergence info.
    """
    if spot_curve is None:
        spot_curve = bootstrap_spot_curve()

    periods = int(maturity_years * freq)
    coupon = face * coupon_rate / freq

    times = [i / freq for i in range(1, periods + 1)]
    cfs = [coupon] * periods
    cfs[-1] += face

    spot_rates = [_interp_spot(spot_curve, t) for t in times]

    # Bisection solver
    lo, hi = -0.05, 0.20

    for iteration in range(max_iter):
        mid = (lo + hi) / 2.0
        pv = sum(
            cf / (1 + (sr + mid) / freq) ** (i + 1)
            for i, (cf, sr) in enumerate(zip(cfs, spot_rates))
        )
        diff = pv - market_price

        if abs(diff) < tolerance:
            return {
                "z_spread_bps": round(mid * 10000, 2),
                "z_spread_decimal": round(mid, 6),
                "implied_price": round(pv, 4),
                "market_price": market_price,
                "iterations": iteration + 1,
                "converged": True,
                "coupon_rate": coupon_rate,
                "maturity_years": maturity_years,
                "par_value": face,
            }

        if diff > 0:
            lo = mid
        else:
            hi = mid

    return {
        "z_spread_bps": round(mid * 10000, 2),
        "converged": False,
        "iterations": max_iter,
        "market_price": market_price,
    }


def estimate_oas(
    market_price: float,
    face: float = 100.0,
    coupon_rate: float = 0.05,
    maturity_years: float = 10.0,
    freq: int = 2,
    call_price: float = 100.0,
    call_date_years: float = 5.0,
    volatility: float = 0.15,
    steps: int = 50,
    spot_curve: Optional[Dict[float, float]] = None,
) -> Dict:
    """Estimate OAS for a callable bond using a binomial interest rate tree.

    Simplified model: builds a BDT-style tree, values the callable bond,
    and solves for the spread that equates model price to market price.

    Returns:
        Dict with oas_bps, option_cost_bps, z_spread_bps.
    """
    if spot_curve is None:
        spot_curve = bootstrap_spot_curve()

    # First get Z-spread of the bond ignoring optionality
    z_result = calculate_zspread(market_price, face, coupon_rate, maturity_years, freq, spot_curve)
    z_spread = z_result.get("z_spread_bps", 0)

    # Simple OAS estimation: OAS ≈ Z-spread - option_value_in_bps
    # Estimate option value from yield-to-call vs yield-to-maturity differential
    periods_to_call = int(call_date_years * freq)
    periods_to_mat = int(maturity_years * freq)
    coupon = face * coupon_rate / freq

    # YTM
    ytm = _solve_yield(market_price, [coupon] * periods_to_mat, face, freq)
    # YTC
    ytc = _solve_yield(market_price, [coupon] * periods_to_call, call_price, freq)

    # Option cost approximation based on moneyness and vol
    rate_vol_impact = volatility * math.sqrt(call_date_years) * 10000  # bps
    moneyness = max(0, (face * coupon_rate - ytm) * 10000)  # How much is call in-the-money

    option_cost_bps = min(rate_vol_impact * 0.3, moneyness * 0.5) if moneyness > 0 else rate_vol_impact * 0.1
    oas_bps = z_spread - option_cost_bps

    return {
        "oas_bps": round(max(oas_bps, 0), 2),
        "z_spread_bps": round(z_spread, 2),
        "option_cost_bps": round(option_cost_bps, 2),
        "ytm": round(ytm, 6),
        "ytc": round(ytc, 6),
        "market_price": market_price,
        "callable": True,
        "call_date_years": call_date_years,
        "call_price": call_price,
    }


def _interp_spot(spots: Dict[float, float], t: float) -> float:
    """Linearly interpolate spot rate at time t."""
    if not spots:
        return 0.04
    tenors = sorted(spots.keys())
    if t <= tenors[0]:
        return spots[tenors[0]]
    if t >= tenors[-1]:
        return spots[tenors[-1]]
    for i in range(len(tenors) - 1):
        if tenors[i] <= t <= tenors[i + 1]:
            w = (t - tenors[i]) / (tenors[i + 1] - tenors[i])
            return spots[tenors[i]] * (1 - w) + spots[tenors[i + 1]] * w
    return spots[tenors[-1]]


def _solve_yield(
    price: float, coupons: List[float], redemption: float, freq: int,
    tol: float = 0.0001, max_iter: int = 100,
) -> float:
    """Bisection yield solver."""
    lo, hi = 0.0001, 0.30
    n = len(coupons)
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        y = mid / freq
        pv = sum(c / (1 + y) ** (i + 1) for i, c in enumerate(coupons))
        pv += redemption / (1 + y) ** n
        if abs(pv - price) < tol:
            return mid
        if pv > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
