"""
OAS (Option-Adjusted Spread) and Z-Spread Calculator for fixed income securities.

Computes Z-spread (zero-volatility spread) over the Treasury curve and
OAS for bonds with embedded options. Essential for relative value analysis
in corporate and mortgage-backed securities.

Free data: Treasury yields from FRED, bond parameters from user input.
"""

import math
from typing import Dict, List, Optional, Tuple


def calculate_z_spread(
    bond_price: float,
    coupon_rate: float,
    face_value: float,
    maturity_years: float,
    treasury_rates: List[float],
    frequency: int = 2
) -> Dict:
    """
    Calculate Z-spread over the Treasury zero curve.

    Args:
        bond_price: Current market price (dirty price)
        coupon_rate: Annual coupon rate (e.g., 0.05 for 5%)
        face_value: Par value (typically 100)
        maturity_years: Years to maturity
        treasury_rates: Zero-coupon Treasury rates for each period
        frequency: Coupon frequency per year (1=annual, 2=semi)

    Returns:
        Dict with z_spread, present values, and convergence info
    """
    n_periods = int(maturity_years * frequency)
    coupon = face_value * coupon_rate / frequency

    # Extend treasury rates if needed
    rates = list(treasury_rates)
    while len(rates) < n_periods:
        rates.append(rates[-1] if rates else 0.03)

    # Newton-Raphson to find z-spread
    z = 0.01  # initial guess 100bps
    for iteration in range(200):
        pv = 0.0
        dpv = 0.0  # derivative w.r.t. z

        for t in range(1, n_periods + 1):
            r = rates[t - 1] / frequency
            discount_rate = r + z / frequency
            period_cf = coupon if t < n_periods else coupon + face_value

            if 1 + discount_rate <= 0:
                break

            df = (1 + discount_rate) ** (-t)
            pv += period_cf * df
            dpv += period_cf * (-t / frequency) * (1 + discount_rate) ** (-t - 1)

        diff = pv - bond_price
        if abs(diff) < 1e-8:
            break

        if abs(dpv) < 1e-12:
            break

        z = z - diff / dpv

    # Final PV breakdown
    cashflows = []
    total_pv = 0.0
    for t in range(1, n_periods + 1):
        r = rates[t - 1] / frequency
        discount_rate = r + z / frequency
        period_cf = coupon if t < n_periods else coupon + face_value
        df = (1 + discount_rate) ** (-t)
        cf_pv = period_cf * df
        total_pv += cf_pv
        cashflows.append({
            "period": t,
            "year": round(t / frequency, 2),
            "cashflow": round(period_cf, 4),
            "treasury_rate": round(rates[t - 1], 6),
            "discount_rate": round(rates[t - 1] + z, 6),
            "present_value": round(cf_pv, 4)
        })

    return {
        "z_spread_bps": round(z * 10000, 2),
        "z_spread_decimal": round(z, 6),
        "bond_price": bond_price,
        "calculated_price": round(total_pv, 4),
        "pricing_error": round(abs(total_pv - bond_price), 6),
        "coupon_rate": coupon_rate,
        "maturity_years": maturity_years,
        "n_periods": n_periods,
        "cashflows": cashflows
    }


def calculate_oas(
    bond_price: float,
    coupon_rate: float,
    face_value: float,
    maturity_years: float,
    treasury_rates: List[float],
    volatility: float = 0.15,
    is_callable: bool = True,
    call_price: float = 100.0,
    call_date_years: float = 3.0,
    frequency: int = 2,
    n_paths: int = 1000
) -> Dict:
    """
    Calculate Option-Adjusted Spread using Monte Carlo simulation.

    Args:
        bond_price: Current market price
        coupon_rate: Annual coupon rate
        face_value: Par value
        maturity_years: Years to maturity
        treasury_rates: Zero-coupon Treasury rates
        volatility: Interest rate volatility for simulation
        is_callable: Whether bond has call option
        call_price: Call strike price
        call_date_years: First call date
        frequency: Coupon frequency
        n_paths: Number of simulation paths

    Returns:
        Dict with OAS, option value, and comparison to Z-spread
    """
    import random

    z_result = calculate_z_spread(
        bond_price, coupon_rate, face_value,
        maturity_years, treasury_rates, frequency
    )
    z_spread = z_result["z_spread_decimal"]

    n_periods = int(maturity_years * frequency)
    coupon = face_value * coupon_rate / frequency
    call_period = int(call_date_years * frequency)

    rates = list(treasury_rates)
    while len(rates) < n_periods:
        rates.append(rates[-1] if rates else 0.03)

    # Monte Carlo: find OAS such that avg simulated price = market price
    random.seed(42)
    oas = z_spread  # start from z-spread

    for oas_iter in range(100):
        total_pv = 0.0

        for path in range(n_paths):
            path_pv = 0.0
            called = False

            for t in range(1, n_periods + 1):
                # Simulate rate shock
                shock = random.gauss(0, volatility / math.sqrt(frequency))
                sim_rate = max(rates[t - 1] + shock, 0.001)
                discount = sim_rate + oas

                cf = coupon
                if t == n_periods and not called:
                    cf += face_value

                # Check call
                if is_callable and t >= call_period and not called:
                    # Simple call rule: call if bond value > call price
                    remaining_pv = 0.0
                    for s in range(t + 1, n_periods + 1):
                        s_cf = coupon if s < n_periods else coupon + face_value
                        s_r = rates[min(s - 1, len(rates) - 1)] + oas
                        remaining_pv += s_cf / (1 + s_r / frequency) ** (s - t)
                    remaining_pv += coupon  # current coupon

                    if remaining_pv > call_price * 1.02:
                        cf = coupon + call_price
                        called = True

                df = (1 + discount / frequency) ** (-t)
                path_pv += cf * df

                if called:
                    break

            total_pv += path_pv

        avg_price = total_pv / n_paths
        diff = avg_price - bond_price

        if abs(diff) < 0.01:
            break

        oas -= diff * 0.0001  # simple gradient step

    option_value_bps = round((z_spread - oas) * 10000, 2)

    return {
        "oas_bps": round(oas * 10000, 2),
        "oas_decimal": round(oas, 6),
        "z_spread_bps": z_result["z_spread_bps"],
        "option_value_bps": option_value_bps,
        "bond_price": bond_price,
        "is_callable": is_callable,
        "call_price": call_price,
        "call_date_years": call_date_years,
        "volatility_assumption": volatility,
        "n_simulation_paths": n_paths,
        "interpretation": (
            f"OAS of {round(oas * 10000, 2)}bps vs Z-spread of {z_result['z_spread_bps']}bps. "
            f"Option cost is {option_value_bps}bps."
        )
    }


def spread_relative_value(bonds: List[Dict]) -> Dict:
    """
    Compare multiple bonds on spread metrics for relative value.

    Args:
        bonds: List of dicts with keys: name, z_spread_bps, oas_bps,
               rating, maturity_years, coupon_rate

    Returns:
        Dict with ranked bonds and spread analysis
    """
    if not bonds:
        return {"error": "No bonds provided"}

    avg_z = sum(b.get("z_spread_bps", 0) for b in bonds) / len(bonds)
    avg_oas = sum(b.get("oas_bps", 0) for b in bonds) / len(bonds)

    ranked = []
    for b in bonds:
        z = b.get("z_spread_bps", 0)
        o = b.get("oas_bps", 0)
        ranked.append({
            **b,
            "z_spread_vs_avg": round(z - avg_z, 2),
            "oas_vs_avg": round(o - avg_oas, 2),
            "option_cost_bps": round(z - o, 2),
            "rich_cheap": "CHEAP" if o > avg_oas * 1.1 else "RICH" if o < avg_oas * 0.9 else "FAIR"
        })

    ranked.sort(key=lambda x: x.get("oas_bps", 0), reverse=True)

    return {
        "n_bonds": len(bonds),
        "average_z_spread": round(avg_z, 2),
        "average_oas": round(avg_oas, 2),
        "bonds_ranked_by_oas": ranked,
        "widest_spread": ranked[0]["name"] if ranked else None,
        "tightest_spread": ranked[-1]["name"] if ranked else None
    }
