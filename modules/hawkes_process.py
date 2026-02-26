"""
Hawkes Process for Trade Clustering — Self-exciting point process model to detect
clustered trading activity, flash crash dynamics, and momentum cascades.

Hawkes processes model events where each occurrence increases the probability
of future events (self-excitation), perfect for modeling trade arrivals.

Phase: 295 | Category: AI/ML Models
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def simulate_hawkes(
    mu: float = 0.5,
    alpha: float = 0.8,
    beta: float = 1.2,
    T: float = 100.0,
    seed: int = 42
) -> List[float]:
    """
    Simulate a univariate Hawkes process via thinning algorithm.

    Args:
        mu: Baseline intensity (events per unit time).
        alpha: Excitation magnitude (must be < beta for stability).
        beta: Decay rate of excitation.
        T: Time horizon.
        seed: Random seed.

    Returns:
        List of event times.
    """
    rng = np.random.RandomState(seed)
    events = []
    t = 0.0

    # Upper bound on intensity
    lambda_bar = mu / (1 - alpha / beta) * 2

    while t < T:
        dt = rng.exponential(1.0 / lambda_bar)
        t += dt
        if t >= T:
            break

        # Current intensity
        lam = mu
        for s in events:
            lam += alpha * np.exp(-beta * (t - s))

        if rng.random() < lam / lambda_bar:
            events.append(t)
            lambda_bar = max(lambda_bar, lam + alpha)

    return events


def estimate_hawkes_params(
    event_times: List[float],
    max_iter: int = 100,
    lr: float = 0.01
) -> Dict:
    """
    Estimate Hawkes process parameters (mu, alpha, beta) via maximum likelihood.

    Uses gradient ascent on the log-likelihood.

    Args:
        event_times: List of event timestamps (sorted ascending).
        max_iter: Maximum optimization iterations.
        lr: Learning rate.

    Returns:
        Dict with estimated parameters, log-likelihood, and branching ratio.
    """
    times = np.array(sorted(event_times), dtype=np.float64)
    n = len(times)
    T = times[-1] - times[0] if n > 1 else 1.0

    if n < 10:
        return {"error": "Need at least 10 events", "n_events": n}

    # Shift to start at 0
    times = times - times[0]
    T = times[-1]

    # Initialize
    mu = n / T * 0.5
    alpha = 0.3
    beta = 1.0

    for iteration in range(max_iter):
        # Compute intensity at each event
        intensities = np.zeros(n)
        A = np.zeros(n)  # recursive kernel sum

        for i in range(n):
            if i == 0:
                A[i] = 0
            else:
                dt = times[i] - times[i-1]
                A[i] = np.exp(-beta * dt) * (1 + A[i-1])
            intensities[i] = mu + alpha * A[i]

        # Log-likelihood
        ll = np.sum(np.log(np.maximum(intensities, 1e-10)))
        ll -= mu * T
        ll -= alpha / beta * np.sum(1 - np.exp(-beta * (T - times)))

        # Gradients
        inv_lam = 1.0 / np.maximum(intensities, 1e-10)
        dmu = np.sum(inv_lam) - T
        dalpha = np.sum(inv_lam * A) - (1/beta) * np.sum(1 - np.exp(-beta * (T - times)))

        dA_dbeta = np.zeros(n)
        for i in range(1, n):
            dt = times[i] - times[i-1]
            dA_dbeta[i] = np.exp(-beta * dt) * (-dt * (1 + A[i-1]) + dA_dbeta[i-1])

        dbeta = alpha * np.sum(inv_lam * dA_dbeta)
        dbeta += alpha / (beta**2) * np.sum(1 - np.exp(-beta * (T - times)))
        dbeta -= alpha / beta * np.sum((T - times) * np.exp(-beta * (T - times)))

        # Update
        mu = max(1e-6, mu + lr * dmu)
        alpha = max(1e-6, min(beta * 0.99, alpha + lr * dalpha))
        beta = max(1e-6, beta + lr * dbeta)

    branching_ratio = alpha / beta

    return {
        "mu": round(float(mu), 6),
        "alpha": round(float(alpha), 6),
        "beta": round(float(beta), 6),
        "branching_ratio": round(float(branching_ratio), 4),
        "stable": branching_ratio < 1.0,
        "log_likelihood": round(float(ll), 4),
        "n_events": n,
        "time_span": round(float(T), 2),
        "avg_intensity": round(float(n / T), 4),
        "interpretation": (
            "Sub-critical (stationary)" if branching_ratio < 0.5
            else "Near-critical (highly clustered)" if branching_ratio < 1.0
            else "Super-critical (explosive, non-stationary)"
        )
    }


def detect_trade_clusters(
    event_times: List[float],
    threshold_multiplier: float = 2.0,
    window: float = 1.0
) -> Dict:
    """
    Detect clusters of elevated trading activity using Hawkes intensity.

    Args:
        event_times: Trade timestamps (e.g., seconds since midnight).
        threshold_multiplier: How many x above baseline to flag a cluster.
        window: Time window for smoothing (same units as event_times).

    Returns:
        Dict with detected clusters, their intensity, duration, and event count.
    """
    times = np.array(sorted(event_times), dtype=np.float64)
    n = len(times)
    if n < 10:
        return {"clusters": [], "n_events": n, "error": "Too few events"}

    # Estimate params
    params = estimate_hawkes_params(event_times)
    if "error" in params:
        return params

    mu = params["mu"]
    alpha = params["alpha"]
    beta = params["beta"]
    threshold = mu * threshold_multiplier

    # Compute intensity at each event
    intensities = []
    kernel_sum = 0.0
    for i in range(n):
        if i > 0:
            dt = times[i] - times[i-1]
            kernel_sum = np.exp(-beta * dt) * (kernel_sum + 1)
        lam = mu + alpha * kernel_sum
        intensities.append(lam)

    intensities = np.array(intensities)

    # Find clusters (contiguous regions above threshold)
    above = intensities > threshold
    clusters = []
    in_cluster = False
    start_idx = 0

    for i in range(n):
        if above[i] and not in_cluster:
            in_cluster = True
            start_idx = i
        elif not above[i] and in_cluster:
            in_cluster = False
            clusters.append({
                "start_time": round(float(times[start_idx]), 4),
                "end_time": round(float(times[i-1]), 4),
                "duration": round(float(times[i-1] - times[start_idx]), 4),
                "n_events": int(i - start_idx),
                "peak_intensity": round(float(max(intensities[start_idx:i])), 4),
                "avg_intensity": round(float(np.mean(intensities[start_idx:i])), 4)
            })

    if in_cluster:
        clusters.append({
            "start_time": round(float(times[start_idx]), 4),
            "end_time": round(float(times[-1]), 4),
            "duration": round(float(times[-1] - times[start_idx]), 4),
            "n_events": int(n - start_idx),
            "peak_intensity": round(float(max(intensities[start_idx:])), 4),
            "avg_intensity": round(float(np.mean(intensities[start_idx:])), 4)
        })

    return {
        "clusters": clusters,
        "n_clusters": len(clusters),
        "n_events": n,
        "baseline_intensity": round(float(mu), 4),
        "threshold": round(float(threshold), 4),
        "hawkes_params": params,
        "pct_time_clustered": round(
            sum(c["duration"] for c in clusters) / (float(times[-1] - times[0]) + 1e-10) * 100, 2
        )
    }
