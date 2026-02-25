# Neural Price Prediction - Phase 85

**LSTM and Statistical Models for Multi-Horizon Forecasting with Uncertainty Quantification**

## Overview

The Neural Price Prediction module provides sophisticated price forecasting capabilities using both machine learning (LSTM-style) and statistical models (ARIMA, baselines). It offers multi-horizon predictions (1-day, 5-day, 20-day) with proper uncertainty quantification through confidence intervals.

## Features

### 1. **LSTM-Style Price Forecasting**
- Exponentially-weighted sequence-based prediction
- Momentum and trend detection
- Multi-step ahead forecasting with dampening

### 2. **Statistical Baselines**
- **ARIMA (AR model)**: Autoregressive forecasting with lag analysis
- **Naive baseline**: Last price persistence with volatility bands
- **Moving Average**: Simple rolling average prediction

### 3. **Uncertainty Quantification**
- 95% confidence intervals for all predictions
- Model disagreement analysis
- Uncertainty scoring (0-100 scale)
- Confidence levels (HIGH/MEDIUM/LOW)

### 4. **Model Comparison**
- Side-by-side comparison of all models
- Ranking by confidence interval width
- Transparent performance metrics

### 5. **Walk-Forward Backtesting**
- Historical accuracy validation
- Mean Absolute Error (MAE) tracking
- Confidence interval coverage testing
- Best model identification

## CLI Commands

### 1. Price Prediction
```bash
python cli.py predict-price AAPL --horizon 5d
```
**Output:**
- Current price
- Multi-day price forecasts
- 95% confidence intervals
- Percentage change predictions

**Horizons:** `1d`, `5d`, `20d`

### 2. Uncertainty Analysis
```bash
python cli.py prediction-confidence TSLA
```
**Output:**
- Uncertainty scores by horizon
- Model agreement/disagreement metrics
- LSTM vs ARIMA comparison
- Overall confidence rating

### 3. Model Comparison
```bash
python cli.py model-comparison NVDA
```
**Output:**
- Ranked model performance
- 5-day predictions from all models
- Confidence interval widths
- Best performing model highlighted

### 4. Historical Backtest
```bash
python cli.py prediction-backtest MSFT --years 1
```
**Output:**
- Walk-forward validation results
- Mean Absolute Error (MAE) percentages
- Confidence interval coverage
- Best model identification

## API Endpoints

### Price Forecast
```
GET /api/v1/neural-prediction?action=predict&ticker=AAPL&horizon=5d
```

### Uncertainty Analysis
```
GET /api/v1/neural-prediction?action=confidence&ticker=TSLA
```

### Model Comparison
```
GET /api/v1/neural-prediction?action=comparison&ticker=NVDA
```

### Backtest
```
GET /api/v1/neural-prediction?action=backtest&ticker=MSFT&years=1
```

## Technical Details

### Data Source
- **Yahoo Finance (yfinance)**: Historical price data
- **Lookback Period**: 252 trading days (1 year) default

### Models

#### LSTM-Style Predictor
- Sequence length: 20 days
- Exponential weighting for recent data emphasis
- Momentum-based extrapolation with dampening
- Normalized inputs for stability

#### ARIMA Model
- AR(5) autoregressive model
- Least squares coefficient estimation
- Lag-based prediction
- Residual variance for confidence intervals

#### Naive Baseline
- Last-price-carries-forward assumption
- Historical volatility for uncertainty bands

#### Moving Average Baseline
- 20-day simple moving average
- Rolling volatility estimates

### Uncertainty Quantification

All models provide:
- **95% Confidence Intervals**: Based on historical volatility and model residuals
- **Expanding Intervals**: Wider bands for longer horizons
- **Model Disagreement**: Percentage difference between LSTM and ARIMA predictions
- **Uncertainty Score**: Composite metric (0-100) combining CI width and model disagreement

## Performance Considerations

- **Execution Time**: ~2-5 seconds per forecast
- **Memory Usage**: Minimal (~50MB peak)
- **Data Requirements**: Minimum 50 days of historical data recommended
- **Backtest Duration**: ~30-60 seconds for 1-year backtest

## Interpretation Guide

### Confidence Levels
- **HIGH**: Uncertainty score < 20, models agree closely
- **MEDIUM**: Uncertainty score 20-50, moderate disagreement
- **LOW**: Uncertainty score > 50, significant disagreement or wide CIs

### Best Use Cases
- **Short-term forecasts (1-5 days)**: Most accurate
- **Comparative analysis**: Evaluate model agreement
- **Risk assessment**: Use CI width for position sizing
- **Strategy validation**: Backtest to verify predictive power

### Limitations
- **Not financial advice**: Predictions are probabilistic, not guarantees
- **Market regime changes**: Models may underperform in high volatility
- **Fundamental events**: Cannot predict earnings surprises, news shocks
- **Overfitting risk**: LSTM implementation is simplified to avoid overfitting

## Example Outputs

### Prediction Output
```
Current Price: $272.14
5-Day Forecast:
Day 1: $279.20 (+2.59%) [CI: $223.02 - $335.37]
Day 2: $285.55 (+4.93%) [CI: $206.10 - $364.99]
...
```

### Uncertainty Analysis
```
Overall Confidence: MEDIUM
1d Horizon: Uncertainty 45/100 (MEDIUM)
5d Horizon: Uncertainty 62/100 (LOW)
Model Disagreement: ±5.2%
```

### Backtest Results
```
Best Model: ARIMA
- MAE: 2.38%
- Median Error: 1.75%
- CI Coverage: 92.3%
```

## Dependencies

- `yfinance`: Yahoo Finance data
- `numpy`: Numerical operations
- `pandas`: Data manipulation
- `scipy`: Statistical functions

## Future Enhancements

Potential improvements for future phases:
- True LSTM/Transformer models (TensorFlow/PyTorch)
- Attention mechanisms for feature importance
- Ensemble methods combining multiple approaches
- Real-time model retraining
- Sentiment integration from news/social data
- Regime-aware model switching
- Options-implied volatility incorporation

## Notes

This implementation prioritizes:
1. **Simplicity**: No heavy ML dependencies
2. **Interpretability**: Clear uncertainty quantification
3. **Reliability**: Statistical baselines for comparison
4. **Speed**: Fast execution for real-time use

For production deep learning models, consider integrating TensorFlow or PyTorch in future iterations.
