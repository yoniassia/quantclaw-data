# Sector Rotation Model — Phase 33

**Economic cycle indicators, relative strength rotation strategies**

## Overview

The Sector Rotation module analyzes 11 sector ETFs using economic cycle indicators and relative strength momentum to generate trading signals. It combines:

1. **Economic Cycle Analysis**: Yield curve, ISM PMI, unemployment rate
2. **Relative Strength**: Performance vs SPY benchmark with risk-adjusted returns
3. **Cycle-Aware Signals**: Trading recommendations based on cycle phase alignment

## Sector ETFs Analyzed

| Ticker | Sector |
|--------|--------|
| XLK | Technology |
| XLF | Financials |
| XLE | Energy |
| XLV | Healthcare |
| XLI | Industrials |
| XLP | Consumer Staples |
| XLU | Utilities |
| XLRE | Real Estate |
| XLC | Communication Services |
| XLB | Materials |
| XLY | Consumer Discretionary |

## Economic Indicators

### FRED Data Sources
- **T10Y2Y**: 10-Year minus 2-Year Treasury Yield Spread (yield curve)
- **NAPM**: ISM Manufacturing PMI
- **UNRATE**: Unemployment Rate

### Cycle Phases
1. **Early**: Recovery phase — favor Financials, Industrials, Materials, Energy
2. **Mid**: Expansion phase — favor Technology, Industrials, Consumer Disc, Materials
3. **Late**: Peak phase — favor Energy, Materials, Industrials
4. **Recession**: Contraction — favor Staples, Utilities, Healthcare

## CLI Usage

### 1. Full Rotation Analysis
```bash
python cli.py sector-rotation [LOOKBACK_DAYS]

# Examples:
python cli.py sector-rotation          # Default 60-day lookback
python cli.py sector-rotation 90       # 90-day lookback
```

**Output**:
- Trading signals: STRONG_BUY, BUY, HOLD, NEUTRAL, AVOID
- Cycle phase with favorable sectors
- Relative strength rankings
- Risk-adjusted returns

### 2. Sector Momentum Only
```bash
python cli.py sector-momentum [LOOKBACK_DAYS]

# Examples:
python cli.py sector-momentum 60
python cli.py sector-momentum 120
```

**Output**:
- Sector rankings by relative strength
- Period returns (vs lookback)
- 20-day and 60-day ROC
- Volatility and Sharpe-like ratios

### 3. Economic Cycle Analysis
```bash
python cli.py economic-cycle
```

**Output**:
- Current cycle phase determination
- Yield curve analysis (spread, trend, inversion status)
- ISM PMI reading and trend
- Unemployment trend
- Favorable sectors for current phase

## API Endpoints

**Base URL**: `/api/v1/sector-rotation`

### 1. Full Rotation Analysis
```
GET /api/v1/sector-rotation?action=rotation&lookback=60
```

### 2. Momentum Rankings
```
GET /api/v1/sector-rotation?action=momentum&lookback=90
```

### 3. Economic Cycle
```
GET /api/v1/sector-rotation?action=cycle
```

## Signal Logic

### Trading Signals
- **STRONG_BUY**: Top 3 ranked + cycle favored
- **BUY**: Top 3 ranked, not cycle favored
- **HOLD**: Cycle favored, not top ranked
- **NEUTRAL**: Middle performance
- **AVOID**: Bottom 3 ranked

### Relative Strength Calculation
```
RS = Sector_Return - SPY_Return
Risk_Adjusted = Period_Return / Annualized_Volatility
```

## Example Output

### Sector Rotation
```json
{
  "cycle_phase": "Late",
  "summary": {
    "strong_buy": 3,
    "buy": 0,
    "hold": 0,
    "avoid": 3
  },
  "signals": [
    {
      "ticker": "XLE",
      "sector": "Energy",
      "signal": "STRONG_BUY",
      "rank": 1,
      "relative_strength": 22.13,
      "period_return": 24.21,
      "cycle_favored": true,
      "risk_adjusted_return": 1.22
    }
  ]
}
```

### Economic Cycle
```json
{
  "cycle_phase": "Mid",
  "indicators": {
    "yield_curve": {
      "current_spread_bps": 98.49,
      "trend": "steepening",
      "inverted": false,
      "signal": "neutral"
    },
    "ism_manufacturing": {
      "current": 50.82,
      "trend": "expanding",
      "expansion": true,
      "signal": "neutral"
    }
  },
  "favorable_sectors": ["XLK", "XLI", "XLY", "XLB"]
}
```

## Data Sources

- **Market Data**: Yahoo Finance (yfinance)
- **Economic Data**: FRED API (with demo fallback)
- **Benchmark**: SPY (S&P 500 ETF)

## Implementation Details

- **Language**: Python 3
- **Dependencies**: yfinance, pandas, numpy
- **Lines of Code**: 411
- **API Route**: `/src/app/api/v1/sector-rotation/route.ts`
- **Module**: `/modules/sector_rotation.py`

## Testing

Run the test suite:
```bash
bash test_sector_rotation.sh
```

Tests include:
- ✓ Economic cycle analysis
- ✓ Sector momentum (60-day and 90-day)
- ✓ Full rotation with signals
- ✓ CLI help display

## Notes

- Uses demo FRED data when API key not configured
- Fetches real-time sector ETF prices from Yahoo Finance
- Calculates all metrics on-the-fly (no caching)
- Production API endpoints require Next.js restart after deployment
