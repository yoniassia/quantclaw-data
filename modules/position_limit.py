"""Position Limit Monitor — regulatory and internal limit tracking.

Monitors positions against exchange-imposed position limits, regulatory
thresholds (e.g., SEC 13D/13G ownership reporting), and internal risk
limits. Alerts when approaching or breaching limits.

Roadmap #247: Position Limit Monitor (reg limits per exchange)
"""

import datetime
from typing import Any


# Common regulatory thresholds (US)
REGULATORY_THRESHOLDS = {
    "sec_13g_passive": 0.05,      # 5% passive investor filing
    "sec_13d_activist": 0.05,     # 5% activist filing
    "sec_16_insider": 0.10,       # 10% beneficial owner
    "hsr_threshold_usd": 111_400_000,  # Hart-Scott-Rodino 2024 threshold
    "cftc_spec_limit_default": 25_000,  # Default CFTC speculative limit (contracts)
}

# Sample exchange position limits (futures contracts)
EXCHANGE_LIMITS = {
    "ES": {"exchange": "CME", "spot_month": 20_000, "all_months": 200_000},
    "NQ": {"exchange": "CME", "spot_month": 10_000, "all_months": 100_000},
    "CL": {"exchange": "NYMEX", "spot_month": 6_000, "all_months": 30_000},
    "GC": {"exchange": "COMEX", "spot_month": 6_000, "all_months": 30_000},
    "ZB": {"exchange": "CBOT", "spot_month": 25_000, "all_months": 100_000},
    "SI": {"exchange": "COMEX", "spot_month": 6_000, "all_months": 30_000},
    "NG": {"exchange": "NYMEX", "spot_month": 1_000, "all_months": 10_000},
    "ZC": {"exchange": "CBOT", "spot_month": 33_000, "all_months": 600_000},
}


def check_equity_ownership_threshold(
    ticker: str,
    shares_held: int,
    shares_outstanding: int,
) -> dict[str, Any]:
    """Check equity position against SEC ownership reporting thresholds.

    Args:
        ticker: Stock ticker.
        shares_held: Current shares held.
        shares_outstanding: Total shares outstanding.

    Returns:
        Dict with ownership percentage and triggered thresholds.
    """
    if shares_outstanding <= 0:
        return {"ticker": ticker, "error": "Invalid shares outstanding"}

    pct = shares_held / shares_outstanding
    triggered = []

    if pct >= REGULATORY_THRESHOLDS["sec_16_insider"]:
        triggered.append({"rule": "SEC 16 (10% beneficial owner)", "threshold": 0.10})
    if pct >= REGULATORY_THRESHOLDS["sec_13d_activist"]:
        triggered.append({"rule": "SEC 13D/13G (5% ownership)", "threshold": 0.05})

    warning_pct = 0.04  # Warn at 4%
    approaching = pct >= warning_pct and pct < 0.05

    return {
        "ticker": ticker,
        "shares_held": shares_held,
        "shares_outstanding": shares_outstanding,
        "ownership_pct": round(pct * 100, 4),
        "triggered_thresholds": triggered,
        "approaching_threshold": approaching,
        "status": "BREACH" if triggered else ("WARNING" if approaching else "OK"),
    }


def check_futures_position_limit(
    symbol: str,
    net_contracts: int,
    is_spot_month: bool = False,
) -> dict[str, Any]:
    """Check futures position against exchange position limits.

    Args:
        symbol: Futures root symbol (e.g., 'ES', 'CL').
        net_contracts: Net position in contracts (absolute value used).
        is_spot_month: Whether position is in spot/delivery month.

    Returns:
        Dict with limit check results.
    """
    limits = EXCHANGE_LIMITS.get(symbol.upper())
    if not limits:
        return {"symbol": symbol, "error": f"No limits data for {symbol}", "status": "UNKNOWN"}

    abs_contracts = abs(net_contracts)
    limit_key = "spot_month" if is_spot_month else "all_months"
    limit = limits[limit_key]
    utilization = abs_contracts / limit if limit > 0 else 0

    if utilization >= 1.0:
        status = "BREACH"
    elif utilization >= 0.80:
        status = "WARNING"
    else:
        status = "OK"

    return {
        "symbol": symbol,
        "exchange": limits["exchange"],
        "net_contracts": net_contracts,
        "abs_contracts": abs_contracts,
        "limit": limit,
        "limit_type": limit_key,
        "utilization_pct": round(utilization * 100, 2),
        "status": status,
    }


def check_hsr_threshold(
    transaction_value_usd: float,
    threshold_usd: float | None = None,
) -> dict[str, Any]:
    """Check if transaction triggers Hart-Scott-Rodino filing.

    Args:
        transaction_value_usd: Total transaction value.
        threshold_usd: HSR threshold (default: 2024 threshold).

    Returns:
        Dict with HSR filing requirement.
    """
    t = threshold_usd or REGULATORY_THRESHOLDS["hsr_threshold_usd"]
    triggered = transaction_value_usd >= t
    return {
        "transaction_value_usd": transaction_value_usd,
        "hsr_threshold_usd": t,
        "filing_required": triggered,
        "status": "FILING_REQUIRED" if triggered else "OK",
    }


def monitor_portfolio_limits(
    positions: list[dict],
    internal_limits: dict | None = None,
) -> dict[str, Any]:
    """Monitor all positions against regulatory and internal limits.

    Args:
        positions: List of position dicts with keys:
            - ticker/symbol, shares/contracts, type ('equity'/'futures'),
            - shares_outstanding (for equity), is_spot_month (for futures),
            - position_value_usd
        internal_limits: Optional dict of ticker -> max_position_usd.

    Returns:
        Summary of all limit checks with alerts.
    """
    results = []
    alerts = []
    internal = internal_limits or {}

    for pos in positions:
        pos_type = pos.get("type", "equity")

        if pos_type == "equity":
            check = check_equity_ownership_threshold(
                pos.get("ticker", "UNK"),
                pos.get("shares", 0),
                pos.get("shares_outstanding", 1),
            )
        elif pos_type == "futures":
            check = check_futures_position_limit(
                pos.get("symbol", "UNK"),
                pos.get("contracts", 0),
                pos.get("is_spot_month", False),
            )
        else:
            check = {"status": "UNKNOWN", "type": pos_type}

        # Internal limit check
        name = pos.get("ticker") or pos.get("symbol", "UNK")
        if name in internal:
            val = pos.get("position_value_usd", 0)
            lim = internal[name]
            if val > lim:
                check["internal_limit_breach"] = True
                check["internal_limit"] = lim
                check["position_value"] = val
                if check.get("status") != "BREACH":
                    check["status"] = "BREACH"

        results.append(check)
        if check.get("status") in ("BREACH", "WARNING"):
            alerts.append(check)

    return {
        "total_positions": len(positions),
        "checks": results,
        "alerts": alerts,
        "alert_count": len(alerts),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
