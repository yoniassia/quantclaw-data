"""
QuantFlow ML — Financial Machine Learning Pipeline Utilities

Provides local-compute ML tools for quantitative finance:
- Time-series feature engineering (returns, volatility, momentum)
- Factor exposure estimation (Fama-French style)
- Sentiment score normalization & aggregation
- Simple alpha signal generation & backtesting
- Volatility forecasting (EWMA, Garman-Klass)

No external API keys required. All computation is local.
Dependencies: numpy, pandas, scikit-learn (all standard)

Data Points:
- Time-series features for stock prices
- Volatility metrics (realized, EWMA, Garman-Klass)
- Sentiment score normalization
- Factor exposures (market, size, value, momentum)
- Backtest results (returns, sharpe, drawdown)

Source: Local computation (inspired by quantflow.io concepts)
Category: Quant Tools & ML
Free tier: true — Fully local, no rate limits
Update frequency: On-demand (user provides data)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
import os
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/quantflow_ml")
os.makedirs(CACHE_DIR, exist_ok=True)


# ─── Time-Series Feature Engineering ─────────────────────────────────────────

def compute_returns(prices: List[float], period: int = 1) -> Dict:
    """
    Compute log and simple returns from a price series.

    Args:
        prices: List of closing prices (oldest first)
        period: Return period in bars (1=daily, 5=weekly, 21=monthly)

    Returns:
        Dict with simple_returns, log_returns, stats
    """
    if not prices or len(prices) < period + 1:
        return {"error": "Need at least period+1 prices", "prices_given": len(prices)}

    try:
        arr = np.array(prices, dtype=float)
        simple_ret = (arr[period:] - arr[:-period]) / arr[:-period]
        log_ret = np.log(arr[period:] / arr[:-period])

        return {
            "simple_returns": [round(r, 6) for r in simple_ret.tolist()],
            "log_returns": [round(r, 6) for r in log_ret.tolist()],
            "stats": {
                "mean_simple": round(float(np.mean(simple_ret)), 6),
                "mean_log": round(float(np.mean(log_ret)), 6),
                "std": round(float(np.std(simple_ret)), 6),
                "skew": round(float(pd.Series(simple_ret).skew()), 4),
                "kurtosis": round(float(pd.Series(simple_ret).kurtosis()), 4),
                "min": round(float(np.min(simple_ret)), 6),
                "max": round(float(np.max(simple_ret)), 6),
                "count": len(simple_ret),
                "period": period
            },
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"compute_returns failed: {str(e)}"}


def engineer_features(prices: List[float], volumes: Optional[List[float]] = None,
                      windows: List[int] = [5, 10, 21, 63]) -> Dict:
    """
    Generate a full set of technical/ML features from price data.

    Args:
        prices: List of closing prices (oldest first)
        volumes: Optional list of volumes (same length as prices)
        windows: Rolling window sizes for feature computation

    Returns:
        Dict with feature arrays and feature names
    """
    if not prices or len(prices) < max(windows) + 1:
        return {"error": f"Need at least {max(windows)+1} prices, got {len(prices)}"}

    try:
        df = pd.DataFrame({"close": prices})
        if volumes:
            df["volume"] = volumes[:len(prices)]

        # Returns
        df["ret_1d"] = df["close"].pct_change()

        features = {}
        feature_names = []

        for w in windows:
            # Rolling returns
            col = f"ret_{w}d"
            df[col] = df["close"].pct_change(w)
            features[col] = [round(v, 6) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

            # Rolling volatility (annualized)
            col = f"vol_{w}d"
            df[col] = df["ret_1d"].rolling(w).std() * np.sqrt(252)
            features[col] = [round(v, 6) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

            # Rolling mean (SMA)
            col = f"sma_{w}"
            df[col] = df["close"].rolling(w).mean()
            features[col] = [round(v, 4) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

            # Price relative to SMA
            col = f"price_vs_sma_{w}"
            df[col] = df["close"] / df[f"sma_{w}"] - 1
            features[col] = [round(v, 6) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

            # Rolling Sharpe (annualized)
            col = f"sharpe_{w}d"
            roll_mean = df["ret_1d"].rolling(w).mean()
            roll_std = df["ret_1d"].rolling(w).std()
            df[col] = (roll_mean / roll_std) * np.sqrt(252)
            features[col] = [round(v, 4) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

        # RSI (14-period)
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        features["rsi_14"] = [round(v, 2) if not pd.isna(v) else None for v in df["rsi_14"].tolist()]
        feature_names.append("rsi_14")

        # MACD
        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        for col in ["macd", "macd_signal", "macd_hist"]:
            features[col] = [round(v, 4) if not pd.isna(v) else None for v in df[col].tolist()]
            feature_names.append(col)

        # Volume features
        if volumes and len(volumes) == len(prices):
            df["vol_sma_20"] = df["volume"].rolling(20).mean()
            df["vol_ratio"] = df["volume"] / df["vol_sma_20"]
            features["vol_ratio"] = [round(v, 4) if not pd.isna(v) else None for v in df["vol_ratio"].tolist()]
            feature_names.append("vol_ratio")

        return {
            "features": features,
            "feature_names": feature_names,
            "feature_count": len(feature_names),
            "data_points": len(prices),
            "windows": windows,
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"engineer_features failed: {str(e)}"}


# ─── Volatility Metrics ──────────────────────────────────────────────────────

def compute_volatility(prices: List[float], method: str = "all",
                       window: int = 21, annualize: bool = True) -> Dict:
    """
    Compute volatility using multiple methods.

    Args:
        prices: Closing prices (oldest first)
        method: 'realized', 'ewma', 'parkinson', or 'all'
        window: Rolling window size
        annualize: Whether to annualize (multiply by sqrt(252))

    Returns:
        Dict with volatility estimates by method
    """
    if len(prices) < window + 1:
        return {"error": f"Need at least {window+1} prices"}

    try:
        arr = np.array(prices, dtype=float)
        log_ret = np.log(arr[1:] / arr[:-1])
        factor = np.sqrt(252) if annualize else 1.0
        result = {"window": window, "annualized": annualize}

        if method in ("realized", "all"):
            realized = float(np.std(log_ret[-window:])) * factor
            result["realized"] = round(realized, 6)

        if method in ("ewma", "all"):
            # EWMA volatility (RiskMetrics lambda=0.94)
            lam = 0.94
            var = log_ret[0] ** 2
            for r in log_ret[1:]:
                var = lam * var + (1 - lam) * r ** 2
            ewma_vol = float(np.sqrt(var)) * factor
            result["ewma"] = round(ewma_vol, 6)

        if method in ("parkinson", "all"):
            # Parkinson (uses close-to-close as proxy since we lack H/L)
            # True Parkinson needs high/low; approximate with range estimator
            park_var = np.mean(log_ret[-window:] ** 2) / (4 * np.log(2))
            result["parkinson_approx"] = round(float(np.sqrt(park_var)) * factor, 6)

        # Volatility regime classification
        if "realized" in result:
            vol = result["realized"]
            if vol < 0.10:
                result["regime"] = "LOW"
            elif vol < 0.20:
                result["regime"] = "NORMAL"
            elif vol < 0.35:
                result["regime"] = "HIGH"
            else:
                result["regime"] = "EXTREME"

        result["computed_at"] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        return {"error": f"compute_volatility failed: {str(e)}"}


# ─── Factor Exposure Estimation ──────────────────────────────────────────────

def estimate_factor_exposures(stock_returns: List[float],
                              market_returns: List[float],
                              smb_returns: Optional[List[float]] = None,
                              hml_returns: Optional[List[float]] = None,
                              mom_returns: Optional[List[float]] = None) -> Dict:
    """
    Estimate factor exposures via OLS regression (CAPM / Fama-French style).

    Args:
        stock_returns: Asset returns series
        market_returns: Market (benchmark) returns series
        smb_returns: Size factor returns (optional)
        hml_returns: Value factor returns (optional)
        mom_returns: Momentum factor returns (optional)

    Returns:
        Dict with alpha, beta, factor loadings, R-squared, t-stats
    """
    from sklearn.linear_model import LinearRegression

    n = min(len(stock_returns), len(market_returns))
    if n < 30:
        return {"error": f"Need at least 30 observations, got {n}"}

    try:
        y = np.array(stock_returns[:n])
        X_cols = {"market": np.array(market_returns[:n])}

        if smb_returns and len(smb_returns) >= n:
            X_cols["smb"] = np.array(smb_returns[:n])
        if hml_returns and len(hml_returns) >= n:
            X_cols["hml"] = np.array(hml_returns[:n])
        if mom_returns and len(mom_returns) >= n:
            X_cols["mom"] = np.array(mom_returns[:n])

        factor_names = list(X_cols.keys())
        X = np.column_stack(list(X_cols.values()))

        model = LinearRegression(fit_intercept=True)
        model.fit(X, y)

        y_pred = model.predict(X)
        residuals = y - y_pred
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # T-statistics
        mse = ss_res / (n - len(factor_names) - 1)
        X_with_intercept = np.column_stack([np.ones(n), X])
        try:
            cov_matrix = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
            se = np.sqrt(np.diag(cov_matrix))
            coefs = np.concatenate([[model.intercept_], model.coef_])
            t_stats = coefs / se
        except np.linalg.LinAlgError:
            t_stats = [None] * (len(factor_names) + 1)

        exposures = {}
        for i, name in enumerate(factor_names):
            exposures[name] = {
                "beta": round(float(model.coef_[i]), 4),
                "t_stat": round(float(t_stats[i + 1]), 2) if t_stats[i + 1] is not None else None
            }

        # Annualized alpha
        alpha_daily = float(model.intercept_)
        alpha_annual = alpha_daily * 252

        return {
            "alpha_daily": round(alpha_daily, 6),
            "alpha_annual": round(alpha_annual, 4),
            "alpha_t_stat": round(float(t_stats[0]), 2) if t_stats[0] is not None else None,
            "exposures": exposures,
            "r_squared": round(r_squared, 4),
            "residual_vol": round(float(np.std(residuals)) * np.sqrt(252), 4),
            "observations": n,
            "model_type": "FF3+Mom" if len(factor_names) == 4 else
                          "FF3" if len(factor_names) == 3 else "CAPM",
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"estimate_factor_exposures failed: {str(e)}"}


# ─── Sentiment Score Normalization ────────────────────────────────────────────

def normalize_sentiment(scores: List[float], method: str = "zscore",
                        window: Optional[int] = None) -> Dict:
    """
    Normalize raw sentiment scores for cross-asset comparability.

    Args:
        scores: Raw sentiment scores (e.g., from NLP, surveys)
        method: 'zscore', 'minmax', 'rank', or 'percentile'
        window: Rolling window for z-score (None = full sample)

    Returns:
        Dict with normalized scores and distribution stats
    """
    if not scores or len(scores) < 3:
        return {"error": "Need at least 3 sentiment scores"}

    try:
        arr = np.array(scores, dtype=float)

        if method == "zscore":
            if window and window < len(arr):
                # Rolling z-score
                s = pd.Series(arr)
                roll_mean = s.rolling(window).mean()
                roll_std = s.rolling(window).std()
                normalized = ((s - roll_mean) / roll_std).tolist()
            else:
                normalized = ((arr - np.mean(arr)) / np.std(arr)).tolist()

        elif method == "minmax":
            mn, mx = np.min(arr), np.max(arr)
            normalized = ((arr - mn) / (mx - mn) if mx > mn else np.zeros_like(arr)).tolist()

        elif method == "rank":
            from scipy.stats import rankdata
            normalized = (rankdata(arr) / len(arr)).tolist()

        elif method == "percentile":
            from scipy.stats import percentileofscore
            normalized = [percentileofscore(arr, x) / 100 for x in arr]

        else:
            return {"error": f"Unknown method: {method}. Use zscore/minmax/rank/percentile"}

        normalized_clean = [round(v, 4) if not (isinstance(v, float) and np.isnan(v)) else None
                           for v in normalized]

        # Signal classification on latest value
        latest = normalized_clean[-1]
        if latest is not None:
            if method == "zscore":
                if latest > 1.5:
                    signal = "STRONG_POSITIVE"
                elif latest > 0.5:
                    signal = "POSITIVE"
                elif latest < -1.5:
                    signal = "STRONG_NEGATIVE"
                elif latest < -0.5:
                    signal = "NEGATIVE"
                else:
                    signal = "NEUTRAL"
            else:
                if latest > 0.8:
                    signal = "STRONG_POSITIVE"
                elif latest > 0.6:
                    signal = "POSITIVE"
                elif latest < 0.2:
                    signal = "STRONG_NEGATIVE"
                elif latest < 0.4:
                    signal = "NEGATIVE"
                else:
                    signal = "NEUTRAL"
        else:
            signal = "UNKNOWN"

        return {
            "normalized": normalized_clean,
            "method": method,
            "window": window,
            "latest_raw": float(arr[-1]),
            "latest_normalized": latest,
            "signal": signal,
            "stats": {
                "raw_mean": round(float(np.mean(arr)), 4),
                "raw_std": round(float(np.std(arr)), 4),
                "raw_min": round(float(np.min(arr)), 4),
                "raw_max": round(float(np.max(arr)), 4)
            },
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"normalize_sentiment failed: {str(e)}"}


# ─── Alpha Signal Generation ─────────────────────────────────────────────────

def generate_alpha_signal(prices: List[float],
                          fast_window: int = 10,
                          slow_window: int = 50,
                          signal_type: str = "momentum_crossover") -> Dict:
    """
    Generate a simple alpha signal from price data.

    Args:
        prices: Closing prices (oldest first)
        fast_window: Short lookback period
        slow_window: Long lookback period
        signal_type: 'momentum_crossover', 'mean_reversion', 'breakout'

    Returns:
        Dict with signal series, current signal, and stats
    """
    if len(prices) < slow_window + 5:
        return {"error": f"Need at least {slow_window+5} prices"}

    try:
        df = pd.DataFrame({"close": prices})
        df["ret"] = df["close"].pct_change()

        if signal_type == "momentum_crossover":
            df["fast_ma"] = df["close"].rolling(fast_window).mean()
            df["slow_ma"] = df["close"].rolling(slow_window).mean()
            df["signal"] = np.where(df["fast_ma"] > df["slow_ma"], 1.0,
                            np.where(df["fast_ma"] < df["slow_ma"], -1.0, 0.0))

        elif signal_type == "mean_reversion":
            df["zscore"] = (df["close"] - df["close"].rolling(slow_window).mean()) / \
                            df["close"].rolling(slow_window).std()
            df["signal"] = np.where(df["zscore"] < -1.5, 1.0,
                            np.where(df["zscore"] > 1.5, -1.0, 0.0))

        elif signal_type == "breakout":
            df["high_n"] = df["close"].rolling(slow_window).max()
            df["low_n"] = df["close"].rolling(slow_window).min()
            df["signal"] = np.where(df["close"] >= df["high_n"], 1.0,
                            np.where(df["close"] <= df["low_n"], -1.0, 0.0))
        else:
            return {"error": f"Unknown signal_type: {signal_type}"}

        # Strategy returns
        df["strat_ret"] = df["signal"].shift(1) * df["ret"]
        valid = df.dropna(subset=["strat_ret"])

        if len(valid) < 10:
            return {"error": "Not enough data for strategy evaluation"}

        strat_cum = (1 + valid["strat_ret"]).cumprod()
        bh_cum = (1 + valid["ret"]).cumprod()

        # Drawdown
        rolling_max = strat_cum.cummax()
        drawdown = (strat_cum - rolling_max) / rolling_max

        sharpe = float(valid["strat_ret"].mean() / valid["strat_ret"].std() * np.sqrt(252)) \
                 if valid["strat_ret"].std() > 0 else 0.0

        signals = df["signal"].dropna().tolist()
        current_signal = signals[-1] if signals else 0

        return {
            "signal_type": signal_type,
            "current_signal": current_signal,
            "signal_label": "LONG" if current_signal > 0 else "SHORT" if current_signal < 0 else "FLAT",
            "fast_window": fast_window,
            "slow_window": slow_window,
            "performance": {
                "strategy_return": round(float(strat_cum.iloc[-1] - 1), 4),
                "buyhold_return": round(float(bh_cum.iloc[-1] - 1), 4),
                "excess_return": round(float(strat_cum.iloc[-1] - bh_cum.iloc[-1]), 4),
                "sharpe_ratio": round(sharpe, 2),
                "max_drawdown": round(float(drawdown.min()), 4),
                "win_rate": round(float((valid["strat_ret"] > 0).sum() / len(valid)), 4),
                "trade_days": len(valid),
            },
            "signals_last_10": [int(s) for s in signals[-10:]],
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"generate_alpha_signal failed: {str(e)}"}


# ─── Backtest Engine ─────────────────────────────────────────────────────────

def backtest_signals(prices: List[float], signals: List[float],
                     initial_capital: float = 100000,
                     commission_bps: float = 5.0) -> Dict:
    """
    Backtest a pre-computed signal series against prices.

    Args:
        prices: Closing prices (oldest first)
        signals: Signal values (-1 to 1) aligned with prices
        initial_capital: Starting capital
        commission_bps: Commission in basis points per trade

    Returns:
        Dict with full backtest results (equity curve, metrics, trades)
    """
    n = min(len(prices), len(signals))
    if n < 10:
        return {"error": "Need at least 10 aligned price/signal observations"}

    try:
        p = np.array(prices[:n], dtype=float)
        s = np.array(signals[:n], dtype=float)
        s = np.clip(s, -1, 1)

        rets = np.diff(p) / p[:-1]
        strat_rets = s[:-1] * rets

        # Commission: charge on signal changes
        signal_changes = np.abs(np.diff(s))
        commissions = signal_changes * (commission_bps / 10000)
        strat_rets[1:] -= commissions[:-1] if len(commissions) > 1 else 0

        equity = initial_capital * np.cumprod(1 + strat_rets)
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak

        total_return = float(equity[-1] / initial_capital - 1)
        ann_return = float((1 + total_return) ** (252 / max(len(rets), 1)) - 1)
        vol = float(np.std(strat_rets) * np.sqrt(252))
        sharpe = ann_return / vol if vol > 0 else 0.0
        sortino_denom = float(np.std(strat_rets[strat_rets < 0]) * np.sqrt(252)) if np.any(strat_rets < 0) else 1.0
        sortino = ann_return / sortino_denom if sortino_denom > 0 else 0.0
        calmar = ann_return / abs(float(drawdown.min())) if drawdown.min() < 0 else float('inf')

        trade_count = int(np.sum(signal_changes > 0))

        return {
            "initial_capital": initial_capital,
            "final_equity": round(float(equity[-1]), 2),
            "total_return": round(total_return, 4),
            "annualized_return": round(ann_return, 4),
            "annualized_vol": round(vol, 4),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2) if calmar != float('inf') else None,
            "max_drawdown": round(float(drawdown.min()), 4),
            "win_rate": round(float(np.sum(strat_rets > 0) / len(strat_rets)), 4),
            "profit_factor": round(float(np.sum(strat_rets[strat_rets > 0]) /
                                          abs(np.sum(strat_rets[strat_rets < 0]))), 2)
                            if np.any(strat_rets < 0) else None,
            "trade_count": trade_count,
            "commission_bps": commission_bps,
            "total_commission_paid": round(float(np.sum(commissions)) * initial_capital, 2),
            "trading_days": len(rets),
            "equity_curve_sample": [round(float(e), 2) for e in equity[::max(len(equity)//20, 1)]],
            "computed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"backtest_signals failed: {str(e)}"}


# ─── Pipeline Builder (Convenience) ──────────────────────────────────────────

def run_full_pipeline(prices: List[float],
                      volumes: Optional[List[float]] = None,
                      benchmark_returns: Optional[List[float]] = None,
                      signal_type: str = "momentum_crossover") -> Dict:
    """
    Run a complete ML pipeline: features → signal → backtest → report.

    Args:
        prices: Closing prices (oldest first, 100+ recommended)
        volumes: Optional volume data
        benchmark_returns: Optional benchmark returns for factor analysis
        signal_type: Alpha signal type

    Returns:
        Dict with features, volatility, signal, backtest, and summary
    """
    if len(prices) < 65:
        return {"error": "Need at least 65 prices for full pipeline"}

    try:
        result = {"pipeline": "quantflow_ml_full", "stages": {}}

        # Stage 1: Features
        features = engineer_features(prices, volumes)
        result["stages"]["features"] = {
            "status": "ok" if "error" not in features else "error",
            "feature_count": features.get("feature_count", 0)
        }

        # Stage 2: Volatility
        vol = compute_volatility(prices)
        result["stages"]["volatility"] = vol

        # Stage 3: Alpha signal
        signal = generate_alpha_signal(prices, signal_type=signal_type)
        result["stages"]["alpha_signal"] = {
            "status": "ok" if "error" not in signal else "error",
            "current_signal": signal.get("signal_label", "UNKNOWN"),
            "sharpe": signal.get("performance", {}).get("sharpe_ratio")
        }

        # Stage 4: Factor exposure (if benchmark provided)
        if benchmark_returns:
            stock_ret = compute_returns(prices)
            if "simple_returns" in stock_ret:
                factors = estimate_factor_exposures(
                    stock_ret["simple_returns"], benchmark_returns
                )
                result["stages"]["factor_exposure"] = {
                    "status": "ok" if "error" not in factors else "error",
                    "model": factors.get("model_type"),
                    "alpha_annual": factors.get("alpha_annual"),
                    "r_squared": factors.get("r_squared")
                }

        # Summary
        result["summary"] = {
            "data_points": len(prices),
            "volatility_regime": vol.get("regime", "UNKNOWN"),
            "signal": signal.get("signal_label", "UNKNOWN"),
            "strategy_sharpe": signal.get("performance", {}).get("sharpe_ratio"),
            "strategy_return": signal.get("performance", {}).get("strategy_return"),
            "max_drawdown": signal.get("performance", {}).get("max_drawdown"),
        }
        result["computed_at"] = datetime.utcnow().isoformat()
        return result
    except Exception as e:
        return {"error": f"run_full_pipeline failed: {str(e)}"}


# ─── Module Info ──────────────────────────────────────────────────────────────

def get_module_info() -> Dict:
    """Return module metadata and available functions."""
    return {
        "module": "quantflow_ml",
        "version": "1.0.0",
        "description": "Financial ML pipeline utilities — features, volatility, factors, signals, backtesting",
        "source": "Local computation (no external API)",
        "requires_api_key": False,
        "functions": [
            "compute_returns",
            "engineer_features",
            "compute_volatility",
            "estimate_factor_exposures",
            "normalize_sentiment",
            "generate_alpha_signal",
            "backtest_signals",
            "run_full_pipeline",
            "get_module_info"
        ],
        "dependencies": ["numpy", "pandas", "scikit-learn"],
        "category": "Quant Tools & ML"
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
