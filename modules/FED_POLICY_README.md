# Fed Policy Prediction Module (Phase 45)

## Overview
FOMC analysis, dot plot tracking, and rate hike probability scoring using Fed funds futures, FRED API data, and yield curve analysis.

## Data Sources
- **FRED API**: Federal funds rate, treasury yields, inflation (CPI), unemployment, GDP
- **Yahoo Finance**: Fed funds futures (ZQ=F) for CME FedWatch-style probability calculations
- **Federal Reserve Website**: FOMC meeting calendar (web scraping)
- **Yield Curve Analysis**: Treasury term structure for implied rate path

## Features

### 1. Comprehensive Fed Watch (`fed-watch`)
Full dashboard combining all Fed policy indicators:
- Current fed funds rate and target range
- Rate hike/cut probabilities from futures
- Yield curve shape and recession signals
- Upcoming FOMC meetings
- Dot plot consensus projection

### 2. Rate Probability (`rate-probability`)
CME FedWatch-style probability calculation:
- Implied rate from 30-day fed funds futures (ZQ=F)
- Probability breakdown: hold / hike / cut
- Rate differential vs current effective rate
- 5-day rate change momentum

### 3. FOMC Calendar (`fomc-calendar`)
Upcoming Federal Reserve meetings:
- Web scraping from federalreserve.gov
- Typical 8 meetings per year schedule
- Next meeting date highlighted
- Fallback to typical schedule if scraping fails

### 4. Dot Plot Analysis (`dot-plot`)
Fed's Summary of Economic Projections (SEP) analysis:
- Terminal rate estimate based on inflation and unemployment
- Hawkish/dovish/neutral consensus projection
- Year-over-year inflation rate calculation
- Unemployment rate tracking

### 5. Yield Curve (`yield-curve`)
Treasury yield curve analysis:
- 1Y, 2Y, 5Y, 10Y, 30Y treasury rates
- 10Y-2Y spread (recession indicator)
- 10Y-3M spread (additional signal)
- Curve shape: inverted / flat / normal
- Implied rate path signal

### 6. Current Rate (`current-rate`)
Current Fed policy stance:
- Effective federal funds rate
- Target range (lower and upper bounds)
- 30-day rate change
- Latest data dates

## CLI Commands

```bash
# Comprehensive analysis
python cli.py fed-watch

# Rate probabilities
python cli.py rate-probability

# FOMC meeting schedule
python cli.py fomc-calendar

# Dot plot consensus
python cli.py dot-plot

# Yield curve analysis
python cli.py yield-curve

# Current fed funds rate
python cli.py current-rate
```

## API Integration

Services added to `/src/app/services.ts`:
- `fed_policy`: Main Fed policy prediction service
- MCP Tool: `get_fed_policy`
- Parameters: `analysis_type` (fed-watch, rate-probability, fomc-calendar, dot-plot, yield-curve, current-rate)

## Data Quality Notes

### FRED API Limitations
- Public FRED API access is limited without an API key
- Some series may return 400 errors
- Module gracefully degrades to fallback data when API is unavailable

### Fed Funds Futures
- ZQ=F (30-day fed funds futures) may have limited data availability
- Simplified probability model (actual CME FedWatch uses more complex calculations)
- Real-time futures data requires active market hours

### FOMC Calendar Scraping
- Federal Reserve website structure may change
- Fallback to typical 8-meeting annual schedule
- Exact dates should be confirmed on federalreserve.gov

## Implementation Details

### Rate Probability Model
```
Implied Rate = 100 - Futures Price
Rate Differential = Implied Rate - Current Rate

If |differential| < 12.5 bps: Hold likely (85% probability)
If differential > 12.5 bps: Hike expected (up to 70% probability)
If differential < -12.5 bps: Cut expected (up to 70% probability)
```

### Yield Curve Signals
- **Inverted (10Y-2Y < 0)**: Market expects rate cuts (recession signal)
- **Flat (10Y-2Y < 0.25)**: Market expects stable rates (caution)
- **Normal (10Y-2Y > 0.25)**: Market expects rate hikes (healthy economy)

### Dot Plot Consensus
- **Hawkish**: Inflation > 3% → expect rate hikes
- **Dovish**: Inflation < 2% AND unemployment > 4.5% → expect rate cuts
- **Neutral**: Otherwise → expect stable rates

## Files
- `/modules/fed_policy.py`: Main implementation (582 LOC)
- `/modules/FED_POLICY_README.md`: This documentation
- Updated `/cli.py`: Command registration
- Updated `/src/app/services.ts`: API service definition
- Updated `/src/app/roadmap.ts`: Phase 45 marked as "done"

## Testing

All commands tested and working:
```bash
✅ python cli.py fed-watch          # Returns comprehensive analysis
✅ python cli.py rate-probability   # Returns futures-based probabilities
✅ python cli.py fomc-calendar      # Returns scraped meeting dates
✅ python cli.py dot-plot           # Returns consensus projection
✅ python cli.py yield-curve        # Returns yield curve data
✅ python cli.py current-rate       # Returns current fed funds rate
```

## Future Enhancements

1. **FRED API Key Integration**
   - Add proper FRED API key configuration
   - Enable full historical data access

2. **Enhanced Futures Analysis**
   - Multiple contract months (ZQG, ZQH, ZQM, etc.)
   - Term structure of fed funds futures
   - More sophisticated probability calculations

3. **Actual Dot Plot Parsing**
   - Parse Fed's quarterly SEP PDF releases
   - Extract individual FOMC member projections
   - Distribution analysis (median, range, dispersion)

4. **Machine Learning Predictions**
   - Train model on historical FOMC decisions
   - Incorporate Fed speeches and minutes sentiment
   - Predict rate changes based on macro indicators

5. **Real-time Alerts**
   - FOMC meeting result notifications
   - Significant futures price movements
   - Yield curve inversion alerts

## Author
QUANTCLAW DATA Build Agent

## Phase
45 of 93 — COMPLETED ✅

## Lines of Code
582 LOC (Python)
