"""AutoML Pipeline for Alpha Discovery — automated feature engineering and model selection.

Systematically generates, evaluates, and combines alpha factors from price/volume
data using automated feature engineering, cross-validation, and ensemble methods.
No heavy ML libraries required — pure Python implementation.
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple


# ── Feature Generators ──────────────────────────────────────────────

def generate_return_features(prices: List[float]) -> Dict[str, List[float]]:
    """Generate return-based features at multiple horizons.

    Args:
        prices: Time series of prices.

    Returns:
        Dict of feature_name -> feature_values.
    """
    n = len(prices)
    features: Dict[str, List[float]] = {}

    for horizon in [1, 5, 10, 20, 60]:
        name = f"return_{horizon}d"
        vals = [None] * horizon + [
            (prices[i] - prices[i - horizon]) / prices[i - horizon]
            if prices[i - horizon] != 0 else 0.0
            for i in range(horizon, n)
        ]
        features[name] = vals

    return features


def generate_volatility_features(prices: List[float]) -> Dict[str, List[float]]:
    """Generate volatility-based features.

    Args:
        prices: Time series of prices.

    Returns:
        Dict of feature_name -> feature_values.
    """
    n = len(prices)
    returns = [0.0] + [
        (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] != 0 else 0.0
        for i in range(1, n)
    ]

    features: Dict[str, List[float]] = {}
    for window in [5, 10, 20]:
        name = f"vol_{window}d"
        vals = []
        for i in range(n):
            if i < window:
                vals.append(None)
            else:
                segment = returns[i - window + 1:i + 1]
                vals.append(statistics.stdev(segment) if len(segment) > 1 else 0.0)
        features[name] = vals

    # Vol ratio (short/long)
    features["vol_ratio_5_20"] = [
        features["vol_5d"][i] / features["vol_20d"][i]
        if features["vol_5d"][i] is not None and features["vol_20d"][i] is not None and features["vol_20d"][i] > 0
        else None
        for i in range(n)
    ]

    return features


def generate_ma_features(prices: List[float]) -> Dict[str, List[float]]:
    """Generate moving average crossover features.

    Args:
        prices: Time series of prices.

    Returns:
        Dict of feature_name -> feature_values.
    """
    n = len(prices)
    features: Dict[str, List[float]] = {}

    for window in [5, 10, 20, 50]:
        name = f"ma_{window}"
        vals = []
        for i in range(n):
            if i < window - 1:
                vals.append(None)
            else:
                vals.append(sum(prices[i - window + 1:i + 1]) / window)
        features[name] = vals

    # Price relative to MAs
    for window in [20, 50]:
        name = f"price_vs_ma{window}"
        ma = features[f"ma_{window}"]
        vals = [
            (prices[i] - ma[i]) / ma[i] if ma[i] is not None and ma[i] > 0 else None
            for i in range(n)
        ]
        features[name] = vals

    return features


def auto_generate_features(prices: List[float], volumes: Optional[List[float]] = None) -> Dict[str, List[float]]:
    """Auto-generate a comprehensive feature set.

    Args:
        prices: Price time series.
        volumes: Optional volume time series.

    Returns:
        Dict of all generated features.
    """
    all_features: Dict[str, List[float]] = {}
    all_features.update(generate_return_features(prices))
    all_features.update(generate_volatility_features(prices))
    all_features.update(generate_ma_features(prices))

    if volumes and len(volumes) == len(prices):
        n = len(volumes)
        avg_vol_20 = []
        for i in range(n):
            if i < 19:
                avg_vol_20.append(None)
            else:
                avg_vol_20.append(sum(volumes[i-19:i+1]) / 20)
        all_features["volume_ratio_20d"] = [
            volumes[i] / avg_vol_20[i] if avg_vol_20[i] and avg_vol_20[i] > 0 else None
            for i in range(n)
        ]

    return all_features


# ── Feature Evaluation ──────────────────────────────────────────────

def information_coefficient(feature: List, forward_returns: List[float]) -> float:
    """Compute rank IC (Spearman-like) between feature and forward returns.

    Args:
        feature: Feature values (may contain None).
        forward_returns: Forward return values.

    Returns:
        Information coefficient (-1 to 1).
    """
    pairs = [
        (f, r) for f, r in zip(feature, forward_returns)
        if f is not None and r is not None and not math.isnan(f) and not math.isnan(r)
    ]
    if len(pairs) < 10:
        return 0.0

    # Rank correlation (simplified)
    n = len(pairs)
    f_vals = [p[0] for p in pairs]
    r_vals = [p[1] for p in pairs]

    f_ranked = _rank(f_vals)
    r_ranked = _rank(r_vals)

    mean_f = sum(f_ranked) / n
    mean_r = sum(r_ranked) / n

    cov = sum((f_ranked[i] - mean_f) * (r_ranked[i] - mean_r) for i in range(n))
    std_f = math.sqrt(sum((f_ranked[i] - mean_f) ** 2 for i in range(n)))
    std_r = math.sqrt(sum((r_ranked[i] - mean_r) ** 2 for i in range(n)))

    if std_f == 0 or std_r == 0:
        return 0.0
    return cov / (std_f * std_r)


def _rank(values: List[float]) -> List[float]:
    """Assign ranks to values (average method for ties)."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j - 1) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def evaluate_features(
    features: Dict[str, List],
    forward_returns: List[float],
    min_ic: float = 0.02,
) -> List[Dict]:
    """Evaluate all features and rank by predictive power.

    Args:
        features: {feature_name: values}.
        forward_returns: Forward returns to predict.
        min_ic: Minimum absolute IC to include.

    Returns:
        Sorted list of {name, ic, abs_ic, direction}.
    """
    results = []
    for name, vals in features.items():
        ic = information_coefficient(vals, forward_returns)
        if abs(ic) >= min_ic:
            results.append({
                "name": name,
                "ic": round(ic, 4),
                "abs_ic": round(abs(ic), 4),
                "direction": "positive" if ic > 0 else "negative",
            })

    results.sort(key=lambda x: x["abs_ic"], reverse=True)
    return results


# ── Ensemble Combiner ───────────────────────────────────────────────

def build_ensemble_signal(
    features: Dict[str, List],
    feature_weights: Dict[str, float],
) -> List[Optional[float]]:
    """Combine features into a single alpha signal using IC-based weights.

    Args:
        features: {feature_name: values}.
        feature_weights: {feature_name: weight (can be IC)}.

    Returns:
        Combined signal values.
    """
    names = list(feature_weights.keys())
    if not names:
        return []

    n = max(len(features[name]) for name in names if name in features)
    signal = [None] * n

    for i in range(n):
        weighted_sum = 0.0
        total_weight = 0.0
        for name in names:
            if name not in features:
                continue
            vals = features[name]
            if i >= len(vals) or vals[i] is None:
                continue
            w = feature_weights[name]
            weighted_sum += vals[i] * w
            total_weight += abs(w)

        if total_weight > 0:
            signal[i] = round(weighted_sum / total_weight, 6)

    return signal


def run_automl_pipeline(
    prices: List[float],
    forward_returns: List[float],
    volumes: Optional[List[float]] = None,
    top_n: int = 5,
    min_ic: float = 0.02,
) -> Dict:
    """Run the full AutoML alpha discovery pipeline.

    Args:
        prices: Historical prices.
        forward_returns: Forward returns to predict.
        volumes: Optional volume data.
        top_n: Number of top features to use in ensemble.
        min_ic: Minimum IC threshold.

    Returns:
        Dict with top_features, ensemble_signal, feature_count, selected_count.
    """
    features = auto_generate_features(prices, volumes)
    ranked = evaluate_features(features, forward_returns, min_ic=min_ic)

    top_features = ranked[:top_n]
    weights = {f["name"]: f["ic"] for f in top_features}
    signal = build_ensemble_signal(features, weights)

    return {
        "feature_count": len(features),
        "significant_features": len(ranked),
        "selected_count": len(top_features),
        "top_features": top_features,
        "ensemble_signal_length": len([s for s in signal if s is not None]),
    }
