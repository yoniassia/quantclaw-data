"""Attention-Based Cross-Asset Signal — use attention mechanisms to weight cross-asset inputs.

Implements a simplified self-attention mechanism over multiple asset return
streams to dynamically learn which cross-asset relationships matter most
for predicting a target asset. Pure Python/math implementation.
"""

import math
from typing import Dict, List, Optional, Tuple


def softmax(scores: List[float]) -> List[float]:
    """Compute softmax over a list of scores.

    Args:
        scores: Raw attention scores.

    Returns:
        Normalized probability distribution.
    """
    max_s = max(scores) if scores else 0
    exps = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(scores)] * len(scores) if scores else []
    return [e / total for e in exps]


def dot_product_attention(
    query: List[float],
    keys: List[List[float]],
    values: List[List[float]],
    scale: bool = True,
) -> Tuple[List[float], List[float]]:
    """Scaled dot-product attention over key-value pairs.

    Args:
        query: Query vector (target asset features).
        keys: List of key vectors (one per cross-asset).
        values: List of value vectors (one per cross-asset).
        scale: Whether to apply sqrt(d_k) scaling.

    Returns:
        Tuple of (weighted_output, attention_weights).
    """
    d_k = len(query)
    scale_factor = math.sqrt(d_k) if scale and d_k > 0 else 1.0

    scores = []
    for key in keys:
        dot = sum(q * k for q, k in zip(query, key))
        scores.append(dot / scale_factor)

    weights = softmax(scores)

    # Weighted sum of values
    dim = len(values[0]) if values else 0
    output = [0.0] * dim
    for w, val in zip(weights, values):
        for i in range(dim):
            output[i] += w * val[i]

    return output, weights


def multi_asset_attention_signal(
    target_returns: List[float],
    cross_asset_returns: Dict[str, List[float]],
    lookback: int = 20,
) -> Dict:
    """Generate attention-weighted cross-asset signal for a target.

    Uses recent return patterns as queries/keys to learn which assets
    are most informative for the target.

    Args:
        target_returns: Recent returns of the target asset.
        cross_asset_returns: {asset_name: [returns]} for cross-assets.
        lookback: Number of periods to use.

    Returns:
        Dict with signal, attention_weights, dominant_driver, confidence.
    """
    target = target_returns[-lookback:] if len(target_returns) >= lookback else target_returns
    assets = list(cross_asset_returns.keys())

    if not assets or not target:
        return {"signal": 0.0, "attention_weights": {}, "dominant_driver": None, "confidence": 0.0}

    keys = []
    values = []
    for name in assets:
        rets = cross_asset_returns[name][-lookback:]
        if len(rets) < len(target):
            rets = rets + [0.0] * (len(target) - len(rets))
        keys.append(rets[:len(target)])
        values.append(rets[:len(target)])

    output, weights = dot_product_attention(target, keys, values)

    # Signal = weighted recent momentum of cross-assets
    signal = sum(output[-5:]) / 5 if len(output) >= 5 else sum(output) / max(len(output), 1)

    attn_map = {name: round(w, 4) for name, w in zip(assets, weights)}
    dominant = max(attn_map, key=attn_map.get) if attn_map else None
    max_weight = max(weights) if weights else 0
    confidence = round(max_weight * min(abs(signal) * 10, 1.0), 4)

    return {
        "signal": round(signal, 6),
        "attention_weights": attn_map,
        "dominant_driver": dominant,
        "confidence": confidence,
    }


def cross_asset_regime_attention(
    asset_returns: Dict[str, List[float]],
    window: int = 60,
) -> Dict:
    """Detect market regime by computing pairwise attention across all assets.

    Args:
        asset_returns: {asset_name: [returns]}.
        window: Lookback window.

    Returns:
        Dict with regime classification, correlation_concentration,
        attention_matrix, and risk_level.
    """
    assets = list(asset_returns.keys())
    n = len(assets)
    if n < 2:
        return {"regime": "insufficient_data", "risk_level": "unknown"}

    # Build attention matrix
    attn_matrix: Dict[str, Dict[str, float]] = {}
    concentration_scores = []

    for target_name in assets:
        target = asset_returns[target_name][-window:]
        others = {k: v[-window:] for k, v in asset_returns.items() if k != target_name}
        if not others:
            continue

        result = multi_asset_attention_signal(target, others, lookback=window)
        attn_matrix[target_name] = result["attention_weights"]

        # Concentration = max weight (high = one asset dominates)
        if result["attention_weights"]:
            max_w = max(result["attention_weights"].values())
            concentration_scores.append(max_w)

    avg_concentration = sum(concentration_scores) / len(concentration_scores) if concentration_scores else 0

    # Classify regime
    if avg_concentration > 0.6:
        regime = "crisis_correlated"
        risk_level = "high"
    elif avg_concentration > 0.4:
        regime = "trending"
        risk_level = "moderate"
    else:
        regime = "diversified"
        risk_level = "low"

    return {
        "regime": regime,
        "correlation_concentration": round(avg_concentration, 4),
        "asset_count": n,
        "risk_level": risk_level,
        "attention_matrix": attn_matrix,
    }


def generate_allocation_from_attention(
    target: str,
    attention_weights: Dict[str, float],
    base_allocation: Dict[str, float],
    tilt_strength: float = 0.2,
) -> Dict[str, float]:
    """Tilt portfolio allocation based on attention weights.

    Args:
        target: Target asset ticker.
        attention_weights: {asset: weight} from attention mechanism.
        base_allocation: Starting allocation {asset: pct}.
        tilt_strength: How much to tilt (0-1).

    Returns:
        Adjusted allocation dict.
    """
    adjusted = dict(base_allocation)
    total_attn = sum(attention_weights.values()) or 1.0

    for asset, attn_w in attention_weights.items():
        if asset in adjusted:
            norm_attn = attn_w / total_attn
            base = adjusted[asset]
            adjusted[asset] = base * (1 - tilt_strength) + norm_attn * tilt_strength

    # Renormalize
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v / total, 4) for k, v in adjusted.items()}

    return adjusted
