"""Kelly Criterion Position Sizer — optimal bet sizing for trading strategies.

Implements the Kelly Criterion and fractional Kelly for determining optimal
position sizes based on win rate, payoff ratios, and portfolio constraints.
"""

import datetime
import json
import math
import urllib.request
from typing import Dict, List, Optional, Tuple


def kelly_fraction(win_rate: float, win_loss_ratio: float) -> float:
    """Compute the Kelly fraction for a binary outcome bet.

    f* = (bp - q) / b
    where b = win/loss ratio, p = win probability, q = 1-p

    Args:
        win_rate: Probability of winning (0-1).
        win_loss_ratio: Average win / average loss.

    Returns:
        Optimal fraction of capital to risk.
    """
    if win_rate <= 0 or win_rate >= 1 or win_loss_ratio <= 0:
        return 0.0
    q = 1 - win_rate
    f = (win_loss_ratio * win_rate - q) / win_loss_ratio
    return max(f, 0.0)


def fractional_kelly(
    win_rate: float, win_loss_ratio: float, fraction: float = 0.5
) -> Dict:
    """Compute fractional Kelly for more conservative sizing.

    Args:
        win_rate: Win probability (0-1).
        win_loss_ratio: Avg win / avg loss.
        fraction: Kelly fraction (0.25=quarter, 0.5=half, 1.0=full).

    Returns:
        Dict with full kelly, fractional kelly, and expected growth.
    """
    full = kelly_fraction(win_rate, win_loss_ratio)
    frac = full * fraction

    # Expected geometric growth rate
    if full > 0:
        g_full = win_rate * math.log(1 + full * win_loss_ratio) + (1 - win_rate) * math.log(1 - full)
        g_frac = win_rate * math.log(1 + frac * win_loss_ratio) + (1 - win_rate) * math.log(1 - frac)
    else:
        g_full = 0
        g_frac = 0

    return {
        "full_kelly_pct": round(full * 100, 2),
        "fractional_kelly_pct": round(frac * 100, 2),
        "fraction_used": fraction,
        "expected_growth_full": round(g_full * 100, 4),
        "expected_growth_frac": round(g_frac * 100, 4),
        "edge": round((win_rate * win_loss_ratio - (1 - win_rate)) * 100, 2),
    }


def kelly_from_trades(trades: List[float]) -> Dict:
    """Compute Kelly sizing from a list of trade P&L values.

    Args:
        trades: List of trade returns (positive = win, negative = loss).

    Returns:
        Dict with kelly metrics derived from trade history.
    """
    if not trades:
        return {"error": "No trades provided"}

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t < 0]

    if not wins or not losses:
        return {"error": "Need both wins and losses to compute Kelly"}

    win_rate = len(wins) / len(trades)
    avg_win = sum(wins) / len(wins)
    avg_loss = abs(sum(losses) / len(losses))
    wl_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")

    result = fractional_kelly(win_rate, wl_ratio)
    result.update({
        "total_trades": len(trades),
        "win_rate": round(win_rate * 100, 2),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "win_loss_ratio": round(wl_ratio, 3),
        "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if sum(losses) != 0 else float("inf"),
    })
    return result


def position_size_calculator(
    account_size: float,
    win_rate: float,
    win_loss_ratio: float,
    kelly_fraction_used: float = 0.5,
    max_position_pct: float = 25.0,
    entry_price: Optional[float] = None,
    stop_loss_price: Optional[float] = None,
) -> Dict:
    """Calculate concrete position size in dollars and shares.

    Args:
        account_size: Total account value in dollars.
        win_rate: Historical win rate (0-1).
        win_loss_ratio: Average win / average loss.
        kelly_fraction_used: Kelly fraction (default half-Kelly).
        max_position_pct: Maximum position size as % of account.
        entry_price: Entry price per share (optional).
        stop_loss_price: Stop loss price (optional).

    Returns:
        Position sizing recommendation with dollar amounts.
    """
    fk = kelly_fraction(win_rate, win_loss_ratio) * kelly_fraction_used
    position_pct = min(fk * 100, max_position_pct)
    position_dollars = account_size * (position_pct / 100)

    result = {
        "account_size": account_size,
        "kelly_position_pct": round(position_pct, 2),
        "position_dollars": round(position_dollars, 2),
        "max_capped_at": max_position_pct,
    }

    if entry_price and entry_price > 0:
        shares = int(position_dollars / entry_price)
        result["entry_price"] = entry_price
        result["shares"] = shares
        result["actual_position"] = round(shares * entry_price, 2)

        if stop_loss_price and stop_loss_price > 0:
            risk_per_share = abs(entry_price - stop_loss_price)
            total_risk = risk_per_share * shares
            result["stop_loss"] = stop_loss_price
            result["risk_per_share"] = round(risk_per_share, 2)
            result["total_risk"] = round(total_risk, 2)
            result["risk_pct_of_account"] = round(total_risk / account_size * 100, 2)

    return result


def kelly_sensitivity_table(
    win_rate_range: Tuple[float, float] = (0.3, 0.7),
    wl_ratio_range: Tuple[float, float] = (0.5, 3.0),
    steps: int = 5,
) -> List[Dict]:
    """Generate a sensitivity table for Kelly fraction across parameters.

    Args:
        win_rate_range: (min, max) win rate to test.
        wl_ratio_range: (min, max) win/loss ratio.
        steps: Number of steps per dimension.

    Returns:
        List of dicts with parameter combinations and Kelly fractions.
    """
    wr_step = (win_rate_range[1] - win_rate_range[0]) / (steps - 1)
    wl_step = (wl_ratio_range[1] - wl_ratio_range[0]) / (steps - 1)

    table = []
    for i in range(steps):
        wr = win_rate_range[0] + i * wr_step
        for j in range(steps):
            wl = wl_ratio_range[0] + j * wl_step
            f = kelly_fraction(wr, wl)
            table.append({
                "win_rate": round(wr, 2),
                "wl_ratio": round(wl, 2),
                "full_kelly_pct": round(f * 100, 2),
                "half_kelly_pct": round(f * 50, 2),
                "has_edge": f > 0,
            })
    return table
