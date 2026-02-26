"""Optimal F Calculator — Ralph Vince's position sizing method for maximizing geometric growth.

Computes the optimal fraction of capital to risk per trade that maximizes the terminal
wealth ratio (TWR). Includes fractional Kelly comparison and risk-of-ruin estimates.
"""

import numpy as np
from typing import Dict, List, Optional


def compute_optimal_f(trade_returns: List[float], resolution: int = 1000) -> Dict:
    """Find optimal f by brute-force search over [0, 1].

    Args:
        trade_returns: List of trade P&L as fraction of risked capital
                       (e.g., +0.05 = 5% gain, -0.03 = 3% loss).
        resolution: Number of f values to test.

    Returns:
        Dict with optimal_f, twr, geometric_mean, and comparison table.
    """
    returns = np.array(trade_returns, dtype=float)
    if len(returns) == 0:
        return {"error": "No trades provided"}

    worst_loss = float(np.min(returns))
    if worst_loss >= 0:
        return {"error": "No losing trades — optimal f is undefined (risk everything)"}

    best_f = 0.0
    best_twr = 1.0
    results = []

    for i in range(1, resolution + 1):
        f = i / resolution
        # HPR = 1 + f * (-return / worst_loss)
        hpr = 1 + f * (-returns / worst_loss)
        if np.any(hpr <= 0):
            break
        twr = float(np.prod(hpr))
        geo_mean = float(twr ** (1.0 / len(returns)))
        if twr > best_twr:
            best_twr = twr
            best_f = f
        if i % (resolution // 10) == 0:
            results.append({"f": round(f, 4), "twr": round(twr, 4), "geo_mean": round(geo_mean, 6)})

    optimal_hpr = 1 + best_f * (-returns / worst_loss)
    geo_mean = float(np.prod(optimal_hpr) ** (1.0 / len(returns)))

    return {
        "optimal_f": round(best_f, 4),
        "terminal_wealth_ratio": round(best_twr, 4),
        "geometric_mean": round(geo_mean, 6),
        "worst_loss": round(worst_loss, 6),
        "n_trades": len(returns),
        "win_rate": round(float(np.mean(returns > 0)), 4),
        "avg_win": round(float(np.mean(returns[returns > 0])), 6) if np.any(returns > 0) else 0.0,
        "avg_loss": round(float(np.mean(returns[returns < 0])), 6) if np.any(returns < 0) else 0.0,
        "sample_f_table": results,
    }


def kelly_vs_optimal_f(trade_returns: List[float]) -> Dict:
    """Compare Kelly Criterion with Optimal F for the same trade series.

    Kelly = (win_rate * avg_win/avg_loss - (1 - win_rate)) / (avg_win/avg_loss)
    """
    returns = np.array(trade_returns, dtype=float)
    wins = returns[returns > 0]
    losses = returns[returns < 0]

    if len(wins) == 0 or len(losses) == 0:
        return {"error": "Need both winning and losing trades"}

    win_rate = len(wins) / len(returns)
    avg_win = float(np.mean(wins))
    avg_loss = float(np.mean(np.abs(losses)))
    win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')

    kelly_f = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio if win_loss_ratio > 0 else 0.0
    kelly_f = max(0.0, kelly_f)

    opt = compute_optimal_f(trade_returns)

    return {
        "kelly_fraction": round(kelly_f, 4),
        "half_kelly": round(kelly_f / 2, 4),
        "quarter_kelly": round(kelly_f / 4, 4),
        "optimal_f": opt.get("optimal_f", 0.0),
        "win_rate": round(win_rate, 4),
        "win_loss_ratio": round(win_loss_ratio, 4),
        "recommendation": "half_kelly" if kelly_f > 0.25 else "kelly",
    }


def risk_of_ruin(win_rate: float, win_loss_ratio: float, risk_per_trade: float,
                  ruin_threshold: float = 0.5) -> Dict:
    """Estimate probability of drawdown exceeding ruin_threshold.

    Uses simplified formula: RoR = ((1 - edge) / (1 + edge)) ^ units
    where edge = win_rate * (1 + win_loss_ratio) - 1
    """
    edge = win_rate * (1 + win_loss_ratio) - 1
    if edge <= 0:
        return {"risk_of_ruin": 1.0, "edge": round(edge, 4), "status": "negative_edge"}

    units = ruin_threshold / risk_per_trade if risk_per_trade > 0 else float('inf')
    ratio = (1 - edge) / (1 + edge) if edge < 1 else 0.0
    ror = ratio ** units if ratio > 0 else 0.0

    return {
        "risk_of_ruin": round(float(ror), 6),
        "edge": round(edge, 4),
        "risk_per_trade": round(risk_per_trade, 4),
        "ruin_threshold": round(ruin_threshold, 4),
        "units_to_ruin": round(float(units), 1),
        "status": "safe" if ror < 0.01 else "caution" if ror < 0.05 else "dangerous",
    }
