"""Minimum Variance Portfolio Builder — construct the portfolio with lowest possible volatility.

Implements analytical and numerical minimum variance optimization with optional constraints
(long-only, max weight, sector). Uses numpy only — no scipy required.
"""

import numpy as np
from typing import Dict, List, Optional


def build_min_variance(cov_matrix: List[List[float]], asset_names: Optional[List[str]] = None,
                       long_only: bool = True, max_weight: float = 1.0) -> Dict:
    """Build minimum variance portfolio from covariance matrix.

    Args:
        cov_matrix: NxN covariance matrix.
        asset_names: Optional asset labels.
        long_only: If True, constrain weights >= 0.
        max_weight: Maximum weight per asset.

    Returns:
        Dict with weights, portfolio_vol, and diversification_ratio.
    """
    cov = np.array(cov_matrix, dtype=float)
    n = cov.shape[0]
    names = asset_names or [f"asset_{i}" for i in range(n)]

    if not long_only and max_weight >= 1.0:
        # Analytical solution: w = Σ^{-1} * 1 / (1' Σ^{-1} 1)
        try:
            inv_cov = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            inv_cov = np.linalg.pinv(cov)
        ones = np.ones(n)
        w = inv_cov @ ones / (ones @ inv_cov @ ones)
    else:
        # Iterative projection for constrained case
        w = np.ones(n) / n
        lr = 0.01
        for _ in range(5000):
            grad = 2 * cov @ w
            w -= lr * grad
            if long_only:
                w = np.maximum(w, 0)
            w = np.minimum(w, max_weight)
            w_sum = np.sum(w)
            if w_sum > 0:
                w /= w_sum

    port_var = float(w @ cov @ w)
    port_vol = float(np.sqrt(port_var))
    asset_vols = np.sqrt(np.diag(cov))
    weighted_vol = float(w @ asset_vols)
    div_ratio = weighted_vol / port_vol if port_vol > 0 else 1.0

    return {
        "weights": {names[i]: round(float(w[i]), 6) for i in range(n) if w[i] > 1e-6},
        "portfolio_volatility": round(port_vol, 6),
        "portfolio_variance": round(port_var, 8),
        "diversification_ratio": round(div_ratio, 4),
        "effective_n_assets": int(np.sum(w > 0.01)),
        "herfindahl_index": round(float(np.sum(w ** 2)), 4),
    }


def rolling_min_variance(returns_matrix: List[List[float]], window: int = 60,
                          asset_names: Optional[List[str]] = None) -> List[Dict]:
    """Compute rolling minimum variance portfolio weights over time.

    Args:
        returns_matrix: rows=assets, cols=periods.
        window: Rolling window for covariance estimation.

    Returns:
        List of portfolio snapshots per period.
    """
    mat = np.array(returns_matrix, dtype=float)
    n_assets, n_periods = mat.shape
    names = asset_names or [f"asset_{i}" for i in range(n_assets)]
    results = []

    for t in range(window, n_periods):
        sub = mat[:, t - window:t]
        cov = np.cov(sub)
        if cov.ndim == 0:
            cov = np.array([[float(cov)]])
        result = build_min_variance(cov.tolist(), names, long_only=True)
        result["period"] = t
        results.append(result)

    return results


def compare_portfolios(cov_matrix: List[List[float]], expected_returns: List[float],
                        asset_names: Optional[List[str]] = None) -> Dict:
    """Compare minimum variance vs equal weight vs inverse volatility portfolios.

    Returns metrics for all three approaches.
    """
    cov = np.array(cov_matrix, dtype=float)
    er = np.array(expected_returns, dtype=float)
    n = cov.shape[0]
    names = asset_names or [f"asset_{i}" for i in range(n)]
    vols = np.sqrt(np.diag(cov))

    # Equal weight
    w_eq = np.ones(n) / n
    # Inverse vol
    inv_vol = 1.0 / np.maximum(vols, 1e-8)
    w_iv = inv_vol / np.sum(inv_vol)
    # Min variance
    mv = build_min_variance(cov_matrix, names, long_only=True)

    def _metrics(w):
        ret = float(w @ er)
        vol = float(np.sqrt(w @ cov @ w))
        sharpe = ret / vol if vol > 0 else 0.0
        return {"return": round(ret, 6), "volatility": round(vol, 6), "sharpe": round(sharpe, 4)}

    return {
        "min_variance": {**mv, **_metrics(np.array([mv["weights"].get(names[i], 0) for i in range(n)]))},
        "equal_weight": _metrics(w_eq),
        "inverse_volatility": _metrics(w_iv),
    }
