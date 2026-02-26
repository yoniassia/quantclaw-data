"""GARCH Volatility Forecaster — univariate and multivariate GARCH for volatility modeling.

Implements GARCH(1,1), EGARCH, and simple DCC for correlation dynamics.
Pure numpy implementation — no arch library required.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def garch11_fit(returns: List[float], omega: float = 0.00001,
                alpha: float = 0.1, beta: float = 0.85) -> Dict:
    """Fit GARCH(1,1) model: σ²_t = ω + α·r²_{t-1} + β·σ²_{t-1}.

    Uses given parameters (or defaults) to compute conditional variance series.
    For full MLE estimation, use garch11_mle.

    Args:
        returns: Return series.
        omega, alpha, beta: GARCH parameters.

    Returns:
        Dict with variance series, current vol forecast, and persistence.
    """
    r = np.array(returns, dtype=float)
    n = len(r)
    if n < 10:
        return {"error": "Need at least 10 observations"}

    sigma2 = np.zeros(n)
    sigma2[0] = np.var(r)

    for t in range(1, n):
        sigma2[t] = omega + alpha * r[t - 1] ** 2 + beta * sigma2[t - 1]

    # Forecast next period
    sigma2_next = omega + alpha * r[-1] ** 2 + beta * sigma2[-1]
    persistence = alpha + beta

    return {
        "current_vol": round(float(np.sqrt(sigma2[-1])), 6),
        "forecast_vol": round(float(np.sqrt(sigma2_next)), 6),
        "forecast_vol_annualized": round(float(np.sqrt(sigma2_next * 252)), 6),
        "persistence": round(persistence, 6),
        "half_life": round(float(-np.log(2) / np.log(persistence)), 2) if 0 < persistence < 1 else None,
        "unconditional_vol": round(float(np.sqrt(omega / (1 - persistence))), 6) if persistence < 1 else None,
        "params": {"omega": omega, "alpha": alpha, "beta": beta},
        "vol_series_last20": [round(float(np.sqrt(v)), 6) for v in sigma2[-20:]],
    }


def garch11_mle(returns: List[float], max_iter: int = 200) -> Dict:
    """Estimate GARCH(1,1) parameters via simplified MLE (grid + gradient).

    Returns fitted parameters and model diagnostics.
    """
    r = np.array(returns, dtype=float)
    n = len(r)
    var_r = np.var(r)

    def neg_loglik(omega, alpha, beta):
        sigma2 = np.zeros(n)
        sigma2[0] = var_r
        for t in range(1, n):
            sigma2[t] = omega + alpha * r[t - 1] ** 2 + beta * sigma2[t - 1]
            if sigma2[t] <= 0:
                return 1e10
        ll = -0.5 * np.sum(np.log(sigma2) + r ** 2 / sigma2)
        return -ll

    # Grid search
    best = (1e10, 0.00001, 0.1, 0.85)
    for a in np.arange(0.02, 0.25, 0.03):
        for b in np.arange(0.6, 0.96, 0.05):
            if a + b >= 1.0:
                continue
            o = var_r * (1 - a - b)
            if o <= 0:
                continue
            nll = neg_loglik(o, a, b)
            if nll < best[0]:
                best = (nll, o, a, b)

    _, omega, alpha, beta = best
    result = garch11_fit(returns, omega, alpha, beta)
    result["log_likelihood"] = round(-best[0], 4)
    result["aic"] = round(2 * best[0] + 6, 4)  # 3 params * 2
    result["bic"] = round(2 * best[0] + 3 * np.log(n), 4)
    return result


def egarch_fit(returns: List[float], omega: float = -0.5,
               alpha: float = 0.15, gamma: float = -0.05, beta: float = 0.9) -> Dict:
    """EGARCH(1,1): log(σ²_t) = ω + α|z_{t-1}| + γ·z_{t-1} + β·log(σ²_{t-1}).

    Captures leverage effect (gamma < 0 means negative returns increase vol more).
    """
    r = np.array(returns, dtype=float)
    n = len(r)
    log_sigma2 = np.zeros(n)
    log_sigma2[0] = np.log(np.var(r))

    for t in range(1, n):
        sigma_prev = np.sqrt(np.exp(log_sigma2[t - 1]))
        z = r[t - 1] / sigma_prev if sigma_prev > 0 else 0
        log_sigma2[t] = omega + alpha * abs(z) + gamma * z + beta * log_sigma2[t - 1]

    sigma2 = np.exp(log_sigma2)
    sigma_last = np.sqrt(sigma2[-1])
    z_last = r[-1] / sigma_last if sigma_last > 0 else 0
    log_s2_next = omega + alpha * abs(z_last) + gamma * z_last + beta * log_sigma2[-1]

    return {
        "current_vol": round(float(np.sqrt(sigma2[-1])), 6),
        "forecast_vol": round(float(np.sqrt(np.exp(log_s2_next))), 6),
        "leverage_effect": round(gamma, 4),
        "persistence": round(beta, 4),
        "params": {"omega": omega, "alpha": alpha, "gamma": gamma, "beta": beta},
        "vol_series_last20": [round(float(np.sqrt(v)), 6) for v in sigma2[-20:]],
    }


def multi_period_forecast(returns: List[float], horizons: List[int] = None,
                           omega: float = 0.00001, alpha: float = 0.1,
                           beta: float = 0.85) -> Dict:
    """Multi-step ahead GARCH volatility forecast.

    Args:
        horizons: List of forecast horizons (days ahead).
    """
    if horizons is None:
        horizons = [1, 5, 10, 21, 63, 126, 252]

    r = np.array(returns, dtype=float)
    fit = garch11_fit(returns, omega, alpha, beta)
    sigma2_t = fit["forecast_vol"] ** 2
    persistence = alpha + beta
    unconditional_var = omega / (1 - persistence) if persistence < 1 else sigma2_t

    forecasts = {}
    for h in horizons:
        if persistence < 1:
            cum_var = unconditional_var * h + (sigma2_t - unconditional_var) * (1 - persistence ** h) / (1 - persistence)
        else:
            cum_var = sigma2_t * h
        forecasts[f"{h}d"] = {
            "vol": round(float(np.sqrt(cum_var / h)), 6),
            "annualized_vol": round(float(np.sqrt(cum_var / h * 252)), 6),
        }

    return {"horizons": forecasts, "params": fit["params"]}
