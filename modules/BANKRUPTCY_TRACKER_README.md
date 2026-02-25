# Bankruptcy & Default Tracker (Phase 197)

Track corporate bankruptcies, Chapter 11 filings, and default notices via SEC EDGAR filings.

## Data Sources

1. **SEC EDGAR 8-K Filings** (Item 1.03)
   - Bankruptcy notices and Chapter 11 filings
   - Form 8-K/A amendments

2. **SEC 10-K/10-Q Filings**
   - Going concern warnings
   - Substantial doubt disclosures

3. **SEC Full-Text Search**
   - Keyword-based bankruptcy detection
   - Real-time RSS feeds

## Features

### 1. Bankruptcy Search (`bankruptcy-search`)
Search recent SEC filings for bankruptcy-related disclosures.

**Keywords Tracked:**
- "chapter 11"
- "chapter 7" 
- "bankruptcy protection"
- "filed for bankruptcy"
- "bankruptcy petition"
- "going concern"
- "substantial doubt"
- "default notice"
- "covenant breach"
- "restructuring plan"
- "debtor in possession"
- "insolvency"

**Parameters:**
- `--days`: Lookback period (default 30)
- `--limit`: Max results (default 50)

**Output:**
```json
[
  {
    "company": "Example Corp",
    "cik": "0001234567",
    "form_type": "8-K",
    "filing_date": "2025-02-15",
    "description": "Bankruptcy filing under Chapter 11...",
    "url": "https://www.sec.gov/...",
    "keywords_found": ["chapter 11", "bankruptcy protection"]
  }
]
```

### 2. Company Bankruptcy Tracker (`bankruptcy-tracker`)
Get bankruptcy risk assessment for a specific company.

**Parameters:**
- `--ticker`: Stock ticker symbol (required)

**Output:**
```json
{
  "ticker": "AAPL",
  "company": "Apple Inc",
  "cik": "0000320193",
  "bankruptcy_risk": "LOW",
  "recent_filings": [],
  "total_bankruptcy_filings": 0
}
```

**Risk Levels:**
- `HIGH`: Recent bankruptcy-related filings found
- `LOW`: No bankruptcy indicators

### 3. Bankruptcy Statistics (`bankruptcy-stats`)
Aggregate bankruptcy trends and statistics.

**Parameters:**
- `--sector`: Optional sector filter
- `--year`: Optional year filter (default: last 365 days)

**Output:**
```json
{
  "period": "2024-01-01 to 2024-12-31",
  "total_filings": 127,
  "unique_companies": 89,
  "by_form_type": {
    "8-K": 76,
    "10-K": 31,
    "10-Q": 20
  },
  "by_month": {
    "2024-01": 8,
    "2024-02": 12,
    ...
  },
  "by_keyword": {
    "chapter 11": 45,
    "going concern": 38,
    "bankruptcy protection": 22
  },
  "top_companies": [
    {
      "company": "Example Corp (0001234567)",
      "filing_count": 5
    }
  ]
}
```

## Usage Examples

### CLI

```bash
# Search last 7 days
python cli.py bankruptcy-search --days 7 --limit 20

# Track specific company
python cli.py bankruptcy-tracker --ticker TSLA

# Get 2024 statistics
python cli.py bankruptcy-stats --year 2024

# Current year stats
python cli.py bankruptcy-stats
```

### MCP Server

```python
# Through MCP protocol
{
  "tool": "search_bankruptcy_filings",
  "parameters": {
    "days": 30,
    "limit": 50
  }
}

{
  "tool": "get_bankruptcy_tracker",
  "parameters": {
    "ticker": "AAPL"
  }
}

{
  "tool": "get_bankruptcy_stats",
  "parameters": {
    "year": 2025
  }
}
```

## Implementation Details

### SEC EDGAR API
- User-Agent: Required by SEC (QuantClaw/1.0)
- Rate Limit: 100 requests/minute
- Formats: RSS/Atom feeds, HTML scraping

### Search Strategy
1. **Multi-form search**: 8-K, 10-K, 10-Q
2. **Keyword combinations**: Multiple bankruptcy-related terms
3. **Deduplication**: By CIK + filing date
4. **Sorting**: Most recent first

### Data Quality
- **Real-time**: RSS feeds updated as filings are made
- **Coverage**: All US public companies
- **False Positives**: Minimal due to SEC filing structure
- **Latency**: <1 hour from SEC publication

## Limitations

1. **PACER Access**: Federal court filings require subscription
   - Free tier provides RSS feeds only
   - Full access requires PACER account

2. **Private Companies**: Only tracks public companies (SEC filers)

3. **International**: US companies only
   - Non-US companies tracked via SEC filings only

4. **Historical Data**: RSS feeds limited to recent filings
   - Full historical search requires EDGAR bulk download

## Future Enhancements

1. **PACER Integration**: Direct Chapter 11 court filings
2. **Predictive Model**: ML bankruptcy risk scoring
3. **Credit Watch**: Link with CDS spreads module
4. **Sector Analysis**: Industry-specific distress indicators
5. **Creditor Analysis**: Track secured vs unsecured debt
6. **DIP Financing**: Debtor-in-possession loan tracking

## Related Modules

- **Phase 30**: CDS Spreads (credit risk pricing)
- **Phase 59**: Earnings Quality (financial distress signals)
- **Phase 61**: Dark Pool Tracker (insider selling)
- **Phase 156**: Corporate Bond Spreads (distress indicators)

## Technical Stack

- **Language**: Python 3
- **Dependencies**: requests, xml.etree.ElementTree (stdlib)
- **API**: SEC EDGAR RSS/Atom feeds
- **Storage**: JSON output (no persistence)

## Lines of Code: 371

---

**Status**: ✅ Done (Phase 197)
**Category**: Alternative Data
**Update Frequency**: Daily (RSS feeds continuously updated)
