"""Time-Series Momentum (Moskowitz-Ooi-Pedersen 2012) — Goes long assets with positive
past returns and short assets with negative past returns. Unlike cross-sectional momentum
which is relative, TSMOM is absolute: each asset's own past return determines direction.

Covers 58+ liquid futures across equities, bonds, currencies, and commodities.
Data sources: Yahoo Finance, FRED (free).
"""

import math
from typing import Dict, List, Optional, Tuple


def tsmom_signal(
    returns: List[float],
    lookback: int = 12,
    volatility_target: float = 0.40,
) -> Dict[str, float]:
    """Compute time-series momentum signal for a single asset.

    Args:
        returns: Monthly returns (most recent last).
        lookback: Formation period in months (default 12).
        volatility_target: Annualized vol target for position sizing.

    Returns:
        Signal dict with direction, magnitude, and vol-scaled position.
    """
    if len(returns) < lookback:
        return {"signal": 0, "cum_return": 0, "position": 0, "vol": 0}

    formation_returns = returns[-lookback:]
    cum_return = 1.0
    for r in formation_returns:
        cum_return *= (1 + r)
    cum_return -= 1.0

    # Realized vol (annualized from monthly)
    mean_r = sum(formation_returns) / len(formation_returns)
    var = sum((r - mean_r) ** 2 for r in formation_returns) / len(formation_returns)
    monthly_vol = math.sqrt(var) if var > 0 else 0.01
    annual_vol = monthly_vol * math.sqrt(12)

    # Signal: sign of excess return
    signal = 1.0 if cum_return > 0 else -1.0

    # Vol-scaled position (Moskowitz et al. scaling)
    position = signal * (volatility_target / annual_vol) if annual_vol > 0 else 0

    return {
        "signal": signal,
        "cum_return": round(cum_return, 6),
        "position": round(position, 4),
        "annual_vol": round(annual_vol, 6),
        "monthly_vol": round(monthly_vol, 6),
    }


def tsmom_portfolio(
    asset_returns: Dict[str, List[float]],
    lookback: int = 12,
    volatility_target: float = 0.40,
    max_leverage: float = 5.0,
) -> Dict[str, object]:
    """Construct a diversified time-series momentum portfolio across multiple assets.

    Args:
        asset_returns: Dict of asset_name -> list of monthly returns.
        lookback: Formation period in months.
        volatility_target: Per-asset annualized vol target.
        max_leverage: Maximum absolute leverage per asset.

    Returns:
        Portfolio with positions, gross/net exposure, and asset-level signals.
    """
    positions = {}
    signals = {}

    for asset, rets in asset_returns.items():
        sig = tsmom_signal(rets, lookback, volatility_target)
        signals[asset] = sig
        pos = max(-max_leverage, min(max_leverage, sig["position"]))
        positions[asset] = round(pos, 4)

    gross_exposure = sum(abs(p) for p in positions.values())
    net_exposure = sum(p for p in positions.values())
    n_long = sum(1 for p in positions.values() if p > 0)
    n_short = sum(1 for p in positions.values() if p < 0)

    return {
        "positions": positions,
        "signals": signals,
        "gross_exposure": round(gross_exposure, 4),
        "net_exposure": round(net_exposure, 4),
        "n_assets": len(positions),
        "n_long": n_long,
        "n_short": n_short,
        "avg_abs_position": round(gross_exposure / len(positions), 4) if positions else 0,
    }


def tsmom_backtest(
    asset_returns: Dict[str, List[float]],
    lookback: int = 12,
    volatility_target: float = 0.40,
    max_leverage: float = 5.0,
) -> Dict[str, object]:
    """Backtest the TSMOM strategy over historical data.

    Args:
        asset_returns: Dict of asset -> monthly returns (same length, aligned).
        lookback: Signal formation period.
        volatility_target: Per-asset vol target.
        max_leverage: Position cap.

    Returns:
        Backtest statistics.
    """
    # Find min length across all assets
    min_len = min(len(r) for r in asset_returns.values()) if asset_returns else 0
    if min_len <= lookback:
        return {"error": f"Need > {lookback} months, have {min_len}"}

    n_assets = len(asset_returns)
    portfolio_returns = []

    for t in range(lookback, min_len):
        period_return = 0.0
        for asset, rets in asset_returns.items():
            sig = tsmom_signal(rets[:t], lookback, volatility_target)
            pos = max(-max_leverage, min(max_leverage, sig["position"]))
            # Scale by 1/N for equal risk budget
            period_return += (pos / n_assets) * rets[t]
        portfolio_returns.append(round(period_return, 8))

    if not portfolio_returns:
        return {"error": "No valid periods"}

    avg = sum(portfolio_returns) / len(portfolio_returns)
    var = sum((r - avg) ** 2 for r in portfolio_returns) / len(portfolio_returns)
    std = math.sqrt(var) if var > 0 else 0.001
    annual_ret = avg * 12
    annual_vol = std * math.sqrt(12)

    # Max drawdown
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in portfolio_returns:
        cumulative *= (1 + r)
        peak = max(peak, cumulative)
        dd = (peak - cumulative) / peak
        max_dd = max(max_dd, dd)

    return {
        "n_periods": len(portfolio_returns),
        "annual_return": round(annual_ret, 6),
        "annual_vol": round(annual_vol, 6),
        "sharpe_ratio": round(annual_ret / annual_vol, 4) if annual_vol > 0 else 0,
        "max_drawdown": round(max_dd, 6),
        "hit_rate": round(sum(1 for r in portfolio_returns if r > 0) / len(portfolio_returns), 4),
        "cumulative_return": round(
            math.prod(1 + r for r in portfolio_returns) - 1, 6
        ),
        "skewness": round(
            sum((r - avg) ** 3 for r in portfolio_returns)
            / (len(portfolio_returns) * std ** 3)
            if std > 0 else 0,
            4,
        ),
    }
