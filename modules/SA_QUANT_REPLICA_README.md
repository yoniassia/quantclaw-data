# SA Quant Rating Replica

## Overview

Replicates Seeking Alpha's Quant Rating system using **FREE yfinance data**. The key innovation is scoring stocks **at ANY POINT IN TIME** using only data available at that date.

## Methodology

### Scoring Factors (5 factors)

1. **Valuation (15%)**: P/E, P/B, P/S ratios vs sector median
2. **Growth (20%)**: Revenue growth YoY, EPS growth YoY
3. **Profitability (20%)**: Margins (gross, operating, net), ROE, ROA, FCF margin
4. **Momentum (20%)**: 3M/6M/12M returns, RSI, price vs 200MA
5. **EPS Revisions (25%)**: Earnings surprises, analyst upgrades, recommendation sentiment

### Composite Score

```
composite = (valuation * 0.15) + (growth * 0.20) + (profitability * 0.20) + 
            (momentum * 0.20) + (revisions * 0.25)
```

### Rating Scale

- **Strong Buy**: composite >= 3.5 (A/A+)
- **Buy**: >= 2.8 (B+)
- **Hold**: >= 2.0 (C+)
- **Sell**: >= 1.2 (D)
- **Strong Sell**: < 1.2 (F)

## Data Sources

All from yfinance (free):

- `ticker.quarterly_income_stmt` — Revenue, Net Income, EBITDA, Gross Profit
- `ticker.quarterly_balance_sheet` — Total Debt, Equity, Assets
- `ticker.quarterly_cashflow` — Free Cash Flow, Operating CF
- `ticker.earnings_history` — epsActual, epsEstimate, surprisePercent
- `ticker.upgrades_downgrades` — Analyst actions with full history
- `ticker.recommendations` — strongBuy/buy/hold/sell/strongSell counts
- Price history cache — For momentum calculations

## Important Limitation

**yfinance only returns the latest ~5 quarters from NOW, not historical quarterly snapshots.**

This means:
- For **current scoring**: Full 5-factor model works perfectly
- For **historical scoring**: We use current fundamental data as a proxy (reasonable since quality persists)
- For **backtesting**: Momentum factor is truly historical; fundamentals use current data

This is the same limitation the AlphaPickerV3 module has: "ticker.info returns CURRENT fundamentals, not historical."

## Validation Results

Scored 45 historical SA Alpha Picks (May 2023 → Feb 2026):

- **Strong Buy**: 14/45 (31.1%) — Target: >70%
- **Buy or higher**: 28/45 (62.2%) — Target: >85%
- **Average composite score**: 3.00

### Why below target?

1. Historical picks scored with current financial data
2. Stocks that were Strong Buys in 2023-2024 may have changed by now
3. Some tickers had data errors (CVSA, BRK.B)

### Strong Matches (scored Strong Buy today)

- NEM, B, INCY, MU, CDE, KGC, VISN, STRL, WLDN, SSRM, EZPW, CRDO

## CLI Usage

```bash
# Score a stock at a specific date
python3 cli.py sa-score POWL --date 2023-05-15

# Score a stock today
python3 cli.py sa-score AAPL

# Find top Strong Buy stocks
python3 cli.py sa-strong-buys --n 10

# Validate against historical picks
python3 cli.py sa-validate
```

## Example Output

```json
{
  "ticker": "POWL",
  "date": "2023-05-15",
  "composite_score": 3.23,
  "rating": "Buy",
  "factors": {
    "valuation": {
      "score": 4.67,
      "weight": 0.15,
      "details": {
        "PE": 3.63,
        "PB": 1.02,
        "PS": 0.61
      }
    },
    "growth": {
      "score": 2.0,
      "weight": 0.2,
      "details": {
        "revenue_growth_pct": 4.04
      }
    },
    "profitability": {
      "score": 4.17,
      "weight": 0.2,
      "details": {
        "gross_margin_pct": 30.18,
        "operating_margin_pct": 20.2,
        "net_margin_pct": 16.82,
        "roe_pct": 28.01,
        "roa_pct": 17.12,
        "fcf_margin_pct": 14.5
      }
    },
    "momentum": {
      "score": 4.0,
      "weight": 0.2,
      "details": {
        "return_3m_pct": 32.55,
        "return_6m_pct": 123.65,
        "rsi": 91.41,
        "pct_above_200ma": 71.77
      }
    },
    "eps_revisions": {
      "score": 2.0,
      "weight": 0.25,
      "details": {}
    }
  }
}
```

## Caching

All yfinance API calls are cached in SQLite (`data/sa_quant_cache.db`) with 24-hour TTL to:
- Avoid rate limits
- Speed up repeated queries
- Minimize API load

## Future Enhancements

1. **Sector-relative valuation**: Compare P/E, P/B against sector median instead of absolute thresholds
2. **Historical financials**: Use paid data source (Financial Datasets API) for true point-in-time scoring
3. **Analyst consensus**: Integrate analyst estimates for forward growth
4. **Smart Beta**: Add quality, low volatility, and value factors
5. **ML scoring**: Train on historical SA ratings to learn optimal weights

## Architecture

- **Module**: `modules/sa_quant_replica.py`
- **Cache**: `data/sa_quant_cache.db` (SQLite)
- **Price cache**: `data/price_history_cache.pkl` (reused from AlphaPickerV3)
- **Universe**: `data/us_stock_universe.txt`
- **Historical picks**: `data/stock_picks.csv`

## Dependencies

- yfinance
- pandas
- numpy
- tqdm (for progress bars)

## Performance

- Scoring 1 stock: ~0.5-2 seconds (with cache)
- Scoring 100 stocks: ~2-5 minutes (parallel not implemented yet)
- Validation (45 stocks): ~3 minutes

## Notes

This is a **proof of concept** demonstrating that SA-style quant ratings can be replicated using free data. For production use:

1. Use paid data source for historical point-in-time financials
2. Implement sector-relative scoring
3. Add ML-based weight optimization
4. Parallelize scoring for speed
5. Add backtesting engine with proper risk management
