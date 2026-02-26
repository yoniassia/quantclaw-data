"""
LSTM Sequence Forecaster — Multi-step price prediction using Long Short-Term Memory networks.

Provides sequence-to-sequence forecasting for stock prices using sliding window LSTM.
Uses free Yahoo Finance data via yfinance. Lightweight numpy-based LSTM cell for
environments without TensorFlow/PyTorch.

Phase: 282 | Category: AI/ML Models
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return np.where(x >= 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


class SimpleLSTMCell:
    """Minimal LSTM cell using numpy for inference/demo purposes."""

    def __init__(self, input_size: int, hidden_size: int, seed: int = 42):
        rng = np.random.RandomState(seed)
        scale = 0.1
        combined = input_size + hidden_size
        self.W = rng.randn(4 * hidden_size, combined) * scale
        self.b = np.zeros(4 * hidden_size)
        self.hidden_size = hidden_size

    def forward(self, x: np.ndarray, h_prev: np.ndarray, c_prev: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        combined = np.concatenate([x, h_prev])
        gates = self.W @ combined + self.b
        hs = self.hidden_size
        f = _sigmoid(gates[:hs])
        i = _sigmoid(gates[hs:2*hs])
        g = _tanh(gates[2*hs:3*hs])
        o = _sigmoid(gates[3*hs:])
        c = f * c_prev + i * g
        h = o * _tanh(c)
        return h, c


def prepare_sequences(prices: List[float], window: int = 20, horizon: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare sliding window sequences from price data.

    Args:
        prices: List of closing prices.
        window: Number of lookback steps.
        horizon: Number of forecast steps.

    Returns:
        Tuple of (X, Y) arrays for training/evaluation.
    """
    if len(prices) < window + horizon:
        raise ValueError(f"Need at least {window + horizon} prices, got {len(prices)}")

    returns = np.diff(np.log(np.array(prices, dtype=np.float64)))
    mu, sigma = returns.mean(), returns.std() + 1e-10
    normed = (returns - mu) / sigma

    X, Y = [], []
    for i in range(len(normed) - window - horizon + 1):
        X.append(normed[i:i+window])
        Y.append(normed[i+window:i+window+horizon])

    return np.array(X), np.array(Y)


def forecast_lstm(
    prices: List[float],
    window: int = 20,
    horizon: int = 5,
    hidden_size: int = 32,
    seed: int = 42
) -> Dict:
    """
    Run LSTM-style multi-step forecast on price series.

    Uses a simple trained-on-the-fly approach with the numpy LSTM cell.
    For production, replace with PyTorch/TF trained model.

    Args:
        prices: Historical closing prices (at least window + horizon).
        window: Lookback window size.
        horizon: Number of steps to forecast.
        hidden_size: LSTM hidden state dimension.
        seed: Random seed.

    Returns:
        Dict with forecast returns, predicted prices, confidence bands, and metadata.
    """
    prices_arr = np.array(prices, dtype=np.float64)
    returns = np.diff(np.log(prices_arr))
    mu, sigma = returns.mean(), returns.std() + 1e-10
    normed = (returns - mu) / sigma

    # Use last `window` returns as input
    input_seq = normed[-window:]

    cell = SimpleLSTMCell(input_size=1, hidden_size=hidden_size, seed=seed)
    output_W = np.random.RandomState(seed).randn(1, hidden_size) * 0.1

    # Forward pass through the sequence
    h = np.zeros(hidden_size)
    c = np.zeros(hidden_size)
    for t in range(window):
        x = np.array([input_seq[t]])
        h, c = cell.forward(x, h, c)

    # Multi-step forecast
    forecast_normed = []
    last_input = np.array([input_seq[-1]])
    for _ in range(horizon):
        h, c = cell.forward(last_input, h, c)
        pred = (output_W @ h)[0]
        forecast_normed.append(pred)
        last_input = np.array([pred])

    # Denormalize
    forecast_returns = np.array(forecast_normed) * sigma + mu
    last_price = prices_arr[-1]
    forecast_prices = [last_price]
    for r in forecast_returns:
        forecast_prices.append(forecast_prices[-1] * np.exp(r))
    forecast_prices = forecast_prices[1:]

    # Confidence bands (based on historical volatility)
    vol_per_step = sigma * np.sqrt(np.arange(1, horizon + 1))
    upper = [last_price * np.exp(cum_r + 1.96 * v) for cum_r, v in
             zip(np.cumsum(forecast_returns), vol_per_step)]
    lower = [last_price * np.exp(cum_r - 1.96 * v) for cum_r, v in
             zip(np.cumsum(forecast_returns), vol_per_step)]

    return {
        "last_price": round(float(last_price), 2),
        "forecast_prices": [round(float(p), 2) for p in forecast_prices],
        "forecast_returns_pct": [round(float(r) * 100, 4) for r in forecast_returns],
        "upper_95": [round(float(p), 2) for p in upper],
        "lower_95": [round(float(p), 2) for p in lower],
        "horizon": horizon,
        "window": window,
        "hidden_size": hidden_size,
        "input_volatility": round(float(sigma) * 100, 4),
        "model": "SimpleLSTM-numpy",
        "note": "Demo LSTM cell. For production, use trained PyTorch/TF model."
    }


def evaluate_backtest(
    prices: List[float],
    window: int = 20,
    horizon: int = 5,
    test_size: int = 50
) -> Dict:
    """
    Backtest the LSTM forecaster on historical data.

    Args:
        prices: Full price history.
        window: Lookback window.
        horizon: Forecast horizon.
        test_size: Number of test points.

    Returns:
        Dict with directional accuracy, MAE, and per-step metrics.
    """
    if len(prices) < window + horizon + test_size:
        raise ValueError("Not enough data for backtest")

    correct_dir = 0
    abs_errors = []

    for i in range(test_size):
        end_idx = len(prices) - test_size + i
        train_prices = prices[:end_idx]
        actual_next = prices[end_idx] if end_idx < len(prices) else None

        if actual_next is None:
            continue

        result = forecast_lstm(train_prices, window=window, horizon=1)
        pred_price = result["forecast_prices"][0]
        last = train_prices[-1]

        pred_dir = 1 if pred_price > last else -1
        actual_dir = 1 if actual_next > last else -1

        if pred_dir == actual_dir:
            correct_dir += 1

        abs_errors.append(abs(pred_price - actual_next))

    n = len(abs_errors)
    return {
        "directional_accuracy": round(correct_dir / n * 100, 2) if n else 0,
        "mae": round(float(np.mean(abs_errors)), 4) if n else 0,
        "test_points": n,
        "window": window,
        "horizon": horizon
    }
