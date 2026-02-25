# Regulatory Event Calendar Module — Phase 78

**Track FOMC, CPI, GDP, NFP releases with historical market reaction backtests and volatility forecasts**

## Overview

This module provides economic event tracking and market reaction analysis for major regulatory and economic releases:
- **FOMC** meetings (Federal Reserve policy decisions)
- **CPI** (Consumer Price Index - inflation data)
- **NFP** (Nonfarm Payrolls - employment report)
- **GDP** (Gross Domestic Product)
- **Other events**: PCE, Retail Sales, UMich Sentiment

## Features

1. **Economic Calendar**: Upcoming event dates with importance ratings
2. **Historical Reactions**: Backtest market moves (SPY) around each event type
3. **Volatility Forecasting**: Predict vol expansion around upcoming events
4. **Trading Implications**: Actionable insights based on historical patterns

## Data Sources

- **Yahoo Finance**: Market data (SPY, VIX) for reaction analysis
- **FRED API**: Economic release dates (fallback to hardcoded dates if API key unavailable)
- **Hardcoded schedules**: FOMC meetings, estimated CPI/NFP dates

## CLI Commands

### 1. Economic Calendar
View upcoming economic events:
```bash
python cli.py econ-calendar
```

Example output:
```
Event      Date         Days   Importance Description
NFP        2026-03-06   8      HIGH       Nonfarm Payrolls Employment Report
CPI        2026-03-13   15     HIGH       Consumer Price Index
FOMC       2026-03-17   19     HIGH       FOMC Meeting Decision
```

### 2. Historical Event Reactions
Backtest market reactions to specific event types:
```bash
python cli.py event-reaction CPI --years 3
python cli.py event-reaction NFP --years 5
python cli.py event-reaction FOMC --years 2
```

Shows:
- Average 1-day and 5-day returns
- Volatility statistics
- Win rates (% positive days)
- Extreme moves
- Recent event history

### 3. Event Volatility Forecast
Forecast volatility around next event:
```bash
python cli.py event-volatility FOMC
python cli.py event-volatility CPI
```

Provides:
- Current VIX level and regime
- Realized volatility
- Historical avg vol increase
- Forecast event volatility
- Trading implications

### 4. Detailed Event Backtest
Full backtest with all event details:
```bash
python cli.py event-backtest NFP --years 5
python cli.py event-backtest CPI --years 3
```

Shows complete event-by-event analysis with:
- Date, value, event-day change
- 1-day and 5-day post-event returns
- Volatility increase
- Summary statistics

## API Endpoints

### Base URL
```
/api/v1/regulatory-calendar
```

### Endpoints

#### 1. Economic Calendar
```
GET /api/v1/regulatory-calendar?action=econ-calendar
```

#### 2. Event Reaction Analysis
```
GET /api/v1/regulatory-calendar?action=event-reaction&eventType=CPI&years=5
```

Parameters:
- `eventType` (required): CPI, NFP, GDP, FOMC, PCE, RETAIL, UMICH
- `years` (optional, default 5): lookback period

#### 3. Event Volatility Forecast
```
GET /api/v1/regulatory-calendar?action=event-volatility&eventType=FOMC
```

Parameters:
- `eventType` (required): CPI, NFP, GDP, FOMC

#### 4. Event Backtest
```
GET /api/v1/regulatory-calendar?action=event-backtest&eventType=NFP&years=5
```

Parameters:
- `eventType` (required): CPI, NFP, GDP, FOMC
- `years` (optional, default 5): lookback period

## Use Cases

### For Traders
- **Event positioning**: Know when to reduce size or hedge
- **Volatility plays**: Identify when to buy/sell options
- **Directional bias**: Historical edge on event reactions

### For Risk Managers
- **Volatility budgeting**: Forecast vol spikes
- **Event risk**: Measure tail risk around releases
- **Correlation**: Understand cross-asset behavior during events

### For Strategists
- **Pattern recognition**: Which events move markets most?
- **Regime analysis**: How do reactions vary by market state?
- **Factor research**: Event-driven risk premiums

## Configuration

### FRED API Key (Optional)
For live economic data from FRED, set an API key:
```python
# In modules/regulatory_calendar.py
FRED_API_KEY = "your_fred_api_key_here"
```

Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html

**Note**: Module works without API key using fallback historical dates.

## Technical Details

### Market Reaction Calculation
- **Event window**: 5 days before/after event
- **Benchmark**: SPY (S&P 500 ETF)
- **Volatility**: Realized vol (annualized stddev of daily returns)
- **VIX**: Current implied volatility context

### Limitations
- Market data limited by Yahoo Finance availability
- Historical event dates are estimates when FRED API unavailable
- Assumes normal market hours (no overnight gaps modeled)

## Examples

### Example 1: CPI Release Analysis
```bash
python cli.py event-reaction CPI --years 3

# Shows:
# - Avg 1d return: -0.2%
# - Avg vol increase: +15%
# - Win rate: 45% (bearish bias)
# - Implications: Consider puts or short-dated straddles
```

### Example 2: FOMC Volatility Forecast
```bash
python cli.py event-volatility FOMC

# Shows:
# - Next FOMC: 2026-03-17 (19 days)
# - Current VIX: 19.5 (NORMAL)
# - Forecast vol: 22% → +13% increase
# - Implication: Vol relatively cheap, consider long vol
```

### Example 3: Full NFP Backtest
```bash
python cli.py event-backtest NFP --years 5

# Returns table of all 60 NFP releases:
# - Date, jobs number, SPY reaction
# - Correlation analysis
# - Best/worst reactions
```

## Contributing

To add new event types:
1. Add series to `EVENT_SERIES` dict
2. Add historical dates to `HISTORICAL_EVENTS`
3. Update CLI help text in `cli.py`
4. Add to API route handlers

## Author
QUANTCLAW DATA Build Agent — Phase 78

## License
Part of the QuantClaw Data platform
