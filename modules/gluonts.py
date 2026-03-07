#!/usr/bin/env python3
"""
GluonTS — Probabilistic Time Series Forecasting Module

Open-source toolkit for probabilistic time series modeling using deep learning.
Supports models like DeepAR, Transformer, SimpleFeedForward for financial forecasting.
Provides graceful fallback to statistical methods when GluonTS is not installed.

Source: https://ts.gluon.ai/
Category: Quant Tools & ML
Free tier: True (pip install gluonts)
Author: QuantClaw Data NightBuilder
Phase: 108
"""

import json
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import numpy as np

# Try to import GluonTS - graceful fallback if not installed
GLUONTS_AVAILABLE = False
try:
    from gluonts.dataset.common import ListDataset
    from gluonts.model.deepar import DeepAREstimator
    from gluonts.model.simple_feedforward import SimpleFeedForwardEstimator
    from gluonts.model.transformer import TransformerEstimator
    from gluonts.mx.trainer import Trainer
    from gluonts.evaluation import make_evaluation_predictions, Evaluator
    GLUONTS_AVAILABLE = True
except ImportError:
    warnings.warn("GluonTS not installed. Using statistical fallback mode. Install with: pip install gluonts mxnet", UserWarning)

# ========== CONFIGURATION ==========

AVAILABLE_ESTIMATORS = {
    'deepar': 'DeepAR - Autoregressive RNN for probabilistic forecasting',
    'transformer': 'Transformer - Attention-based forecasting model',
    'feedforward': 'SimpleFeedForward - Basic neural network estimator',
    'statistical': 'Statistical - Fallback moving average method (no GluonTS required)'
}

DEFAULT_FREQ = '1D'  # Daily frequency
DEFAULT_PREDICTION_LENGTH = 30
DEFAULT_EPOCHS = 5

# ========== HELPER FUNCTIONS ==========

def _statistical_forecast(data: List[float], prediction_length: int) -> Dict[str, Any]:
    """
    Fallback statistical forecast using moving average and trend.
    Used when GluonTS is not available.
    """
    if len(data) < 2:
        return {
            'error': 'Insufficient data for statistical forecast',
            'mean': [],
            'quantiles': {}
        }
    
    # Simple moving average with trend
    window = min(7, len(data))
    recent = data[-window:]
    ma = np.mean(recent)
    
    # Linear trend
    if len(data) >= 3:
        x = np.arange(len(data))
        y = np.array(data)
        trend = np.polyfit(x[-window:], y[-window:], 1)[0]
    else:
        trend = 0
    
    # Generate forecast
    forecast = []
    std = np.std(recent) if len(recent) > 1 else ma * 0.1
    
    for i in range(prediction_length):
        point = ma + trend * (i + 1)
        forecast.append(float(point))
    
    # Simple quantiles (normal approximation)
    quantiles = {
        '0.1': [f - 1.28 * std for f in forecast],
        '0.5': forecast,
        '0.9': [f + 1.28 * std for f in forecast]
    }
    
    return {
        'mean': forecast,
        'quantiles': quantiles,
        'method': 'statistical_fallback',
        'std': float(std)
    }

# ========== CORE FUNCTIONS ==========

def list_available_estimators() -> Dict[str, str]:
    """
    List all available forecasting estimators.
    
    Returns:
        Dictionary of estimator names and descriptions
    """
    estimators = AVAILABLE_ESTIMATORS.copy()
    if not GLUONTS_AVAILABLE:
        estimators = {k: v for k, v in estimators.items() if k == 'statistical'}
        estimators['note'] = 'GluonTS not installed - only statistical fallback available'
    
    return {
        'estimators': estimators,
        'gluonts_available': GLUONTS_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    }

def create_dataset_from_prices(
    prices_dict: Dict[str, List[float]],
    freq: str = DEFAULT_FREQ,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create GluonTS dataset from price dictionary.
    
    Args:
        prices_dict: Dictionary with 'ticker' -> list of prices
        freq: Frequency string (e.g., '1D', '1H', '5min')
        start_date: Start date (ISO format), defaults to today - len(prices)
        
    Returns:
        Dictionary with dataset info or error
    """
    try:
        if not prices_dict:
            return {'error': 'Empty prices dictionary provided'}
        
        datasets = []
        for ticker, prices in prices_dict.items():
            if not prices or len(prices) == 0:
                continue
                
            if start_date is None:
                from datetime import timedelta
                start = datetime.now() - timedelta(days=len(prices))
            else:
                start = datetime.fromisoformat(start_date)
            
            dataset_entry = {
                'ticker': ticker,
                'target': prices,
                'start': start.isoformat(),
                'freq': freq,
                'length': len(prices)
            }
            datasets.append(dataset_entry)
        
        return {
            'dataset': datasets,
            'num_series': len(datasets),
            'freq': freq,
            'gluonts_available': GLUONTS_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Failed to create dataset: {str(e)}'}

def forecast_timeseries(
    dataset: Dict[str, Any],
    prediction_length: int = DEFAULT_PREDICTION_LENGTH,
    estimator_type: str = 'statistical',
    epochs: int = DEFAULT_EPOCHS
) -> Dict[str, Any]:
    """
    Forecast time series using specified estimator.
    
    Args:
        dataset: Dataset created by create_dataset_from_prices()
        prediction_length: Number of steps to forecast
        estimator_type: Type of estimator ('deepar', 'transformer', 'feedforward', 'statistical')
        epochs: Training epochs (ignored for statistical)
        
    Returns:
        Dictionary with forecasts or error
    """
    try:
        if 'error' in dataset:
            return dataset
        
        if 'dataset' not in dataset or not dataset['dataset']:
            return {'error': 'Invalid dataset format'}
        
        forecasts = []
        
        for series in dataset['dataset']:
            ticker = series['ticker']
            target = series['target']
            
            # Use statistical fallback if GluonTS not available or requested
            if not GLUONTS_AVAILABLE or estimator_type == 'statistical':
                forecast = _statistical_forecast(target, prediction_length)
                forecast['ticker'] = ticker
                forecasts.append(forecast)
            else:
                # GluonTS forecasting
                try:
                    # Create GluonTS dataset
                    train_ds = ListDataset(
                        [{'target': target, 'start': series['start']}],
                        freq=series['freq']
                    )
                    
                    # Select estimator
                    if estimator_type == 'deepar':
                        estimator = DeepAREstimator(
                            freq=series['freq'],
                            prediction_length=prediction_length,
                            trainer=Trainer(epochs=epochs)
                        )
                    elif estimator_type == 'transformer':
                        estimator = TransformerEstimator(
                            freq=series['freq'],
                            prediction_length=prediction_length,
                            trainer=Trainer(epochs=epochs)
                        )
                    else:  # feedforward
                        estimator = SimpleFeedForwardEstimator(
                            freq=series['freq'],
                            prediction_length=prediction_length,
                            trainer=Trainer(epochs=epochs)
                        )
                    
                    predictor = estimator.train(train_ds)
                    forecast_iter = predictor.predict(train_ds)
                    forecast_obj = list(forecast_iter)[0]
                    
                    forecasts.append({
                        'ticker': ticker,
                        'mean': forecast_obj.mean.tolist(),
                        'quantiles': {
                            '0.1': forecast_obj.quantile(0.1).tolist(),
                            '0.5': forecast_obj.quantile(0.5).tolist(),
                            '0.9': forecast_obj.quantile(0.9).tolist()
                        },
                        'method': estimator_type
                    })
                except Exception as e:
                    # Fallback to statistical on GluonTS error
                    forecast = _statistical_forecast(target, prediction_length)
                    forecast['ticker'] = ticker
                    forecast['fallback_reason'] = str(e)
                    forecasts.append(forecast)
        
        return {
            'forecasts': forecasts,
            'prediction_length': prediction_length,
            'estimator': estimator_type,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Forecast failed: {str(e)}'}

def train_deepar_model(
    dataset: Dict[str, Any],
    prediction_length: int = DEFAULT_PREDICTION_LENGTH,
    epochs: int = DEFAULT_EPOCHS
) -> Dict[str, Any]:
    """
    Train a DeepAR model on the provided dataset.
    
    Args:
        dataset: Dataset created by create_dataset_from_prices()
        prediction_length: Number of steps to forecast
        epochs: Training epochs
        
    Returns:
        Dictionary with training info and model performance
    """
    if not GLUONTS_AVAILABLE:
        return {'error': 'GluonTS not installed. Use forecast_timeseries() with estimator_type="statistical"'}
    
    return forecast_timeseries(dataset, prediction_length, 'deepar', epochs)

def evaluate_forecast(
    forecast: Dict[str, Any],
    actual: List[float]
) -> Dict[str, Any]:
    """
    Evaluate forecast accuracy against actual values.
    
    Args:
        forecast: Forecast dictionary from forecast_timeseries()
        actual: Actual observed values
        
    Returns:
        Dictionary with evaluation metrics
    """
    try:
        if 'error' in forecast:
            return forecast
        
        if 'forecasts' not in forecast or not forecast['forecasts']:
            return {'error': 'Invalid forecast format'}
        
        results = []
        
        for fc in forecast['forecasts']:
            if 'mean' not in fc:
                continue
            
            predicted = np.array(fc['mean'])
            observed = np.array(actual[:len(predicted)])
            
            if len(observed) == 0:
                continue
            
            # Calculate metrics
            mae = np.mean(np.abs(predicted - observed))
            mse = np.mean((predicted - observed) ** 2)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((observed - predicted) / observed)) * 100 if np.all(observed != 0) else None
            
            results.append({
                'ticker': fc.get('ticker', 'unknown'),
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'mape': float(mape) if mape is not None else None,
                'samples': len(observed)
            })
        
        return {
            'evaluation': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Evaluation failed: {str(e)}'}

def generate_sample_dataset(
    ticker: str = 'SAMPLE',
    periods: int = 100
) -> Dict[str, Any]:
    """
    Generate a sample dataset for testing.
    
    Args:
        ticker: Ticker symbol for the sample
        periods: Number of data points to generate
        
    Returns:
        Dictionary with sample dataset
    """
    try:
        # Generate synthetic price data with trend and noise
        np.random.seed(42)
        trend = np.linspace(100, 120, periods)
        noise = np.random.normal(0, 2, periods)
        prices = (trend + noise).tolist()
        
        return create_dataset_from_prices(
            {ticker: prices},
            freq=DEFAULT_FREQ
        )
        
    except Exception as e:
        return {'error': f'Failed to generate sample: {str(e)}'}

# ========== MAIN ENTRY POINT ==========

if __name__ == "__main__":
    # Demo usage
    print("=== GluonTS Module Demo ===\n")
    
    # List estimators
    estimators = list_available_estimators()
    print("Available Estimators:")
    print(json.dumps(estimators, indent=2))
    print()
    
    # Generate sample data
    print("Generating sample dataset...")
    dataset = generate_sample_dataset('AAPL', 90)
    if 'error' not in dataset:
        print(f"✓ Created dataset with {dataset['num_series']} series")
        print()
        
        # Forecast
        print("Running forecast...")
        forecast = forecast_timeseries(dataset, prediction_length=10)
        if 'error' not in forecast:
            print(f"✓ Generated {len(forecast['forecasts'])} forecasts")
            for fc in forecast['forecasts']:
                print(f"  {fc['ticker']}: {len(fc['mean'])} predictions (method: {fc.get('method', 'unknown')})")
            print()
            
            # Evaluate (using last 10 points as "actual")
            sample_actual = dataset['dataset'][0]['target'][-10:]
            eval_result = evaluate_forecast(forecast, sample_actual)
            if 'error' not in eval_result:
                print("Evaluation Metrics:")
                print(json.dumps(eval_result, indent=2))
        else:
            print(f"✗ Forecast error: {forecast['error']}")
    else:
        print(f"✗ Dataset error: {dataset['error']}")
