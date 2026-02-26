"""
Random Forest Feature Importance Ranker — Identify which technical/fundamental
factors drive stock returns using ensemble tree-based importance scoring.

Uses free data sources (yfinance, FRED). Computes permutation importance
and Gini importance to rank alpha signals.

Phase: 284 | Category: AI/ML Models
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class DecisionStump:
    """Simple decision tree stump for random forest building block."""

    def __init__(self, feature_idx: int, threshold: float, left_val: float, right_val: float):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left_val = left_val
        self.right_val = right_val

    def predict(self, x: np.ndarray) -> float:
        if x[self.feature_idx] <= self.threshold:
            return self.left_val
        return self.right_val


class SimpleDecisionTree:
    """Minimal decision tree for regression (max_depth limited)."""

    def __init__(self, max_depth: int = 5, min_samples: int = 5, seed: int = 42):
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.rng = np.random.RandomState(seed)
        self.tree = None
        self.feature_importances_ = None

    def _best_split(self, X: np.ndarray, y: np.ndarray, feature_subset: np.ndarray):
        best_mse = np.inf
        best_feat, best_thresh = None, None
        n = len(y)
        total_var = np.var(y) * n

        for feat in feature_subset:
            thresholds = np.percentile(X[:, feat], [20, 40, 60, 80])
            for t in thresholds:
                left = y[X[:, feat] <= t]
                right = y[X[:, feat] > t]
                if len(left) < self.min_samples or len(right) < self.min_samples:
                    continue
                mse = np.var(left) * len(left) + np.var(right) * len(right)
                if mse < best_mse:
                    best_mse = mse
                    best_feat = feat
                    best_thresh = t

        reduction = total_var - best_mse if best_feat is not None else 0
        return best_feat, best_thresh, reduction

    def _build(self, X: np.ndarray, y: np.ndarray, depth: int) -> dict:
        if depth >= self.max_depth or len(y) < self.min_samples * 2:
            return {"leaf": True, "value": float(np.mean(y))}

        n_features = X.shape[1]
        subset_size = max(1, int(np.sqrt(n_features)))
        feat_subset = self.rng.choice(n_features, subset_size, replace=False)

        feat, thresh, reduction = self._best_split(X, y, feat_subset)
        if feat is None:
            return {"leaf": True, "value": float(np.mean(y))}

        if self.feature_importances_ is not None:
            self.feature_importances_[feat] += reduction

        mask = X[:, feat] <= thresh
        return {
            "leaf": False,
            "feature": feat,
            "threshold": thresh,
            "left": self._build(X[mask], y[mask], depth + 1),
            "right": self._build(X[~mask], y[~mask], depth + 1),
        }

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.feature_importances_ = np.zeros(X.shape[1])
        self.tree = self._build(X, y, 0)
        total = self.feature_importances_.sum()
        if total > 0:
            self.feature_importances_ /= total

    def _predict_one(self, node: dict, x: np.ndarray) -> float:
        if node["leaf"]:
            return node["value"]
        if x[node["feature"]] <= node["threshold"]:
            return self._predict_one(node["left"], x)
        return self._predict_one(node["right"], x)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_one(self.tree, x) for x in X])


def compute_technical_features(prices: List[float]) -> np.ndarray:
    """
    Compute common technical features from price series.

    Returns array of features: [RSI_14, SMA_ratio_20, SMA_ratio_50,
    volatility_20, momentum_10, momentum_20, volume_proxy, mean_reversion_5]

    Args:
        prices: List of closing prices (at least 60 data points).

    Returns:
        Feature matrix (n_samples x n_features).
    """
    p = np.array(prices, dtype=np.float64)
    n = len(p)
    if n < 60:
        raise ValueError("Need at least 60 price points")

    features = []
    for i in range(50, n):
        # RSI 14
        changes = np.diff(p[i-14:i+1])
        gains = np.mean(changes[changes > 0]) if np.any(changes > 0) else 0
        losses = -np.mean(changes[changes < 0]) if np.any(changes < 0) else 1e-10
        rsi = 100 - 100 / (1 + gains / (losses + 1e-10))

        sma20 = np.mean(p[i-19:i+1])
        sma50 = np.mean(p[i-49:i+1])
        vol20 = np.std(np.diff(np.log(p[i-20:i+1])))
        mom10 = (p[i] / p[i-10] - 1) * 100
        mom20 = (p[i] / p[i-20] - 1) * 100
        mr5 = (p[i] / np.mean(p[i-4:i+1]) - 1) * 100

        features.append([rsi, p[i]/sma20, p[i]/sma50, vol20, mom10, mom20, mr5])

    return np.array(features)


def rank_feature_importance(
    prices: List[float],
    feature_names: Optional[List[str]] = None,
    n_trees: int = 50,
    max_depth: int = 5,
    horizon: int = 5,
    seed: int = 42
) -> Dict:
    """
    Rank feature importance for predicting forward returns using random forest.

    Args:
        prices: Historical prices (60+ points).
        feature_names: Optional names for features.
        n_trees: Number of trees in the forest.
        max_depth: Max tree depth.
        horizon: Forward return horizon (days).
        seed: Random seed.

    Returns:
        Dict with ranked features, importance scores, and model stats.
    """
    default_names = ["RSI_14", "Price/SMA20", "Price/SMA50", "Volatility_20",
                     "Momentum_10", "Momentum_20", "MeanReversion_5"]
    if feature_names is None:
        feature_names = default_names

    X = compute_technical_features(prices)
    p = np.array(prices, dtype=np.float64)
    start_idx = len(p) - len(X)

    # Forward returns as target
    y = []
    valid_X = []
    for i in range(len(X)):
        price_idx = start_idx + i
        if price_idx + horizon < len(p):
            fwd_ret = (p[price_idx + horizon] / p[price_idx] - 1) * 100
            y.append(fwd_ret)
            valid_X.append(X[i])

    X_arr = np.array(valid_X)
    y_arr = np.array(y)

    # Train random forest
    importances = np.zeros(X_arr.shape[1])
    predictions = np.zeros(len(y_arr))
    rng = np.random.RandomState(seed)

    for t in range(n_trees):
        # Bootstrap sample
        idx = rng.choice(len(y_arr), len(y_arr), replace=True)
        tree = SimpleDecisionTree(max_depth=max_depth, seed=seed + t)
        tree.fit(X_arr[idx], y_arr[idx])
        importances += tree.feature_importances_
        predictions += tree.predict(X_arr)

    importances /= n_trees
    predictions /= n_trees

    # Rank
    ranked_idx = np.argsort(-importances)
    rankings = []
    for rank, idx in enumerate(ranked_idx):
        name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
        rankings.append({
            "rank": rank + 1,
            "feature": name,
            "importance": round(float(importances[idx]), 4),
            "importance_pct": round(float(importances[idx]) * 100, 2)
        })

    # Model performance
    ss_res = np.sum((y_arr - predictions) ** 2)
    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
    r2 = 1 - ss_res / (ss_tot + 1e-10)

    return {
        "rankings": rankings,
        "r_squared": round(float(r2), 4),
        "n_trees": n_trees,
        "n_samples": len(y_arr),
        "n_features": X_arr.shape[1],
        "horizon_days": horizon,
        "top_feature": rankings[0]["feature"],
        "model": "RandomForest-numpy"
    }


def permutation_importance(
    prices: List[float],
    n_trees: int = 30,
    n_permutations: int = 10,
    seed: int = 42
) -> Dict:
    """
    Compute permutation importance by measuring accuracy drop when each feature is shuffled.

    Args:
        prices: Historical prices.
        n_trees: Number of trees.
        n_permutations: Shuffles per feature.
        seed: Random seed.

    Returns:
        Dict with permutation importance scores per feature.
    """
    feature_names = ["RSI_14", "Price/SMA20", "Price/SMA50", "Volatility_20",
                     "Momentum_10", "Momentum_20", "MeanReversion_5"]

    X = compute_technical_features(prices)
    p = np.array(prices, dtype=np.float64)
    start_idx = len(p) - len(X)

    y = []
    valid_X = []
    for i in range(len(X)):
        price_idx = start_idx + i
        if price_idx + 5 < len(p):
            y.append((p[price_idx + 5] / p[price_idx] - 1) * 100)
            valid_X.append(X[i])

    X_arr = np.array(valid_X)
    y_arr = np.array(y)
    rng = np.random.RandomState(seed)

    # Train forest
    trees = []
    for t in range(n_trees):
        idx = rng.choice(len(y_arr), len(y_arr), replace=True)
        tree = SimpleDecisionTree(max_depth=5, seed=seed + t)
        tree.fit(X_arr[idx], y_arr[idx])
        trees.append(tree)

    def _forest_mse(X_input):
        preds = np.mean([t.predict(X_input) for t in trees], axis=0)
        return float(np.mean((y_arr - preds) ** 2))

    baseline_mse = _forest_mse(X_arr)
    perm_scores = []

    for feat in range(X_arr.shape[1]):
        drops = []
        for _ in range(n_permutations):
            X_perm = X_arr.copy()
            rng.shuffle(X_perm[:, feat])
            drops.append(_forest_mse(X_perm) - baseline_mse)
        name = feature_names[feat] if feat < len(feature_names) else f"feature_{feat}"
        perm_scores.append({
            "feature": name,
            "mean_mse_increase": round(float(np.mean(drops)), 6),
            "std": round(float(np.std(drops)), 6)
        })

    perm_scores.sort(key=lambda x: -x["mean_mse_increase"])
    for i, s in enumerate(perm_scores):
        s["rank"] = i + 1

    return {
        "baseline_mse": round(baseline_mse, 6),
        "permutation_rankings": perm_scores,
        "n_permutations": n_permutations,
        "n_trees": n_trees
    }
