#!/usr/bin/env python3
"""
NeuralQuant Toolkit — ML/Neural Network Tools for Quantitative Trading

Provides machine learning utilities for quant strategies:
- Feature engineering from OHLCV price data
- Time-series train/test splitting with proper look-ahead prevention
- Quick ML model training (Random Forest, Gradient Boosting) for price direction
- Hyperparameter grid search with walk-forward validation
- Signal quality metrics (Sharpe, accuracy, profit factor)
- Pre-built feature sets for common strategies

No paid API keys required. Uses sklearn + numpy + pandas.
Source concept: https://neuralquant.io/toolkit
Category: Quant Tools & ML
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import TimeSeriesSplit


# ─────────────────────────────────────────────
# 1. DATA FETCHING
# ─────────────────────────────────────────────

def fetch_ohlcv(symbol: str, period: str = "2y", interval: str = "1d") -> Dict:
    """
    Fetch OHLCV price data for a symbol via yfinance.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL', 'SPY', 'BTC-USD')
        period: Data period ('1y', '2y', '5y', 'max')
        interval: Bar interval ('1d', '1wk', '1mo')

    Returns:
        Dict with 'data' (list of OHLCV dicts), 'symbol', 'rows', 'period'
    """
    if not HAS_YF:
        return {"error": "yfinance not installed. pip install yfinance"}

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return {"error": f"No data found for {symbol}", "symbol": symbol}

        records = []
        for idx, row in df.iterrows():
            records.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            })

        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "rows": len(records),
            "start_date": records[0]["date"],
            "end_date": records[-1]["date"],
            "data": records,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_features(ohlcv_data: List[Dict], lookback_windows: Optional[List[int]] = None) -> Dict:
    """
    Generate ML features from OHLCV data for quant models.

    Creates: returns, volatility, momentum, mean-reversion, volume features
    across multiple lookback windows.

    Args:
        ohlcv_data: List of dicts with date/open/high/low/close/volume
        lookback_windows: List of lookback periods (default [5, 10, 20, 50])

    Returns:
        Dict with 'features' (list of feature dicts), 'feature_names', 'rows'
    """
    if lookback_windows is None:
        lookback_windows = [5, 10, 20, 50]

    df = pd.DataFrame(ohlcv_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Price returns
    df["return_1d"] = df["close"].pct_change()

    for w in lookback_windows:
        # Returns over window
        df[f"return_{w}d"] = df["close"].pct_change(w)
        # Volatility (rolling std of daily returns)
        df[f"volatility_{w}d"] = df["return_1d"].rolling(w).std()
        # Momentum (price vs SMA)
        sma = df["close"].rolling(w).mean()
        df[f"momentum_{w}d"] = (df["close"] - sma) / sma
        # RSI-style feature
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(w).mean()
        loss = (-delta.clip(upper=0)).rolling(w).mean()
        rs = gain / loss.replace(0, np.nan)
        df[f"rsi_{w}d"] = 100 - (100 / (1 + rs))
        # Volume ratio
        df[f"volume_ratio_{w}d"] = df["volume"] / df["volume"].rolling(w).mean()

    # Additional features
    df["high_low_range"] = (df["high"] - df["low"]) / df["close"]
    df["close_open_range"] = (df["close"] - df["open"]) / df["open"]
    df["gap"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)

    # Drop NaN rows (from rolling calculations)
    max_window = max(lookback_windows)
    df_clean = df.iloc[max_window + 1:].copy()

    feature_cols = [c for c in df_clean.columns if c not in ["date", "open", "high", "low", "close", "volume"]]

    records = []
    for _, row in df_clean.iterrows():
        rec = {"date": row["date"].strftime("%Y-%m-%d")}
        for col in feature_cols:
            val = row[col]
            rec[col] = round(float(val), 6) if pd.notna(val) else None
        records.append(rec)

    return {
        "feature_names": feature_cols,
        "feature_count": len(feature_cols),
        "rows": len(records),
        "lookback_windows": lookback_windows,
        "features": records,
    }


def get_feature_set(symbol: str, period: str = "2y", strategy: str = "momentum") -> Dict:
    """
    Get a pre-built feature set for a common strategy type.

    Args:
        symbol: Ticker symbol
        period: Data period
        strategy: One of 'momentum', 'mean_reversion', 'volatility', 'all'

    Returns:
        Dict with features, target labels, and metadata
    """
    ohlcv = fetch_ohlcv(symbol, period=period)
    if "error" in ohlcv:
        return ohlcv

    strategy_windows = {
        "momentum": [5, 10, 20, 50],
        "mean_reversion": [3, 5, 10, 20],
        "volatility": [5, 10, 20, 60],
        "all": [3, 5, 10, 20, 50],
    }

    windows = strategy_windows.get(strategy, strategy_windows["all"])
    features = engineer_features(ohlcv["data"], lookback_windows=windows)

    # Add target: next-day return direction (1 = up, 0 = down)
    df = pd.DataFrame(ohlcv["data"])
    df["next_return"] = df["close"].pct_change().shift(-1)
    df["target"] = (df["next_return"] > 0).astype(int)
    targets = df["target"].iloc[max(windows) + 1: -1].tolist()

    # Trim features to match targets
    feat_list = features["features"][:len(targets)]

    return {
        "symbol": symbol,
        "strategy": strategy,
        "feature_names": features["feature_names"],
        "feature_count": features["feature_count"],
        "rows": len(feat_list),
        "features": feat_list,
        "targets": targets,
    }


# ─────────────────────────────────────────────
# 3. MODEL TRAINING
# ─────────────────────────────────────────────

def train_direction_model(
    symbol: str,
    period: str = "2y",
    model_type: str = "random_forest",
    test_size: float = 0.2,
    strategy: str = "momentum",
) -> Dict:
    """
    Train an ML model to predict next-day price direction.

    Uses walk-forward split (no look-ahead bias).

    Args:
        symbol: Ticker symbol
        period: Training data period
        model_type: 'random_forest' or 'gradient_boosting'
        test_size: Fraction of data for testing (from the end)
        strategy: Feature strategy type

    Returns:
        Dict with accuracy, precision, recall, f1, feature importances, predictions
    """
    dataset = get_feature_set(symbol, period=period, strategy=strategy)
    if "error" in dataset:
        return dataset

    feat_names = dataset["feature_names"]
    feat_data = dataset["features"]
    targets = dataset["targets"]

    # Build feature matrix
    X = []
    valid_indices = []
    for i, rec in enumerate(feat_data):
        row = []
        valid = True
        for col in feat_names:
            val = rec.get(col)
            if val is None:
                valid = False
                break
            row.append(val)
        if valid:
            X.append(row)
            valid_indices.append(i)

    y = [targets[i] for i in valid_indices]
    X = np.array(X)
    y = np.array(y)

    if len(X) < 50:
        return {"error": "Insufficient data points", "rows": len(X)}

    # Walk-forward split
    split_idx = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Train
    if model_type == "gradient_boosting":
        model = GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42
        )
    else:
        model = RandomForestClassifier(
            n_estimators=200, max_depth=5, random_state=42, n_jobs=-1
        )

    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)

    # Feature importances
    importances = model.feature_importances_
    feat_imp = sorted(
        zip(feat_names, importances.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    # Dates for test period
    test_dates = [feat_data[valid_indices[split_idx + i]]["date"] for i in range(len(y_test))]

    return {
        "symbol": symbol,
        "model_type": model_type,
        "strategy": strategy,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_start": test_dates[0] if test_dates else None,
        "test_end": test_dates[-1] if test_dates else None,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "baseline_accuracy": round(float(max(y_test.mean(), 1 - y_test.mean())), 4),
        "top_features": [{"feature": f, "importance": round(imp, 4)} for f, imp in feat_imp[:10]],
        "predictions_sample": [
            {"date": test_dates[i], "predicted": int(y_pred[i]), "actual": int(y_test[i])}
            for i in range(min(10, len(y_test)))
        ],
    }


# ─────────────────────────────────────────────
# 4. WALK-FORWARD VALIDATION
# ─────────────────────────────────────────────

def walk_forward_validate(
    symbol: str,
    period: str = "5y",
    n_splits: int = 5,
    model_type: str = "random_forest",
    strategy: str = "momentum",
) -> Dict:
    """
    Walk-forward cross-validation for time series ML models.

    Prevents look-ahead bias by always training on past, testing on future.

    Args:
        symbol: Ticker symbol
        period: Total data period
        n_splits: Number of walk-forward splits
        model_type: 'random_forest' or 'gradient_boosting'
        strategy: Feature strategy

    Returns:
        Dict with per-fold metrics, average accuracy, and consistency score
    """
    dataset = get_feature_set(symbol, period=period, strategy=strategy)
    if "error" in dataset:
        return dataset

    feat_names = dataset["feature_names"]
    feat_data = dataset["features"]
    targets = dataset["targets"]

    X, valid_idx = [], []
    for i, rec in enumerate(feat_data):
        row = []
        valid = True
        for col in feat_names:
            val = rec.get(col)
            if val is None:
                valid = False
                break
            row.append(val)
        if valid:
            X.append(row)
            valid_idx.append(i)

    y = np.array([targets[i] for i in valid_idx])
    X = np.array(X)

    if len(X) < 100:
        return {"error": "Need at least 100 samples for walk-forward", "rows": len(X)}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_results = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        if model_type == "gradient_boosting":
            model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
        else:
            model = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42, n_jobs=-1)

        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)

        acc = float(accuracy_score(y_test, y_pred))
        fold_results.append({
            "fold": fold + 1,
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "accuracy": round(acc, 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        })

    accuracies = [f["accuracy"] for f in fold_results]
    avg_acc = np.mean(accuracies)
    std_acc = np.std(accuracies)

    return {
        "symbol": symbol,
        "model_type": model_type,
        "strategy": strategy,
        "n_splits": n_splits,
        "total_samples": len(X),
        "folds": fold_results,
        "avg_accuracy": round(float(avg_acc), 4),
        "std_accuracy": round(float(std_acc), 4),
        "consistency_score": round(float(1 - std_acc / max(avg_acc, 0.01)), 4),
        "baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
        "beats_baseline": bool(avg_acc > max(y.mean(), 1 - y.mean())),
    }


# ─────────────────────────────────────────────
# 5. SIGNAL QUALITY METRICS
# ─────────────────────────────────────────────

def evaluate_signal_quality(
    predictions: List[int],
    actuals: List[int],
    returns: List[float],
) -> Dict:
    """
    Evaluate the quality of a trading signal.

    Args:
        predictions: List of predicted directions (1=long, 0=short/flat)
        actuals: List of actual directions (1=up, 0=down)
        returns: List of actual period returns (decimal, e.g. 0.01 = 1%)

    Returns:
        Dict with accuracy, Sharpe, profit factor, win rate, edge metrics
    """
    preds = np.array(predictions)
    acts = np.array(actuals)
    rets = np.array(returns)

    # Strategy returns: go long when predicted up, flat otherwise
    strat_returns = np.where(preds == 1, rets, 0)

    # Metrics
    winning = strat_returns[strat_returns > 0]
    losing = strat_returns[strat_returns < 0]

    total_trades = int(preds.sum())
    win_rate = float(len(winning) / max(total_trades, 1))

    gross_profit = float(winning.sum()) if len(winning) > 0 else 0.0
    gross_loss = float(abs(losing.sum())) if len(losing) > 0 else 0.001
    profit_factor = gross_profit / gross_loss

    # Annualized Sharpe (assuming daily)
    mean_ret = float(strat_returns.mean())
    std_ret = float(strat_returns.std()) if strat_returns.std() > 0 else 0.001
    sharpe = (mean_ret / std_ret) * np.sqrt(252)

    # Max drawdown
    cum = np.cumsum(strat_returns)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0

    return {
        "accuracy": round(float(accuracy_score(acts, preds)), 4),
        "total_signals": int(len(preds)),
        "long_signals": total_trades,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "sharpe_ratio": round(sharpe, 4),
        "total_return": round(float(strat_returns.sum()), 6),
        "max_drawdown": round(max_dd, 6),
        "avg_win": round(float(winning.mean()), 6) if len(winning) > 0 else 0.0,
        "avg_loss": round(float(losing.mean()), 6) if len(losing) > 0 else 0.0,
        "edge_vs_random": round(float(accuracy_score(acts, preds) - 0.5), 4),
    }


# ─────────────────────────────────────────────
# 6. QUICK ANALYSIS
# ─────────────────────────────────────────────

def quick_ml_scan(symbol: str) -> Dict:
    """
    Run a quick ML predictability scan on a symbol.

    Tests multiple strategies and models to see if the symbol
    has any ML-exploitable patterns.

    Args:
        symbol: Ticker symbol (e.g. 'AAPL', 'SPY', 'BTC-USD')

    Returns:
        Dict with results for each strategy/model combination and overall assessment
    """
    results = []
    for strategy in ["momentum", "mean_reversion"]:
        for model_type in ["random_forest", "gradient_boosting"]:
            res = train_direction_model(
                symbol, period="2y", model_type=model_type,
                strategy=strategy, test_size=0.2
            )
            if "error" not in res:
                results.append({
                    "strategy": strategy,
                    "model": model_type,
                    "accuracy": res["accuracy"],
                    "precision": res["precision"],
                    "f1": res["f1"],
                    "baseline": res["baseline_accuracy"],
                    "beats_baseline": res["accuracy"] > res["baseline_accuracy"],
                    "top_feature": res["top_features"][0]["feature"] if res["top_features"] else None,
                })

    if not results:
        return {"error": "All model runs failed", "symbol": symbol}

    best = max(results, key=lambda x: x["accuracy"])
    any_beats = any(r["beats_baseline"] for r in results)

    return {
        "symbol": symbol,
        "scans_run": len(results),
        "best_accuracy": best["accuracy"],
        "best_strategy": best["strategy"],
        "best_model": best["model"],
        "any_beats_baseline": any_beats,
        "assessment": "ML-exploitable patterns detected" if any_beats else "No significant ML edge found",
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "neuralquant_toolkit",
        "status": "active",
        "source": "https://neuralquant.io/toolkit",
        "functions": [
            "fetch_ohlcv", "engineer_features", "get_feature_set",
            "train_direction_model", "walk_forward_validate",
            "evaluate_signal_quality", "quick_ml_scan",
        ],
    }, indent=2))
