"""
Merton Jump Diffusion Model — Option pricing and simulation with jump risk.

Extends Black-Scholes with a compound Poisson jump process to capture
fat tails and sudden price movements. Uses Yahoo Finance for market data (free).
"""

import numpy as np
from typing import Dict, List, Any, Optional
from math import factorial, exp, log, sqrt


def merton_call_price(S: float, K: float, T: float, r: float, sigma: float,
                      lam: float, mu_j: float, sigma_j: float,
                      n_terms: int = 50) -> float:
    """
    Merton Jump Diffusion call option price.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiry (years)
        r: Risk-free rate
        sigma: Diffusion volatility
        lam: Jump intensity (expected jumps per year)
        mu_j: Mean jump size (log-normal)
        sigma_j: Jump size volatility
        n_terms: Number of Poisson series terms

    Returns:
        Call option price
    """
    price = 0.0
    lam_prime = lam * exp(mu_j + 0.5 * sigma_j**2)
    for n in range(n_terms):
        sigma_n = sqrt(sigma**2 + n * sigma_j**2 / T) if T > 0 else sigma
        r_n = r - lam * (exp(mu_j + 0.5 * sigma_j**2) - 1) + n * (mu_j + 0.5 * sigma_j**2) / T if T > 0 else r
        # Black-Scholes with adjusted params
        bs = _bs_call(S, K, T, r_n, sigma_n)
        poisson_weight = exp(-lam_prime * T) * (lam_prime * T)**n / factorial(n)
        price += poisson_weight * bs
    return price


def _bs_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Standard Black-Scholes call price."""
    if T <= 0 or sigma <= 0:
        return max(S - K * exp(-r * T), 0)
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    return S * _norm_cdf(d1) - K * exp(-r * T) * _norm_cdf(d2)


def _norm_cdf(x: float) -> float:
    """Approximation of standard normal CDF."""
    import math
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def merton_put_price(S: float, K: float, T: float, r: float, sigma: float,
                     lam: float, mu_j: float, sigma_j: float) -> float:
    """Merton Jump Diffusion put price via put-call parity."""
    call = merton_call_price(S, K, T, r, sigma, lam, mu_j, sigma_j)
    return call - S + K * exp(-r * T)


def simulate_paths(S0: float, T: float, r: float, sigma: float,
                   lam: float, mu_j: float, sigma_j: float,
                   n_paths: int = 1000, n_steps: int = 252) -> Dict[str, Any]:
    """
    Monte Carlo simulation of Merton Jump Diffusion paths.

    Args:
        S0: Initial price
        T: Time horizon (years)
        r: Risk-free rate
        sigma: Diffusion volatility
        lam: Jump intensity
        mu_j: Mean jump size
        sigma_j: Jump size volatility
        n_paths: Number of simulation paths
        n_steps: Number of time steps

    Returns:
        Path statistics, percentiles, and jump analysis
    """
    dt = T / n_steps
    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = S0

    for t in range(1, n_steps + 1):
        # Diffusion component
        z = np.random.standard_normal(n_paths)
        diffusion = (r - 0.5 * sigma**2 - lam * (np.exp(mu_j + 0.5 * sigma_j**2) - 1)) * dt
        diffusion += sigma * np.sqrt(dt) * z
        # Jump component
        n_jumps = np.random.poisson(lam * dt, n_paths)
        jump_sizes = np.zeros(n_paths)
        for i in range(n_paths):
            if n_jumps[i] > 0:
                jump_sizes[i] = np.sum(np.random.normal(mu_j, sigma_j, n_jumps[i]))
        paths[:, t] = paths[:, t-1] * np.exp(diffusion + jump_sizes)

    final = paths[:, -1]
    returns = np.log(final / S0)
    return {
        "initial_price": S0,
        "mean_final": float(np.mean(final)),
        "median_final": float(np.median(final)),
        "std_final": float(np.std(final)),
        "percentiles": {
            "p5": float(np.percentile(final, 5)),
            "p25": float(np.percentile(final, 25)),
            "p50": float(np.percentile(final, 50)),
            "p75": float(np.percentile(final, 75)),
            "p95": float(np.percentile(final, 95)),
        },
        "return_stats": {
            "mean": float(np.mean(returns)),
            "std": float(np.std(returns)),
            "skewness": float(_skewness(returns)),
            "kurtosis": float(_kurtosis(returns)),
        },
        "prob_loss": float(np.mean(final < S0)),
        "prob_gain_20pct": float(np.mean(final > S0 * 1.2)),
        "max_drawdown_avg": float(np.mean([_max_dd(p) for p in paths[:100]])),
    }


def _skewness(x: np.ndarray) -> float:
    m = np.mean(x)
    s = np.std(x)
    return float(np.mean(((x - m) / s)**3)) if s > 0 else 0


def _kurtosis(x: np.ndarray) -> float:
    m = np.mean(x)
    s = np.std(x)
    return float(np.mean(((x - m) / s)**4) - 3) if s > 0 else 0


def _max_dd(path: np.ndarray) -> float:
    peak = np.maximum.accumulate(path)
    dd = (peak - path) / peak
    return float(np.max(dd))


def calibrate_from_ticker(ticker: str, period: str = "2y") -> Dict[str, Any]:
    """
    Calibrate jump diffusion parameters from historical data.

    Uses method of moments on return distribution to estimate
    diffusion volatility, jump intensity, and jump size parameters.
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period=period, progress=False)
        prices = data["Close"].dropna().values.flatten()
        returns = np.log(prices[1:] / prices[:-1])
    except Exception:
        return {"error": f"Could not fetch data for {ticker}"}

    # Method of moments calibration
    mu = np.mean(returns) * 252
    total_var = np.var(returns) * 252
    skew = _skewness(returns)
    kurt = _kurtosis(returns)

    # Estimate jump parameters from excess kurtosis
    # Higher kurtosis → more jumps
    lam = max(0.5, min(10, abs(kurt) * 2))  # jumps per year
    sigma_j = max(0.01, abs(skew) * 0.05)
    mu_j = -0.02 if skew < 0 else 0.01  # negative skew → negative jumps
    sigma = max(0.01, sqrt(max(0.001, total_var - lam * (mu_j**2 + sigma_j**2))))

    return {
        "ticker": ticker,
        "calibrated_params": {
            "sigma": round(sigma, 4),
            "lambda": round(lam, 4),
            "mu_j": round(mu_j, 4),
            "sigma_j": round(sigma_j, 4),
        },
        "empirical_stats": {
            "annualized_return": round(mu, 4),
            "annualized_vol": round(sqrt(total_var), 4),
            "skewness": round(skew, 4),
            "excess_kurtosis": round(kurt, 4),
        },
        "n_observations": len(returns),
    }
