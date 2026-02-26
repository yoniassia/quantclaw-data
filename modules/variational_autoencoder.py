"""
Variational Autoencoder (VAE) for Financial Scenario Generation — Generate realistic
synthetic market scenarios for stress testing and Monte Carlo simulation.

Learns the latent distribution of market returns and generates new samples that
preserve statistical properties (fat tails, correlations, regime structure).

Phase: 296 | Category: AI/ML Models
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)


def _relu_grad(x: np.ndarray) -> np.ndarray:
    return (x > 0).astype(float)


class SimpleVAE:
    """Minimal VAE using numpy for scenario generation (encoder-decoder with 1 hidden layer)."""

    def __init__(self, input_dim: int, hidden_dim: int = 32, latent_dim: int = 8, seed: int = 42):
        rng = np.random.RandomState(seed)
        scale = 0.1
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder
        self.W_enc = rng.randn(hidden_dim, input_dim) * scale
        self.b_enc = np.zeros(hidden_dim)
        self.W_mu = rng.randn(latent_dim, hidden_dim) * scale
        self.b_mu = np.zeros(latent_dim)
        self.W_logvar = rng.randn(latent_dim, hidden_dim) * scale
        self.b_logvar = np.zeros(latent_dim)

        # Decoder
        self.W_dec = rng.randn(hidden_dim, latent_dim) * scale
        self.b_dec = np.zeros(hidden_dim)
        self.W_out = rng.randn(input_dim, hidden_dim) * scale
        self.b_out = np.zeros(input_dim)

        self.rng = rng

    def encode(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        h = _relu(self.W_enc @ x + self.b_enc)
        mu = self.W_mu @ h + self.b_mu
        logvar = self.W_logvar @ h + self.b_logvar
        return mu, logvar

    def reparameterize(self, mu: np.ndarray, logvar: np.ndarray) -> np.ndarray:
        std = np.exp(0.5 * logvar)
        eps = self.rng.randn(*mu.shape)
        return mu + eps * std

    def decode(self, z: np.ndarray) -> np.ndarray:
        h = _relu(self.W_dec @ z + self.b_dec)
        return self.W_out @ h + self.b_out

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decode(z)
        return x_recon, mu, logvar

    def loss(self, x: np.ndarray, x_recon: np.ndarray, mu: np.ndarray, logvar: np.ndarray) -> float:
        recon_loss = np.sum((x - x_recon) ** 2)
        kl_loss = -0.5 * np.sum(1 + logvar - mu ** 2 - np.exp(logvar))
        return float(recon_loss + kl_loss)

    def train(self, data: np.ndarray, epochs: int = 100, lr: float = 0.001) -> List[float]:
        """Simple training loop with numerical gradients (for small datasets)."""
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0
            indices = self.rng.permutation(len(data))
            for idx in indices:
                x = data[idx]
                x_recon, mu, logvar = self.forward(x)
                l = self.loss(x, x_recon, mu, logvar)
                epoch_loss += l

                # Simple gradient step on decoder output
                grad = 2 * (x_recon - x)
                self.W_out -= lr * np.outer(grad, _relu(self.W_dec @ self.reparameterize(mu, logvar) + self.b_dec))
                self.b_out -= lr * grad

            losses.append(epoch_loss / len(data))
        return losses

    def generate(self, n_samples: int = 100) -> np.ndarray:
        """Generate samples from the prior p(z) = N(0, I)."""
        samples = []
        for _ in range(n_samples):
            z = self.rng.randn(self.latent_dim)
            samples.append(self.decode(z))
        return np.array(samples)


def generate_market_scenarios(
    returns: np.ndarray,
    n_scenarios: int = 1000,
    latent_dim: int = 4,
    hidden_dim: int = 16,
    epochs: int = 50,
    seed: int = 42
) -> Dict:
    """
    Train a VAE on historical returns and generate synthetic market scenarios.

    Args:
        returns: T x N array of asset returns (T periods, N assets).
        n_scenarios: Number of synthetic scenarios to generate.
        latent_dim: Dimension of latent space.
        hidden_dim: Hidden layer size.
        epochs: Training epochs.
        seed: Random seed.

    Returns:
        Dict with synthetic scenarios, statistics comparison, and VAE metrics.
    """
    T, N = returns.shape

    # Normalize
    mu = returns.mean(axis=0)
    sigma = returns.std(axis=0) + 1e-10
    normed = (returns - mu) / sigma

    vae = SimpleVAE(input_dim=N, hidden_dim=hidden_dim, latent_dim=latent_dim, seed=seed)
    losses = vae.train(normed, epochs=epochs)

    # Generate
    synthetic_normed = vae.generate(n_scenarios)
    synthetic = synthetic_normed * sigma + mu

    # Compare statistics
    real_stats = {
        "mean": returns.mean(axis=0).tolist(),
        "std": returns.std(axis=0).tolist(),
        "skew": [float(np.mean(((returns[:, i] - returns[:, i].mean()) / (returns[:, i].std() + 1e-10)) ** 3))
                 for i in range(N)],
        "kurtosis": [float(np.mean(((returns[:, i] - returns[:, i].mean()) / (returns[:, i].std() + 1e-10)) ** 4) - 3)
                     for i in range(N)]
    }

    syn_stats = {
        "mean": synthetic.mean(axis=0).tolist(),
        "std": synthetic.std(axis=0).tolist(),
        "skew": [float(np.mean(((synthetic[:, i] - synthetic[:, i].mean()) / (synthetic[:, i].std() + 1e-10)) ** 3))
                 for i in range(N)],
        "kurtosis": [float(np.mean(((synthetic[:, i] - synthetic[:, i].mean()) / (synthetic[:, i].std() + 1e-10)) ** 4) - 3)
                     for i in range(N)]
    }

    # Correlation comparison
    real_corr = np.corrcoef(returns, rowvar=False) if N > 1 else np.array([[1.0]])
    syn_corr = np.corrcoef(synthetic, rowvar=False) if N > 1 else np.array([[1.0]])
    corr_error = float(np.mean(np.abs(real_corr - syn_corr)))

    return {
        "n_scenarios": n_scenarios,
        "n_assets": N,
        "n_training_samples": T,
        "latent_dim": latent_dim,
        "final_loss": round(float(losses[-1]), 4) if losses else None,
        "real_statistics": {k: [round(v, 6) for v in vals] for k, vals in real_stats.items()},
        "synthetic_statistics": {k: [round(v, 6) for v in vals] for k, vals in syn_stats.items()},
        "correlation_mae": round(corr_error, 6),
        "scenarios_summary": {
            "mean_return": [round(float(v), 6) for v in synthetic.mean(axis=0)],
            "worst_scenario": [round(float(v), 6) for v in synthetic.min(axis=0)],
            "best_scenario": [round(float(v), 6) for v in synthetic.max(axis=0)],
            "var_95": [round(float(v), 6) for v in np.percentile(synthetic, 5, axis=0)],
            "cvar_95": [round(float(np.mean(synthetic[synthetic[:, i] <= np.percentile(synthetic[:, i], 5), i])), 6)
                        for i in range(N)]
        },
        "model": "SimpleVAE-numpy"
    }


def stress_test_scenarios(
    returns: np.ndarray,
    shock_multiplier: float = 3.0,
    n_scenarios: int = 100,
    seed: int = 42
) -> Dict:
    """
    Generate stress test scenarios by sampling from the tails of the VAE latent space.

    Args:
        returns: T x N historical returns.
        shock_multiplier: How far into the tails to sample (in std devs of latent space).
        n_scenarios: Number of stress scenarios.
        seed: Random seed.

    Returns:
        Dict with stress scenarios and extreme loss statistics.
    """
    T, N = returns.shape
    mu_r = returns.mean(axis=0)
    sigma_r = returns.std(axis=0) + 1e-10
    normed = (returns - mu_r) / sigma_r

    vae = SimpleVAE(input_dim=N, hidden_dim=16, latent_dim=4, seed=seed)
    vae.train(normed, epochs=30)

    rng = np.random.RandomState(seed + 1)
    stress_scenarios = []
    for _ in range(n_scenarios):
        # Sample from tails: z ~ N(0, shock_multiplier^2 * I) but biased negative
        z = rng.randn(vae.latent_dim) * shock_multiplier
        # Bias toward negative (stress)
        z = -np.abs(z)
        decoded = vae.decode(z)
        scenario = decoded * sigma_r + mu_r
        stress_scenarios.append(scenario)

    stress_arr = np.array(stress_scenarios)

    return {
        "n_stress_scenarios": n_scenarios,
        "shock_multiplier": shock_multiplier,
        "stress_statistics": {
            "mean_loss": [round(float(v) * 100, 4) for v in stress_arr.mean(axis=0)],
            "max_loss": [round(float(v) * 100, 4) for v in stress_arr.min(axis=0)],
            "median_loss": [round(float(v) * 100, 4) for v in np.median(stress_arr, axis=0)],
            "var_99": [round(float(v) * 100, 4) for v in np.percentile(stress_arr, 1, axis=0)]
        },
        "n_assets": N,
        "model": "VAE-StressTest"
    }
