"""
Synthetic Control Method (#292)

Constructs a synthetic counterfactual from a weighted combination of control
units to estimate what would have happened absent an intervention/event.
Used for policy analysis, M&A impact, and regulatory change studies.
"""

import math
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _generate_unit_series(name: str, length: int = 200, treatment_idx: int = None,
                          treatment_effect: float = 0.0) -> List[float]:
    """Generate synthetic time series for a unit."""
    seed = int(hashlib.md5(f"{name}synth".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    base = 50 + rng.gauss(0, 15)
    trend = rng.gauss(0.05, 0.02)
    series = []
    val = base
    
    for i in range(length):
        val += trend + rng.gauss(0, 0.8)
        if treatment_idx is not None and i >= treatment_idx:
            val += treatment_effect / (length - treatment_idx)
        series.append(round(val, 4))
    
    return series


def _optimize_weights(treated_pre: List[float], control_pre: List[List[float]]) -> List[float]:
    """Find optimal weights for control units to match treated unit pre-treatment.
    Uses iterative projection (simplified constrained optimization)."""
    n_controls = len(control_pre)
    if n_controls == 0:
        return []
    
    # Initialize equal weights
    weights = [1.0 / n_controls] * n_controls
    
    # Iterative refinement
    for iteration in range(100):
        # Compute synthetic
        synthetic = [sum(weights[j] * control_pre[j][t] for j in range(n_controls))
                     for t in range(len(treated_pre))]
        
        # Gradient: minimize sum of squared errors
        for j in range(n_controls):
            grad = sum(2 * (synthetic[t] - treated_pre[t]) * control_pre[j][t]
                       for t in range(len(treated_pre)))
            weights[j] -= 0.0001 * grad
        
        # Project to simplex (non-negative, sum to 1)
        weights = [max(0, w) for w in weights]
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        else:
            weights = [1.0 / n_controls] * n_controls
    
    return [round(w, 6) for w in weights]


def synthetic_control_analysis(treated_unit: str, control_units: List[str] = None,
                                pre_periods: int = 120, post_periods: int = 60,
                                treatment_effect: float = None) -> Dict:
    """
    Construct a synthetic control and estimate treatment effect.
    
    Args:
        treated_unit: Name/ticker of the treated unit
        control_units: List of control unit names/tickers
        pre_periods: Number of pre-treatment periods
        post_periods: Number of post-treatment periods
        treatment_effect: Simulated treatment effect (auto-generated if None)
    
    Returns:
        Dict with synthetic control weights, gap estimates, and inference
    """
    if control_units is None:
        control_units = [f"Control_{i}" for i in range(1, 8)]
    
    total_length = pre_periods + post_periods
    treatment_idx = pre_periods
    
    # Generate treatment effect if not provided
    if treatment_effect is None:
        seed = int(hashlib.md5(treated_unit.encode()).hexdigest()[:8], 16)
        treatment_effect = random.Random(seed).gauss(5, 3)
    
    # Generate series
    treated_series = _generate_unit_series(treated_unit, total_length, treatment_idx, treatment_effect)
    control_series = [_generate_unit_series(u, total_length) for u in control_units]
    
    # Split pre/post
    treated_pre = treated_series[:pre_periods]
    treated_post = treated_series[pre_periods:]
    control_pre = [s[:pre_periods] for s in control_series]
    control_post = [s[pre_periods:] for s in control_series]
    
    # Optimize weights
    weights = _optimize_weights(treated_pre, control_pre)
    
    # Construct synthetic control
    synthetic_pre = [sum(weights[j] * control_pre[j][t] for j in range(len(control_units)))
                     for t in range(pre_periods)]
    synthetic_post = [sum(weights[j] * control_post[j][t] for j in range(len(control_units)))
                      for t in range(post_periods)]
    
    # Pre-treatment fit (RMSPE)
    pre_gaps = [treated_pre[t] - synthetic_pre[t] for t in range(pre_periods)]
    pre_rmspe = math.sqrt(sum(g ** 2 for g in pre_gaps) / pre_periods)
    
    # Post-treatment gaps (treatment effect estimates)
    post_gaps = [treated_post[t] - synthetic_post[t] for t in range(post_periods)]
    avg_post_gap = sum(post_gaps) / post_periods
    post_rmspe = math.sqrt(sum(g ** 2 for g in post_gaps) / post_periods)
    
    # Ratio of post/pre RMSPE (inference)
    rmspe_ratio = post_rmspe / pre_rmspe if pre_rmspe > 0 else float('inf')
    
    # Significant if ratio > 2 (rule of thumb) or post gaps consistently one-sided
    pct_positive_gaps = sum(1 for g in post_gaps if g > 0) / post_periods
    significant = rmspe_ratio > 2 or pct_positive_gaps > 0.85 or pct_positive_gaps < 0.15
    
    # Donor weights (non-zero only)
    donor_weights = {control_units[j]: weights[j] for j in range(len(control_units)) if weights[j] > 0.01}
    
    return {
        "treated_unit": treated_unit,
        "n_control_units": len(control_units),
        "pre_periods": pre_periods,
        "post_periods": post_periods,
        "donor_weights": donor_weights,
        "n_active_donors": len(donor_weights),
        "pre_treatment_rmspe": round(pre_rmspe, 4),
        "post_treatment_rmspe": round(post_rmspe, 4),
        "rmspe_ratio": round(rmspe_ratio, 4),
        "avg_treatment_effect": round(avg_post_gap, 4),
        "cumulative_effect": round(sum(post_gaps), 4),
        "pct_positive_gaps": round(pct_positive_gaps, 4),
        "significant": significant,
        "post_gap_series": [round(g, 4) for g in post_gaps[:20]],  # first 20
        "interpretation": f"Estimated treatment effect of {round(avg_post_gap, 2)} units "
                         f"({'significant' if significant else 'not significant'}). "
                         f"Pre-fit RMSPE: {round(pre_rmspe, 2)}, ratio: {round(rmspe_ratio, 2)}",
        "generated_at": datetime.utcnow().isoformat()
    }


def placebo_test(treated_unit: str, control_units: List[str] = None,
                 n_placebos: int = 5) -> Dict:
    """
    Run placebo tests by applying synthetic control to each control unit
    (treating it as if it received treatment). Used for inference.
    
    Returns p-value estimate based on where treated unit's effect ranks.
    """
    if control_units is None:
        control_units = [f"Control_{i}" for i in range(1, 8)]
    
    # Run actual treatment
    actual = synthetic_control_analysis(treated_unit, control_units)
    actual_ratio = actual["rmspe_ratio"]
    
    # Run placebos
    placebo_ratios = []
    for i, placebo_unit in enumerate(control_units[:n_placebos]):
        remaining = [u for u in control_units if u != placebo_unit] + [treated_unit]
        placebo = synthetic_control_analysis(placebo_unit, remaining)
        placebo_ratios.append({
            "unit": placebo_unit,
            "rmspe_ratio": placebo["rmspe_ratio"],
            "avg_effect": placebo["avg_treatment_effect"]
        })
    
    # P-value: fraction of placebos with ratio >= treated
    rank = sum(1 for p in placebo_ratios if p["rmspe_ratio"] >= actual_ratio)
    p_value = (rank + 1) / (len(placebo_ratios) + 1)
    
    return {
        "treated_unit": treated_unit,
        "treated_rmspe_ratio": actual_ratio,
        "treated_effect": actual["avg_treatment_effect"],
        "placebos": placebo_ratios,
        "p_value": round(p_value, 4),
        "significant_10pct": p_value < 0.10,
        "significant_5pct": p_value < 0.05,
        "rank": rank + 1,
        "total_units": len(placebo_ratios) + 1,
        "generated_at": datetime.utcnow().isoformat()
    }


def compare_methods(treated_unit: str, event_name: str = "policy_change") -> Dict:
    """
    Compare synthetic control vs simple difference-in-differences estimate.
    """
    control_units = [f"Control_{i}" for i in range(1, 6)]
    
    sc_result = synthetic_control_analysis(treated_unit, control_units)
    
    # Simple DiD: average of controls as counterfactual
    total = sc_result["pre_periods"] + sc_result["post_periods"]
    treated = _generate_unit_series(treated_unit, total, sc_result["pre_periods"], 5)
    controls = [_generate_unit_series(u, total) for u in control_units]
    
    pre = sc_result["pre_periods"]
    treated_diff = sum(treated[pre:]) / sc_result["post_periods"] - sum(treated[:pre]) / pre
    control_diff = sum(
        sum(c[pre:]) / sc_result["post_periods"] - sum(c[:pre]) / pre 
        for c in controls
    ) / len(controls)
    did_estimate = treated_diff - control_diff
    
    return {
        "treated_unit": treated_unit,
        "event": event_name,
        "synthetic_control_effect": sc_result["avg_treatment_effect"],
        "did_estimate": round(did_estimate, 4),
        "difference": round(sc_result["avg_treatment_effect"] - did_estimate, 4),
        "sc_significant": sc_result["significant"],
        "sc_pre_fit_rmspe": sc_result["pre_treatment_rmspe"],
        "recommendation": "synthetic_control" if sc_result["pre_treatment_rmspe"] < 2 else "difference_in_differences",
        "generated_at": datetime.utcnow().isoformat()
    }
