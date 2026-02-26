"""
Heston Stochastic Volatility Model — Option pricing with mean-reverting variance.

Implements the Heston (1993) model where volatility follows a CIR process.
Provides Monte Carlo pricing, implied volatility surface generation, and
parameter calibration from market data. Uses Yahoo Finance (free).
"""

import numpy as np
from typing import Dict, List, Any, Optional
from math import log, sqrt, exp


def heston_mc_price(S0: float, K: float, T: float, r: float,
                    v0: float, kappa: float, theta: float,
                    sigma_v: float, rho: float,
                    n_paths: int = 10000, n_steps: int = 252,
                    option_type: str = "call") -> Dict[str, Any]:
    """
    Monte Carlo pricing under the Heston model.

    Args:
        S0: Initial stock price
        K: Strike price
        T: Time to expiry (years)
        r: Risk-free rate
        v0: Initial variance
        kappa: Mean reversion speed
        theta: Long-run variance
        sigma_v: Vol of vol
        rho: Correlation between price and vol
        n_paths: Number of MC paths
        n_steps: Time steps
        option_type: "call" or "put"

    Returns:
        Option price, Greeks estimates, and simulation statistics
    """
    dt = T / n_steps
    sqrt_dt = sqrt(dt)

    S = np.full(n_paths, S0)
    v = np.full(n_paths, v0)

    for _ in range(n_steps):
        z1 = np.random.standard_normal(n_paths)
        z2 = rho * z1 + sqrt(1 - rho**2) * np.random.standard_normal(n_paths)

        v_pos = np.maximum(v, 0)  # Ensure non-negative variance
        S = S * np.exp((r - 0.5 * v_pos) * dt + np.sqrt(v_pos) * sqrt_dt * z1)
        v = v + kappa * (theta - v_pos) * dt + sigma_v * np.sqrt(v_pos) * sqrt_dt * z2
        v = np.maximum(v, 0)

    if option_type == "call":
        payoffs = np.maximum(S - K, 0)
    else:
        payoffs = np.maximum(K - S, 0)

    price = float(exp(-r * T) * np.mean(payoffs))
    se = float(exp(-r * T) * np.std(payoffs) / sqrt(n_paths))

    return {
        "price": round(price, 4),
        "std_error": round(se, 6),
        "option_type": option_type,
        "parameters": {
            "S0": S0, "K": K, "T": T, "r": r,
            "v0": v0, "kappa": kappa, "theta": theta,
            "sigma_v": sigma_v, "rho": rho,
        },
        "final_price_stats": {
            "mean": float(np.mean(S)),
            "std": float(np.std(S)),
            "skewness": float(_skew(np.log(S / S0))),
        },
        "final_vol_stats": {
            "mean_vol": float(np.mean(np.sqrt(np.maximum(v, 0)))),
            "std_vol": float(np.std(np.sqrt(np.maximum(v, 0)))),
        },
    }


def _skew(x: np.ndarray) -> float:
    m, s = np.mean(x), np.std(x)
    return float(np.mean(((x - m) / s)**3)) if s > 0 else 0.0


def generate_vol_surface(S0: float, r: float, v0: float, kappa: float,
                         theta: float, sigma_v: float, rho: float,
                         strikes_pct: Optional[List[float]] = None,
                         expiries: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Generate implied volatility surface from Heston parameters.

    Args:
        S0: Spot price
        r: Risk-free rate
        v0-rho: Heston parameters
        strikes_pct: Strike as % of spot (e.g., [0.8, 0.9, 1.0, 1.1, 1.2])
        expiries: Expiry times in years

    Returns:
        Implied vol surface grid
    """
    if strikes_pct is None:
        strikes_pct = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]
    if expiries is None:
        expiries = [0.083, 0.25, 0.5, 1.0, 2.0]

    surface = []
    for T in expiries:
        row = []
        for k_pct in strikes_pct:
            K = S0 * k_pct
            result = heston_mc_price(S0, K, T, r, v0, kappa, theta, sigma_v, rho,
                                     n_paths=5000, n_steps=max(50, int(252 * T)))
            # Approximate implied vol from price using Newton's method
            iv = _implied_vol_newton(result["price"], S0, K, T, r)
            row.append(round(iv, 4))
        surface.append({
            "expiry": T,
            "expiry_label": f"{int(T*12)}M" if T >= 1/12 else f"{int(T*252)}D",
            "strikes_pct": strikes_pct,
            "implied_vols": row,
        })

    return {
        "spot": S0,
        "surface": surface,
        "parameters": {"v0": v0, "kappa": kappa, "theta": theta, "sigma_v": sigma_v, "rho": rho},
        "skew_metric": surface[-1]["implied_vols"][0] - surface[-1]["implied_vols"][-1] if surface else 0,
    }


def _implied_vol_newton(price: float, S: float, K: float, T: float, r: float,
                        tol: float = 1e-6, max_iter: int = 50) -> float:
    """Newton's method for implied vol from BS call price."""
    sigma = 0.3  # initial guess
    for _ in range(max_iter):
        bs = _bs_call(S, K, T, r, sigma)
        vega = _bs_vega(S, K, T, r, sigma)
        if vega < 1e-10:
            break
        sigma -= (bs - price) / vega
        sigma = max(0.01, min(5.0, sigma))
        if abs(bs - price) < tol:
            break
    return sigma


def _bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K * exp(-r * T), 0)
    import math
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    return S * _ncdf(d1) - K * exp(-r * T) * _ncdf(d2)


def _bs_vega(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    return S * sqrt(T) * _npdf(d1)


def _ncdf(x):
    import math
    return 0.5 * (1 + math.erf(x / sqrt(2)))


def _npdf(x):
    import math
    return exp(-0.5 * x**2) / sqrt(2 * math.pi)


def calibrate_heston(ticker: str = "SPY", period: str = "2y") -> Dict[str, Any]:
    """
    Estimate Heston parameters from historical returns.

    Uses realized variance dynamics to estimate kappa, theta, sigma_v, and rho.
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period=period, progress=False)
        prices = data["Close"].dropna().values.flatten()
        returns = np.log(prices[1:] / prices[:-1])
    except Exception:
        return {"error": f"Could not fetch data for {ticker}"}

    # Rolling realized variance (21-day windows)
    window = 21
    if len(returns) < window * 3:
        return {"error": "Insufficient data"}
    rv = np.array([np.var(returns[i:i+window]) * 252 for i in range(len(returns) - window)])

    # Estimate CIR parameters via OLS on variance dynamics
    v0 = float(rv[-1])
    theta = float(np.mean(rv))
    # Mean reversion from AR(1) on variance
    rv_lag = rv[:-1]
    rv_lead = rv[1:]
    dt = 1/252
    if np.var(rv_lag) > 0:
        beta = np.corrcoef(rv_lag, rv_lead)[0, 1]
        kappa = float(-np.log(max(beta, 0.01)) / dt) if beta > 0 else 5.0
        kappa = min(max(kappa, 0.5), 20.0)
    else:
        kappa = 2.0
    sigma_v = float(np.std(np.diff(rv)) * sqrt(252) / max(np.mean(np.sqrt(rv)), 0.01))
    sigma_v = min(max(sigma_v, 0.1), 3.0)
    rho = float(np.corrcoef(returns[window:], rv[:-1] if len(rv) > len(returns[window:]) else rv[:len(returns[window:])])[0, 1])

    # Feller condition check
    feller = 2 * kappa * theta > sigma_v**2

    return {
        "ticker": ticker,
        "parameters": {
            "v0": round(v0, 6),
            "kappa": round(kappa, 4),
            "theta": round(theta, 6),
            "sigma_v": round(sigma_v, 4),
            "rho": round(rho, 4),
        },
        "feller_condition_met": feller,
        "current_implied_vol": round(sqrt(v0), 4),
        "long_run_vol": round(sqrt(theta), 4),
        "n_observations": len(returns),
    }
