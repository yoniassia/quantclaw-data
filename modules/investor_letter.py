"""Investor Letter Generator — Generates quarterly/monthly investor letter content
with performance attribution, market commentary structure, and portfolio updates.
Uses free data sources for benchmarks and market context."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def generate_performance_table(fund_returns: Dict, benchmarks: Dict) -> Dict:
    """Generate a performance comparison table for investor letters.
    
    Args:
        fund_returns: Dict with keys like 'mtd', 'qtd', 'ytd', 'itd', 'si' (decimals)
        benchmarks: Dict of benchmark_name -> same return keys
    
    Returns:
        Formatted performance table data with alpha calculations
    """
    periods = ["mtd", "qtd", "ytd", "1yr", "3yr_ann", "5yr_ann", "itd_ann"]
    
    rows = [{"name": "Fund", **{p: round(fund_returns.get(p, 0) * 100, 2) for p in periods}}]
    
    alphas = {}
    for bm_name, bm_rets in benchmarks.items():
        row = {"name": bm_name}
        for p in periods:
            bm_val = bm_rets.get(p, 0)
            row[p] = round(bm_val * 100, 2)
            if p not in alphas:
                alphas[p] = []
            alphas[p].append(fund_returns.get(p, 0) - bm_val)
        rows.append(row)
    
    alpha_row = {"name": "Alpha (avg)"}
    for p in periods:
        if alphas.get(p):
            alpha_row[p] = round(sum(alphas[p]) / len(alphas[p]) * 100, 2)
    rows.append(alpha_row)
    
    return {
        "columns": periods,
        "rows": rows,
        "as_of_date": datetime.now().strftime("%Y-%m-%d")
    }


def generate_attribution_summary(contributors: List[Dict],
                                   detractors: List[Dict],
                                   sector_attribution: Optional[Dict] = None) -> Dict:
    """Generate performance attribution section for investor letter.
    
    Args:
        contributors: Top contributors [{'name': str, 'contribution_bps': float, 'narrative': str}]
        detractors: Top detractors (same format, negative bps)
        sector_attribution: Optional sector-level attribution dict
    
    Returns:
        Structured attribution data for letter generation
    """
    total_positive = sum(c.get("contribution_bps", 0) for c in contributors)
    total_negative = sum(d.get("contribution_bps", 0) for d in detractors)
    
    return {
        "top_contributors": [
            {
                "name": c["name"],
                "contribution_bps": c["contribution_bps"],
                "contribution_pct": round(c["contribution_bps"] / 100, 2),
                "narrative": c.get("narrative", "")
            } for c in sorted(contributors, key=lambda x: x["contribution_bps"], reverse=True)[:5]
        ],
        "top_detractors": [
            {
                "name": d["name"],
                "contribution_bps": d["contribution_bps"],
                "contribution_pct": round(d["contribution_bps"] / 100, 2),
                "narrative": d.get("narrative", "")
            } for d in sorted(detractors, key=lambda x: x["contribution_bps"])[:5]
        ],
        "net_attribution_bps": round(total_positive + total_negative, 2),
        "sector_attribution": sector_attribution,
        "concentration": {
            "top5_positive_bps": round(total_positive, 2),
            "top5_negative_bps": round(total_negative, 2)
        }
    }


def generate_letter_outline(period: str, fund_name: str, fund_return: float,
                              benchmark_return: float, aum: float,
                              market_themes: List[str],
                              positioning_changes: List[str],
                              outlook_points: List[str]) -> Dict:
    """Generate a structured investor letter outline.
    
    Args:
        period: e.g., 'Q4 2025', 'December 2025'
        fund_name: Fund name
        fund_return: Period gross return (decimal)
        benchmark_return: Benchmark return (decimal)
        aum: Assets under management
        market_themes: Key market themes for commentary
        positioning_changes: Notable portfolio changes
        outlook_points: Forward-looking views
    
    Returns:
        Complete letter outline with sections and suggested content
    """
    alpha = fund_return - benchmark_return
    outperformed = alpha > 0
    
    sections = [
        {
            "title": "Dear Investors",
            "type": "greeting",
            "guidance": f"Open with {period} summary. Fund returned {fund_return*100:.1f}% "
                       f"{'outperforming' if outperformed else 'underperforming'} benchmark by "
                       f"{abs(alpha)*100:.0f}bps."
        },
        {
            "title": "Performance Summary",
            "type": "performance",
            "guidance": "Include performance table, attribution highlights, "
                       "and risk metrics (Sharpe, Sortino, max DD)."
        },
        {
            "title": "Market Commentary",
            "type": "commentary",
            "themes": market_themes,
            "guidance": "Discuss key market themes and their impact on the portfolio."
        },
        {
            "title": "Portfolio Positioning",
            "type": "positioning",
            "changes": positioning_changes,
            "guidance": "Explain key trades, sector tilts, and rationale."
        },
        {
            "title": "Outlook",
            "type": "outlook",
            "points": outlook_points,
            "guidance": "Forward-looking views with appropriate disclaimers."
        },
        {
            "title": "Operational Update",
            "type": "operational",
            "guidance": f"AUM: ${aum/1e6:.0f}M. Note any team changes, "
                       "infrastructure updates, or compliance matters."
        }
    ]
    
    return {
        "fund_name": fund_name,
        "period": period,
        "fund_return_pct": round(fund_return * 100, 2),
        "benchmark_return_pct": round(benchmark_return * 100, 2),
        "alpha_bps": round(alpha * 10000, 1),
        "aum": aum,
        "sections": sections,
        "metadata": {
            "generated": datetime.now().isoformat(),
            "disclaimer": "Past performance is not indicative of future results."
        }
    }


def risk_metrics_section(returns: List[float], benchmark_returns: List[float],
                          risk_free_rate: float = 0.05) -> Dict:
    """Calculate risk metrics for investor letter inclusion.
    
    Args:
        returns: List of periodic returns (decimal)
        benchmark_returns: Benchmark returns for same periods
        risk_free_rate: Annual risk-free rate
    
    Returns:
        Dict of risk metrics formatted for letter inclusion
    """
    import statistics
    
    n = len(returns)
    if n < 2:
        return {"error": "Need at least 2 periods"}
    
    mean_ret = statistics.mean(returns)
    std_ret = statistics.stdev(returns)
    
    # Annualize (assuming monthly)
    ann_ret = (1 + mean_ret) ** 12 - 1
    ann_vol = std_ret * (12 ** 0.5)
    
    # Sharpe
    sharpe = (ann_ret - risk_free_rate) / ann_vol if ann_vol > 0 else 0
    
    # Sortino
    downside = [r for r in returns if r < 0]
    down_dev = statistics.stdev(downside) * (12 ** 0.5) if len(downside) > 1 else 0.001
    sortino = (ann_ret - risk_free_rate) / down_dev
    
    # Max drawdown
    cumulative = [1.0]
    for r in returns:
        cumulative.append(cumulative[-1] * (1 + r))
    peak = cumulative[0]
    max_dd = 0
    for val in cumulative:
        peak = max(peak, val)
        dd = (val - peak) / peak
        max_dd = min(max_dd, dd)
    
    # Beta & alpha vs benchmark
    if len(benchmark_returns) == n:
        bm_mean = statistics.mean(benchmark_returns)
        cov = sum((r - mean_ret) * (b - bm_mean) for r, b in zip(returns, benchmark_returns)) / (n - 1)
        bm_var = statistics.variance(benchmark_returns)
        beta = cov / bm_var if bm_var > 0 else 1.0
        ann_bm_ret = (1 + bm_mean) ** 12 - 1
        jensen_alpha = ann_ret - (risk_free_rate + beta * (ann_bm_ret - risk_free_rate))
    else:
        beta = None
        jensen_alpha = None
    
    return {
        "annualized_return_pct": round(ann_ret * 100, 2),
        "annualized_volatility_pct": round(ann_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "beta": round(beta, 3) if beta else None,
        "jensen_alpha_pct": round(jensen_alpha * 100, 2) if jensen_alpha else None,
        "winning_months": sum(1 for r in returns if r > 0),
        "losing_months": sum(1 for r in returns if r <= 0),
        "win_rate_pct": round(sum(1 for r in returns if r > 0) / n * 100, 1),
        "best_month_pct": round(max(returns) * 100, 2),
        "worst_month_pct": round(min(returns) * 100, 2),
        "periods": n
    }
