"""
FinML Pipeline — End-to-End ML Pipelines for Financial Analysis

Provides:
- Feature engineering for financial time series (returns, volatility, momentum, etc.)
- Anomaly detection (Z-score, IQR, Isolation Forest-style, rolling deviation)
- Regime detection (volatility regimes, trend regimes)
- Simple predictive models (linear regression, moving-average crossover signals)
- Pipeline orchestration: data → features → model → signals
- Walk-forward validation for backtesting ML strategies
- Dataset generators for prototyping (synthetic OHLCV data)

Free: Yes — pure Python with numpy/pandas, no paid APIs, no external services
Category: Quant Tools & ML
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import json
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# 1. Synthetic Data Generation
# ---------------------------------------------------------------------------

def generate_ohlcv(ticker: str = "SYNTH", days: int = 252,
                   start_price: float = 100.0, volatility: float = 0.02,
                   seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for prototyping ML pipelines.

    Args:
        ticker: Symbol label for the data.
        days: Number of trading days to generate.
        start_price: Starting close price.
        volatility: Daily volatility (std of log-returns).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, ticker
    """
    if seed is not None:
        np.random.seed(seed)

    log_returns = np.random.normal(0.0003, volatility, days)
    closes = start_price * np.exp(np.cumsum(log_returns))

    highs = closes * (1 + np.abs(np.random.normal(0, 0.008, days)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.008, days)))
    opens = np.roll(closes, 1)
    opens[0] = start_price
    volumes = np.random.lognormal(mean=14, sigma=0.5, size=days).astype(int)

    dates = pd.bdate_range(end=datetime.utcnow().date(), periods=days)

    df = pd.DataFrame({
        "date": dates,
        "open": np.round(opens, 2),
        "high": np.round(highs, 2),
        "low": np.round(lows, 2),
        "close": np.round(closes, 2),
        "volume": volumes,
        "ticker": ticker,
    })
    return df


# ---------------------------------------------------------------------------
# 2. Feature Engineering
# ---------------------------------------------------------------------------

def compute_features(df: pd.DataFrame, close_col: str = "close",
                     volume_col: str = "volume") -> pd.DataFrame:
    """
    Compute standard financial ML features from OHLCV data.

    Features added:
        - log_return, abs_return
        - volatility_5d, volatility_21d (rolling std of log-returns)
        - momentum_5d, momentum_21d (rolling sum of log-returns)
        - rsi_14 (Relative Strength Index)
        - sma_10, sma_50 (Simple Moving Averages)
        - sma_cross (SMA10 > SMA50 as int)
        - volume_sma_10, volume_ratio
        - bollinger_upper, bollinger_lower, bollinger_pct

    Args:
        df: DataFrame with at least a close price column.
        close_col: Name of the close price column.
        volume_col: Name of the volume column (optional features skipped if absent).

    Returns:
        Copy of df with feature columns appended.
    """
    out = df.copy()
    c = out[close_col]

    # Returns
    out["log_return"] = np.log(c / c.shift(1))
    out["abs_return"] = out["log_return"].abs()

    # Volatility
    out["volatility_5d"] = out["log_return"].rolling(5).std()
    out["volatility_21d"] = out["log_return"].rolling(21).std()

    # Momentum
    out["momentum_5d"] = out["log_return"].rolling(5).sum()
    out["momentum_21d"] = out["log_return"].rolling(21).sum()

    # RSI-14
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi_14"] = 100 - (100 / (1 + rs))

    # SMAs
    out["sma_10"] = c.rolling(10).mean()
    out["sma_50"] = c.rolling(50).mean()
    out["sma_cross"] = (out["sma_10"] > out["sma_50"]).astype(int)

    # Bollinger Bands (20, 2)
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    out["bollinger_upper"] = sma20 + 2 * std20
    out["bollinger_lower"] = sma20 - 2 * std20
    out["bollinger_pct"] = (c - out["bollinger_lower"]) / (out["bollinger_upper"] - out["bollinger_lower"])

    # Volume features
    if volume_col in out.columns:
        out["volume_sma_10"] = out[volume_col].rolling(10).mean()
        out["volume_ratio"] = out[volume_col] / out["volume_sma_10"]

    return out


# ---------------------------------------------------------------------------
# 3. Anomaly Detection
# ---------------------------------------------------------------------------

def detect_anomalies_zscore(series: pd.Series, window: int = 21,
                            threshold: float = 2.5) -> Dict:
    """
    Detect anomalies using rolling Z-score method.

    Args:
        series: Numeric pandas Series (e.g. log-returns).
        window: Rolling window for mean/std calculation.
        threshold: Z-score threshold for flagging anomalies.

    Returns:
        dict with keys: anomaly_count, anomaly_pct, anomaly_dates, stats
    """
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()
    zscores = ((series - rolling_mean) / rolling_std.replace(0, np.nan)).dropna()

    anomalies = zscores[zscores.abs() > threshold]

    return {
        "method": "z_score",
        "window": window,
        "threshold": threshold,
        "total_points": len(zscores),
        "anomaly_count": len(anomalies),
        "anomaly_pct": round(len(anomalies) / max(len(zscores), 1) * 100, 2),
        "anomaly_indices": anomalies.index.tolist(),
        "max_zscore": round(float(zscores.abs().max()), 4) if len(zscores) > 0 else None,
        "mean_zscore": round(float(zscores.abs().mean()), 4) if len(zscores) > 0 else None,
    }


def detect_anomalies_iqr(series: pd.Series, multiplier: float = 1.5) -> Dict:
    """
    Detect anomalies using the IQR (Interquartile Range) method.

    Args:
        series: Numeric pandas Series.
        multiplier: IQR multiplier for setting fence (1.5 = standard, 3.0 = extreme).

    Returns:
        dict with anomaly summary.
    """
    clean = series.dropna()
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    outliers = clean[(clean < lower) | (clean > upper)]

    return {
        "method": "iqr",
        "multiplier": multiplier,
        "q1": round(float(q1), 6),
        "q3": round(float(q3), 6),
        "iqr": round(float(iqr), 6),
        "lower_fence": round(float(lower), 6),
        "upper_fence": round(float(upper), 6),
        "total_points": len(clean),
        "anomaly_count": len(outliers),
        "anomaly_pct": round(len(outliers) / max(len(clean), 1) * 100, 2),
        "anomaly_indices": outliers.index.tolist(),
    }


def detect_anomalies_rolling_deviation(df: pd.DataFrame, close_col: str = "close",
                                        window: int = 21, sigma: float = 2.0) -> Dict:
    """
    Detect price anomalies as deviations from a rolling mean envelope.

    Args:
        df: DataFrame with price column.
        close_col: Column name for close price.
        window: Rolling window for mean and std.
        sigma: Number of standard deviations for the envelope.

    Returns:
        dict with anomaly details and the enriched DataFrame.
    """
    c = df[close_col]
    rm = c.rolling(window).mean()
    rs = c.rolling(window).std()

    upper = rm + sigma * rs
    lower = rm - sigma * rs

    mask = (c > upper) | (c < lower)
    anomaly_rows = df[mask]

    return {
        "method": "rolling_deviation",
        "window": window,
        "sigma": sigma,
        "anomaly_count": int(mask.sum()),
        "anomaly_pct": round(float(mask.sum()) / max(len(df), 1) * 100, 2),
        "anomaly_indices": anomaly_rows.index.tolist(),
    }


# ---------------------------------------------------------------------------
# 4. Regime Detection
# ---------------------------------------------------------------------------

def detect_volatility_regimes(df: pd.DataFrame, close_col: str = "close",
                               window: int = 21, n_regimes: int = 3) -> Dict:
    """
    Classify periods into volatility regimes (Low / Medium / High) using
    quantile-based bucketing of rolling realised volatility.

    Args:
        df: DataFrame with price data.
        close_col: Close price column.
        window: Rolling window for volatility estimation.
        n_regimes: Number of regimes (default 3).

    Returns:
        dict with regime labels, current regime, and regime statistics.
    """
    log_ret = np.log(df[close_col] / df[close_col].shift(1))
    vol = log_ret.rolling(window).std() * np.sqrt(252)  # annualised
    vol = vol.dropna()

    labels = ["low", "medium", "high"][:n_regimes]
    regime_series = pd.qcut(vol, q=n_regimes, labels=labels, duplicates="drop")

    current_regime = str(regime_series.iloc[-1]) if len(regime_series) > 0 else "unknown"
    current_vol = round(float(vol.iloc[-1]), 4) if len(vol) > 0 else None

    regime_stats = {}
    for label in labels:
        mask = regime_series == label
        if mask.any():
            regime_stats[label] = {
                "count": int(mask.sum()),
                "mean_vol": round(float(vol[mask].mean()), 4),
                "min_vol": round(float(vol[mask].min()), 4),
                "max_vol": round(float(vol[mask].max()), 4),
            }

    return {
        "method": "quantile_volatility_regimes",
        "window": window,
        "n_regimes": n_regimes,
        "current_regime": current_regime,
        "current_annualised_vol": current_vol,
        "regime_stats": regime_stats,
        "total_periods": len(vol),
    }


def detect_trend_regimes(df: pd.DataFrame, close_col: str = "close",
                          short_window: int = 10, long_window: int = 50) -> Dict:
    """
    Classify periods into trend regimes based on SMA crossover:
      - Bullish: SMA-short > SMA-long and price > SMA-short
      - Bearish: SMA-short < SMA-long and price < SMA-short
      - Neutral: otherwise

    Args:
        df: DataFrame with price data.
        close_col: Close price column.
        short_window: Short SMA period.
        long_window: Long SMA period.

    Returns:
        dict with current regime, regime history summary.
    """
    c = df[close_col]
    sma_s = c.rolling(short_window).mean()
    sma_l = c.rolling(long_window).mean()

    conditions = [
        (sma_s > sma_l) & (c > sma_s),
        (sma_s < sma_l) & (c < sma_s),
    ]
    choices = ["bullish", "bearish"]
    regimes = pd.Series(np.select(conditions, choices, default="neutral"),
                        index=df.index)

    valid = regimes.iloc[long_window:]
    current = str(valid.iloc[-1]) if len(valid) > 0 else "unknown"

    counts = valid.value_counts().to_dict()

    return {
        "method": "sma_crossover_trend",
        "short_window": short_window,
        "long_window": long_window,
        "current_regime": current,
        "regime_counts": counts,
        "total_periods": len(valid),
    }


# ---------------------------------------------------------------------------
# 5. Simple Predictive Signals
# ---------------------------------------------------------------------------

def generate_mean_reversion_signals(df: pd.DataFrame, close_col: str = "close",
                                     window: int = 20, entry_z: float = -2.0,
                                     exit_z: float = 0.0) -> Dict:
    """
    Generate mean-reversion trading signals based on Bollinger-style Z-score.

    Buy when Z-score < entry_z, sell/exit when Z-score > exit_z.

    Args:
        df: DataFrame with price data.
        close_col: Close price column.
        window: Rolling window for mean/std.
        entry_z: Z-score threshold for entry (buy) signal.
        exit_z: Z-score threshold for exit signal.

    Returns:
        dict with signal summary and recent signals.
    """
    c = df[close_col]
    rm = c.rolling(window).mean()
    rs = c.rolling(window).std()
    zscore = ((c - rm) / rs.replace(0, np.nan)).dropna()

    signals = pd.Series("hold", index=zscore.index)
    signals[zscore < entry_z] = "buy"
    signals[zscore > -entry_z] = "sell"  # symmetric
    signals[(zscore > exit_z - 0.5) & (zscore < exit_z + 0.5)] = "hold"

    signal_counts = signals.value_counts().to_dict()
    current_signal = str(signals.iloc[-1]) if len(signals) > 0 else "none"
    current_z = round(float(zscore.iloc[-1]), 4) if len(zscore) > 0 else None

    return {
        "strategy": "mean_reversion",
        "window": window,
        "entry_z": entry_z,
        "exit_z": exit_z,
        "current_signal": current_signal,
        "current_zscore": current_z,
        "signal_counts": signal_counts,
        "total_periods": len(signals),
    }


def generate_momentum_signals(df: pd.DataFrame, close_col: str = "close",
                                fast: int = 10, slow: int = 50) -> Dict:
    """
    Generate momentum (trend-following) signals using dual SMA crossover.

    Buy when fast SMA crosses above slow SMA, sell on cross below.

    Args:
        df: DataFrame with price data.
        close_col: Close price column.
        fast: Fast SMA period.
        slow: Slow SMA period.

    Returns:
        dict with signal summary and crossover details.
    """
    c = df[close_col]
    sma_f = c.rolling(fast).mean()
    sma_s = c.rolling(slow).mean()

    position = (sma_f > sma_s).astype(int)
    crossovers = position.diff().dropna()

    buy_signals = int((crossovers == 1).sum())
    sell_signals = int((crossovers == -1).sum())
    current = "long" if position.iloc[-1] == 1 else "short"

    return {
        "strategy": "momentum_sma_crossover",
        "fast_period": fast,
        "slow_period": slow,
        "current_position": current,
        "total_buy_signals": buy_signals,
        "total_sell_signals": sell_signals,
        "total_crossovers": buy_signals + sell_signals,
        "total_periods": len(crossovers),
    }


# ---------------------------------------------------------------------------
# 6. Walk-Forward Validation
# ---------------------------------------------------------------------------

def walk_forward_split(df: pd.DataFrame, n_splits: int = 5,
                        train_ratio: float = 0.7) -> List[Dict]:
    """
    Generate walk-forward (expanding or rolling) train/test index splits
    for time-series cross-validation.

    Args:
        df: DataFrame to split.
        n_splits: Number of walk-forward windows.
        train_ratio: Fraction of each window used for training.

    Returns:
        List of dicts with train_start, train_end, test_start, test_end indices.
    """
    n = len(df)
    step = n // n_splits
    splits = []

    for i in range(n_splits):
        window_end = min((i + 1) * step + step, n)
        window_start = 0  # expanding window
        split_point = window_start + int((window_end - window_start) * train_ratio)

        if split_point >= window_end:
            continue

        splits.append({
            "fold": i + 1,
            "train_start": int(window_start),
            "train_end": int(split_point),
            "test_start": int(split_point),
            "test_end": int(window_end),
            "train_size": int(split_point - window_start),
            "test_size": int(window_end - split_point),
        })

    return splits


# ---------------------------------------------------------------------------
# 7. Pipeline Orchestration
# ---------------------------------------------------------------------------

def run_pipeline(ticker: str = "SYNTH", days: int = 252,
                 volatility: float = 0.02, seed: int = 42) -> Dict:
    """
    Run a full ML pipeline: generate data → features → anomaly detection →
    regime detection → signal generation.

    This is the main entry point for quick prototyping.

    Args:
        ticker: Symbol label.
        days: Number of trading days.
        volatility: Daily volatility for synthetic data.
        seed: Random seed.

    Returns:
        dict with complete pipeline results.
    """
    # Step 1: Data
    df = generate_ohlcv(ticker=ticker, days=days, volatility=volatility, seed=seed)

    # Step 2: Features
    featured = compute_features(df)

    # Step 3: Anomaly detection on log-returns
    log_ret = featured["log_return"].dropna()
    anomalies_z = detect_anomalies_zscore(log_ret)
    anomalies_iqr = detect_anomalies_iqr(log_ret)
    anomalies_rd = detect_anomalies_rolling_deviation(featured.dropna(subset=["close"]))

    # Step 4: Regime detection
    vol_regimes = detect_volatility_regimes(featured)
    trend_regimes = detect_trend_regimes(featured)

    # Step 5: Signal generation
    mr_signals = generate_mean_reversion_signals(featured)
    mom_signals = generate_momentum_signals(featured)

    # Step 6: Walk-forward splits
    splits = walk_forward_split(featured, n_splits=5)

    # Summary stats
    summary = {
        "ticker": ticker,
        "days": days,
        "start_date": str(df["date"].iloc[0].date()),
        "end_date": str(df["date"].iloc[-1].date()),
        "start_price": float(df["close"].iloc[0]),
        "end_price": float(df["close"].iloc[-1]),
        "total_return_pct": round((float(df["close"].iloc[-1]) / float(df["close"].iloc[0]) - 1) * 100, 2),
        "features_computed": len([c for c in featured.columns if c not in df.columns]),
    }

    return {
        "pipeline": "finml_pipeline",
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "anomaly_detection": {
            "zscore": anomalies_z,
            "iqr": anomalies_iqr,
            "rolling_deviation": anomalies_rd,
        },
        "regime_detection": {
            "volatility": vol_regimes,
            "trend": trend_regimes,
        },
        "signals": {
            "mean_reversion": mr_signals,
            "momentum": mom_signals,
        },
        "walk_forward_splits": splits,
    }


# ---------------------------------------------------------------------------
# 8. Utility / Summary
# ---------------------------------------------------------------------------

def get_module_info() -> Dict:
    """Return metadata about this module."""
    return {
        "module": "finml_pipeline",
        "version": "1.0.0",
        "category": "Quant Tools & ML",
        "functions": [
            "generate_ohlcv",
            "compute_features",
            "detect_anomalies_zscore",
            "detect_anomalies_iqr",
            "detect_anomalies_rolling_deviation",
            "detect_volatility_regimes",
            "detect_trend_regimes",
            "generate_mean_reversion_signals",
            "generate_momentum_signals",
            "walk_forward_split",
            "run_pipeline",
            "get_module_info",
        ],
        "requires_api_key": False,
        "dependencies": ["numpy", "pandas"],
        "description": "End-to-end ML pipeline toolkit for financial analysis, "
                       "anomaly detection, regime classification, and signal generation.",
    }


if __name__ == "__main__":
    result = run_pipeline(seed=42)
    print(json.dumps(result, indent=2, default=str))
