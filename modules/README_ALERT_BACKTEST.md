# Alert Backtesting Module - Phase 41

## Overview
Test alert strategies historically, measure signal quality, and identify false positive rates. Helps traders validate alert conditions before deploying them in production.

## Features

### 1. Alert Backtesting
- Backtest any technical indicator-based alert condition on historical data
- Measures hit rates at 1-day, 5-day, and 20-day horizons
- Calculates profit factor, Sharpe ratio, and max drawdown
- Provides signal quality score (0-100)

### 2. Signal Quality Analysis
- Tests 10 common alert conditions automatically
- Ranks conditions by quality score
- Shows hit rates, profit factors, and Sharpe ratios
- Identifies best-performing alert strategies for a symbol

### 3. Alert Potential
- Analyzes how frequently different conditions trigger
- Measures volatility metrics (daily std, annualized vol, daily range)
- Helps identify which alerts are worth setting for a symbol

## Supported Technical Indicators

- **RSI**: `rsi<30`, `rsi>70`, etc.
- **MACD**: `macd>macd_signal`, `macd<macd_signal`, `macd>0`, etc.
- **Bollinger Bands**: `close<bb_lower`, `close>bb_upper`, `price>bb_lower`, etc.
- **Moving Averages**: `close>sma_50`, `price<sma_200`, etc.
- **Volume**: `volume_ratio>2`, `volume_ratio>3`, etc.

## CLI Usage

### Backtest a Specific Alert Condition
```bash
python cli.py alert-backtest AAPL --condition "rsi<30" --period 1y
python cli.py alert-backtest TSLA --condition "macd>macd_signal" --period 6mo
python cli.py alert-backtest NVDA --condition "close<bb_lower" --period 2y
```

### Analyze Signal Quality (Test Multiple Conditions)
```bash
python cli.py signal-quality AAPL --period 1y
python cli.py signal-quality MSFT --period 2y
```

### Check Alert Potential (Trigger Frequency)
```bash
python cli.py alert-potential GOOGL --period 1y
python cli.py alert-potential SPY --period 6mo
```

## API Usage

### Endpoint: `/api/v1/alert-backtest`

**Backtest a condition:**
```bash
GET /api/v1/alert-backtest?symbol=AAPL&condition=rsi<30&period=1y&action=backtest
```

**Signal quality analysis:**
```bash
GET /api/v1/alert-backtest?symbol=AAPL&period=1y&action=signal-quality
```

**Alert potential:**
```bash
GET /api/v1/alert-backtest?symbol=AAPL&period=1y&action=alert-potential
```

**POST request (for complex conditions):**
```bash
curl -X POST http://localhost:3030/api/v1/alert-backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "condition": "rsi<30",
    "period": "1y",
    "action": "backtest"
  }'
```

## Response Format

### Backtest Response
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "condition": "rsi<30",
    "total_signals": 24,
    "hit_rate_1d": 0.625,
    "hit_rate_5d": 0.708,
    "hit_rate_20d": 0.833,
    "false_positive_rate": 0.375,
    "avg_win": 1.45,
    "avg_loss": -0.89,
    "profit_factor": 2.31,
    "signal_quality_score": 72.5,
    "sharpe_ratio": 1.84,
    "max_drawdown": 0.0523,
    "signals": [...]
  }
}
```

### Signal Quality Response
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "period": "1y",
    "conditions_tested": 10,
    "conditions_with_signals": 8,
    "top_conditions": [
      {
        "condition": "rsi<30",
        "signals": 24,
        "hit_rate_1d": 0.625,
        "profit_factor": 2.31,
        "quality_score": 72.5,
        "sharpe": 1.84
      },
      ...
    ]
  }
}
```

## Metrics Explained

- **Hit Rate**: Percentage of signals where price moved in expected direction
- **Profit Factor**: (Total wins) / (Total losses). > 1.0 is profitable
- **Signal Quality Score**: Weighted score (0-100) combining hit rate, profit factor, and consistency
- **Sharpe Ratio**: Risk-adjusted return metric. > 1.0 is good, > 2.0 is excellent
- **Max Drawdown**: Largest peak-to-trough decline in cumulative returns
- **False Positive Rate**: 1 - Hit Rate (signals that fired but moved wrong direction)

## Quality Score Calculation

```python
hit_rate_score = hit_rate * 40  # 40% weight
pf_score = min(profit_factor / 3.0, 1.0) * 30  # 30% weight, capped at 3.0
consistency_score = (1 - abs(hit_rate_5d - hit_rate_1d)) * 30  # 30% weight
signal_quality_score = hit_rate_score + pf_score + consistency_score
```

## Interpretation Guide

### Signal Quality Score Ranges
- **80-100**: Excellent - Deploy with confidence
- **60-79**: Good - Worth using with monitoring
- **40-59**: Mediocre - Use with caution or additional filters
- **< 40**: Poor - Avoid or combine with other indicators

### Profit Factor Interpretation
- **> 2.0**: Strong edge
- **1.5 - 2.0**: Solid edge
- **1.0 - 1.5**: Slight edge
- **< 1.0**: Losing strategy

## Example Workflow

```bash
# 1. Check alert potential for a symbol
python cli.py alert-potential AAPL --period 1y

# 2. Analyze which conditions work best
python cli.py signal-quality AAPL --period 1y

# 3. Backtest the best condition in detail
python cli.py alert-backtest AAPL --condition "rsi<30" --period 1y

# 4. Deploy the validated alert
# (Use Phase 40 Smart Alerts module)
```

## Technical Details

- **Data Source**: Yahoo Finance via yfinance
- **Indicators Calculated**: RSI (14-period), MACD (12,26,9), Bollinger Bands (20,2), SMAs (20,50,200), Volume ratios
- **Forward Returns**: 1-day, 5-day, and 20-day holding periods
- **Direction Detection**: Automatically determines long/short bias from condition
- **Lines of Code**: ~550

## Files

- `modules/alert_backtest.py` - Core backtesting logic
- `src/app/api/v1/alert-backtest/route.ts` - API route
- `cli.py` - Command dispatcher (updated)
- `src/app/services.ts` - Service registry (updated)
- `src/app/roadmap.ts` - Phase 41 marked as "done"

## Next Steps

- Phase 42: Custom Alert DSL for complex multi-condition rules
- Phase 80: Alert Backtesting Dashboard with visualizations
- Integration with Phase 10 (Smart Alerts) for auto-validation before deployment

## Testing

Run the test suite:
```bash
./test_alert_backtest.sh
```

## Notes

- API endpoint requires Next.js dev server restart to become active
- Uses free APIs only (yfinance)
- No API keys required
- Caches indicator calculations for performance
