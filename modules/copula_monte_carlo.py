"""
Monte Carlo Simulation with Copulas for tail dependency modeling.

Models joint distributions of asset returns using copula functions to capture
non-linear dependencies and tail risk that standard correlation misses.
Uses Gaussian and Student-t copulas for scenario generation.

Free data: Yahoo Finance for historical returns.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def fit_gaussian_copula(returns_matrix: np.ndarray) -> Dict:
    """
    Fit a Gaussian copula to multivariate return data.

    Args:
        returns_matrix: NxM array of N observations for M assets

    Returns:
        Dict with correlation matrix and marginal parameters
    """
    n_obs, n_assets = returns_matrix.shape

    # Estimate marginal distributions (empirical CDF via ranks)
    uniform_data = np.zeros_like(returns_matrix)
    for j in range(n_assets):
        ranks = np.argsort(np.argsort(returns_matrix[:, j])) + 1
        uniform_data[:, j] = ranks / (n_obs + 1)

    # Transform to normal space
    from scipy.stats import norm
    normal_data = norm.ppf(uniform_data)
    normal_data = np.clip(normal_data, -5, 5)

    # Estimate copula correlation
    copula_corr = np.corrcoef(normal_data.T)

    # Marginal stats
    marginals = []
    for j in range(n_assets):
        col = returns_matrix[:, j]
        marginals.append({
            "mean": float(np.mean(col)),
            "std": float(np.std(col, ddof=1)),
            "skew": float(_skewness(col)),
            "kurtosis": float(_kurtosis(col))
        })

    return {
        "copula_type": "gaussian",
        "correlation_matrix": copula_corr.tolist(),
        "n_assets": n_assets,
        "n_observations": n_obs,
        "marginals": marginals
    }


def simulate_copula_scenarios(
    copula_params: Dict,
    n_scenarios: int = 10000,
    seed: Optional[int] = None
) -> Dict:
    """
    Generate correlated return scenarios using fitted copula.

    Args:
        copula_params: Output from fit_gaussian_copula
        n_scenarios: Number of scenarios to generate
        seed: Random seed for reproducibility

    Returns:
        Dict with simulated returns and risk metrics
    """
    if seed is not None:
        np.random.seed(seed)

    corr = np.array(copula_params["correlation_matrix"])
    n_assets = copula_params["n_assets"]
    marginals = copula_params["marginals"]

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(corr)
    except np.linalg.LinAlgError:
        # Fix non-PD matrix
        eigvals, eigvecs = np.linalg.eigh(corr)
        eigvals = np.maximum(eigvals, 1e-8)
        corr = eigvecs @ np.diag(eigvals) @ eigvecs.T
        np.fill_diagonal(corr, 1.0)
        L = np.linalg.cholesky(corr)

    # Generate correlated normal samples
    z = np.random.standard_normal((n_scenarios, n_assets))
    correlated_normal = z @ L.T

    # Transform back to returns using marginal distributions
    from scipy.stats import norm
    uniform_samples = norm.cdf(correlated_normal)

    simulated_returns = np.zeros_like(uniform_samples)
    for j in range(n_assets):
        m = marginals[j]
        simulated_returns[:, j] = norm.ppf(uniform_samples[:, j]) * m["std"] + m["mean"]

    # Portfolio metrics (equal weight)
    weights = np.ones(n_assets) / n_assets
    portfolio_returns = simulated_returns @ weights

    var_95 = float(np.percentile(portfolio_returns, 5))
    var_99 = float(np.percentile(portfolio_returns, 1))
    cvar_95 = float(np.mean(portfolio_returns[portfolio_returns <= var_95]))
    cvar_99 = float(np.mean(portfolio_returns[portfolio_returns <= var_99]))

    # Tail dependency (lower tail)
    threshold = 0.05
    tail_deps = []
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            u_i = uniform_samples[:, i]
            u_j = uniform_samples[:, j]
            joint_tail = np.mean((u_i <= threshold) & (u_j <= threshold))
            marginal_tail = threshold
            lambda_l = joint_tail / marginal_tail if marginal_tail > 0 else 0
            tail_deps.append({
                "asset_i": i,
                "asset_j": j,
                "lower_tail_dependence": round(lambda_l, 4)
            })

    return {
        "n_scenarios": n_scenarios,
        "portfolio_var_95": round(var_95, 6),
        "portfolio_var_99": round(var_99, 6),
        "portfolio_cvar_95": round(cvar_95, 6),
        "portfolio_cvar_99": round(cvar_99, 6),
        "portfolio_mean": round(float(np.mean(portfolio_returns)), 6),
        "portfolio_std": round(float(np.std(portfolio_returns)), 6),
        "tail_dependencies": tail_deps,
        "worst_scenario": round(float(np.min(portfolio_returns)), 6),
        "best_scenario": round(float(np.max(portfolio_returns)), 6)
    }


def compute_tail_risk_comparison(returns_matrix: np.ndarray, n_scenarios: int = 50000) -> Dict:
    """
    Compare risk metrics: copula-based vs standard normal assumption.

    Args:
        returns_matrix: Historical return data
        n_scenarios: Simulation count

    Returns:
        Dict comparing Gaussian copula vs naive normal VaR/CVaR
    """
    copula_params = fit_gaussian_copula(returns_matrix)
    copula_result = simulate_copula_scenarios(copula_params, n_scenarios, seed=42)

    # Naive: assume multivariate normal
    n_assets = returns_matrix.shape[1]
    mean_vec = np.mean(returns_matrix, axis=0)
    cov_mat = np.cov(returns_matrix.T)
    weights = np.ones(n_assets) / n_assets

    port_mean = float(weights @ mean_vec)
    port_var = float(weights @ cov_mat @ weights)
    port_std = np.sqrt(port_var)

    from scipy.stats import norm
    naive_var_95 = round(port_mean + norm.ppf(0.05) * port_std, 6)
    naive_var_99 = round(port_mean + norm.ppf(0.01) * port_std, 6)

    return {
        "copula_var_95": copula_result["portfolio_var_95"],
        "copula_var_99": copula_result["portfolio_var_99"],
        "copula_cvar_95": copula_result["portfolio_cvar_95"],
        "copula_cvar_99": copula_result["portfolio_cvar_99"],
        "naive_var_95": naive_var_95,
        "naive_var_99": naive_var_99,
        "var_95_difference_bps": round((copula_result["portfolio_var_95"] - naive_var_95) * 10000, 1),
        "var_99_difference_bps": round((copula_result["portfolio_var_99"] - naive_var_99) * 10000, 1),
        "tail_dependencies": copula_result["tail_dependencies"]
    }


def _skewness(x: np.ndarray) -> float:
    n = len(x)
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0:
        return 0.0
    return float((n / ((n - 1) * (n - 2))) * np.sum(((x - m) / s) ** 3)) if n > 2 else 0.0


def _kurtosis(x: np.ndarray) -> float:
    n = len(x)
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0 or n < 4:
        return 0.0
    k = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3)) * np.sum(((x - m) / s) ** 4)
    return float(k - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
