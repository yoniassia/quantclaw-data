#!/usr/bin/env python3
"""
Darts Time Series Forecasting Library
Darts is an open-source Python library for time series forecasting, supporting classical 
and deep learning models for financial data analysis. Enables ML pipelines for predicting 
stock prices, volatility, or economic indicators.

Source: https://unit8co.github.io/darts/
Category: Quant Tools & ML
Free tier: True (open-source)
Update frequency: Library (monthly GitHub updates)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

try:
    from darts import TimeSeries
    from darts.models import Prophet, ExponentialSmoothing, ARIMA, NaiveSeasonal
    from darts.metrics import mape, rmse, mae
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False


def forecast_price(symbol: str, data: pd.DataFrame, periods: int = 10, 
                   model_type: str = 'prophet') -> Dict:
    """
    Forecast future prices using Darts time series models.
    
    Args:
        symbol: Stock ticker symbol
        data: DataFrame with 'date' and 'close' columns
        periods: Number of periods to forecast
        model_type: Model to use ('prophet', 'arima', 'ets', 'naive')
    
    Returns:
        Dict with forecast values, confidence intervals, and metrics
    """
    if not DARTS_AVAILABLE:
        return {
            'error': 'darts library not installed. Install with: pip install darts',
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
    
    try:
        # Convert to Darts TimeSeries
        if 'date' not in data.columns or 'close' not in data.columns:
            return {'error': 'DataFrame must have date and close columns'}
        
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date')
        
        ts = TimeSeries.from_dataframe(
            data, 
            time_col='date', 
            value_cols='close',
            fill_missing_dates=True
        )
        
        # Split train/test
        train_size = int(len(ts) * 0.8)
        train, test = ts[:train_size], ts[train_size:]
        
        # Select and fit model
        if model_type == 'prophet':
            model = Prophet()
        elif model_type == 'arima':
            model = ARIMA(p=5, d=1, q=2)
        elif model_type == 'ets':
            model = ExponentialSmoothing()
        elif model_type == 'naive':
            model = NaiveSeasonal(K=5)
        else:
            return {'error': f'Unknown model type: {model_type}'}
        
        model.fit(train)
        
        # Forecast
        forecast = model.predict(n=periods)
        
        # Backtest on test set if available
        metrics = {}
        if len(test) > 0:
            backtest_pred = model.predict(n=len(test))
            metrics = {
                'mape': float(mape(test, backtest_pred)),
                'rmse': float(rmse(test, backtest_pred)),
                'mae': float(mae(test, backtest_pred))
            }
        
        # Extract forecast values
        forecast_df = forecast.pd_dataframe()
        forecast_values = forecast_df['close'].tolist()
        forecast_dates = [d.isoformat() for d in forecast_df.index]
        
        return {
            'symbol': symbol,
            'model': model_type,
            'forecast_horizon': periods,
            'forecast_dates': forecast_dates,
            'forecast_values': forecast_values,
            'last_actual_price': float(ts.last_value()),
            'last_actual_date': ts.end_time().isoformat(),
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'symbol': symbol,
            'model': model_type,
            'timestamp': datetime.now().isoformat()
        }


def forecast_volatility(symbol: str, returns: pd.DataFrame, periods: int = 10) -> Dict:
    """
    Forecast volatility using Darts models on return series.
    
    Args:
        symbol: Stock ticker
        returns: DataFrame with 'date' and 'returns' columns
        periods: Forecast horizon
    
    Returns:
        Dict with volatility forecast
    """
    if not DARTS_AVAILABLE:
        return {'error': 'darts library not installed'}
    
    try:
        returns = returns.copy()
        returns['date'] = pd.to_datetime(returns['date'])
        returns = returns.sort_values('date')
        
        # Calculate rolling volatility
        returns['volatility'] = returns['returns'].rolling(window=20).std() * np.sqrt(252)
        returns = returns.dropna()
        
        ts = TimeSeries.from_dataframe(
            returns,
            time_col='date',
            value_cols='volatility'
        )
        
        # Fit ETS model (good for volatility)
        model = ExponentialSmoothing()
        model.fit(ts)
        
        forecast = model.predict(n=periods)
        forecast_df = forecast.pd_dataframe()
        
        return {
            'symbol': symbol,
            'metric': 'annualized_volatility',
            'forecast_horizon': periods,
            'forecast_dates': [d.isoformat() for d in forecast_df.index],
            'forecast_values': forecast_df['volatility'].tolist(),
            'current_volatility': float(ts.last_value()),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}


def get_model_info() -> Dict:
    """
    Get available Darts models and their characteristics.
    
    Returns:
        Dict with model catalog and installation status
    """
    models = {
        'prophet': {
            'name': 'Prophet (Facebook)',
            'type': 'additive',
            'use_case': 'trend + seasonality',
            'speed': 'medium',
            'hyperparameters': ['growth', 'changepoint_prior_scale', 'seasonality_prior_scale']
        },
        'arima': {
            'name': 'ARIMA',
            'type': 'statistical',
            'use_case': 'stationary series',
            'speed': 'fast',
            'hyperparameters': ['p', 'd', 'q']
        },
        'ets': {
            'name': 'Exponential Smoothing',
            'type': 'smoothing',
            'use_case': 'level + trend + seasonality',
            'speed': 'fast',
            'hyperparameters': ['seasonal_periods']
        },
        'naive_seasonal': {
            'name': 'Naive Seasonal',
            'type': 'baseline',
            'use_case': 'simple benchmark',
            'speed': 'instant',
            'hyperparameters': ['K (seasonal period)']
        }
    }
    
    return {
        'library': 'Darts',
        'version_check': DARTS_AVAILABLE,
        'models': models,
        'install_cmd': 'pip install darts',
        'documentation': 'https://unit8co.github.io/darts/',
        'timestamp': datetime.now().isoformat()
    }


# Demo function for testing
def demo_forecast():
    """
    Demo function showing Darts usage with synthetic financial data.
    """
    if not DARTS_AVAILABLE:
        return {'error': 'darts not installed'}
    
    # Generate synthetic price data
    dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
    np.random.seed(42)
    trend = np.linspace(100, 120, 252)
    noise = np.random.normal(0, 2, 252)
    prices = trend + noise + 5 * np.sin(np.linspace(0, 8*np.pi, 252))
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    result = forecast_price('DEMO', data, periods=30, model_type='prophet')
    return result


if __name__ == '__main__':
    import json
    
    # Run demo
    info = get_model_info()
    print(json.dumps(info, indent=2))
    
    if DARTS_AVAILABLE:
        print("\n=== Running Demo Forecast ===")
        demo = demo_forecast()
        print(json.dumps(demo, indent=2))
    else:
        print("\nInstall darts to run forecasts: pip install darts")
