"""Cross-Sectional Momentum (Jegadeesh-Titman) — Ranks stocks by past returns and
constructs long-short portfolios buying winners and selling losers. Implements the
classic 1993 Jegadeesh-Titman momentum strategy with configurable formation and
holding periods.

Data sources: Yahoo Finance (free historical prices).
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


def compute_momentum_scores(
    returns: Dict[str, float],
    skip_last_month: bool = True,
) -> List[Tuple[str, float]]:
    """Rank assets by momentum (past cumulative return).

    Args:
        returns: Dict mapping ticker -> cumulative return over formation period.
                 If skip_last_month is True, these should exclude the most recent month
                 (short-term reversal adjustment per Jegadeesh-Titman).
        skip_last_month: Whether the input already skips the last month (documentation flag).

    Returns:
        Sorted list of (ticker, return) tuples, highest momentum first.
    """
    ranked = sorted(returns.items(), key=lambda x: x[1], reverse=True)
    return ranked


def construct_long_short_portfolio(
    ranked_assets: List[Tuple[str, float]],
    n_long: int = 10,
    n_short: int = 10,
    equal_weight: bool = True,
) -> Dict[str, Dict[str, float]]:
    """Construct a long-short momentum portfolio from ranked assets.

    Args:
        ranked_assets: Sorted list from compute_momentum_scores (best first).
        n_long: Number of assets in long leg (top momentum).
        n_short: Number of assets in short leg (bottom momentum).
        equal_weight: If True, equal-weight within each leg.

    Returns:
        Dict with 'long', 'short' keys mapping to {ticker: weight} dicts.
    """
    if len(ranked_assets) < n_long + n_short:
        raise ValueError(
            f"Need at least {n_long + n_short} assets, got {len(ranked_assets)}"
        )

    long_assets = ranked_assets[:n_long]
    short_assets = ranked_assets[-n_short:]

    if equal_weight:
        long_w = 1.0 / n_long
        short_w = 1.0 / n_short
    else:
        # Momentum-weighted
        long_total = sum(abs(r) for _, r in long_assets) or 1.0
        short_total = sum(abs(r) for _, r in short_assets) or 1.0
        long_w = None
        short_w = None

    long_portfolio = {}
    short_portfolio = {}

    for ticker, ret in long_assets:
        w = long_w if equal_weight else abs(ret) / long_total
        long_portfolio[ticker] = round(w, 6)

    for ticker, ret in short_assets:
        w = short_w if equal_weight else abs(ret) / short_total
        short_portfolio[ticker] = round(w, 6)

    return {
        "long": long_portfolio,
        "short": short_portfolio,
        "n_long": n_long,
        "n_short": n_short,
        "long_avg_return": round(sum(r for _, r in long_assets) / n_long, 6),
        "short_avg_return": round(sum(r for _, r in short_assets) / n_short, 6),
        "spread": round(
            sum(r for _, r in long_assets) / n_long
            - sum(r for _, r in short_assets) / n_short,
            6,
        ),
    }


def momentum_backtest(
    price_data: Dict[str, List[Tuple[str, float]]],
    formation_months: int = 12,
    holding_months: int = 1,
    skip_month: bool = True,
    n_long: int = 10,
    n_short: int = 10,
) -> Dict[str, object]:
    """Backtest Jegadeesh-Titman cross-sectional momentum strategy.

    Args:
        price_data: Dict of ticker -> list of (date_str, price) monthly observations,
                    sorted chronologically.
        formation_months: Lookback period for ranking (default 12 = J12).
        holding_months: Holding period (default 1 = K1).
        skip_month: Skip most recent month in formation (reversal adjustment).
        n_long: Number of long positions.
        n_short: Number of short positions.

    Returns:
        Backtest results with period returns and summary statistics.
    """
    # Get all unique dates across tickers
    all_dates = set()
    for ticker, prices in price_data.items():
        for date_str, _ in prices:
            all_dates.add(date_str)
    sorted_dates = sorted(all_dates)

    required_months = formation_months + (1 if skip_month else 0) + holding_months
    if len(sorted_dates) < required_months:
        return {"error": f"Need {required_months} months of data, have {len(sorted_dates)}"}

    # Build price lookup
    price_lookup: Dict[str, Dict[str, float]] = {}
    for ticker, prices in price_data.items():
        price_lookup[ticker] = {d: p for d, p in prices}

    period_returns = []
    start_idx = formation_months + (1 if skip_month else 0)

    for i in range(start_idx, len(sorted_dates) - holding_months + 1, holding_months):
        formation_start = i - formation_months - (1 if skip_month else 0)
        formation_end = i - (1 if skip_month else 0)
        hold_end = min(i + holding_months, len(sorted_dates)) - 1

        # Compute formation returns
        returns = {}
        for ticker in price_data:
            start_date = sorted_dates[formation_start]
            end_date = sorted_dates[formation_end]
            if start_date in price_lookup[ticker] and end_date in price_lookup[ticker]:
                p0 = price_lookup[ticker][start_date]
                p1 = price_lookup[ticker][end_date]
                if p0 > 0:
                    returns[ticker] = (p1 - p0) / p0

        if len(returns) < n_long + n_short:
            continue

        ranked = compute_momentum_scores(returns)
        portfolio = construct_long_short_portfolio(ranked, n_long, n_short)

        # Compute holding period return
        hold_start_date = sorted_dates[i]
        hold_end_date = sorted_dates[hold_end]
        long_ret = 0.0
        short_ret = 0.0

        for ticker, w in portfolio["long"].items():
            if hold_start_date in price_lookup[ticker] and hold_end_date in price_lookup[ticker]:
                p0 = price_lookup[ticker][hold_start_date]
                p1 = price_lookup[ticker][hold_end_date]
                if p0 > 0:
                    long_ret += w * (p1 - p0) / p0

        for ticker, w in portfolio["short"].items():
            if hold_start_date in price_lookup[ticker] and hold_end_date in price_lookup[ticker]:
                p0 = price_lookup[ticker][hold_start_date]
                p1 = price_lookup[ticker][hold_end_date]
                if p0 > 0:
                    short_ret += w * (p1 - p0) / p0

        period_returns.append({
            "date": hold_start_date,
            "long_return": round(long_ret, 6),
            "short_return": round(short_ret, 6),
            "spread_return": round(long_ret - short_ret, 6),
        })

    if not period_returns:
        return {"error": "No valid periods for backtest"}

    spreads = [p["spread_return"] for p in period_returns]
    avg = sum(spreads) / len(spreads)
    var = sum((s - avg) ** 2 for s in spreads) / len(spreads) if len(spreads) > 1 else 0
    std = var ** 0.5

    return {
        "formation_months": formation_months,
        "holding_months": holding_months,
        "skip_month": skip_month,
        "n_periods": len(period_returns),
        "avg_spread_return": round(avg, 6),
        "std_spread_return": round(std, 6),
        "sharpe_ratio": round(avg / std, 4) if std > 0 else 0,
        "hit_rate": round(sum(1 for s in spreads if s > 0) / len(spreads), 4),
        "max_spread": round(max(spreads), 6),
        "min_spread": round(min(spreads), 6),
        "period_returns": period_returns,
    }
