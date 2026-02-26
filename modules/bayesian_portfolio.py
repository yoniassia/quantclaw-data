"""
Bayesian Portfolio Optimization — Posterior-based portfolio construction using
conjugate priors and MCMC-lite sampling for robust weight estimation.

Addresses estimation error in mean-variance optimization by incorporating
prior beliefs about expected returns and covariance structure.

Phase: 293 | Category: AI/ML Models
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def _inverse_wishart_sample(df: int, scale: np.ndarray, rng: np.random.RandomState) -> np.ndarray:
    """Approximate Inverse-Wishart sample via Bartlett decomposition."""
    p = scale.shape[0]
    L = np.linalg.cholesky(scale)
    A = np.zeros((p, p))
    for i in range(p):
        A[i, i] = np.sqrt(rng.chisquare(df - i))
        for j in range(i):
            A[i, j] = rng.randn()
    LA = L @ np.linalg.inv(A)
    return LA @ LA.T


def estimate_posterior_returns(
    returns: np.ndarray,
    prior_mean: Optional[np.ndarray] = None,
    prior_precision: float = 1.0,
    n_samples: int = 1000,
    seed: int = 42
) -> Dict:
    """
    Estimate posterior distribution of expected returns using conjugate Normal-Inverse-Wishart prior.

    Args:
        returns: T x N array of asset returns (T periods, N assets).
        prior_mean: Prior expected returns (default: zero vector).
        prior_precision: Strength of prior belief (higher = more weight on prior).
        n_samples: Number of posterior samples.
        seed: Random seed.

    Returns:
        Dict with posterior mean, std, credible intervals per asset, and sampled covariances.
    """
    T, N = returns.shape
    rng = np.random.RandomState(seed)

    sample_mean = returns.mean(axis=0)
    sample_cov = np.cov(returns, rowvar=False) * (T - 1) / T

    if prior_mean is None:
        prior_mean = np.zeros(N)

    # Posterior parameters (conjugate update)
    kappa_0 = prior_precision
    kappa_n = kappa_0 + T
    mu_n = (kappa_0 * prior_mean + T * sample_mean) / kappa_n

    nu_0 = N + 2
    nu_n = nu_0 + T
    psi_0 = np.eye(N) * np.diag(sample_cov).mean()
    diff = sample_mean - prior_mean
    psi_n = psi_0 + T * sample_cov + (kappa_0 * T / kappa_n) * np.outer(diff, diff)

    # Sample from posterior
    mu_samples = np.zeros((n_samples, N))
    for s in range(n_samples):
        sigma_sample = _inverse_wishart_sample(nu_n, psi_n, rng)
        sigma_sample = (sigma_sample + sigma_sample.T) / 2  # symmetrize
        mu_cov = sigma_sample / kappa_n
        try:
            L = np.linalg.cholesky(mu_cov + np.eye(N) * 1e-8)
            mu_samples[s] = mu_n + L @ rng.randn(N)
        except np.linalg.LinAlgError:
            mu_samples[s] = mu_n + rng.randn(N) * np.sqrt(np.diag(mu_cov))

    posterior_mean = mu_samples.mean(axis=0)
    posterior_std = mu_samples.std(axis=0)
    ci_lower = np.percentile(mu_samples, 2.5, axis=0)
    ci_upper = np.percentile(mu_samples, 97.5, axis=0)

    return {
        "posterior_mean": posterior_mean.tolist(),
        "posterior_std": posterior_std.tolist(),
        "ci_95_lower": ci_lower.tolist(),
        "ci_95_upper": ci_upper.tolist(),
        "sample_mean": sample_mean.tolist(),
        "prior_mean": prior_mean.tolist(),
        "shrinkage": round(float(kappa_0 / kappa_n), 4),
        "n_assets": N,
        "n_periods": T,
        "n_samples": n_samples
    }


def optimize_bayesian_portfolio(
    returns: np.ndarray,
    asset_names: Optional[List[str]] = None,
    risk_aversion: float = 2.0,
    prior_mean: Optional[np.ndarray] = None,
    prior_precision: float = 1.0,
    n_samples: int = 500,
    long_only: bool = True,
    seed: int = 42
) -> Dict:
    """
    Bayesian portfolio optimization — average optimal weights across posterior samples.

    Instead of point-estimate MVO, samples from the posterior and averages the
    resulting optimal portfolios, yielding more robust weights.

    Args:
        returns: T x N return matrix.
        asset_names: Optional list of asset names.
        risk_aversion: Risk aversion parameter (lambda).
        prior_mean: Prior on expected returns.
        prior_precision: Prior strength.
        n_samples: Posterior samples to draw.
        long_only: Constrain weights >= 0.
        seed: Random seed.

    Returns:
        Dict with optimal weights, expected return/risk, and comparison to classical MVO.
    """
    T, N = returns.shape
    rng = np.random.RandomState(seed)
    if asset_names is None:
        asset_names = [f"Asset_{i}" for i in range(N)]

    sample_mean = returns.mean(axis=0)
    sample_cov = np.cov(returns, rowvar=False)

    # Classical MVO weights
    try:
        inv_cov = np.linalg.inv(sample_cov + np.eye(N) * 1e-8)
        mvo_weights = inv_cov @ sample_mean / risk_aversion
        if long_only:
            mvo_weights = np.maximum(mvo_weights, 0)
        w_sum = mvo_weights.sum()
        if w_sum > 0:
            mvo_weights /= w_sum
        else:
            mvo_weights = np.ones(N) / N
    except np.linalg.LinAlgError:
        mvo_weights = np.ones(N) / N

    # Bayesian: sample posterior, compute weights for each sample, average
    posterior = estimate_posterior_returns(returns, prior_mean, prior_precision, n_samples, seed)
    mu_samples_arr = np.array([
        np.array(posterior["posterior_mean"]) + rng.randn(N) * np.array(posterior["posterior_std"])
        for _ in range(n_samples)
    ])

    weight_samples = np.zeros((n_samples, N))
    for s in range(n_samples):
        try:
            inv_cov = np.linalg.inv(sample_cov + np.eye(N) * 1e-8)
            w = inv_cov @ mu_samples_arr[s] / risk_aversion
            if long_only:
                w = np.maximum(w, 0)
            w_sum = w.sum()
            if w_sum > 0:
                w /= w_sum
            else:
                w = np.ones(N) / N
            weight_samples[s] = w
        except np.linalg.LinAlgError:
            weight_samples[s] = np.ones(N) / N

    bayesian_weights = weight_samples.mean(axis=0)
    weight_std = weight_samples.std(axis=0)

    # Normalize
    bw_sum = bayesian_weights.sum()
    if bw_sum > 0:
        bayesian_weights /= bw_sum

    # Portfolio stats
    bay_ret = float(bayesian_weights @ sample_mean) * 252
    bay_vol = float(np.sqrt(bayesian_weights @ sample_cov @ bayesian_weights)) * np.sqrt(252)
    mvo_ret = float(mvo_weights @ sample_mean) * 252
    mvo_vol = float(np.sqrt(mvo_weights @ sample_cov @ mvo_weights)) * np.sqrt(252)

    allocations = []
    for i in range(N):
        allocations.append({
            "asset": asset_names[i],
            "bayesian_weight": round(float(bayesian_weights[i]), 4),
            "mvo_weight": round(float(mvo_weights[i]), 4),
            "weight_std": round(float(weight_std[i]), 4),
            "diff": round(float(bayesian_weights[i] - mvo_weights[i]), 4)
        })

    allocations.sort(key=lambda x: -x["bayesian_weight"])

    return {
        "allocations": allocations,
        "bayesian_portfolio": {
            "expected_return_ann": round(bay_ret * 100, 2),
            "volatility_ann": round(bay_vol * 100, 2),
            "sharpe": round(bay_ret / (bay_vol + 1e-10), 3)
        },
        "mvo_portfolio": {
            "expected_return_ann": round(mvo_ret * 100, 2),
            "volatility_ann": round(mvo_vol * 100, 2),
            "sharpe": round(mvo_ret / (mvo_vol + 1e-10), 3)
        },
        "risk_aversion": risk_aversion,
        "prior_precision": prior_precision,
        "n_posterior_samples": n_samples,
        "model": "Bayesian-MVO-NormalInverseWishart"
    }
