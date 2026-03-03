# SPACInsider Module

**Module:** `spacinsider.py`  
**Source:** SPACInsider.com (web scraping)  
**Update Frequency:** Real-time (4-hour cache)  
**Free:** Yes (public data)

---

## Overview

The SPACInsider module provides comprehensive SPAC (Special Purpose Acquisition Company) lifecycle tracking and analysis by scraping public data from SPACInsider.com. This module covers the entire SPAC journey from IPO filing through merger completion or liquidation.

## Data Coverage

### 1. Active SPAC Listings (`period='active'`)
Track currently trading SPACs with key metrics:
- Symbol and company name
- Trust value and redemption deadlines
- Unit split information
- Sponsor details
- IPO date and focus sector

### 2. SPAC Mergers & Deals (`period='merger'`)
Monitor announced and pending SPAC mergers:
- Target company identification
- Announcement and vote dates
- Deal completion status
- Transaction valuation
- Industry sector

### 3. Post-Merger Performance (`period='performance'`)
Analyze de-SPAC performance:
- Merger close dates
- IPO price vs current price
- NAV comparison
- Return calculations

### 4. SPAC IPOs (`period='ipo'`)
Recent SPAC IPO filings and pricings:
- Filing dates (S-1 submissions)
- Pricing dates and offering size
- Unit price and underwriter
- Sponsor information

### 5. SPAC Liquidations (`period='liquidation'`)
Track SPACs approaching deadlines:
- Redemption deadlines
- Days remaining
- Trust value at risk
- Extension status

---

## Usage

### Basic Import

```python
from modules import spacinsider

# Get active SPACs
df = spacinsider.get_data(period='active')

# Get merger announcements
df = spacinsider.get_data(period='merger')

# Get recent IPOs
df = spacinsider.get_data(period='ipo')

# Get liquidation candidates
df = spacinsider.get_data(period='liquidation')

# Get performance data
df = spacinsider.get_data(period='performance')
```

### Filtering by Ticker

```python
# Find specific SPAC
df = spacinsider.get_data(period='active', ticker='IPOA')

# Search pattern
df = spacinsider.get_data(period='active', ticker='CHAS')
```

### Parameters

- **`ticker`** (str, optional): Filter results by ticker symbol
- **`period`** (str, required): Data category
  - `'active'`: Active SPAC listings (default)
  - `'merger'`: SPAC mergers/deals
  - `'performance'`: Post-merger performance
  - `'ipo'`: Recent SPAC IPOs
  - `'liquidation'`: Liquidation candidates

---

## Output Schema

### Active SPACs

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Trading ticker symbol |
| `name` | str | SPAC company name |
| `status` | str | Current status (Active, Searching, etc.) |
| `trust_value` | float | Trust account value (millions) |
| `redemption_deadline` | date | Final redemption deadline |
| `unit_split` | str | Units per share structure |
| `sponsor` | str | Sponsor/management team |
| `ipo_date` | date | IPO pricing date |
| `focus` | str | Target sector/industry |
| `fetch_time` | datetime | Data retrieval timestamp |

### Merger SPACs

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | SPAC ticker |
| `name` | str | SPAC name |
| `target_company` | str | Merger target |
| `announcement_date` | date | Deal announcement date |
| `vote_date` | date | Shareholder vote date |
| `completion_status` | str | Deal status |
| `deal_value` | float | Transaction valuation |
| `industry` | str | Target industry |
| `fetch_time` | datetime | Timestamp |

### IPO SPACs

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Ticker symbol |
| `name` | str | SPAC name |
| `filing_date` | date | S-1 filing date |
| `pricing_date` | date | IPO pricing date |
| `offering_size` | float | Offering amount (millions) |
| `unit_price` | float | Initial unit price |
| `underwriter` | str | Lead underwriter |
| `sponsor` | str | Sponsor team |
| `fetch_time` | datetime | Timestamp |

### Liquidation SPACs

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | SPAC ticker |
| `name` | str | SPAC name |
| `deadline` | date | Liquidation deadline |
| `trust_value` | float | Trust account value |
| `status` | str | Current status |
| `days_remaining` | int | Days until deadline |
| `extension_status` | str | Extension filed/approved |
| `fetch_time` | datetime | Timestamp |

---

## Implementation Notes

### Data Source Method

SPACInsider.com does not have a publicly documented API. This module uses **web scraping** of public pages:

1. **Primary method:** Parse Next.js embedded JSON data from `__NEXT_DATA__` script tags
2. **Fallback method:** Extract data from HTML tables when JSON parsing fails
3. **Caching:** 4-hour cache to minimize requests and improve performance

### API Key Management (Future)

If SPACInsider launches a documented API, the module checks for keys in this order:

1. Environment variable `SPACINSIDER_API_KEY`
2. `.env` file in quantclaw-data directory
3. `~/.credentials/spacinsider.json`

### Cache Configuration

- **Location:** `../cache/spacinsider_[period].json`
- **TTL:** 4 hours (14,400 seconds)
- **Format:** JSON serialized DataFrame records

---

## Dependencies

- `requests` — HTTP requests
- `pandas` — DataFrame operations
- `beautifulsoup4` — HTML parsing
- `lxml` — BS4 parser (recommended)

Install missing dependencies:
```bash
pip install requests pandas beautifulsoup4 lxml
```

---

## Testing

Run the test suite:

```bash
./test_spacinsider.sh
```

Or test manually:

```bash
# CLI test interface
python3 modules/spacinsider.py active
python3 modules/spacinsider.py merger
python3 modules/spacinsider.py ipo
python3 modules/spacinsider.py liquidation

# Python import test
python3 -c "
from modules import spacinsider
df = spacinsider.get_data(period='active')
print(df.head())
"
```

---

## Example Use Cases

### 1. Find SPACs Near Deadline

```python
from modules import spacinsider

# Get liquidation candidates
df = spacinsider.get_data(period='liquidation')

# Filter for urgent (< 30 days)
if 'days_remaining' in df.columns:
    urgent = df[df['days_remaining'] < 30].sort_values('days_remaining')
    print(f"Found {len(urgent)} SPACs with <30 days to deadline")
```

### 2. Monitor Merger Pipeline

```python
# Get all announced mergers
mergers = spacinsider.get_data(period='merger')

# Filter by industry
if 'industry' in mergers.columns:
    tech_mergers = mergers[mergers['industry'].str.contains('Tech|Software', case=False, na=False)]
    print(f"Tech mergers: {len(tech_mergers)}")
```

### 3. Track Recent IPO Activity

```python
# Get recent SPAC IPOs
ipos = spacinsider.get_data(period='ipo')

# Analyze by sponsor
if 'sponsor' in ipos.columns:
    sponsor_counts = ipos['sponsor'].value_counts()
    print("Top SPAC sponsors:")
    print(sponsor_counts.head(5))
```

### 4. NAV Arbitrage Opportunities

```python
# Get active SPACs
active = spacinsider.get_data(period='active')

# Find those near NAV with upcoming deadline
# (Potential redemption arbitrage)
if 'trust_value' in active.columns:
    nav_candidates = active[active['trust_value'].notna()]
    print(f"SPACs with trust value data: {len(nav_candidates)}")
```

---

## Limitations

1. **No Official API:** Module relies on web scraping, which may break if site structure changes
2. **Rate Limiting:** Respectful 15-second timeout; avoid excessive calls
3. **Data Completeness:** Depends on what SPACInsider publishes publicly
4. **Performance Data:** Real-time price tracking requires integration with price data sources
5. **Dynamic Content:** Some data may require JavaScript rendering (future enhancement)

---

## Troubleshooting

### No Data Returned

```python
df = spacinsider.get_data(period='active')
if 'message' in df.columns:
    print(df['message'].iloc[0])
```

**Possible causes:**
- Site structure changed (update parsing logic)
- Network connectivity issues
- SPACInsider temporarily down

### Empty DataFrame

```python
if df.empty:
    # Clear cache and retry
    os.remove('/home/quant/apps/quantclaw-data/cache/spacinsider_active.json')
    df = spacinsider.get_data(period='active')
```

### BeautifulSoup Errors

Ensure dependencies installed:
```bash
pip install beautifulsoup4 lxml html5lib
```

---

## Future Enhancements

1. **API Integration:** If SPACInsider releases official API, switch from scraping
2. **Price Integration:** Connect to price feed for performance calculations
3. **SEC Filing Links:** Add direct links to S-1, merger proxy filings
4. **Warrant Tracking:** Separate warrant redemption dates and terms
5. **Historical Archive:** Track status changes over time
6. **Alert System:** Notify on deadline approaches or merger votes

---

## Version History

- **v1.0** (2026-03-03): Initial release
  - Web scraping implementation
  - Five data categories (active, merger, ipo, liquidation, performance)
  - 4-hour caching
  - CLI and Python API

---

## Related Modules

- `ipo_pipeline.py` — SEC EDGAR S-1 IPO filings
- `ipo_spac_pipeline.py` — SEC EDGAR SPAC-specific filings
- `finnhub_ipo_calendar.py` — Finnhub IPO calendar with performance

---

## Contact & Support

For module issues or enhancement requests:
- Internal: File ticket with QuantClaw Data team
- SPACInsider data questions: Visit spacinsider.com or contact their support

---

*Module created 2026-03-03 | Part of QuantClaw Data (556+ modules)*
