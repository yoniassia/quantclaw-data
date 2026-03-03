# Finnhub IPO Calendar Module

## Overview

Real-time IPO calendar data from Finnhub.io with performance tracking. Tracks upcoming and recent IPOs across US exchanges (NASDAQ, NYSE, etc.) with pricing details and post-IPO performance metrics.

## Data Source

- **Provider:** Finnhub.io IPO Calendar API
- **Update Frequency:** Real-time
- **API Tier:** Free tier available (60 calls/min)
- **Historical Data:** Recent IPOs with performance tracking
- **Coverage:** US exchanges (NASDAQ, NYSE, AMEX, etc.)

## Features

- ✅ Upcoming IPOs (next 30 days by default)
- ✅ Recent IPOs (last 30 days by default)
- ✅ IPO pricing details (price range, shares, exchange)
- ✅ Performance tracking (IPO price vs current price)
- ✅ Return percentage calculation
- ✅ Filter by ticker, company name, or exchange
- ✅ Custom date ranges
- ✅ 4-hour caching for fast repeat queries

## Installation

### 1. API Key Setup

Choose one of these methods to provide your Finnhub API key:

**Method A: Environment Variable**
```bash
export FINNHUB_API_KEY="your_api_key_here"
```

**Method B: .env File**
```bash
# In /home/quant/apps/quantclaw-data/.env
FINNHUB_API_KEY=your_api_key_here
```

**Method C: Credentials File**
```bash
# Create ~/.credentials/finnhub.json
{
  "api_key": "your_api_key_here"
}
```

### 2. Get a Free API Key

Visit [finnhub.io](https://finnhub.io) to sign up for a free API key.
- Free tier: 60 calls/minute
- No credit card required
- Demo key available for testing

### 3. Dependencies

```bash
pip install pandas requests
```

## Usage

### Python API

```python
from modules import finnhub_ipo_calendar

# Get upcoming IPOs (next 30 days)
df = finnhub_ipo_calendar.get_data(period='upcoming')

# Get recent IPOs (last 30 days)
df = finnhub_ipo_calendar.get_data(period='recent')

# Get recent IPOs with performance tracking
df = finnhub_ipo_calendar.get_data(
    period='recent',
    days=30,
    fetch_prices=True  # Fetch current prices for return calculation
)

# Custom date range
df = finnhub_ipo_calendar.get_data(
    from_date='2026-01-01',
    to_date='2026-03-31',
    fetch_prices=True
)

# Filter by exchange
df = finnhub_ipo_calendar.get_data(
    period='upcoming',
    exchange='NASDAQ'
)

# Filter by company name
df = finnhub_ipo_calendar.get_data(
    period='recent',
    company_name='Tech'
)

# Search for specific ticker
df = finnhub_ipo_calendar.get_data(ticker='AAPL')
```

### Command Line

```bash
# Run tests
./test_finnhub_ipo.sh

# Get upcoming IPOs
python3 modules/finnhub_ipo_calendar.py upcoming

# Get recent IPOs
python3 modules/finnhub_ipo_calendar.py recent

# Search for ticker
python3 modules/finnhub_ipo_calendar.py TSLA

# Comprehensive test
python3 modules/finnhub_ipo_calendar.py test
```

## DataFrame Columns

| Column | Type | Description |
|--------|------|-------------|
| `company` | str | Company name |
| `symbol` | str | Stock ticker symbol |
| `date` | datetime | IPO date or expected date |
| `exchange` | str | Exchange (NASDAQ, NYSE, etc.) |
| `shares` | str/int | Total shares value |
| `price_range` | str | Expected/actual price range |
| `status` | str | IPO status (expected, priced, etc.) |
| `ipo_price` | float | IPO price (midpoint of range) |
| `current_price` | float | Current market price (if available) |
| `return_pct` | float | Return % since IPO (if available) |
| `fetch_time` | str | ISO timestamp of data fetch |

## Parameters

### `get_data()` Parameters

- **`ticker`** (str, optional): Filter by ticker symbol
- **`period`** (str): 'upcoming' or 'recent' (default: 'upcoming')
- **`days`** (int): Number of days to look ahead/back (default: 30)
- **`from_date`** (str, optional): Custom start date (YYYY-MM-DD)
- **`to_date`** (str, optional): Custom end date (YYYY-MM-DD)
- **`exchange`** (str, optional): Filter by exchange
- **`company_name`** (str, optional): Filter by company name (partial match)
- **`fetch_prices`** (bool): Fetch current prices for performance tracking (default: True)

## Caching

- **Cache TTL:** 4 hours (IPO data updates frequently)
- **Cache Location:** `../cache/finnhub_ipo_*.json`
- **Cache Key:** Based on date range or period type

## Rate Limits

Finnhub free tier allows:
- 60 API calls per minute
- Module includes automatic rate limiting (0.1s delay between price fetches)
- Price tracking is optional to save API calls

## Example Output

```json
[
  {
    "company": "Example Tech Inc",
    "symbol": "EXMP",
    "date": "2026-03-15",
    "exchange": "NASDAQ",
    "shares": 10000000,
    "price_range": "15.0-18.0",
    "status": "expected",
    "ipo_price": 16.5,
    "current_price": null,
    "return_pct": null,
    "fetch_time": "2026-03-03T14:30:00"
  }
]
```

## Use Cases

1. **IPO Calendar Tracking**: Monitor upcoming IPOs for investment opportunities
2. **Performance Analysis**: Track post-IPO performance of recent listings
3. **Market Sentiment**: Analyze IPO volume and pricing trends
4. **Screening**: Filter IPOs by exchange, sector, or size
5. **Alerts**: Build notification systems for specific IPO events

## Integration with QuantClaw

This module follows the standard QuantClaw Data module pattern:
- `get_data()` function returns pandas DataFrame
- JSON caching with TTL
- CLI test interface
- Error handling with graceful fallbacks

## Related Modules

- **ipo_pipeline.py**: SEC EDGAR S-1 filing tracker
- **ipo_spac_pipeline.py**: SPAC merger and de-SPAC tracker

## Troubleshooting

### "No IPOs found"
- Check date range - IPOs may be sparse in certain periods
- Verify API key is valid
- Try demo key for testing

### "Error fetching IPO calendar"
- Check internet connection
- Verify API key is not rate limited
- Check Finnhub API status

### Performance is slow
- Set `fetch_prices=False` to skip current price lookups
- Reduce `days` parameter to fetch less data
- Cache is used automatically to speed up repeat queries

## API Documentation

- [Finnhub IPO Calendar API](https://finnhub.io/docs/api/ipo-calendar)
- [Finnhub Quote API](https://finnhub.io/docs/api/quote)

## License

Part of QuantClaw Data (Module #557)

## Author

Built by Quant (MoneyClawX) for QuantClaw Data pipeline
Created: March 3, 2026
