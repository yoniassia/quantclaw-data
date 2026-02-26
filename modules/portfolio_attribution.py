"""
Portfolio Attribution Engine — Brinson-Hood-Beebower performance attribution.

Decomposes portfolio returns into allocation effect, selection effect, and
interaction effect versus a benchmark. Supports single-period and multi-period
(linking) attribution across sectors/asset classes.
"""

import json
from typing import Dict, List, Optional, Tuple


def brinson_single_period(
    portfolio_weights: Dict[str, float],
    portfolio_returns: Dict[str, float],
    benchmark_weights: Dict[str, float],
    benchmark_returns: Dict[str, float]
) -> Dict:
    """
    Single-period Brinson-Hood-Beebower attribution.

    Decomposes active return into:
    - Allocation Effect: Over/underweighting sectors that outperform
    - Selection Effect: Picking better securities within sectors
    - Interaction Effect: Combined allocation + selection

    Args:
        portfolio_weights: Sector -> weight (must sum to ~1.0)
        portfolio_returns: Sector -> return
        benchmark_weights: Sector -> weight
        benchmark_returns: Sector -> return

    Returns:
        Dict with sector-level and total attribution effects
    """
    all_sectors = set(list(portfolio_weights.keys()) + list(benchmark_weights.keys()))

    # Total returns
    port_total = sum(portfolio_weights.get(s, 0) * portfolio_returns.get(s, 0) for s in all_sectors)
    bench_total = sum(benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0) for s in all_sectors)
    active_return = port_total - bench_total

    sector_attribution = {}
    total_allocation = 0
    total_selection = 0
    total_interaction = 0

    for sector in sorted(all_sectors):
        wp = portfolio_weights.get(sector, 0)
        wb = benchmark_weights.get(sector, 0)
        rp = portfolio_returns.get(sector, 0)
        rb = benchmark_returns.get(sector, 0)

        # Brinson-Hood-Beebower decomposition
        allocation = (wp - wb) * (rb - bench_total)
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)

        sector_attribution[sector] = {
            "portfolio_weight": round(wp, 4),
            "benchmark_weight": round(wb, 4),
            "active_weight": round(wp - wb, 4),
            "portfolio_return": round(rp, 4),
            "benchmark_return": round(rb, 4),
            "allocation_effect": round(allocation, 6),
            "selection_effect": round(selection, 6),
            "interaction_effect": round(interaction, 6),
            "total_effect": round(allocation + selection + interaction, 6)
        }

        total_allocation += allocation
        total_selection += selection
        total_interaction += interaction

    return {
        "portfolio_return": round(port_total, 6),
        "benchmark_return": round(bench_total, 6),
        "active_return": round(active_return, 6),
        "allocation_effect": round(total_allocation, 6),
        "selection_effect": round(total_selection, 6),
        "interaction_effect": round(total_interaction, 6),
        "attribution_sum": round(total_allocation + total_selection + total_interaction, 6),
        "residual": round(active_return - (total_allocation + total_selection + total_interaction), 8),
        "sector_attribution": sector_attribution
    }


def brinson_fachler(
    portfolio_weights: Dict[str, float],
    portfolio_returns: Dict[str, float],
    benchmark_weights: Dict[str, float],
    benchmark_returns: Dict[str, float]
) -> Dict:
    """
    Brinson-Fachler attribution variant (no interaction term).

    Merges interaction into allocation, giving cleaner two-way decomposition.

    Args:
        portfolio_weights: Sector -> weight
        portfolio_returns: Sector -> return
        benchmark_weights: Sector -> weight
        benchmark_returns: Sector -> return

    Returns:
        Dict with allocation and selection effects (no interaction)
    """
    all_sectors = set(list(portfolio_weights.keys()) + list(benchmark_weights.keys()))

    bench_total = sum(benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0) for s in all_sectors)
    port_total = sum(portfolio_weights.get(s, 0) * portfolio_returns.get(s, 0) for s in all_sectors)

    sector_attr = {}
    total_alloc = 0
    total_select = 0

    for sector in sorted(all_sectors):
        wp = portfolio_weights.get(sector, 0)
        wb = benchmark_weights.get(sector, 0)
        rp = portfolio_returns.get(sector, 0)
        rb = benchmark_returns.get(sector, 0)

        # Brinson-Fachler: allocation absorbs interaction
        allocation = (wp - wb) * (rb - bench_total)
        selection = wp * (rp - rb)

        sector_attr[sector] = {
            "allocation_effect": round(allocation, 6),
            "selection_effect": round(selection, 6),
            "total_effect": round(allocation + selection, 6)
        }
        total_alloc += allocation
        total_select += selection

    return {
        "portfolio_return": round(port_total, 6),
        "benchmark_return": round(bench_total, 6),
        "active_return": round(port_total - bench_total, 6),
        "allocation_effect": round(total_alloc, 6),
        "selection_effect": round(total_select, 6),
        "sector_attribution": sector_attr
    }


def multi_period_linking(period_attributions: List[Dict]) -> Dict:
    """
    Link single-period attributions across multiple periods using geometric linking.

    Args:
        period_attributions: List of single-period Brinson results

    Returns:
        Linked multi-period attribution
    """
    if not period_attributions:
        return {"error": "No periods provided"}

    # Cumulative returns
    cum_port = 1.0
    cum_bench = 1.0
    linked_alloc = 0.0
    linked_select = 0.0
    linked_interact = 0.0

    for i, period in enumerate(period_attributions):
        pr = period.get("portfolio_return", 0)
        br = period.get("benchmark_return", 0)

        # Carino smoothing factor
        if i > 0:
            scale = cum_bench  # simplified scaling
        else:
            scale = 1.0

        linked_alloc += period.get("allocation_effect", 0) * scale
        linked_select += period.get("selection_effect", 0) * scale
        linked_interact += period.get("interaction_effect", 0) * scale

        cum_port *= (1 + pr)
        cum_bench *= (1 + br)

    return {
        "cumulative_portfolio_return": round(cum_port - 1, 6),
        "cumulative_benchmark_return": round(cum_bench - 1, 6),
        "cumulative_active_return": round((cum_port - 1) - (cum_bench - 1), 6),
        "linked_allocation_effect": round(linked_alloc, 6),
        "linked_selection_effect": round(linked_select, 6),
        "linked_interaction_effect": round(linked_interact, 6),
        "periods_linked": len(period_attributions)
    }


def top_contributors(attribution_result: Dict, n: int = 5) -> Dict:
    """
    Extract top positive and negative contributors from attribution results.

    Args:
        attribution_result: Output from brinson_single_period
        n: Number of top/bottom to return

    Returns:
        Dict with top contributors and detractors
    """
    sectors = attribution_result.get("sector_attribution", {})
    if not sectors:
        return {"error": "No sector attribution data"}

    items = [(s, d["total_effect"]) for s, d in sectors.items()]
    items.sort(key=lambda x: x[1], reverse=True)

    return {
        "top_contributors": [{"sector": s, "effect": round(e, 6)} for s, e in items[:n]],
        "top_detractors": [{"sector": s, "effect": round(e, 6)} for s, e in items[-n:]],
        "total_sectors": len(items)
    }
