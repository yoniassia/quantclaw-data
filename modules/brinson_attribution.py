"""
Brinson-Hood-Beebower Portfolio Attribution Engine.

Decomposes portfolio excess return into allocation effect, selection effect,
and interaction effect relative to a benchmark. Standard institutional
performance attribution methodology.

Free data: Portfolio weights/returns provided by user or from CSV.
"""

from typing import Dict, List, Optional
import json


def brinson_single_period(
    portfolio_weights: List[float],
    portfolio_returns: List[float],
    benchmark_weights: List[float],
    benchmark_returns: List[float],
    sector_names: Optional[List[str]] = None
) -> Dict:
    """
    Single-period Brinson-Hood-Beebower attribution.

    Args:
        portfolio_weights: Portfolio weight per sector (must sum to 1)
        portfolio_returns: Portfolio return per sector
        benchmark_weights: Benchmark weight per sector
        benchmark_returns: Benchmark return per sector
        sector_names: Optional sector labels

    Returns:
        Dict with allocation, selection, interaction effects per sector
    """
    n = len(portfolio_weights)
    if not (len(portfolio_returns) == len(benchmark_weights) == len(benchmark_returns) == n):
        raise ValueError("All input lists must have equal length")

    if sector_names is None:
        sector_names = [f"Sector_{i+1}" for i in range(n)]

    total_port_return = sum(w * r for w, r in zip(portfolio_weights, portfolio_returns))
    total_bench_return = sum(w * r for w, r in zip(benchmark_weights, benchmark_returns))
    excess_return = total_port_return - total_bench_return

    sectors = []
    total_allocation = 0.0
    total_selection = 0.0
    total_interaction = 0.0

    for i in range(n):
        wp = portfolio_weights[i]
        wb = benchmark_weights[i]
        rp = portfolio_returns[i]
        rb = benchmark_returns[i]

        allocation = (wp - wb) * rb
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)

        total_allocation += allocation
        total_selection += selection
        total_interaction += interaction

        sectors.append({
            "sector": sector_names[i],
            "portfolio_weight": round(wp, 4),
            "benchmark_weight": round(wb, 4),
            "portfolio_return": round(rp, 4),
            "benchmark_return": round(rb, 4),
            "allocation_effect": round(allocation, 6),
            "selection_effect": round(selection, 6),
            "interaction_effect": round(interaction, 6),
            "total_effect": round(allocation + selection + interaction, 6)
        })

    return {
        "total_portfolio_return": round(total_port_return, 6),
        "total_benchmark_return": round(total_bench_return, 6),
        "excess_return": round(excess_return, 6),
        "allocation_effect": round(total_allocation, 6),
        "selection_effect": round(total_selection, 6),
        "interaction_effect": round(total_interaction, 6),
        "sum_of_effects": round(total_allocation + total_selection + total_interaction, 6),
        "sectors": sectors
    }


def brinson_multi_period(
    periods: List[Dict]
) -> Dict:
    """
    Multi-period Brinson attribution with geometric linking.

    Args:
        periods: List of dicts, each with keys:
            portfolio_weights, portfolio_returns, benchmark_weights,
            benchmark_returns, sector_names (optional), period_label (optional)

    Returns:
        Dict with per-period and cumulative attribution
    """
    period_results = []
    cumulative_port = 1.0
    cumulative_bench = 1.0
    cumulative_allocation = 0.0
    cumulative_selection = 0.0
    cumulative_interaction = 0.0

    for idx, p in enumerate(periods):
        result = brinson_single_period(
            p["portfolio_weights"],
            p["portfolio_returns"],
            p["benchmark_weights"],
            p["benchmark_returns"],
            p.get("sector_names")
        )
        label = p.get("period_label", f"Period_{idx+1}")
        result["period"] = label

        cumulative_port *= (1 + result["total_portfolio_return"])
        cumulative_bench *= (1 + result["total_benchmark_return"])
        cumulative_allocation += result["allocation_effect"]
        cumulative_selection += result["selection_effect"]
        cumulative_interaction += result["interaction_effect"]

        period_results.append(result)

    return {
        "n_periods": len(periods),
        "cumulative_portfolio_return": round(cumulative_port - 1, 6),
        "cumulative_benchmark_return": round(cumulative_bench - 1, 6),
        "cumulative_excess_return": round((cumulative_port - 1) - (cumulative_bench - 1), 6),
        "cumulative_allocation": round(cumulative_allocation, 6),
        "cumulative_selection": round(cumulative_selection, 6),
        "cumulative_interaction": round(cumulative_interaction, 6),
        "periods": period_results
    }


def attribution_summary_table(attribution_result: Dict) -> str:
    """
    Format attribution result as a readable text table.

    Args:
        attribution_result: Output from brinson_single_period

    Returns:
        Formatted string table
    """
    lines = []
    lines.append(f"Portfolio Return: {attribution_result['total_portfolio_return']:.4%}")
    lines.append(f"Benchmark Return: {attribution_result['total_benchmark_return']:.4%}")
    lines.append(f"Excess Return:    {attribution_result['excess_return']:.4%}")
    lines.append("")
    lines.append(f"{'Sector':<20} {'Alloc':>10} {'Select':>10} {'Inter':>10} {'Total':>10}")
    lines.append("-" * 62)

    for s in attribution_result["sectors"]:
        lines.append(
            f"{s['sector']:<20} "
            f"{s['allocation_effect']:>10.4%} "
            f"{s['selection_effect']:>10.4%} "
            f"{s['interaction_effect']:>10.4%} "
            f"{s['total_effect']:>10.4%}"
        )

    lines.append("-" * 62)
    lines.append(
        f"{'TOTAL':<20} "
        f"{attribution_result['allocation_effect']:>10.4%} "
        f"{attribution_result['selection_effect']:>10.4%} "
        f"{attribution_result['interaction_effect']:>10.4%} "
        f"{attribution_result['sum_of_effects']:>10.4%}"
    )

    return "\n".join(lines)
