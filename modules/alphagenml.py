#!/usr/bin/env python3
"""
AlphaGen ML — QuantClaw Data Module
====================================
Wrapper for AlphaGen ML, an open-source ML framework (2025) for quantitative
trading alpha signal generation using deep learning models.

Since the alphagenml pip package may not be available, this module provides:
- Standalone alpha signal generation using scikit-learn / numpy
- Feature engineering pipelines for financial time series
- Backtesting integration for ML-generated signals
- Sample data generation for testing

Source: https://alphagenml.com
Category: Quant Tools & ML
Free tier: Fully open-source
Generated: 2026-03-07 (NightBuilder)
"""

import json
import os
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Try importing the real library; fall back to built-in implementations
_HAS_ALPHAGENML = False
try:
    import alphagenml as _aml
    _HAS_ALPHAGENML = True
except ImportError:
    _aml = None

# Try optional ML deps
_HAS_SKLEARN = False
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, mean_squared_error
    _HAS_SKLEARN = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Sample Data Generation
# ---------------------------------------------------------------------------

def generate_sample_data(
    tickers: Optional[List[str]] = None,
    days: int = 252,
    start_date: str = "2025-01-02",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic OHLCV stock data for testing.

    Args:
        tickers: List of ticker symbols. Defaults to ['AAPL','MSFT','GOOG','AMZN','TSLA'].
        days: Number of trading days to generate.
        start_date: Start date string (YYYY-MM-DD).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, ticker, open, high, low, close, volume, returns
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]

    rng = np.random.RandomState(seed)
    records = []
    dates = pd.bdate_range(start=start_date, periods=days)

    for ticker in tickers:
        base_price = rng.uniform(50, 500)
        price = base_price
        for d in dates:
            daily_ret = rng.normal(0.0004, 0.018)
            price *= (1 + daily_ret)
            o = price * (1 + rng.normal(0, 0.003))
            h = price * (1 + abs(rng.normal(0, 0.008)))
            l = price * (1 - abs(rng.normal(0, 0.008)))
            c = price
            v = int(rng.lognormal(17, 0.8))
            records.append({
                "date": d,
                "ticker": ticker,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "volume": v,
                "returns": round(daily_ret, 6),
            })

    return pd.DataFrame(records)


def save_sample_csv(path: str = "sample_stocks.csv", **kwargs) -> str:
    """Generate sample data and save to CSV. Returns the file path."""
    df = generate_sample_data(**kwargs)
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Feature Engineering
# ---------------------------------------------------------------------------

def compute_alpha_features(
    df: pd.DataFrame,
    price_col: str = "close",
    volume_col: str = "volume",
    group_col: Optional[str] = "ticker",
) -> pd.DataFrame:
    """
    Compute a rich set of alpha features from OHLCV data.

    Features generated per group:
        - returns_1d .. returns_20d: multi-horizon returns
        - volatility_5d, volatility_20d: rolling std of returns
        - momentum_5d, momentum_20d: price momentum
        - rsi_14: Relative Strength Index
        - volume_ratio_5d: volume vs 5-day avg
        - mean_reversion_20d: distance from 20d moving average
        - price_range: (high-low)/close
        - gap: open vs prior close

    Args:
        df: DataFrame with at least price_col and volume_col.
        price_col: Column name for close price.
        volume_col: Column name for volume.
        group_col: Column to group by (e.g. 'ticker'). None for single-asset.

    Returns:
        DataFrame with original columns plus alpha features.
    """
    out = df.copy()

    def _add_features(g: pd.DataFrame) -> pd.DataFrame:
        c = g[price_col].astype(float)
        v = g[volume_col].astype(float) if volume_col in g.columns else pd.Series(0, index=g.index)
        ret = c.pct_change()

        for n in [1, 2, 3, 5, 10, 20]:
            g[f"returns_{n}d"] = c.pct_change(n)

        g["volatility_5d"] = ret.rolling(5).std()
        g["volatility_20d"] = ret.rolling(20).std()

        for n in [5, 20]:
            g[f"momentum_{n}d"] = c / c.shift(n) - 1

        # RSI-14
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        g["rsi_14"] = 100 - (100 / (1 + rs))

        # Volume ratio
        g["volume_ratio_5d"] = v / v.rolling(5).mean().replace(0, np.nan)

        # Mean reversion
        ma20 = c.rolling(20).mean()
        g["mean_reversion_20d"] = (c - ma20) / ma20.replace(0, np.nan)

        # Price range
        if "high" in g.columns and "low" in g.columns:
            g["price_range"] = (g["high"].astype(float) - g["low"].astype(float)) / c.replace(0, np.nan)

        # Gap
        if "open" in g.columns:
            g["gap"] = g["open"].astype(float) / c.shift(1).replace(0, np.nan) - 1

        return g

    if group_col and group_col in out.columns:
        parts = []
        for _, g in out.groupby(group_col):
            parts.append(_add_features(g))
        out = pd.concat(parts)
    else:
        out = _add_features(out)

    return out


# ---------------------------------------------------------------------------
# Alpha Signal Generation (ML-based)
# ---------------------------------------------------------------------------

def generate_alpha_signals(
    df: pd.DataFrame,
    target_horizon: int = 5,
    price_col: str = "close",
    group_col: Optional[str] = "ticker",
    method: str = "gradient_boosting",
    train_ratio: float = 0.7,
) -> pd.DataFrame:
    """
    Train an ML model on alpha features and generate forward-looking signals.

    Args:
        df: OHLCV DataFrame (will compute features if missing).
        target_horizon: Forward return horizon in days for the target variable.
        price_col: Close price column.
        group_col: Grouping column.
        method: 'gradient_boosting' or 'random_forest'.
        train_ratio: Fraction of data used for training.

    Returns:
        DataFrame with 'alpha_signal' (predicted forward return) and
        'alpha_rank' (cross-sectional percentile rank) columns appended.
    """
    if not _HAS_SKLEARN:
        raise ImportError("scikit-learn is required for ML alpha generation. pip install scikit-learn")

    # Ensure features exist
    if "rsi_14" not in df.columns:
        df = compute_alpha_features(df, price_col=price_col, group_col=group_col)

    out = df.copy()

    # Build target: forward N-day return
    def _add_target(g):
        g["_target"] = g[price_col].astype(float).pct_change(target_horizon).shift(-target_horizon)
        return g

    if group_col and group_col in out.columns:
        parts = []
        for _, g in out.groupby(group_col):
            parts.append(_add_target(g))
        out = pd.concat(parts)
    else:
        out = _add_target(out)

    feature_cols = [c for c in out.columns if c.startswith(("returns_", "volatility_", "momentum_",
                                                             "rsi_", "volume_ratio_", "mean_reversion_",
                                                             "price_range", "gap"))]
    if not feature_cols:
        raise ValueError("No alpha features found. Run compute_alpha_features first.")

    # Drop rows with NaN in features or target
    mask = out[feature_cols + ["_target"]].notna().all(axis=1)
    valid = out[mask].copy()

    if len(valid) < 50:
        warnings.warn(f"Only {len(valid)} valid rows — results may be unreliable.")

    split_idx = int(len(valid) * train_ratio)
    train = valid.iloc[:split_idx]
    test = valid.iloc[split_idx:]

    scaler = StandardScaler()
    X_train = scaler.fit_transform(train[feature_cols])
    y_train = train["_target"].values
    X_test = scaler.transform(test[feature_cols])

    if method == "random_forest":
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        y_train_cls = (y_train > 0).astype(int)
        model.fit(X_train, y_train_cls)
        preds = model.predict_proba(X_test)[:, 1]
    else:
        model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

    # Write predictions back
    out["alpha_signal"] = np.nan
    out.loc[test.index, "alpha_signal"] = preds

    # Cross-sectional rank (percentile) per date
    if group_col and group_col in out.columns and "date" in out.columns:
        out["alpha_rank"] = out.groupby("date")["alpha_signal"].rank(pct=True)
    else:
        out["alpha_rank"] = out["alpha_signal"].rank(pct=True)

    out.drop(columns=["_target"], inplace=True, errors="ignore")

    # Store model metadata
    out.attrs["model_method"] = method
    out.attrs["feature_cols"] = feature_cols
    out.attrs["train_size"] = len(train)
    out.attrs["test_size"] = len(test)

    return out


def get_feature_importance(
    df: pd.DataFrame,
    target_horizon: int = 5,
    price_col: str = "close",
    group_col: Optional[str] = "ticker",
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Train a model and return feature importance rankings.

    Returns:
        DataFrame with columns: feature, importance (sorted descending).
    """
    if not _HAS_SKLEARN:
        raise ImportError("scikit-learn required")

    if "rsi_14" not in df.columns:
        df = compute_alpha_features(df, price_col=price_col, group_col=group_col)

    feature_cols = [c for c in df.columns if c.startswith(("returns_", "volatility_", "momentum_",
                                                            "rsi_", "volume_ratio_", "mean_reversion_",
                                                            "price_range", "gap"))]

    def _add_target(g):
        g["_target"] = g[price_col].astype(float).pct_change(target_horizon).shift(-target_horizon)
        return g

    if group_col and group_col in df.columns:
        parts = []
        for _, g in df.groupby(group_col):
            parts.append(_add_target(g))
        df = pd.concat(parts)
    else:
        df = _add_target(df)

    mask = df[feature_cols + ["_target"]].notna().all(axis=1)
    valid = df[mask]

    model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
    model.fit(valid[feature_cols], valid["_target"])

    imp = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)

    return imp


# ---------------------------------------------------------------------------
# Signal Evaluation / Backtesting
# ---------------------------------------------------------------------------

def backtest_signals(
    df: pd.DataFrame,
    signal_col: str = "alpha_signal",
    price_col: str = "close",
    group_col: Optional[str] = "ticker",
    long_threshold: float = 0.6,
    short_threshold: float = 0.4,
    holding_period: int = 5,
) -> Dict[str, Any]:
    """
    Simple long/short backtest of alpha signals.

    Args:
        df: DataFrame with alpha_signal and price data.
        signal_col: Column with signal values.
        price_col: Close price column.
        group_col: Grouping column.
        long_threshold: Signal percentile above which to go long.
        short_threshold: Signal percentile below which to go short.
        holding_period: Days to hold position.

    Returns:
        Dictionary with backtest metrics: total_return, sharpe, win_rate, num_trades, etc.
    """
    sig = df.dropna(subset=[signal_col]).copy()
    if len(sig) == 0:
        return {"error": "No valid signals to backtest"}

    # Use rank if available, else raw signal
    rank_col = "alpha_rank" if "alpha_rank" in sig.columns else signal_col

    # Forward returns for evaluation
    def _fwd(g):
        g["_fwd_ret"] = g[price_col].astype(float).pct_change(holding_period).shift(-holding_period)
        return g

    if group_col and group_col in sig.columns:
        parts = []
        for _, g in sig.groupby(group_col):
            parts.append(_fwd(g))
        sig = pd.concat(parts)
    else:
        sig = _fwd(sig)

    valid = sig.dropna(subset=["_fwd_ret", rank_col])

    longs = valid[valid[rank_col] >= long_threshold]["_fwd_ret"]
    shorts = valid[valid[rank_col] <= short_threshold]["_fwd_ret"]

    long_ret = longs.mean() if len(longs) > 0 else 0
    short_ret = -shorts.mean() if len(shorts) > 0 else 0
    ls_ret = (long_ret + short_ret) / 2

    all_trades = pd.concat([longs, -shorts]) if len(shorts) > 0 else longs
    win_rate = (all_trades > 0).mean() if len(all_trades) > 0 else 0
    sharpe = (all_trades.mean() / all_trades.std() * np.sqrt(252 / holding_period)) if all_trades.std() > 0 else 0

    return {
        "total_return_long": round(float(long_ret), 6),
        "total_return_short": round(float(short_ret), 6),
        "total_return_ls": round(float(ls_ret), 6),
        "sharpe_ratio": round(float(sharpe), 4),
        "win_rate": round(float(win_rate), 4),
        "num_trades_long": int(len(longs)),
        "num_trades_short": int(len(shorts)),
        "holding_period_days": holding_period,
    }


# ---------------------------------------------------------------------------
# Portfolio Construction from Signals
# ---------------------------------------------------------------------------

def signals_to_weights(
    df: pd.DataFrame,
    date: Optional[str] = None,
    signal_col: str = "alpha_signal",
    group_col: str = "ticker",
    top_n: int = 5,
    method: str = "equal_weight",
) -> Dict[str, float]:
    """
    Convert alpha signals to portfolio weights for a given date.

    Args:
        df: DataFrame with alpha signals.
        date: Target date (uses latest available if None).
        signal_col: Signal column.
        group_col: Ticker/asset column.
        top_n: Number of top assets to include.
        method: 'equal_weight' or 'signal_weight' (proportional to signal).

    Returns:
        Dict mapping ticker -> weight (sums to 1.0).
    """
    sig = df.dropna(subset=[signal_col])

    if date is not None:
        if "date" in sig.columns:
            sig = sig[sig["date"] == pd.Timestamp(date)]
    elif "date" in sig.columns:
        sig = sig[sig["date"] == sig["date"].max()]

    if len(sig) == 0:
        return {}

    ranked = sig.nlargest(top_n, signal_col)

    if method == "signal_weight":
        total = ranked[signal_col].sum()
        if total <= 0:
            return {r[group_col]: round(1.0 / len(ranked), 4) for _, r in ranked.iterrows()}
        return {r[group_col]: round(float(r[signal_col] / total), 4) for _, r in ranked.iterrows()}
    else:
        w = round(1.0 / len(ranked), 4)
        return {r[group_col]: w for _, r in ranked.iterrows()}


# ---------------------------------------------------------------------------
# Convenience / Info
# ---------------------------------------------------------------------------

def module_info() -> Dict[str, Any]:
    """Return module metadata."""
    return {
        "module": "alphagenml",
        "version": "1.0.0",
        "source": "https://alphagenml.com",
        "category": "Quant Tools & ML",
        "has_native_lib": _HAS_ALPHAGENML,
        "has_sklearn": _HAS_SKLEARN,
        "functions": [
            "generate_sample_data",
            "save_sample_csv",
            "compute_alpha_features",
            "generate_alpha_signals",
            "get_feature_importance",
            "backtest_signals",
            "signals_to_weights",
            "module_info",
        ],
        "description": "ML-powered alpha signal generation for quantitative trading",
    }


if __name__ == "__main__":
    print(json.dumps(module_info(), indent=2))

    # Quick demo
    print("\n--- Generating sample data ---")
    df = generate_sample_data(days=100)
    print(f"Shape: {df.shape}, Tickers: {df['ticker'].nunique()}")

    print("\n--- Computing features ---")
    df = compute_alpha_features(df)
    print(f"Features added, shape: {df.shape}")

    if _HAS_SKLEARN:
        print("\n--- Generating alpha signals ---")
        df = generate_alpha_signals(df)
        print(f"Signals generated, non-null: {df['alpha_signal'].notna().sum()}")

        print("\n--- Backtesting ---")
        bt = backtest_signals(df)
        print(json.dumps(bt, indent=2))
