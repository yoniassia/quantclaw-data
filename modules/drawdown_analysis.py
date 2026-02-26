"""Drawdown Analysis Suite — Comprehensive drawdown analytics including underwater
equity curves, recovery analysis, drawdown duration tracking, conditional drawdown
at risk (CDaR), and historical drawdown comparison across assets."""

import json
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def calculate_drawdowns(returns: List[float], dates: Optional[List[str]] = None) -> Dict:
    """Calculate complete drawdown series from a return stream.
    
    Args:
        returns: List of periodic returns (decimal, e.g., 0.02 = +2%)
        dates: Optional list of date strings matching returns
    
    Returns:
        Full drawdown analysis with underwater curve and drawdown periods
    """
    if not returns:
        return {"error": "No returns provided"}
    
    cumulative = [1.0]
    for r in returns:
        cumulative.append(cumulative[-1] * (1 + r))
    
    peak = cumulative[0]
    drawdowns = []
    underwater = []
    
    for i, val in enumerate(cumulative):
        peak = max(peak, val)
        dd = (val - peak) / peak if peak > 0 else 0
        drawdowns.append(round(dd, 6))
        underwater.append({
            "period": i,
            "date": dates[i - 1] if dates and i > 0 and i <= len(dates) else None,
            "cumulative_value": round(val, 6),
            "peak": round(peak, 6),
            "drawdown_pct": round(dd * 100, 4)
        })
    
    # Identify distinct drawdown periods
    dd_periods = []
    in_dd = False
    start_idx = 0
    trough_idx = 0
    trough_val = 0
    
    for i in range(1, len(drawdowns)):
        if drawdowns[i] < 0 and not in_dd:
            in_dd = True
            start_idx = i
            trough_idx = i
            trough_val = drawdowns[i]
        elif in_dd and drawdowns[i] < trough_val:
            trough_idx = i
            trough_val = drawdowns[i]
        elif in_dd and drawdowns[i] == 0:
            dd_periods.append({
                "start_period": start_idx,
                "trough_period": trough_idx,
                "end_period": i,
                "start_date": dates[start_idx - 1] if dates and start_idx <= len(dates) else None,
                "trough_date": dates[trough_idx - 1] if dates and trough_idx <= len(dates) else None,
                "recovery_date": dates[i - 1] if dates and i <= len(dates) else None,
                "max_drawdown_pct": round(trough_val * 100, 4),
                "decline_periods": trough_idx - start_idx,
                "recovery_periods": i - trough_idx,
                "total_periods": i - start_idx
            })
            in_dd = False
    
    # Handle ongoing drawdown
    if in_dd:
        dd_periods.append({
            "start_period": start_idx,
            "trough_period": trough_idx,
            "end_period": None,
            "max_drawdown_pct": round(trough_val * 100, 4),
            "decline_periods": trough_idx - start_idx,
            "recovery_periods": None,
            "total_periods": None,
            "status": "ongoing"
        })
    
    max_dd = min(drawdowns)
    avg_dd = statistics.mean([d for d in drawdowns if d < 0]) if any(d < 0 for d in drawdowns) else 0
    
    return {
        "max_drawdown_pct": round(max_dd * 100, 4),
        "average_drawdown_pct": round(avg_dd * 100, 4),
        "current_drawdown_pct": round(drawdowns[-1] * 100, 4),
        "num_drawdown_periods": len(dd_periods),
        "time_underwater_pct": round(sum(1 for d in drawdowns if d < 0) / len(drawdowns) * 100, 2),
        "drawdown_periods": sorted(dd_periods, key=lambda x: x["max_drawdown_pct"])[:20],
        "total_periods": len(returns)
    }


def drawdown_risk_metrics(returns: List[float], confidence: float = 0.95) -> Dict:
    """Calculate drawdown-based risk metrics including CDaR and Ulcer Index.
    
    Args:
        returns: List of periodic returns
        confidence: Confidence level for CDaR (default 95%)
    
    Returns:
        Drawdown risk metrics
    """
    # Build drawdown series
    cumulative = [1.0]
    for r in returns:
        cumulative.append(cumulative[-1] * (1 + r))
    
    peak = cumulative[0]
    dd_series = []
    for val in cumulative:
        peak = max(peak, val)
        dd_series.append((val - peak) / peak if peak > 0 else 0)
    
    abs_dds = [abs(d) for d in dd_series if d < 0]
    
    if not abs_dds:
        return {
            "max_drawdown_pct": 0,
            "cdar_pct": 0,
            "ulcer_index": 0,
            "pain_index": 0,
            "calmar_ratio": None,
            "sterling_ratio": None
        }
    
    # Conditional Drawdown at Risk (CDaR)
    sorted_dds = sorted(abs_dds, reverse=True)
    cutoff = int(len(sorted_dds) * (1 - confidence))
    cdar = statistics.mean(sorted_dds[:max(cutoff, 1)])
    
    # Ulcer Index (RMS of drawdowns)
    ulcer = (statistics.mean([d ** 2 for d in dd_series])) ** 0.5
    
    # Pain Index (average drawdown depth)
    pain = statistics.mean([abs(d) for d in dd_series])
    
    # Annualized return for ratios
    total_return = cumulative[-1] / cumulative[0] - 1
    n_years = len(returns) / 252  # assume daily
    ann_return = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1
    
    max_dd = max(abs_dds)
    
    # Calmar ratio (ann return / max DD)
    calmar = ann_return / max_dd if max_dd > 0 else None
    
    # Sterling ratio (ann return / avg of worst 5 DDs)
    worst5 = sorted_dds[:5]
    sterling = ann_return / statistics.mean(worst5) if worst5 else None
    
    return {
        "max_drawdown_pct": round(max_dd * 100, 4),
        "cdar_pct": round(cdar * 100, 4),
        "cdar_confidence": confidence,
        "ulcer_index": round(ulcer, 6),
        "pain_index": round(pain, 6),
        "calmar_ratio": round(calmar, 4) if calmar else None,
        "sterling_ratio": round(sterling, 4) if sterling else None,
        "annualized_return_pct": round(ann_return * 100, 2),
        "periods_analyzed": len(returns)
    }


def recovery_analysis(returns: List[float], threshold: float = -0.05) -> Dict:
    """Analyze recovery patterns after drawdowns exceed a threshold.
    
    Args:
        returns: List of periodic returns
        threshold: Drawdown threshold to trigger analysis (e.g., -0.05 = -5%)
    
    Returns:
        Recovery statistics and patterns
    """
    dd_data = calculate_drawdowns(returns)
    
    significant_dds = [
        p for p in dd_data.get("drawdown_periods", [])
        if p["max_drawdown_pct"] / 100 <= threshold
    ]
    
    recovery_times = [p["recovery_periods"] for p in significant_dds if p.get("recovery_periods")]
    decline_times = [p["decline_periods"] for p in significant_dds]
    depths = [abs(p["max_drawdown_pct"]) for p in significant_dds]
    
    return {
        "threshold_pct": threshold * 100,
        "num_significant_drawdowns": len(significant_dds),
        "avg_depth_pct": round(statistics.mean(depths), 2) if depths else 0,
        "max_depth_pct": round(max(depths), 2) if depths else 0,
        "avg_decline_periods": round(statistics.mean(decline_times), 1) if decline_times else 0,
        "avg_recovery_periods": round(statistics.mean(recovery_times), 1) if recovery_times else 0,
        "median_recovery_periods": round(statistics.median(recovery_times), 1) if recovery_times else 0,
        "max_recovery_periods": max(recovery_times) if recovery_times else 0,
        "recovery_ratio": round(
            statistics.mean(recovery_times) / statistics.mean(decline_times), 2
        ) if recovery_times and decline_times and statistics.mean(decline_times) > 0 else None,
        "unrecovered_count": sum(1 for p in significant_dds if p.get("status") == "ongoing"),
        "drawdowns": significant_dds
    }


def compare_drawdowns(asset_returns: Dict[str, List[float]]) -> Dict:
    """Compare drawdown profiles across multiple assets/strategies.
    
    Args:
        asset_returns: Dict of asset_name -> list of returns
    
    Returns:
        Comparative drawdown metrics
    """
    comparisons = []
    
    for name, returns in asset_returns.items():
        dd = calculate_drawdowns(returns)
        risk = drawdown_risk_metrics(returns)
        
        comparisons.append({
            "asset": name,
            "max_drawdown_pct": dd["max_drawdown_pct"],
            "avg_drawdown_pct": dd["average_drawdown_pct"],
            "current_drawdown_pct": dd["current_drawdown_pct"],
            "time_underwater_pct": dd["time_underwater_pct"],
            "num_drawdowns": dd["num_drawdown_periods"],
            "calmar_ratio": risk.get("calmar_ratio"),
            "ulcer_index": risk.get("ulcer_index"),
            "pain_index": risk.get("pain_index")
        })
    
    # Rank by max drawdown (least negative = best)
    comparisons.sort(key=lambda x: x["max_drawdown_pct"], reverse=True)
    
    return {
        "comparison": comparisons,
        "best_max_dd": comparisons[0]["asset"] if comparisons else None,
        "worst_max_dd": comparisons[-1]["asset"] if comparisons else None,
        "asset_count": len(comparisons)
    }
