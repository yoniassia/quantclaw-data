#!/usr/bin/env python3
"""
Kats — Time Series Analysis Toolkit for Trading Signals

Implements core Kats-style functionality (Meta's open-source toolkit) using
statsmodels/scipy/numpy. Provides forecasting, anomaly detection, changepoint
detection, trend decomposition, and ensemble methods for quant trading.

Source: https://facebookresearch.github.io/Kats/
Category: Quant Tools & ML
Free tier: True (no API keys, pure computation)
Update frequency: N/A (library — operates on user-supplied data)

Functions:
- forecast_timeseries: Holt-Winters / exponential smoothing forecasting
- detect_anomalies: Z-score and IQR-based anomaly detection
- detect_changepoints: CUSUM changepoint detection
- decompose_timeseries: Trend/seasonal/residual decomposition
- ensemble_forecast: Ensemble of multiple forecasting methods
- compute_acf: Autocorrelation analysis
- detect_seasonality: Detect dominant seasonal period
- rolling_statistics: Rolling mean/std/z-score for regime detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
import warnings

warnings.filterwarnings("ignore")


def _to_series(data: Union[List, Dict, pd.Series, pd.DataFrame],
               value_col: str = "value",
               date_col: str = "time") -> pd.Series:
    """Convert various inputs to a pandas Series with datetime index."""
    if isinstance(data, pd.Series):
        s = data.copy()
    elif isinstance(data, pd.DataFrame):
        if date_col in data.columns and value_col in data.columns:
            s = pd.Series(data[value_col].values, index=pd.to_datetime(data[date_col]))
        elif date_col in data.columns:
            num_cols = data.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                s = pd.Series(data[num_cols[0]].values, index=pd.to_datetime(data[date_col]))
            else:
                raise ValueError("No numeric column found in DataFrame")
        else:
            s = data.iloc[:, 0]
    elif isinstance(data, dict):
        if "values" in data:
            vals = data["values"]
            dates = data.get("dates", data.get("times", None))
            if dates:
                s = pd.Series(vals, index=pd.to_datetime(dates))
            else:
                s = pd.Series(vals)
        else:
            s = pd.Series(data)
    elif isinstance(data, list):
        s = pd.Series(data)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")

    s = s.astype(float)
    return s


def forecast_timeseries(data: Union[List, Dict, pd.Series],
                        steps: int = 10,
                        method: str = "holt_winters",
                        seasonal_periods: Optional[int] = None,
                        confidence: float = 0.95) -> Dict:
    """
    Forecast future values using exponential smoothing methods.

    Args:
        data: Time series data (list of values, dict with 'values' key, or pd.Series)
        steps: Number of future steps to predict
        method: 'holt_winters', 'simple_exp', or 'double_exp'
        seasonal_periods: Period for seasonal component (auto-detected if None)
        confidence: Confidence level for prediction intervals

    Returns:
        Dict with forecast values, confidence intervals, model info, and fit metrics.
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

    series = _to_series(data)
    n = len(series)

    if n < 4:
        return {"error": "Need at least 4 data points for forecasting", "n": n}

    # Auto-detect seasonal period if needed
    if seasonal_periods is None and method == "holt_winters" and n >= 14:
        seasonal_periods = _detect_period(series)

    try:
        if method == "simple_exp":
            model = SimpleExpSmoothing(series.values).fit(optimized=True)
        elif method == "double_exp":
            model = ExponentialSmoothing(
                series.values, trend="add", seasonal=None
            ).fit(optimized=True)
        else:  # holt_winters
            if seasonal_periods and seasonal_periods >= 2 and n >= 2 * seasonal_periods:
                model = ExponentialSmoothing(
                    series.values, trend="add", seasonal="add",
                    seasonal_periods=seasonal_periods
                ).fit(optimized=True)
            else:
                model = ExponentialSmoothing(
                    series.values, trend="add", seasonal=None
                ).fit(optimized=True)

        forecast = model.forecast(steps)

        # Compute prediction intervals from residuals
        residuals = series.values - model.fittedvalues
        std_resid = float(np.std(residuals))
        from scipy import stats
        z = stats.norm.ppf((1 + confidence) / 2)
        steps_arr = np.arange(1, steps + 1)
        margin = z * std_resid * np.sqrt(steps_arr)

        result = {
            "method": method,
            "forecast": [round(float(v), 4) for v in forecast],
            "lower_bound": [round(float(v), 4) for v in (forecast - margin)],
            "upper_bound": [round(float(v), 4) for v in (forecast + margin)],
            "confidence": confidence,
            "steps": steps,
            "fit_metrics": {
                "aic": round(float(model.aic), 2) if hasattr(model, "aic") else None,
                "mse": round(float(np.mean(residuals ** 2)), 6),
                "mae": round(float(np.mean(np.abs(residuals))), 6),
            },
            "seasonal_periods": seasonal_periods,
            "n_observations": n,
        }

        if series.index is not None and hasattr(series.index, 'freq') and series.index.freq:
            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date, periods=steps + 1, freq=series.index.freq)[1:]
            result["forecast_dates"] = [str(d) for d in future_dates]

        return result

    except Exception as e:
        return {"error": f"Forecasting failed: {str(e)}", "method": method}


def detect_anomalies(data: Union[List, Dict, pd.Series],
                     method: str = "zscore",
                     threshold: float = 3.0,
                     window: Optional[int] = None) -> Dict:
    """
    Detect anomalies in time series data.

    Args:
        data: Time series data
        method: 'zscore' (global z-score), 'iqr' (interquartile range),
                or 'rolling_zscore' (local z-score with rolling window)
        threshold: Sensitivity threshold (z-score cutoff or IQR multiplier)
        window: Rolling window size (for rolling_zscore; auto = len/10)

    Returns:
        Dict with anomaly indices, values, scores, and summary statistics.
    """
    series = _to_series(data)
    values = series.values
    n = len(values)

    if n < 5:
        return {"error": "Need at least 5 data points", "n": n}

    anomaly_mask = np.zeros(n, dtype=bool)
    scores = np.zeros(n)

    if method == "zscore":
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return {"anomalies": [], "count": 0, "method": method, "note": "zero variance"}
        scores = np.abs((values - mean) / std)
        anomaly_mask = scores > threshold

    elif method == "iqr":
        q1, q3 = np.percentile(values, [25, 75])
        iqr = q3 - q1
        if iqr == 0:
            return {"anomalies": [], "count": 0, "method": method, "note": "zero IQR"}
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        anomaly_mask = (values < lower) | (values > upper)
        scores = np.where(values > upper, (values - upper) / iqr,
                          np.where(values < lower, (lower - values) / iqr, 0.0))

    elif method == "rolling_zscore":
        if window is None:
            window = max(5, n // 10)
        rolling_mean = pd.Series(values).rolling(window=window, center=True).mean().values
        rolling_std = pd.Series(values).rolling(window=window, center=True).std().values
        valid = rolling_std > 0
        scores[valid] = np.abs((values[valid] - rolling_mean[valid]) / rolling_std[valid])
        anomaly_mask = scores > threshold
    else:
        return {"error": f"Unknown method: {method}"}

    indices = np.where(anomaly_mask)[0].tolist()
    anomalies = [
        {"index": int(i), "value": round(float(values[i]), 4),
         "score": round(float(scores[i]), 4)}
        for i in indices
    ]

    return {
        "method": method,
        "threshold": threshold,
        "anomalies": anomalies,
        "count": len(anomalies),
        "total_points": n,
        "anomaly_pct": round(100.0 * len(anomalies) / n, 2),
        "stats": {
            "mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values)), 4),
            "min": round(float(np.min(values)), 4),
            "max": round(float(np.max(values)), 4),
        },
    }


def detect_changepoints(data: Union[List, Dict, pd.Series],
                        threshold: float = 4.0,
                        drift: float = 0.5,
                        method: str = "cusum") -> Dict:
    """
    Detect changepoints (regime shifts) in time series.

    Args:
        data: Time series data
        threshold: Detection threshold (higher = fewer detections)
        drift: Allowable drift before flagging (CUSUM parameter)
        method: 'cusum' (cumulative sum) or 'mean_shift'

    Returns:
        Dict with changepoint locations, magnitudes, and segment info.
    """
    series = _to_series(data)
    values = series.values
    n = len(values)

    if n < 10:
        return {"error": "Need at least 10 data points", "n": n}

    changepoints = []

    if method == "cusum":
        mean = np.mean(values)
        std = np.std(values)
        if std == 0:
            return {"changepoints": [], "count": 0, "method": method}

        normalized = (values - mean) / std
        s_pos = np.zeros(n)
        s_neg = np.zeros(n)

        for i in range(1, n):
            s_pos[i] = max(0, s_pos[i - 1] + normalized[i] - drift)
            s_neg[i] = max(0, s_neg[i - 1] - normalized[i] - drift)

            if s_pos[i] > threshold:
                changepoints.append({
                    "index": int(i),
                    "direction": "increase",
                    "magnitude": round(float(s_pos[i]), 4),
                    "value": round(float(values[i]), 4),
                })
                s_pos[i] = 0
            elif s_neg[i] > threshold:
                changepoints.append({
                    "index": int(i),
                    "direction": "decrease",
                    "magnitude": round(float(s_neg[i]), 4),
                    "value": round(float(values[i]), 4),
                })
                s_neg[i] = 0

    elif method == "mean_shift":
        min_segment = max(5, n // 20)
        for i in range(min_segment, n - min_segment):
            left = values[:i]
            right = values[i:]
            diff = abs(np.mean(right) - np.mean(left))
            pooled_std = np.sqrt((np.var(left) + np.var(right)) / 2)
            if pooled_std > 0 and diff / pooled_std > threshold:
                changepoints.append({
                    "index": int(i),
                    "direction": "increase" if np.mean(right) > np.mean(left) else "decrease",
                    "magnitude": round(float(diff / pooled_std), 4),
                    "value": round(float(values[i]), 4),
                    "left_mean": round(float(np.mean(left)), 4),
                    "right_mean": round(float(np.mean(right)), 4),
                })

    # Deduplicate nearby changepoints
    if len(changepoints) > 1:
        filtered = [changepoints[0]]
        for cp in changepoints[1:]:
            if cp["index"] - filtered[-1]["index"] >= max(3, n // 50):
                filtered.append(cp)
            elif cp["magnitude"] > filtered[-1]["magnitude"]:
                filtered[-1] = cp
        changepoints = filtered

    return {
        "method": method,
        "threshold": threshold,
        "changepoints": changepoints,
        "count": len(changepoints),
        "total_points": n,
    }


def decompose_timeseries(data: Union[List, Dict, pd.Series],
                         period: Optional[int] = None,
                         model: str = "additive") -> Dict:
    """
    Decompose time series into trend, seasonal, and residual components.

    Args:
        data: Time series data
        period: Seasonal period (auto-detected if None)
        model: 'additive' or 'multiplicative'

    Returns:
        Dict with trend, seasonal, residual arrays and strength metrics.
    """
    from statsmodels.tsa.seasonal import seasonal_decompose

    series = _to_series(data)
    n = len(series)

    if period is None:
        period = _detect_period(series)
    if period is None or period < 2:
        period = min(7, n // 3) if n >= 9 else 2

    if n < 2 * period:
        return {"error": f"Need at least {2 * period} points for period={period}", "n": n}

    try:
        result = seasonal_decompose(series.values, model=model, period=period)

        # Compute strength of trend and seasonality
        var_resid = np.nanvar(result.resid)
        trend_strength = max(0, 1 - var_resid / np.nanvar(result.trend + result.resid))
        seasonal_strength = max(0, 1 - var_resid / np.nanvar(result.seasonal + result.resid))

        return {
            "model": model,
            "period": period,
            "trend": [round(float(v), 4) if not np.isnan(v) else None for v in result.trend],
            "seasonal": [round(float(v), 4) if not np.isnan(v) else None for v in result.seasonal],
            "residual": [round(float(v), 4) if not np.isnan(v) else None for v in result.resid],
            "trend_strength": round(float(trend_strength), 4),
            "seasonal_strength": round(float(seasonal_strength), 4),
            "n_observations": n,
        }
    except Exception as e:
        return {"error": f"Decomposition failed: {str(e)}"}


def ensemble_forecast(data: Union[List, Dict, pd.Series],
                      steps: int = 10,
                      methods: Optional[List[str]] = None,
                      weights: Optional[List[float]] = None) -> Dict:
    """
    Ensemble forecast combining multiple methods for improved accuracy.

    Args:
        data: Time series data
        steps: Number of future steps to predict
        methods: List of methods to ensemble (default: all three)
        weights: Weights for each method (default: equal weighting)

    Returns:
        Dict with ensemble forecast, individual method forecasts, and spread.
    """
    if methods is None:
        methods = ["holt_winters", "double_exp", "simple_exp"]
    if weights is None:
        weights = [1.0 / len(methods)] * len(methods)

    if len(weights) != len(methods):
        return {"error": "weights must match methods length"}

    # Normalize weights
    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]

    individual_results = {}
    valid_forecasts = []
    valid_weights = []

    for i, method in enumerate(methods):
        result = forecast_timeseries(data, steps=steps, method=method)
        individual_results[method] = result
        if "error" not in result:
            valid_forecasts.append(np.array(result["forecast"]))
            valid_weights.append(weights[i])

    if not valid_forecasts:
        return {"error": "All forecasting methods failed", "details": individual_results}

    # Renormalize weights for valid methods
    w_sum = sum(valid_weights)
    valid_weights = [w / w_sum for w in valid_weights]

    # Weighted ensemble
    ensemble = np.zeros(steps)
    for fc, w in zip(valid_forecasts, valid_weights):
        ensemble += w * fc

    # Spread (disagreement) between methods
    if len(valid_forecasts) > 1:
        stacked = np.vstack(valid_forecasts)
        spread = np.std(stacked, axis=0)
    else:
        spread = np.zeros(steps)

    return {
        "ensemble_forecast": [round(float(v), 4) for v in ensemble],
        "spread": [round(float(v), 4) for v in spread],
        "methods_used": [m for i, m in enumerate(methods)
                         if "error" not in individual_results[m]],
        "methods_failed": [m for m in methods if "error" in individual_results[m]],
        "individual_forecasts": {
            m: r.get("forecast", r.get("error"))
            for m, r in individual_results.items()
        },
        "steps": steps,
    }


def compute_acf(data: Union[List, Dict, pd.Series],
                max_lags: Optional[int] = None) -> Dict:
    """
    Compute autocorrelation function (ACF) for lag analysis.

    Args:
        data: Time series data
        max_lags: Maximum number of lags (default: min(40, n//2))

    Returns:
        Dict with ACF values, significant lags, and dominant period.
    """
    from statsmodels.tsa.stattools import acf

    series = _to_series(data)
    n = len(series)

    if n < 10:
        return {"error": "Need at least 10 data points", "n": n}

    if max_lags is None:
        max_lags = min(40, n // 2)

    acf_values = acf(series.values, nlags=max_lags, fft=True)

    # Significance threshold (approximate 95% CI)
    sig_threshold = 1.96 / np.sqrt(n)
    significant_lags = [
        {"lag": int(i), "acf": round(float(acf_values[i]), 4)}
        for i in range(1, len(acf_values))
        if abs(acf_values[i]) > sig_threshold
    ]

    # Find dominant period (first significant peak after lag 1)
    dominant_period = None
    for i in range(2, len(acf_values) - 1):
        if acf_values[i] > acf_values[i - 1] and acf_values[i] > acf_values[i + 1]:
            if acf_values[i] > sig_threshold:
                dominant_period = int(i)
                break

    return {
        "acf": [round(float(v), 4) for v in acf_values],
        "max_lags": max_lags,
        "significant_lags": significant_lags,
        "significance_threshold": round(float(sig_threshold), 4),
        "dominant_period": dominant_period,
        "n_observations": n,
    }


def detect_seasonality(data: Union[List, Dict, pd.Series],
                       max_period: Optional[int] = None) -> Dict:
    """
    Detect the dominant seasonal period in time series data.

    Args:
        data: Time series data
        max_period: Maximum period to search (default: n//3)

    Returns:
        Dict with detected period, strength, and candidate periods.
    """
    series = _to_series(data)
    values = series.values
    n = len(values)

    if n < 10:
        return {"error": "Need at least 10 data points", "n": n}

    if max_period is None:
        max_period = min(n // 3, 365)

    # Use FFT for period detection
    detrended = values - np.linspace(values[0], values[-1], n)
    fft = np.fft.rfft(detrended)
    power = np.abs(fft) ** 2

    # Skip DC component (index 0) and very high freq
    min_period = 2
    candidates = []
    for i in range(1, len(power)):
        period = n / i
        if min_period <= period <= max_period:
            candidates.append({
                "period": round(float(period), 1),
                "power": round(float(power[i]), 4),
            })

    candidates.sort(key=lambda x: x["power"], reverse=True)
    top_candidates = candidates[:5]

    detected = top_candidates[0] if top_candidates else None

    # Compute seasonality strength via decomposition if we have a period
    strength = None
    if detected and detected["period"] >= 2:
        period_int = int(round(detected["period"]))
        if n >= 2 * period_int and period_int >= 2:
            decomp = decompose_timeseries(data, period=period_int)
            if "error" not in decomp:
                strength = decomp.get("seasonal_strength")

    return {
        "detected_period": detected["period"] if detected else None,
        "seasonality_strength": strength,
        "top_candidates": top_candidates,
        "n_observations": n,
        "max_period_searched": max_period,
    }


def rolling_statistics(data: Union[List, Dict, pd.Series],
                       window: int = 20,
                       metrics: Optional[List[str]] = None) -> Dict:
    """
    Compute rolling statistics for regime detection and trading signals.

    Args:
        data: Time series data
        window: Rolling window size
        metrics: List of metrics to compute (default: all).
                 Options: 'mean', 'std', 'zscore', 'skew', 'kurt', 'sharpe'

    Returns:
        Dict with rolling metric arrays and regime classification.
    """
    series = _to_series(data)
    values = series.values
    n = len(values)

    if n < window + 1:
        return {"error": f"Need at least {window + 1} data points", "n": n, "window": window}

    if metrics is None:
        metrics = ["mean", "std", "zscore", "skew", "sharpe"]

    s = pd.Series(values)
    result = {"window": window, "n_observations": n}

    if "mean" in metrics:
        rm = s.rolling(window).mean()
        result["rolling_mean"] = [round(float(v), 4) if not np.isnan(v) else None for v in rm]

    if "std" in metrics:
        rs = s.rolling(window).std()
        result["rolling_std"] = [round(float(v), 4) if not np.isnan(v) else None for v in rs]

    if "zscore" in metrics:
        rm = s.rolling(window).mean()
        rs = s.rolling(window).std()
        z = (s - rm) / rs.replace(0, np.nan)
        result["rolling_zscore"] = [round(float(v), 4) if not np.isnan(v) else None for v in z]

    if "skew" in metrics:
        rsk = s.rolling(window).skew()
        result["rolling_skew"] = [round(float(v), 4) if not np.isnan(v) else None for v in rsk]

    if "kurt" in metrics:
        rk = s.rolling(window).kurt()
        result["rolling_kurt"] = [round(float(v), 4) if not np.isnan(v) else None for v in rk]

    if "sharpe" in metrics:
        returns = s.pct_change()
        rm_ret = returns.rolling(window).mean()
        rs_ret = returns.rolling(window).std()
        sharpe = (rm_ret / rs_ret.replace(0, np.nan)) * np.sqrt(252)
        result["rolling_sharpe"] = [round(float(v), 4) if not np.isnan(v) else None for v in sharpe]

    # Regime classification based on rolling z-score
    if "zscore" in metrics:
        z_vals = np.array([v if v is not None else 0 for v in result["rolling_zscore"]])
        current_z = z_vals[-1] if len(z_vals) > 0 else 0
        if current_z > 2:
            regime = "overbought"
        elif current_z > 1:
            regime = "trending_up"
        elif current_z < -2:
            regime = "oversold"
        elif current_z < -1:
            regime = "trending_down"
        else:
            regime = "neutral"
        result["current_regime"] = regime
        result["current_zscore"] = round(float(current_z), 4)

    return result


def _detect_period(series: pd.Series) -> Optional[int]:
    """Auto-detect dominant seasonal period using FFT."""
    values = series.values
    n = len(values)
    if n < 10:
        return None

    detrended = values - np.linspace(values[0], values[-1], n)
    fft = np.fft.rfft(detrended)
    power = np.abs(fft) ** 2

    best_period = None
    best_power = 0
    for i in range(1, len(power)):
        period = n / i
        if 2 <= period <= n // 3 and power[i] > best_power:
            best_power = power[i]
            best_period = int(round(period))

    return best_period


if __name__ == "__main__":
    # Quick self-test with synthetic data
    np.random.seed(42)
    t = np.arange(100)
    data = 50 + 0.3 * t + 10 * np.sin(2 * np.pi * t / 20) + np.random.normal(0, 2, 100)
    data_list = data.tolist()

    print("=== Forecast ===")
    print(json.dumps(forecast_timeseries(data_list, steps=5), indent=2))

    print("\n=== Anomalies ===")
    noisy = data_list.copy()
    noisy[50] = 200  # inject spike
    print(json.dumps(detect_anomalies(noisy), indent=2))

    print("\n=== Changepoints ===")
    shifted = data_list[:50] + [v + 30 for v in data_list[50:]]
    print(json.dumps(detect_changepoints(shifted), indent=2))

    print("\n=== Decomposition ===")
    d = decompose_timeseries(data_list, period=20)
    print(f"Trend strength: {d.get('trend_strength')}, Seasonal: {d.get('seasonal_strength')}")

    print("\n=== Ensemble ===")
    e = ensemble_forecast(data_list, steps=5)
    print(json.dumps({k: v for k, v in e.items() if k != "individual_forecasts"}, indent=2))
