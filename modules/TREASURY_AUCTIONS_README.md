# US Treasury Auctions & Debt Module — Phase 118 ✅

**Status:** COMPLETE  
**Lines of Code:** 476  
**Build Date:** 2026-02-25  

## Overview

Comprehensive US Treasury auction data and debt holdings tracking module. Provides real-time access to Treasury auction results, upcoming auction schedules, foreign holdings tracking, and debt outstanding metrics.

## Data Sources

- **TreasuryDirect.gov Auction Query API** — Real-time auction results with bid-to-cover ratios
- **Fiscal Data API v2** — Debt to the Penny data (debt outstanding)
- **TIC (Treasury International Capital)** — Foreign holdings data (documentation for future implementation)

## Features Implemented

### 1. Recent Auction Results ✅
- Query auctions by security type (Bill, Note, Bond, TIPS, FRN)
- Bid-to-cover ratios
- Competitive vs non-competitive bidding breakdown
- High/low/median pricing
- Customizable lookback periods

### 2. Upcoming Auction Schedule ✅
- Forward-looking auction calendar
- Offering amounts
- Security terms and maturities
- Announcement dates

### 3. Debt Outstanding ✅
- Current total US public debt
- Intragovernmental holdings
- Debt held by public
- Historical trend tracking

### 4. TIC Foreign Holdings 📝
- Debt outstanding trend (12-month historical)
- Framework for country-level holdings (requires Excel parsing)
- Major holder reference data

### 5. Auction Performance Analysis ✅
- Average bid-to-cover by security type
- Yield analysis
- Auction volume statistics
- Recent auction highlights

### 6. Comprehensive Dashboard ✅
- Recent auctions (last 14 days)
- Upcoming auctions (next 14 days)
- Current debt outstanding
- Performance summary (90-day lookback)

## CLI Commands

```bash
# Recent auction results
python cli.py treasury-recent [days] [type]
python cli.py treasury-recent 30 Bill      # Last 30 days of Bill auctions
python cli.py treasury-recent 90 Note      # Last 90 days of Note auctions

# Upcoming auctions
python cli.py treasury-upcoming [days]
python cli.py treasury-upcoming 30         # Next 30 days

# TIC foreign holdings
python cli.py treasury-tic [country]
python cli.py treasury-tic                 # Debt trend + major holders info

# Debt outstanding
python cli.py treasury-debt                # Current US debt snapshot

# Performance analysis
python cli.py treasury-performance [days]
python cli.py treasury-performance 90      # 90-day auction performance

# Comprehensive dashboard
python cli.py treasury-dashboard           # Full dashboard
```

## MCP Tools (6 tools added)

All functions exposed via MCP server for AI agent integration:

1. `treasury_recent_auctions` — Get recent auction results
2. `treasury_upcoming_auctions` — Get upcoming auction schedule
3. `treasury_tic_holdings` — Get TIC foreign holdings data
4. `treasury_debt_outstanding` — Get current debt outstanding
5. `treasury_auction_performance` — Analyze auction performance
6. `treasury_dashboard` — Comprehensive dashboard

## Example Output

### Recent Auctions (Bill)
```json
{
  "success": true,
  "data": [
    {
      "cusip": "912797SL2",
      "security_type": "Bill",
      "security_term": "6-Week",
      "auction_date": "2026-02-24T00:00:00",
      "bid_to_cover": 2.76,
      "high_investment_rate": 3.701,
      "allotted_amount_in_millions": 93375.13,
      "total_tendered": 257462.53
    }
  ]
}
```

### Debt Outstanding
```json
{
  "success": true,
  "data": {
    "record_date": "2026-02-23",
    "total_public_debt_billions": 38758072.04,
    "debt_held_by_public_billions": 31113461.80,
    "intragovernmental_holdings_billions": 7644610.24
  }
}
```

### Performance Analysis
```json
{
  "success": true,
  "data": {
    "Note": {
      "auction_count": 6,
      "avg_bid_to_cover": 2.41,
      "total_amount_auctioned": 359749.0
    },
    "Bill": {
      "auction_count": 12,
      "avg_bid_to_cover": 2.87,
      "total_amount_auctioned": 1089234.5
    }
  }
}
```

## Technical Implementation

### Core Functions

- `get_auction_results()` — Query Treasury Direct auction API
- `get_upcoming_auctions()` — Get announced auctions
- `get_tic_foreign_holdings()` — Debt trend + TIC reference
- `get_debt_outstanding()` — Current debt via Fiscal Data API v2
- `analyze_auction_performance()` — Statistical analysis across security types
- `get_treasury_dashboard()` — Aggregated dashboard view

### API Details

**Treasury Direct API:**
- Base: `https://www.treasurydirect.gov/TA_WS/securities`
- Endpoints: `/auctioned`, `/announced`
- Format: JSON
- No API key required
- Rate limit: Reasonable (no documented limit)

**Fiscal Data API v2:**
- Base: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2`
- Endpoint: `/accounting/od/debt_to_penny`
- Format: JSON
- No API key required
- 100 requests per hour (soft limit)

### Error Handling

- Graceful fallback on API failures
- Timeout handling (30 seconds)
- Invalid parameter validation
- Detailed error messages

## Refresh Schedule

- **Auction Results:** Real-time (as auctions occur)
- **Debt Outstanding:** Daily (updated each business day)
- **Upcoming Auctions:** Real-time (as announced)
- **TIC Holdings:** Monthly (2-month lag in official reports)

## Future Enhancements

1. **TIC Excel Parsing** — Parse monthly Excel reports for country-level holdings breakdown
2. **Historical Auction Database** — Build local cache for faster historical queries
3. **Yield Curve Integration** — Cross-reference auction yields with secondary market
4. **Foreign Holdings Trends** — Time-series analysis of major holder positions
5. **Auction Outcome Prediction** — ML model for bid-to-cover forecasting

## Files Modified

1. **modules/treasury_auctions.py** (NEW) — 476 lines
2. **cli.py** — Added 6 CLI commands
3. **mcp_server.py** — Added 6 MCP tools + imports
4. **src/app/roadmap.ts** — Marked phase 118 as "done", updated data source status

## Testing

All CLI commands tested and verified:
- ✅ `treasury-recent` — Bills, Notes, multiple time periods
- ✅ `treasury-upcoming` — 14-day and 30-day lookouts
- ✅ `treasury-debt` — Current debt snapshot
- ✅ `treasury-tic` — 12-month debt trend
- ✅ `treasury-performance` — 30-day and 90-day analysis
- ✅ `treasury-dashboard` — Full dashboard output

## Bloomberg Terminal Equivalent

This module replicates functionality from:
- **Bloomberg BTMM** — Treasury auction monitor
- **Bloomberg WDCI** — World debt statistics
- **Bloomberg DDIS** — Debt issuance calendar

## Dependencies

```python
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
```

All dependencies already present in QuantClaw Data environment.

---

**Phase 118 Complete!** 🎉  
**US Treasury auctions & debt data now live in QuantClaw.**
