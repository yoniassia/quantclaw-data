"""Compliance Pre-Trade Check Engine — automated rule-based order validation.

Validates proposed trades against configurable compliance rules including
position limits, concentration limits, restricted lists, and wash sale
prevention. Designed for institutional order management workflows.

Roadmap #246: Compliance Pre-Trade Check Engine
"""

import datetime
from typing import Any


DEFAULT_RULES = {
    "max_position_pct": 0.10,       # Max 10% of portfolio in single name
    "max_sector_pct": 0.30,         # Max 30% in a single sector
    "max_order_pct_adv": 0.25,      # Max 25% of average daily volume
    "restricted_list": [],           # Restricted tickers
    "wash_sale_window_days": 30,     # Wash sale lookback
    "max_single_order_usd": 5_000_000,
    "min_market_cap_usd": 100_000_000,  # No micro-caps
}


def check_position_concentration(
    ticker: str,
    order_value_usd: float,
    current_position_usd: float,
    portfolio_nav: float,
    max_pct: float = 0.10,
) -> dict[str, Any]:
    """Check if order would breach single-name concentration limits.

    Args:
        ticker: Security ticker.
        order_value_usd: Proposed order value.
        current_position_usd: Current position value in this name.
        portfolio_nav: Total portfolio NAV.
        max_pct: Maximum allowed percentage.

    Returns:
        Dict with pass/fail, current and projected concentrations.
    """
    if portfolio_nav <= 0:
        return {"ticker": ticker, "passed": False, "reason": "Invalid NAV"}

    current_pct = current_position_usd / portfolio_nav
    projected_pct = (current_position_usd + order_value_usd) / portfolio_nav

    passed = projected_pct <= max_pct
    return {
        "ticker": ticker,
        "check": "position_concentration",
        "passed": passed,
        "current_pct": round(current_pct * 100, 2),
        "projected_pct": round(projected_pct * 100, 2),
        "limit_pct": round(max_pct * 100, 2),
        "reason": None if passed else f"Projected {projected_pct*100:.1f}% exceeds {max_pct*100:.0f}% limit",
    }


def check_restricted_list(
    ticker: str, restricted: list[str]
) -> dict[str, Any]:
    """Check if ticker is on restricted/banned list.

    Args:
        ticker: Security ticker.
        restricted: List of restricted tickers.

    Returns:
        Dict with pass/fail result.
    """
    is_restricted = ticker.upper() in [r.upper() for r in restricted]
    return {
        "ticker": ticker,
        "check": "restricted_list",
        "passed": not is_restricted,
        "reason": f"{ticker} is on restricted list" if is_restricted else None,
    }


def check_adv_limit(
    ticker: str,
    order_shares: int,
    avg_daily_volume: int,
    max_pct_adv: float = 0.25,
) -> dict[str, Any]:
    """Check if order size exceeds percentage of average daily volume.

    Args:
        ticker: Security ticker.
        order_shares: Proposed order size in shares.
        avg_daily_volume: Average daily volume.
        max_pct_adv: Maximum allowed percentage of ADV.

    Returns:
        Dict with pass/fail result.
    """
    if avg_daily_volume <= 0:
        return {"ticker": ticker, "check": "adv_limit", "passed": False, "reason": "No volume data"}

    pct_adv = order_shares / avg_daily_volume
    passed = pct_adv <= max_pct_adv
    return {
        "ticker": ticker,
        "check": "adv_limit",
        "passed": passed,
        "order_pct_adv": round(pct_adv * 100, 2),
        "limit_pct_adv": round(max_pct_adv * 100, 2),
        "reason": None if passed else f"Order is {pct_adv*100:.1f}% of ADV (limit {max_pct_adv*100:.0f}%)",
    }


def check_wash_sale(
    ticker: str,
    side: str,
    recent_trades: list[dict],
    window_days: int = 30,
) -> dict[str, Any]:
    """Check for potential wash sale violations.

    Args:
        ticker: Security ticker.
        side: 'buy' or 'sell'.
        recent_trades: List of recent trades with keys: ticker, side, date.
        window_days: Lookback window in days.

    Returns:
        Dict with pass/fail and flagged trades.
    """
    today = datetime.date.today()
    opposite = "sell" if side.lower() == "buy" else "buy"
    flagged = []

    for t in recent_trades:
        if t.get("ticker", "").upper() != ticker.upper():
            continue
        if t.get("side", "").lower() != opposite:
            continue
        trade_date = t.get("date")
        if isinstance(trade_date, str):
            trade_date = datetime.date.fromisoformat(trade_date)
        if (today - trade_date).days <= window_days:
            flagged.append(t)

    passed = len(flagged) == 0
    return {
        "ticker": ticker,
        "check": "wash_sale",
        "passed": passed,
        "flagged_trades": len(flagged),
        "window_days": window_days,
        "reason": None if passed else f"{len(flagged)} opposite trades within {window_days}d window",
    }


def run_all_checks(
    ticker: str,
    side: str,
    order_shares: int,
    order_value_usd: float,
    current_position_usd: float,
    portfolio_nav: float,
    avg_daily_volume: int,
    recent_trades: list[dict] | None = None,
    rules: dict | None = None,
) -> dict[str, Any]:
    """Run full pre-trade compliance check suite.

    Args:
        ticker: Security ticker.
        side: 'buy' or 'sell'.
        order_shares: Proposed order size.
        order_value_usd: Proposed order value.
        current_position_usd: Current position value.
        portfolio_nav: Total portfolio NAV.
        avg_daily_volume: ADV for the security.
        recent_trades: Recent trade history.
        rules: Compliance rules dict (uses DEFAULT_RULES if None).

    Returns:
        Dict with all check results and overall pass/fail.
    """
    r = rules or DEFAULT_RULES
    checks = [
        check_position_concentration(ticker, order_value_usd, current_position_usd, portfolio_nav, r.get("max_position_pct", 0.10)),
        check_restricted_list(ticker, r.get("restricted_list", [])),
        check_adv_limit(ticker, order_shares, avg_daily_volume, r.get("max_order_pct_adv", 0.25)),
        check_wash_sale(ticker, side, recent_trades or [], r.get("wash_sale_window_days", 30)),
    ]

    # Order size check
    max_order = r.get("max_single_order_usd", 5_000_000)
    size_check = {
        "ticker": ticker,
        "check": "max_order_size",
        "passed": order_value_usd <= max_order,
        "order_usd": order_value_usd,
        "limit_usd": max_order,
        "reason": None if order_value_usd <= max_order else f"Order ${order_value_usd:,.0f} exceeds ${max_order:,.0f} limit",
    }
    checks.append(size_check)

    all_passed = all(c["passed"] for c in checks)
    failures = [c for c in checks if not c["passed"]]

    return {
        "ticker": ticker,
        "side": side,
        "all_passed": all_passed,
        "checks": checks,
        "failures": failures,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
