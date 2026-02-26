"""
Variance Swap Pricer — Fair strike calculation and P&L analysis for variance swaps.

Prices variance swaps using realized vs implied variance, replicating portfolio
approach, and mark-to-market P&L tracking. Uses Yahoo Finance for data (free).
"""

import numpy as np
from typing import Dict, List, Any, Optional
from math import sqrt, log, exp


def fair_strike(ticker: str = "SPY", period: str = "1y",
                annualize: bool = True) -> Dict[str, Any]:
    """
    Calculate the fair variance swap strike from historical data.

    The fair strike approximates the risk-neutral expected variance using
    realized variance with a variance risk premium adjustment.

    Args:
        ticker: Underlying asset ticker
        period: Historical lookback period
        annualize: Whether to annualize the result

    Returns:
        Fair strike (in vol terms), realized variance, and risk premium estimate
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period=period, progress=False)
        prices = data["Close"].dropna().values.flatten()
        returns = np.log(prices[1:] / prices[:-1])
    except Exception:
        return {"error": f"Could not fetch data for {ticker}"}

    n = len(returns)
    if n < 30:
        return {"error": "Insufficient data"}

    # Realized variance (annualized)
    rv = float(np.var(returns, ddof=1) * 252) if annualize else float(np.var(returns, ddof=1))
    rv_vol = sqrt(rv)

    # Estimate variance risk premium (~15-20% above realized historically)
    # Using rolling sub-sample approach
    window = min(63, n // 3)
    rolling_rv = [np.var(returns[i:i+window]) * 252 for i in range(0, n - window, window)]
    if len(rolling_rv) > 2:
        vrp_ratio = 1.0 + float(np.std(rolling_rv) / np.mean(rolling_rv)) * 0.5
    else:
        vrp_ratio = 1.15

    fair_var = rv * vrp_ratio
    fair_vol = sqrt(fair_var)

    # Recent realized vol (last 30 days)
    recent_rv = float(np.var(returns[-30:]) * 252) if n >= 30 else rv

    return {
        "ticker": ticker,
        "fair_strike_variance": round(fair_var, 6),
        "fair_strike_vol": round(fair_vol * 100, 2),  # in % terms
        "realized_variance": round(rv, 6),
        "realized_vol_pct": round(rv_vol * 100, 2),
        "recent_30d_rv_pct": round(sqrt(recent_rv) * 100, 2),
        "variance_risk_premium_ratio": round(vrp_ratio, 4),
        "implied_vrp_bps": round((fair_var - rv) * 10000, 2),
        "n_observations": n,
    }


def mark_to_market(ticker: str, strike_var: float, notional: float,
                   entry_date_offset: int = 63, position: str = "long") -> Dict[str, Any]:
    """
    Mark-to-market a variance swap position.

    Args:
        ticker: Underlying asset
        strike_var: Variance swap strike (annualized variance, not vol)
        notional: Vega notional ($ per vol point)
        entry_date_offset: Trading days since entry
        position: "long" or "short" variance

    Returns:
        Current P&L, accrued variance, and time decay analysis
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period="1y", progress=False)
        prices = data["Close"].dropna().values.flatten()
        returns = np.log(prices[1:] / prices[:-1])
    except Exception:
        return {"error": f"Could not fetch data for {ticker}"}

    if len(returns) < entry_date_offset:
        entry_date_offset = len(returns)

    # Accrued realized variance since entry
    trade_returns = returns[-entry_date_offset:]
    accrued_rv = float(np.sum(trade_returns**2) * 252 / len(trade_returns))
    days_elapsed = len(trade_returns)
    total_days = 252  # assume 1Y swap

    # Projected final variance (weighted avg of accrued + strike for remaining)
    weight_elapsed = days_elapsed / total_days
    projected_var = weight_elapsed * accrued_rv + (1 - weight_elapsed) * strike_var

    # Variance notional = vega_notional / (2 * strike_vol)
    strike_vol = sqrt(strike_var)
    var_notional = notional / (2 * strike_vol) if strike_vol > 0 else 0

    # P&L
    direction = 1 if position == "long" else -1
    pnl = direction * var_notional * (projected_var - strike_var)
    accrued_pnl = direction * var_notional * weight_elapsed * (accrued_rv - strike_var)

    return {
        "ticker": ticker,
        "position": position,
        "strike_variance": round(strike_var, 6),
        "strike_vol_pct": round(strike_vol * 100, 2),
        "accrued_realized_var": round(accrued_rv, 6),
        "accrued_realized_vol_pct": round(sqrt(accrued_rv) * 100, 2),
        "days_elapsed": days_elapsed,
        "days_remaining": total_days - days_elapsed,
        "weight_elapsed": round(weight_elapsed, 4),
        "projected_final_var": round(projected_var, 6),
        "vega_notional": notional,
        "variance_notional": round(var_notional, 2),
        "estimated_pnl": round(pnl, 2),
        "accrued_pnl": round(accrued_pnl, 2),
        "breakeven_vol_remaining": round(sqrt(max(0, (strike_var - weight_elapsed * accrued_rv) / max(1 - weight_elapsed, 0.01))) * 100, 2),
    }


def variance_term_structure(ticker: str = "SPY") -> Dict[str, Any]:
    """
    Calculate realized variance term structure across multiple horizons.

    Returns:
        Annualized realized variance for 1W, 1M, 3M, 6M, 1Y windows
    """
    try:
        import yfinance as yf
        data = yf.download(ticker, period="2y", progress=False)
        prices = data["Close"].dropna().values.flatten()
        returns = np.log(prices[1:] / prices[:-1])
    except Exception:
        return {"error": f"Could not fetch data for {ticker}"}

    windows = {"1W": 5, "2W": 10, "1M": 21, "3M": 63, "6M": 126, "1Y": 252}
    term_structure = []
    for label, w in windows.items():
        if len(returns) >= w:
            rv = float(np.var(returns[-w:]) * 252)
            term_structure.append({
                "tenor": label,
                "days": w,
                "realized_var": round(rv, 6),
                "realized_vol_pct": round(sqrt(rv) * 100, 2),
            })

    # Contango/backwardation
    if len(term_structure) >= 2:
        short_vol = term_structure[0]["realized_vol_pct"]
        long_vol = term_structure[-1]["realized_vol_pct"]
        shape = "contango" if long_vol > short_vol else "backwardation"
    else:
        shape = "unknown"

    return {
        "ticker": ticker,
        "term_structure": term_structure,
        "curve_shape": shape,
    }
