"""
QuantLib — Quantitative Finance Calculations

Library: QuantLib (C++ with Python SWIG bindings)
Free: Yes (open-source, no API keys)
Update: Static (library-based calculations)

Provides:
- European & American option pricing (Black-Scholes, Binomial)
- Bond pricing and yield calculations
- Implied volatility extraction
- Interest rate curve building
- Greeks (delta, gamma, vega, theta, rho)
- Monte Carlo option pricing
- Fixed income analytics (duration, convexity)

Usage:
  from modules.quantlib import price_european_option, calculate_bond_yield
  result = price_european_option(spot=100, strike=105, rate=0.05, volatility=0.2, maturity_years=1.0)
  bond = calculate_bond_yield(face=1000, coupon_rate=0.05, price=950, years=10)
"""

import QuantLib as ql
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ql_date(dt: Optional[Union[str, date, datetime]] = None) -> ql.Date:
    """Convert a Python date/string to a QuantLib Date. Defaults to today."""
    if dt is None:
        today = date.today()
        return ql.Date(today.day, today.month, today.year)
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d").date()
    if isinstance(dt, datetime):
        dt = dt.date()
    return ql.Date(dt.day, dt.month, dt.year)


def _set_eval_date(eval_date: Optional[str] = None) -> ql.Date:
    """Set the global evaluation date and return it."""
    d = _ql_date(eval_date)
    ql.Settings.instance().evaluationDate = d
    return d


# ---------------------------------------------------------------------------
# Option Pricing
# ---------------------------------------------------------------------------

def price_european_option(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity_years: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Price a European option using Black-Scholes-Merton.

    Args:
        spot: Current underlying price.
        strike: Option strike price.
        rate: Risk-free interest rate (annualized, e.g. 0.05 for 5%).
        volatility: Annualized volatility (e.g. 0.20 for 20%).
        maturity_years: Time to expiration in years.
        option_type: 'call' or 'put'.
        dividend_yield: Continuous dividend yield (default 0).
        eval_date: Evaluation date as 'YYYY-MM-DD' (default today).

    Returns:
        dict with price, delta, gamma, vega, theta, rho.
    """
    try:
        today = _set_eval_date(eval_date)
        maturity = today + ql.Period(int(round(maturity_years * 365)), ql.Days)

        opt_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)

        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        flat_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(rate)), ql.Actual365Fixed())
        )
        div_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(dividend_yield)), ql.Actual365Fixed())
        )
        vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(today, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(volatility)), ql.Actual365Fixed())
        )

        bsm_process = ql.BlackScholesMertonProcess(spot_handle, div_ts, flat_ts, vol_ts)
        option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))

        return {
            "model": "Black-Scholes-Merton",
            "option_type": option_type.lower(),
            "spot": spot,
            "strike": strike,
            "rate": rate,
            "volatility": volatility,
            "maturity_years": maturity_years,
            "price": round(option.NPV(), 6),
            "delta": round(option.delta(), 6),
            "gamma": round(option.gamma(), 6),
            "vega": round(option.vega() / 100, 6),  # per 1% vol move
            "theta": round(option.theta() / 365, 6),  # per day
            "rho": round(option.rho() / 100, 6),  # per 1% rate move
        }
    except Exception as e:
        return {"error": str(e), "function": "price_european_option"}


def price_american_option(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity_years: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    steps: int = 200,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Price an American option using a Binomial tree (CRR).

    Args:
        spot: Current underlying price.
        strike: Option strike price.
        rate: Risk-free rate.
        volatility: Annualized volatility.
        maturity_years: Time to expiration in years.
        option_type: 'call' or 'put'.
        dividend_yield: Continuous dividend yield.
        steps: Number of binomial tree steps (default 200).
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with price and greeks.
    """
    try:
        today = _set_eval_date(eval_date)
        maturity = today + ql.Period(int(round(maturity_years * 365)), ql.Days)

        opt_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.AmericanExercise(today, maturity)
        option = ql.VanillaOption(payoff, exercise)

        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        flat_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(rate)), ql.Actual365Fixed())
        )
        div_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(dividend_yield)), ql.Actual365Fixed())
        )
        vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(today, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(volatility)), ql.Actual365Fixed())
        )

        bsm_process = ql.BlackScholesMertonProcess(spot_handle, div_ts, flat_ts, vol_ts)
        option.setPricingEngine(ql.BinomialVanillaEngine(bsm_process, "crr", steps))

        return {
            "model": "Binomial-CRR",
            "option_type": option_type.lower(),
            "spot": spot,
            "strike": strike,
            "rate": rate,
            "volatility": volatility,
            "maturity_years": maturity_years,
            "steps": steps,
            "price": round(option.NPV(), 6),
            "delta": round(option.delta(), 6),
            "gamma": round(option.gamma(), 6),
        }
    except Exception as e:
        return {"error": str(e), "function": "price_american_option"}


def calculate_implied_volatility(
    option_price: float,
    spot: float,
    strike: float,
    rate: float,
    maturity_years: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Calculate implied volatility from an observed option price.

    Args:
        option_price: Observed market price of the option.
        spot: Underlying price.
        strike: Strike price.
        rate: Risk-free rate.
        maturity_years: Time to expiration in years.
        option_type: 'call' or 'put'.
        dividend_yield: Continuous dividend yield.
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with implied_volatility.
    """
    try:
        today = _set_eval_date(eval_date)
        maturity = today + ql.Period(int(round(maturity_years * 365)), ql.Days)

        opt_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)

        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        flat_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(rate)), ql.Actual365Fixed())
        )
        div_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(dividend_yield)), ql.Actual365Fixed())
        )
        vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(today, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(0.20)), ql.Actual365Fixed())
        )

        bsm_process = ql.BlackScholesMertonProcess(spot_handle, div_ts, flat_ts, vol_ts)
        option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))

        iv = option.impliedVolatility(option_price, bsm_process)

        return {
            "implied_volatility": round(iv, 6),
            "implied_volatility_pct": round(iv * 100, 2),
            "option_price": option_price,
            "spot": spot,
            "strike": strike,
            "option_type": option_type.lower(),
        }
    except Exception as e:
        return {"error": str(e), "function": "calculate_implied_volatility"}


# ---------------------------------------------------------------------------
# Fixed Income
# ---------------------------------------------------------------------------

def calculate_bond_yield(
    face: float,
    coupon_rate: float,
    price: float,
    years: int,
    frequency: int = 2,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Calculate yield-to-maturity for a fixed-rate bond.

    Args:
        face: Face/par value of the bond.
        coupon_rate: Annual coupon rate (e.g. 0.05 for 5%).
        price: Current market (clean) price.
        years: Years to maturity.
        frequency: Coupon payments per year (default 2 = semi-annual).
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with ytm, clean_price, dirty_price, duration, convexity.
    """
    try:
        today = _set_eval_date(eval_date)
        calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
        settlement = calendar.advance(today, 2, ql.Days)
        maturity = calendar.advance(settlement, years, ql.Years)

        # QuantLib bonds use face=100 internally
        price_per_100 = (price / face) * 100.0

        tenor = ql.Period(int(12 / frequency), ql.Months)
        schedule = ql.Schedule(
            settlement, maturity, tenor, calendar,
            ql.Unadjusted, ql.Unadjusted,
            ql.DateGeneration.Backward, False
        )

        bond = ql.FixedRateBond(
            2, 100.0,
            schedule,
            [coupon_rate],
            ql.Actual365Fixed(),
        )

        bond_price = ql.BondPrice(price_per_100, ql.BondPrice.Clean)
        ytm = ql.BondFunctions.bondYield(
            bond, bond_price, ql.Actual365Fixed(), ql.Compounded, ql.Semiannual
        )

        duration = ql.BondFunctions.duration(
            bond, ytm, ql.Actual365Fixed(), ql.Compounded, ql.Semiannual
        )
        convexity = ql.BondFunctions.convexity(
            bond, ytm, ql.Actual365Fixed(), ql.Compounded, ql.Semiannual
        )

        return {
            "face": face,
            "coupon_rate": coupon_rate,
            "market_price": price,
            "years_to_maturity": years,
            "yield_to_maturity": round(ytm, 6),
            "ytm_pct": round(ytm * 100, 4),
            "duration": round(duration, 4),
            "convexity": round(convexity, 4),
        }
    except Exception as e:
        return {"error": str(e), "function": "calculate_bond_yield"}


def price_bond(
    face: float,
    coupon_rate: float,
    ytm: float,
    years: int,
    frequency: int = 2,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Price a fixed-rate bond given a yield-to-maturity.

    Args:
        face: Face value.
        coupon_rate: Annual coupon rate.
        ytm: Yield to maturity.
        years: Years to maturity.
        frequency: Payments per year.
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with clean_price, dirty_price, duration, convexity.
    """
    try:
        today = _set_eval_date(eval_date)
        calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
        settlement = calendar.advance(today, 2, ql.Days)
        maturity = calendar.advance(settlement, years, ql.Years)

        tenor = ql.Period(int(12 / frequency), ql.Months)
        schedule = ql.Schedule(
            settlement, maturity, tenor, calendar,
            ql.Unadjusted, ql.Unadjusted,
            ql.DateGeneration.Backward, False
        )

        # QuantLib bonds use face=100 internally; scale output back
        bond = ql.FixedRateBond(2, 100.0, schedule, [coupon_rate], ql.Actual365Fixed())

        flat_curve = ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(ytm)), ql.Actual365Fixed())
        curve_handle = ql.YieldTermStructureHandle(flat_curve)
        engine = ql.DiscountingBondEngine(curve_handle)
        bond.setPricingEngine(engine)

        # Scale prices back to user's face value
        scale = face / 100.0
        clean = bond.cleanPrice() * scale
        dirty = bond.dirtyPrice() * scale
        duration = ql.BondFunctions.duration(
            bond, ytm, ql.Actual365Fixed(), ql.Compounded, ql.Semiannual
        )
        convexity = ql.BondFunctions.convexity(
            bond, ytm, ql.Actual365Fixed(), ql.Compounded, ql.Semiannual
        )

        return {
            "face": face,
            "coupon_rate": coupon_rate,
            "ytm": ytm,
            "years_to_maturity": years,
            "clean_price": round(clean, 4),
            "dirty_price": round(dirty, 4),
            "duration": round(duration, 4),
            "convexity": round(convexity, 4),
        }
    except Exception as e:
        return {"error": str(e), "function": "price_bond"}


# ---------------------------------------------------------------------------
# Interest Rate Curves
# ---------------------------------------------------------------------------

def build_yield_curve(
    tenors_years: List[float],
    rates: List[float],
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Build an interpolated yield curve from tenor/rate pairs.

    Args:
        tenors_years: List of tenors in years (e.g. [0.25, 0.5, 1, 2, 5, 10, 30]).
        rates: Corresponding zero rates (e.g. [0.04, 0.042, 0.045, ...]).
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with discount factors and zero rates at each tenor.
    """
    try:
        today = _set_eval_date(eval_date)

        dates = [today + ql.Period(int(round(t * 365)), ql.Days) for t in tenors_years]
        curve = ql.ZeroCurve(dates, rates, ql.Actual365Fixed())
        curve_handle = ql.YieldTermStructureHandle(curve)

        results = []
        for t, d in zip(tenors_years, dates):
            df = curve.discount(d)
            zr = curve.zeroRate(d, ql.Actual365Fixed(), ql.Continuous).rate()
            results.append({
                "tenor_years": t,
                "date": str(d),
                "discount_factor": round(df, 6),
                "zero_rate": round(zr, 6),
            })

        return {
            "eval_date": str(today),
            "interpolation": "linear",
            "points": results,
        }
    except Exception as e:
        return {"error": str(e), "function": "build_yield_curve"}


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

def monte_carlo_european(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity_years: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    num_paths: int = 100000,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Price a European option using Monte Carlo simulation.

    Args:
        spot: Current underlying price.
        strike: Strike price.
        rate: Risk-free rate.
        volatility: Annualized volatility.
        maturity_years: Time to expiration.
        option_type: 'call' or 'put'.
        dividend_yield: Continuous dividend yield.
        num_paths: Number of simulation paths.
        eval_date: Evaluation date 'YYYY-MM-DD'.

    Returns:
        dict with mc_price, error_estimate, and BS reference price.
    """
    try:
        today = _set_eval_date(eval_date)
        maturity = today + ql.Period(int(round(maturity_years * 365)), ql.Days)

        opt_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(opt_type, strike)
        exercise = ql.EuropeanExercise(maturity)
        option = ql.VanillaOption(payoff, exercise)

        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
        flat_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(rate)), ql.Actual365Fixed())
        )
        div_ts = ql.YieldTermStructureHandle(
            ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(dividend_yield)), ql.Actual365Fixed())
        )
        vol_ts = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(today, ql.NullCalendar(), ql.QuoteHandle(ql.SimpleQuote(volatility)), ql.Actual365Fixed())
        )

        bsm_process = ql.BlackScholesMertonProcess(spot_handle, div_ts, flat_ts, vol_ts)

        # Monte Carlo engine
        rng = "pseudorandom"
        mc_engine = ql.MCEuropeanEngine(bsm_process, rng, timeSteps=1, requiredSamples=num_paths)
        option.setPricingEngine(mc_engine)
        mc_price = option.NPV()
        mc_error = option.errorEstimate()

        # Analytical reference
        option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        bs_price = option.NPV()

        return {
            "model": "Monte-Carlo",
            "num_paths": num_paths,
            "mc_price": round(mc_price, 6),
            "error_estimate": round(mc_error, 6),
            "bs_reference_price": round(bs_price, 6),
            "price_diff": round(abs(mc_price - bs_price), 6),
        }
    except Exception as e:
        return {"error": str(e), "function": "monte_carlo_european"}


# ---------------------------------------------------------------------------
# Volatility Surface
# ---------------------------------------------------------------------------

def get_greeks(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity_years: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
    eval_date: Optional[str] = None,
) -> Dict:
    """
    Calculate all option Greeks for a European option.

    Returns:
        dict with delta, gamma, vega, theta, rho, and option price.
    """
    result = price_european_option(
        spot=spot, strike=strike, rate=rate, volatility=volatility,
        maturity_years=maturity_years, option_type=option_type,
        dividend_yield=dividend_yield, eval_date=eval_date
    )
    if "error" in result:
        return result
    return {
        "spot": spot,
        "strike": strike,
        "option_type": option_type.lower(),
        "price": result["price"],
        "delta": result["delta"],
        "gamma": result["gamma"],
        "vega": result["vega"],
        "theta": result["theta"],
        "rho": result["rho"],
    }


def forward_rate(
    rate1: float,
    tenor1_years: float,
    rate2: float,
    tenor2_years: float,
) -> Dict:
    """
    Calculate the forward rate between two points on the yield curve.

    Args:
        rate1: Zero rate at tenor 1.
        tenor1_years: First tenor in years.
        rate2: Zero rate at tenor 2.
        tenor2_years: Second tenor in years (must be > tenor1).

    Returns:
        dict with forward_rate and tenors.
    """
    try:
        if tenor2_years <= tenor1_years:
            return {"error": "tenor2 must be greater than tenor1"}

        # f = (r2*t2 - r1*t1) / (t2 - t1)  (continuous compounding)
        fwd = (rate2 * tenor2_years - rate1 * tenor1_years) / (tenor2_years - tenor1_years)
        return {
            "forward_rate": round(fwd, 6),
            "forward_rate_pct": round(fwd * 100, 4),
            "from_tenor": tenor1_years,
            "to_tenor": tenor2_years,
            "rate_at_t1": rate1,
            "rate_at_t2": rate2,
        }
    except Exception as e:
        return {"error": str(e), "function": "forward_rate"}


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------

def get_module_info() -> Dict:
    """Return module metadata."""
    return {
        "module": "quantlib",
        "version": "1.0.0",
        "quantlib_version": ql.__version__ if hasattr(ql, '__version__') else "1.41",
        "source": "https://www.quantlib.org/",
        "category": "Quant Tools & ML",
        "free_tier": True,
        "requires_api_key": False,
        "functions": [
            "price_european_option",
            "price_american_option",
            "calculate_implied_volatility",
            "calculate_bond_yield",
            "price_bond",
            "build_yield_curve",
            "monte_carlo_european",
            "get_greeks",
            "forward_rate",
            "get_module_info",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
    print("\n--- European Call (S=100, K=105, r=5%, vol=20%, T=1yr) ---")
    print(json.dumps(price_european_option(100, 105, 0.05, 0.20, 1.0), indent=2))
    print("\n--- Bond Yield (Face=1000, Coupon=5%, Price=950, 10yr) ---")
    print(json.dumps(calculate_bond_yield(1000, 0.05, 950, 10), indent=2))
