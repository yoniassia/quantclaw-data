#!/usr/bin/env python3
"""
Darts Time Series Forecasting — QuantClaw Data Module

Provides time series forecasting capabilities using the Darts library.
Supports classical models (Exponential Smoothing, Theta, ARIMA, FFT)
and basic ML models for financial time series prediction.

Source: https://unit8co.github.io/darts/
Category: Quant Tools & ML
Free tier: True (open-source library, no API keys)
Update frequency: N/A (local computation)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union


def _ensure_darts():
    """Lazy import darts to avoid startup cost."""
    try:
        import darts
        return True
    except ImportError:
        return False


def _prices_to_timeseries(prices: List[float], start_date: str = None, freq: str = "B"):
    """
    Convert a list of prices into a Darts TimeSeries object.

    Args:
        prices: List of float prices (chronological order).
        start_date: ISO date string for first data point (default: generates sequential index).
        freq: Pandas frequency string ('B'=business day, 'D'=daily, 'W'=weekly, 'M'=monthly).

    Returns:
        darts.TimeSeries object.
    """
    from darts import TimeSeries

    n = len(prices)
    # Use daily freq for index generation to avoid business-day alignment issues
    if start_date:
        idx = pd.date_range(start=start_date, periods=n, freq="D")
    else:
        idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="D")

    df = pd.DataFrame({"price": prices}, index=idx)
    # Let darts infer frequency from the regular daily index
    return TimeSeries.from_dataframe(df, value_cols="price", freq="D")


def forecast_exponential_smoothing(
    prices: List[float],
    horizon: int = 10,
    seasonal_periods: Optional[int] = None,
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Forecast future values using Exponential Smoothing (Holt-Winters).

    Args:
        prices: Historical price series (list of floats, chronological).
        horizon: Number of periods to forecast.
        seasonal_periods: Seasonal period length (e.g., 5 for weekly on business days, 21 for monthly).
        start_date: ISO start date for the series.
        freq: Frequency string ('B', 'D', 'W', 'M').

    Returns:
        Dict with forecast values, dates, model info, and metadata.

    Example:
        >>> result = forecast_exponential_smoothing([100, 102, 101, 103, 105, 104, 106], horizon=5)
        >>> print(result['forecast'])
    """
    try:
        from darts.models import ExponentialSmoothing

        if len(prices) < 3:
            return {"error": "Need at least 3 data points", "min_required": 3}

        series = _prices_to_timeseries(prices, start_date, freq)
        model = ExponentialSmoothing(seasonal_periods=seasonal_periods)
        model.fit(series)
        prediction = model.predict(horizon)

        forecast_values = prediction.values().flatten().tolist()
        forecast_dates = [str(t) for t in prediction.time_index]

        return {
            "model": "ExponentialSmoothing",
            "input_length": len(prices),
            "horizon": horizon,
            "forecast": forecast_values,
            "forecast_dates": forecast_dates,
            "last_price": prices[-1],
            "forecast_mean": round(float(np.mean(forecast_values)), 4),
            "forecast_trend": "up" if forecast_values[-1] > prices[-1] else "down",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "model": "ExponentialSmoothing"}


def forecast_theta(
    prices: List[float],
    horizon: int = 10,
    theta: float = 2.0,
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Forecast using the Theta method (robust baseline for financial series).

    Args:
        prices: Historical price series.
        horizon: Forecast horizon.
        theta: Theta parameter (default 2.0, standard Theta method).
        start_date: ISO start date.
        freq: Frequency string.

    Returns:
        Dict with forecast values, dates, and model metadata.

    Example:
        >>> result = forecast_theta([100, 102, 104, 103, 105, 107, 108], horizon=5)
    """
    try:
        from darts.models import Theta

        if len(prices) < 3:
            return {"error": "Need at least 3 data points"}

        series = _prices_to_timeseries(prices, start_date, freq)
        model = Theta(theta=theta)
        model.fit(series)
        prediction = model.predict(horizon)

        forecast_values = prediction.values().flatten().tolist()
        forecast_dates = [str(t) for t in prediction.time_index]

        return {
            "model": "Theta",
            "theta": theta,
            "input_length": len(prices),
            "horizon": horizon,
            "forecast": forecast_values,
            "forecast_dates": forecast_dates,
            "last_price": prices[-1],
            "forecast_mean": round(float(np.mean(forecast_values)), 4),
            "forecast_trend": "up" if forecast_values[-1] > prices[-1] else "down",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "model": "Theta"}


def forecast_fft(
    prices: List[float],
    horizon: int = 10,
    nr_freqs_to_keep: int = 10,
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Forecast using FFT (Fast Fourier Transform) — captures cyclical patterns.

    Args:
        prices: Historical price series.
        horizon: Forecast horizon.
        nr_freqs_to_keep: Number of dominant frequencies to retain.
        start_date: ISO start date.
        freq: Frequency string.

    Returns:
        Dict with forecast values and model info.

    Example:
        >>> result = forecast_fft(list(range(50, 100)), horizon=10)
    """
    try:
        from darts.models import FFT

        if len(prices) < 5:
            return {"error": "Need at least 5 data points for FFT"}

        series = _prices_to_timeseries(prices, start_date, freq)
        model = FFT(nr_freqs_to_keep=nr_freqs_to_keep)
        model.fit(series)
        prediction = model.predict(horizon)

        forecast_values = prediction.values().flatten().tolist()
        forecast_dates = [str(t) for t in prediction.time_index]

        return {
            "model": "FFT",
            "nr_freqs_to_keep": nr_freqs_to_keep,
            "input_length": len(prices),
            "horizon": horizon,
            "forecast": forecast_values,
            "forecast_dates": forecast_dates,
            "last_price": prices[-1],
            "forecast_mean": round(float(np.mean(forecast_values)), 4),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "model": "FFT"}


def forecast_naive(
    prices: List[float],
    horizon: int = 10,
    method: str = "drift",
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Naive/baseline forecast (drift, mean, or last-value).

    Args:
        prices: Historical price series.
        horizon: Forecast horizon.
        method: 'drift' (linear extrapolation), 'mean', or 'last'.
        start_date: ISO start date.
        freq: Frequency string.

    Returns:
        Dict with forecast values (useful as benchmark).

    Example:
        >>> result = forecast_naive([100, 102, 104], horizon=5, method='drift')
    """
    try:
        from darts.models import NaiveDrift, NaiveMean, NaiveSeasonal

        if len(prices) < 2:
            return {"error": "Need at least 2 data points"}

        series = _prices_to_timeseries(prices, start_date, freq)

        if method == "drift":
            model = NaiveDrift()
        elif method == "mean":
            model = NaiveMean()
        elif method == "last":
            model = NaiveSeasonal(K=1)
        else:
            return {"error": f"Unknown method: {method}. Use 'drift', 'mean', or 'last'."}

        model.fit(series)
        prediction = model.predict(horizon)

        forecast_values = prediction.values().flatten().tolist()
        forecast_dates = [str(t) for t in prediction.time_index]

        return {
            "model": f"Naive({method})",
            "input_length": len(prices),
            "horizon": horizon,
            "forecast": forecast_values,
            "forecast_dates": forecast_dates,
            "last_price": prices[-1],
            "forecast_mean": round(float(np.mean(forecast_values)), 4),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "model": f"Naive({method})"}


def compare_forecasts(
    prices: List[float],
    horizon: int = 10,
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Run multiple models and compare their forecasts side-by-side.

    Args:
        prices: Historical price series.
        horizon: Forecast horizon.
        start_date: ISO start date.
        freq: Frequency string.

    Returns:
        Dict with results from each model and a consensus forecast.

    Example:
        >>> result = compare_forecasts([100, 102, 101, 103, 105, 107, 108, 110], horizon=5)
        >>> print(result['consensus'])
    """
    try:
        results = {}
        all_forecasts = []

        for name, fn in [
            ("exponential_smoothing", lambda p, h, s, f: forecast_exponential_smoothing(p, h, start_date=s, freq=f)),
            ("theta", lambda p, h, s, f: forecast_theta(p, h, start_date=s, freq=f)),
            ("fft", lambda p, h, s, f: forecast_fft(p, h, start_date=s, freq=f)),
            ("naive_drift", lambda p, h, s, f: forecast_naive(p, h, "drift", s, f)),
        ]:
            r = fn(prices, horizon, start_date, freq)
            results[name] = r
            if "forecast" in r and "error" not in r:
                all_forecasts.append(r["forecast"])

        # Compute consensus (average of all model forecasts)
        if all_forecasts:
            consensus = np.mean(all_forecasts, axis=0).tolist()
            consensus = [round(v, 4) for v in consensus]
        else:
            consensus = []

        return {
            "models": results,
            "consensus": consensus,
            "num_models": len(all_forecasts),
            "input_length": len(prices),
            "horizon": horizon,
            "last_price": prices[-1],
            "consensus_trend": "up" if consensus and consensus[-1] > prices[-1] else "down",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def backtest_model(
    prices: List[float],
    model_name: str = "theta",
    forecast_horizon: int = 5,
    train_ratio: float = 0.8,
    start_date: str = None,
    freq: str = "B",
) -> Dict[str, Any]:
    """
    Backtest a forecasting model with train/test split and compute error metrics.

    Args:
        prices: Full historical price series.
        model_name: One of 'exponential_smoothing', 'theta', 'fft', 'naive_drift'.
        forecast_horizon: Number of periods to forecast in test.
        train_ratio: Fraction of data used for training (default 0.8).
        start_date: ISO start date.
        freq: Frequency string.

    Returns:
        Dict with MAE, MAPE, RMSE, predicted vs actual values.

    Example:
        >>> result = backtest_model(list(range(100, 150)), model_name='theta', forecast_horizon=5)
        >>> print(f"MAPE: {result.get('mape')}%")
    """
    try:
        n = len(prices)
        if n < 10:
            return {"error": "Need at least 10 data points for backtesting"}

        split = int(n * train_ratio)
        if split < 3 or (n - split) < forecast_horizon:
            return {"error": "Not enough data for the requested train/test split and horizon"}

        train_prices = prices[:split]
        actual = prices[split : split + forecast_horizon]

        model_map = {
            "exponential_smoothing": lambda p, h, s, f: forecast_exponential_smoothing(p, h, start_date=s, freq=f),
            "theta": lambda p, h, s, f: forecast_theta(p, h, start_date=s, freq=f),
            "fft": lambda p, h, s, f: forecast_fft(p, h, start_date=s, freq=f),
            "naive_drift": lambda p, h, s, f: forecast_naive(p, h, "drift", s, f),
        }

        fn = model_map.get(model_name)
        if not fn:
            return {"error": f"Unknown model: {model_name}. Choose from {list(model_map.keys())}"}

        result = fn(train_prices, len(actual), start_date, freq)
        if "error" in result:
            return result

        predicted = result["forecast"][: len(actual)]
        actual_arr = np.array(actual)
        pred_arr = np.array(predicted)

        mae = float(np.mean(np.abs(actual_arr - pred_arr)))
        rmse = float(np.sqrt(np.mean((actual_arr - pred_arr) ** 2)))
        mape = float(np.mean(np.abs((actual_arr - pred_arr) / (actual_arr + 1e-10))) * 100)

        return {
            "model": model_name,
            "train_size": split,
            "test_size": len(actual),
            "forecast_horizon": forecast_horizon,
            "actual": actual,
            "predicted": predicted,
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 2),
            "direction_accuracy": round(
                sum(
                    1
                    for i in range(1, len(actual))
                    if (actual[i] - actual[i - 1]) * (predicted[i] - predicted[i - 1]) > 0
                )
                / max(len(actual) - 1, 1)
                * 100,
                1,
            ),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "model": model_name}


def analyze_seasonality(
    prices: List[float],
    freq: str = "B",
    start_date: str = None,
    max_lag: int = 50,
) -> Dict[str, Any]:
    """
    Detect seasonality and autocorrelation patterns in a price series.

    Args:
        prices: Historical price series.
        freq: Frequency string.
        start_date: ISO start date.
        max_lag: Maximum lag for autocorrelation analysis.

    Returns:
        Dict with detected seasonal periods, autocorrelation values, stationarity info.

    Example:
        >>> result = analyze_seasonality([100 + i % 5 * 2 for i in range(100)])
    """
    try:
        from darts.utils.statistics import check_seasonality, stationarity_tests

        if len(prices) < 20:
            return {"error": "Need at least 20 data points for seasonality analysis"}

        series = _prices_to_timeseries(prices, start_date, freq)

        # Check seasonality at different periods
        seasonal_results = []
        for m in [5, 10, 21, 63, 252]:  # week, 2-week, month, quarter, year (business days)
            if m < len(prices) // 2:
                try:
                    is_seasonal, period = check_seasonality(series, m=m)
                    if is_seasonal:
                        seasonal_results.append({"period": m, "detected_at": period})
                except Exception:
                    pass

        # Basic stationarity check
        try:
            is_stationary, p_value = stationarity_tests(series)
        except Exception:
            is_stationary, p_value = None, None

        # Autocorrelation via numpy
        arr = np.array(prices)
        arr_norm = arr - arr.mean()
        acf_vals = []
        for lag in range(1, min(max_lag, len(arr) // 2)):
            corr = np.corrcoef(arr_norm[:-lag], arr_norm[lag:])[0, 1]
            acf_vals.append({"lag": lag, "correlation": round(float(corr), 4)})

        top_lags = sorted(acf_vals, key=lambda x: abs(x["correlation"]), reverse=True)[:5]

        return {
            "series_length": len(prices),
            "seasonal_periods": seasonal_results,
            "is_stationary": bool(is_stationary) if is_stationary is not None else None,
            "stationarity_pvalue": round(float(p_value), 4) if p_value is not None else None,
            "top_autocorrelations": top_lags,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_model_list() -> List[Dict[str, str]]:
    """
    List all available forecasting models with descriptions.

    Returns:
        List of dicts with model name, type, and description.

    Example:
        >>> models = get_model_list()
        >>> for m in models: print(m['name'])
    """
    return [
        {
            "name": "exponential_smoothing",
            "type": "classical",
            "description": "Holt-Winters exponential smoothing. Good for trending and seasonal data.",
            "min_data_points": 3,
        },
        {
            "name": "theta",
            "type": "classical",
            "description": "Theta method — robust baseline, won M3 competition. Great for financial series.",
            "min_data_points": 3,
        },
        {
            "name": "fft",
            "type": "spectral",
            "description": "Fast Fourier Transform — captures cyclical/periodic patterns.",
            "min_data_points": 5,
        },
        {
            "name": "naive_drift",
            "type": "baseline",
            "description": "Linear drift extrapolation. Useful as benchmark.",
            "min_data_points": 2,
        },
        {
            "name": "naive_mean",
            "type": "baseline",
            "description": "Forecasts the historical mean. Simple benchmark.",
            "min_data_points": 2,
        },
        {
            "name": "naive_last",
            "type": "baseline",
            "description": "Repeats the last value. Random walk benchmark.",
            "min_data_points": 2,
        },
    ]


if __name__ == "__main__":
    print(json.dumps({
        "module": "darts_forecasting",
        "status": "active",
        "source": "https://unit8co.github.io/darts/",
        "models": [m["name"] for m in get_model_list()],
    }, indent=2))
