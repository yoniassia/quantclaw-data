"""
Convertible Bond Arbitrage Scanner — Identify convertible bond mispricings
by comparing market price to theoretical value using simplified Black-Scholes
based convertible pricing.

Roadmap item #345: Convertible Bond Arbitrage Scanner
"""

import math
from typing import Any


def _norm_cdf(x: float) -> float:
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def price_convertible(
    par: float = 1000,
    coupon_rate: float = 2.0,
    years_to_maturity: float = 5.0,
    conversion_ratio: float = 20.0,
    stock_price: float = 45.0,
    stock_volatility: float = 0.35,
    risk_free_rate: float = 4.5,
    credit_spread_bps: float = 200,
    dividend_yield: float = 0.0,
) -> dict[str, Any]:
    """
    Price a convertible bond using a simplified model combining bond floor
    and equity option value.

    Args:
        par: Par value of bond.
        coupon_rate: Annual coupon rate %.
        years_to_maturity: Years to maturity.
        conversion_ratio: Number of shares per bond.
        stock_price: Current stock price.
        stock_volatility: Annual stock volatility (decimal).
        risk_free_rate: Risk-free rate %.
        credit_spread_bps: Issuer credit spread in bps.
        dividend_yield: Annual dividend yield (decimal).

    Returns:
        Dict with theoretical price, bond floor, option value, greeks.
    """
    rf = risk_free_rate / 100
    cs = credit_spread_bps / 10000
    coupon = par * (coupon_rate / 100)
    T = years_to_maturity

    # Bond floor (straight bond value)
    discount_rate = rf + cs
    bond_floor = 0
    for t in range(1, int(T) + 1):
        bond_floor += coupon / (1 + discount_rate) ** t
    bond_floor += par / (1 + discount_rate) ** T

    # Conversion value
    conversion_value = conversion_ratio * stock_price

    # Option component (Black-Scholes on conversion right)
    strike = par / conversion_ratio  # effective strike per share
    d1 = (math.log(stock_price / strike) + (rf - dividend_yield + 0.5 * stock_volatility ** 2) * T) / (stock_volatility * math.sqrt(T))
    d2 = d1 - stock_volatility * math.sqrt(T)

    call_per_share = (stock_price * math.exp(-dividend_yield * T) * _norm_cdf(d1)
                      - strike * math.exp(-rf * T) * _norm_cdf(d2))
    option_value = call_per_share * conversion_ratio

    theoretical_price = bond_floor + option_value

    # Greeks
    delta = _norm_cdf(d1) * conversion_ratio / par  # per $1 of par
    gamma = (math.exp(-d1 ** 2 / 2) / (math.sqrt(2 * math.pi))
             / (stock_price * stock_volatility * math.sqrt(T))
             * conversion_ratio / par)
    vega = (stock_price * math.exp(-dividend_yield * T)
            * math.exp(-d1 ** 2 / 2) / math.sqrt(2 * math.pi)
            * math.sqrt(T) * conversion_ratio / 100)  # per 1% vol change

    return {
        "theoretical_price": round(theoretical_price, 2),
        "bond_floor": round(bond_floor, 2),
        "conversion_value": round(conversion_value, 2),
        "option_value": round(option_value, 2),
        "parity": round(conversion_value / par * 100, 2),
        "premium_over_parity_pct": round((theoretical_price / conversion_value - 1) * 100, 2) if conversion_value > 0 else None,
        "premium_over_bond_floor_pct": round((theoretical_price / bond_floor - 1) * 100, 2),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "vega": round(vega, 2),
        "effective_strike": round(strike, 2),
    }


def scan_arbitrage_opportunities(
    bonds: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Scan a universe of convertible bonds for arbitrage opportunities.

    Identifies bonds trading below theoretical value (cheap) or above (rich).

    Args:
        bonds: List of convertible bond dicts. If None, uses synthetic universe.

    Returns:
        Dict with opportunities sorted by mispricing magnitude.
    """
    if bonds is None:
        import random
        rng = random.Random(77)
        bonds = []
        for i in range(30):
            stock_px = rng.uniform(20, 200)
            vol = rng.uniform(0.20, 0.60)
            cr = round(1000 / (stock_px * rng.uniform(0.8, 1.3)), 2)
            bonds.append({
                "issuer": f"Convertible_{i:02d}",
                "market_price": None,  # will be set below
                "coupon_rate": round(rng.uniform(0.5, 5.0), 2),
                "years_to_maturity": round(rng.uniform(1, 7), 1),
                "conversion_ratio": cr,
                "stock_price": round(stock_px, 2),
                "stock_volatility": round(vol, 3),
                "credit_spread_bps": rng.randint(100, 500),
            })

    opportunities = []
    for b in bonds:
        theo = price_convertible(
            coupon_rate=b.get("coupon_rate", 2.0),
            years_to_maturity=b.get("years_to_maturity", 5.0),
            conversion_ratio=b.get("conversion_ratio", 20.0),
            stock_price=b.get("stock_price", 45.0),
            stock_volatility=b.get("stock_volatility", 0.35),
            credit_spread_bps=b.get("credit_spread_bps", 200),
        )

        # Simulate market price with some noise
        import random
        rng2 = random.Random(hash(b.get("issuer", "")) + 1)
        market_px = b.get("market_price") or round(theo["theoretical_price"] * rng2.uniform(0.92, 1.08), 2)

        mispricing = market_px - theo["theoretical_price"]
        mispricing_pct = (mispricing / theo["theoretical_price"]) * 100

        opportunities.append({
            "issuer": b.get("issuer", "Unknown"),
            "market_price": market_px,
            "theoretical_price": theo["theoretical_price"],
            "mispricing": round(mispricing, 2),
            "mispricing_pct": round(mispricing_pct, 2),
            "signal": "CHEAP" if mispricing_pct < -3 else "RICH" if mispricing_pct > 3 else "FAIR",
            "delta": theo["delta"],
            "hedge_shares": round(theo["delta"] * 1000, 0),  # shares to short per bond
            "parity_pct": theo["parity"],
        })

    opportunities.sort(key=lambda x: x["mispricing_pct"])

    cheap = [o for o in opportunities if o["signal"] == "CHEAP"]
    rich = [o for o in opportunities if o["signal"] == "RICH"]

    return {
        "total_scanned": len(opportunities),
        "cheap_count": len(cheap),
        "rich_count": len(rich),
        "fair_count": len(opportunities) - len(cheap) - len(rich),
        "top_cheap": cheap[:5],
        "top_rich": rich[-5:][::-1],
        "all_opportunities": opportunities,
    }


def hedge_ratio_calculator(
    delta: float,
    position_bonds: int = 10,
    par: float = 1000,
    stock_price: float = 45.0,
) -> dict[str, Any]:
    """
    Calculate delta hedge for a convertible bond position.

    Args:
        delta: Bond delta (per $1 par).
        position_bonds: Number of bonds held.
        par: Par value per bond.
        stock_price: Current stock price.

    Returns:
        Dict with shares to short, hedge cost, and position metrics.
    """
    total_par = position_bonds * par
    shares_to_short = round(delta * total_par)
    short_proceeds = shares_to_short * stock_price

    return {
        "bonds_held": position_bonds,
        "total_par_value": total_par,
        "delta": delta,
        "shares_to_short": shares_to_short,
        "short_value": round(short_proceeds, 2),
        "hedge_ratio": round(shares_to_short / position_bonds, 1),
        "net_delta_exposure": 0,
        "note": "Delta-neutral hedge. Rebalance when delta moves >0.05.",
    }
