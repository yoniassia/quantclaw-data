"""
Hidden Markov Model Regime Detector — Identifies market regimes (bull/bear/sideways)
using Gaussian HMM fitted to returns data.

Uses Yahoo Finance for price data (free). Implements a simplified Gaussian HMM
with Baum-Welch (EM) algorithm for regime detection without heavy dependencies.
"""

import numpy as np
from typing import Dict, List, Any, Optional


def _fetch_returns(ticker: str, period: str = "2y") -> np.ndarray:
    """Fetch log returns for a ticker."""
    try:
        import yfinance as yf
        data = yf.download(ticker, period=period, progress=False)
        prices = data["Close"].dropna().values.flatten()
        return np.log(prices[1:] / prices[:-1])
    except Exception:
        return np.array([])


class SimpleGaussianHMM:
    """Minimal 2-3 state Gaussian HMM with EM fitting."""

    def __init__(self, n_states: int = 2, n_iter: int = 50):
        self.n_states = n_states
        self.n_iter = n_iter
        self.means = None
        self.stds = None
        self.trans_matrix = None
        self.start_prob = None

    def fit(self, obs: np.ndarray):
        """Fit HMM via simplified EM."""
        n = len(obs)
        k = self.n_states
        # Initialize with quantile-based clustering
        quantiles = np.linspace(0, 1, k + 1)
        self.means = np.array([np.quantile(obs, (quantiles[i] + quantiles[i+1]) / 2) for i in range(k)])
        self.stds = np.full(k, np.std(obs) / k)
        self.trans_matrix = np.full((k, k), 1.0 / k)
        np.fill_diagonal(self.trans_matrix, 0.9)
        self.trans_matrix /= self.trans_matrix.sum(axis=1, keepdims=True)
        self.start_prob = np.full(k, 1.0 / k)

        for _ in range(self.n_iter):
            # E-step: compute responsibilities
            log_lik = np.zeros((n, k))
            for j in range(k):
                s = max(self.stds[j], 1e-8)
                log_lik[:, j] = -0.5 * ((obs - self.means[j]) / s) ** 2 - np.log(s)
            # Normalize to get gamma (simplified, ignoring transition for speed)
            log_lik -= log_lik.max(axis=1, keepdims=True)
            gamma = np.exp(log_lik)
            gamma /= gamma.sum(axis=1, keepdims=True) + 1e-10
            # M-step
            for j in range(k):
                w = gamma[:, j]
                wsum = w.sum() + 1e-10
                self.means[j] = np.sum(w * obs) / wsum
                self.stds[j] = np.sqrt(np.sum(w * (obs - self.means[j])**2) / wsum + 1e-8)
            # Update transitions from gamma
            for i in range(k):
                for j in range(k):
                    self.trans_matrix[i, j] = np.sum(gamma[:-1, i] * gamma[1:, j]) + 1e-6
            self.trans_matrix /= self.trans_matrix.sum(axis=1, keepdims=True)

        # Sort states by mean (bear < sideways < bull)
        order = np.argsort(self.means)
        self.means = self.means[order]
        self.stds = self.stds[order]
        self.trans_matrix = self.trans_matrix[order][:, order]
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """Viterbi-like MAP state assignment."""
        n = len(obs)
        k = self.n_states
        log_lik = np.zeros((n, k))
        for j in range(k):
            s = max(self.stds[j], 1e-8)
            log_lik[:, j] = -0.5 * ((obs - self.means[j]) / s)**2 - np.log(s)
        return np.argmax(log_lik, axis=1)


def detect_regimes(ticker: str = "SPY", period: str = "2y",
                   n_states: int = 3) -> Dict[str, Any]:
    """
    Detect market regimes for a given ticker using Gaussian HMM.

    Args:
        ticker: Asset ticker symbol
        period: Lookback period
        n_states: Number of regimes (2=bull/bear, 3=bull/sideways/bear)

    Returns:
        Regime parameters, current regime, transition matrix, and recent history
    """
    returns = _fetch_returns(ticker, period)
    if len(returns) < 60:
        return {"error": f"Insufficient data for {ticker}"}

    model = SimpleGaussianHMM(n_states=n_states)
    model.fit(returns)
    states = model.predict(returns)

    labels = ["bear", "sideways", "bull"] if n_states == 3 else ["bear", "bull"]
    current_state = int(states[-1])
    current_label = labels[current_state] if current_state < len(labels) else f"state_{current_state}"

    # Regime durations
    regime_changes = np.where(np.diff(states) != 0)[0]
    durations = np.diff(np.concatenate([[0], regime_changes, [len(states)]]))

    # State statistics
    state_stats = []
    for i in range(n_states):
        mask = states == i
        label = labels[i] if i < len(labels) else f"state_{i}"
        state_stats.append({
            "state": i,
            "label": label,
            "mean_daily_return": float(model.means[i]),
            "annualized_return": float(model.means[i] * 252),
            "daily_volatility": float(model.stds[i]),
            "annualized_volatility": float(model.stds[i] * np.sqrt(252)),
            "frequency": float(mask.sum() / len(states)),
        })

    # Recent regime history (last 30 days)
    recent = [{"day": -i, "regime": labels[int(s)] if int(s) < len(labels) else f"state_{s}"}
              for i, s in enumerate(reversed(states[-30:]))]

    return {
        "ticker": ticker,
        "n_states": n_states,
        "current_regime": current_label,
        "current_state": current_state,
        "days_in_current_regime": int(len(states) - regime_changes[-1] - 1) if len(regime_changes) > 0 else len(states),
        "state_statistics": state_stats,
        "transition_matrix": model.trans_matrix.tolist(),
        "avg_regime_duration_days": float(np.mean(durations)),
        "total_regime_changes": len(regime_changes),
        "recent_history": recent[:10],
    }


def compare_regimes(tickers: List[str], period: str = "2y") -> List[Dict[str, Any]]:
    """
    Compare current regime across multiple assets.

    Args:
        tickers: List of tickers to analyze
        period: Lookback period

    Returns:
        List of regime summaries per ticker
    """
    results = []
    for t in tickers:
        try:
            r = detect_regimes(t, period, n_states=3)
            if "error" not in r:
                results.append({
                    "ticker": t,
                    "current_regime": r["current_regime"],
                    "days_in_regime": r["days_in_current_regime"],
                    "bull_frequency": next((s["frequency"] for s in r["state_statistics"] if s["label"] == "bull"), 0),
                    "bear_frequency": next((s["frequency"] for s in r["state_statistics"] if s["label"] == "bear"), 0),
                })
        except Exception:
            continue
    return results
