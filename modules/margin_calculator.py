"""Margin Calculator — Reg-T, Portfolio Margin, and SPAN estimation.

Calculates margin requirements under different methodologies:
- Reg-T: Standard rule-based margin (50% initial, 25% maintenance)
- Portfolio Margin: Risk-based using theoretical price scenarios
- SPAN: CME-style margin for futures and options

Roadmap #248: Margin Calculator (SPAN/Reg-T/portfolio margin)
"""

import math
from typing import Any


# Reg-T constants
REG_T_INITIAL = 0.50       # 50% initial margin
REG_T_MAINTENANCE = 0.25   # 25% maintenance margin
REG_T_SHORT_INITIAL = 0.50
REG_T_SHORT_MAINTENANCE = 0.30

# Options margin multipliers
OPTION_MULTIPLIER = 100

# Sample SPAN parameters (per contract)
SPAN_MARGINS = {
    "ES": {"initial": 12_650, "maintenance": 11_500},
    "NQ": {"initial": 18_700, "maintenance": 17_000},
    "CL": {"initial": 7_700, "maintenance": 7_000},
    "GC": {"initial": 10_200, "maintenance": 9_300},
    "ZB": {"initial": 2_500, "maintenance": 2_000},
    "SI": {"initial": 14_000, "maintenance": 12_700},
    "NG": {"initial": 4_500, "maintenance": 4_100},
    "ZC": {"initial": 1_650, "maintenance": 1_500},
    "6E": {"initial": 2_500, "maintenance": 2_300},
    "YM": {"initial": 9_500, "maintenance": 8_600},
}


def calc_reg_t_equity(
    positions: list[dict],
) -> dict[str, Any]:
    """Calculate Reg-T margin for equity positions.

    Args:
        positions: List of dicts with keys: ticker, shares, price, side ('long'/'short').

    Returns:
        Dict with initial margin, maintenance margin, and per-position details.
    """
    details = []
    total_initial = 0.0
    total_maintenance = 0.0
    total_market_value = 0.0

    for pos in positions:
        shares = abs(pos.get("shares", 0))
        price = pos.get("price", 0)
        side = pos.get("side", "long").lower()
        market_value = shares * price

        if side == "long":
            initial = market_value * REG_T_INITIAL
            maintenance = market_value * REG_T_MAINTENANCE
        else:
            initial = market_value * REG_T_SHORT_INITIAL
            maintenance = market_value * REG_T_SHORT_MAINTENANCE

        details.append({
            "ticker": pos.get("ticker", "UNK"),
            "side": side,
            "shares": shares,
            "price": price,
            "market_value": round(market_value, 2),
            "initial_margin": round(initial, 2),
            "maintenance_margin": round(maintenance, 2),
        })

        total_initial += initial
        total_maintenance += maintenance
        total_market_value += market_value

    return {
        "methodology": "Reg-T",
        "total_market_value": round(total_market_value, 2),
        "total_initial_margin": round(total_initial, 2),
        "total_maintenance_margin": round(total_maintenance, 2),
        "positions": details,
    }


def calc_span_futures(
    positions: list[dict],
) -> dict[str, Any]:
    """Calculate SPAN-style margin for futures positions.

    Args:
        positions: List of dicts with keys: symbol, contracts.

    Returns:
        Dict with SPAN margin requirements.
    """
    details = []
    total_initial = 0.0
    total_maintenance = 0.0

    for pos in positions:
        symbol = pos.get("symbol", "").upper()
        contracts = abs(pos.get("contracts", 0))
        margins = SPAN_MARGINS.get(symbol)

        if not margins:
            details.append({
                "symbol": symbol,
                "contracts": contracts,
                "error": f"No SPAN data for {symbol}",
            })
            continue

        initial = contracts * margins["initial"]
        maintenance = contracts * margins["maintenance"]

        details.append({
            "symbol": symbol,
            "contracts": contracts,
            "initial_per_contract": margins["initial"],
            "maintenance_per_contract": margins["maintenance"],
            "initial_margin": initial,
            "maintenance_margin": maintenance,
        })

        total_initial += initial
        total_maintenance += maintenance

    return {
        "methodology": "SPAN",
        "total_initial_margin": round(total_initial, 2),
        "total_maintenance_margin": round(total_maintenance, 2),
        "positions": details,
    }


def calc_portfolio_margin(
    positions: list[dict],
    scenarios: int = 10,
    max_move_pct: float = 0.15,
) -> dict[str, Any]:
    """Estimate portfolio margin using theoretical price scenarios.

    Simulates portfolio P&L under a range of up/down moves and
    uses the worst-case loss as the margin requirement.

    Args:
        positions: List of dicts with keys: ticker, shares, price, beta, side.
        scenarios: Number of scenarios per direction.
        max_move_pct: Maximum market move to simulate.

    Returns:
        Dict with portfolio margin estimate.
    """
    moves = []
    for i in range(1, scenarios + 1):
        pct = max_move_pct * i / scenarios
        moves.append(pct)
        moves.append(-pct)
    moves.append(0.0)

    worst_loss = 0.0
    worst_scenario = 0.0

    for move in moves:
        pnl = 0.0
        for pos in positions:
            shares = pos.get("shares", 0)
            price = pos.get("price", 0)
            beta = pos.get("beta", 1.0)
            side_mult = 1 if pos.get("side", "long").lower() == "long" else -1

            stock_move = move * beta
            position_pnl = side_mult * shares * price * stock_move
            pnl += position_pnl

        if pnl < worst_loss:
            worst_loss = pnl
            worst_scenario = move

    margin_req = abs(worst_loss)
    total_mv = sum(abs(p.get("shares", 0) * p.get("price", 0)) for p in positions)

    return {
        "methodology": "Portfolio Margin (estimated)",
        "total_market_value": round(total_mv, 2),
        "margin_requirement": round(margin_req, 2),
        "margin_pct": round(margin_req / total_mv * 100, 2) if total_mv else 0,
        "worst_case_loss": round(worst_loss, 2),
        "worst_scenario_move": round(worst_scenario * 100, 2),
        "scenarios_tested": len(moves),
    }


def compare_methodologies(
    equity_positions: list[dict],
    futures_positions: list[dict] | None = None,
) -> dict[str, Any]:
    """Compare margin requirements across methodologies.

    Args:
        equity_positions: Equity positions for Reg-T and Portfolio Margin.
        futures_positions: Futures positions for SPAN.

    Returns:
        Comparison of all applicable margin calculations.
    """
    reg_t = calc_reg_t_equity(equity_positions)
    pm = calc_portfolio_margin(equity_positions)

    result = {
        "reg_t_initial": reg_t["total_initial_margin"],
        "reg_t_maintenance": reg_t["total_maintenance_margin"],
        "portfolio_margin": pm["margin_requirement"],
        "pm_savings_vs_reg_t": round(
            (1 - pm["margin_requirement"] / reg_t["total_initial_margin"]) * 100, 1
        ) if reg_t["total_initial_margin"] > 0 else 0,
    }

    if futures_positions:
        span = calc_span_futures(futures_positions)
        result["span_initial"] = span["total_initial_margin"]
        result["span_maintenance"] = span["total_maintenance_margin"]

    return result
