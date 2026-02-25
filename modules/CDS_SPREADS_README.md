# CDS Spreads Module — Phase 30 ✅

**Status:** COMPLETE  
**Lines of Code:** 486  
**Category:** Fixed Income  

## Overview

Sovereign and corporate credit risk signals from credit default swap markets. Real, functional module using free APIs and market-implied credit risk proxies.

## Data Sources

1. **FRED API** (Federal Reserve Economic Data)
   - ICE BofA High Yield Option-Adjusted Spread (BAMLH0A0HYM2)
   - ICE BofA Corporate Option-Adjusted Spread (BAMLC0A0CM)
   - ICE BofA BBB/BB/B/CCC spreads
   - Moody's Aaa/Baa Corporate Bond Yields
   - Treasury yield curve spreads
   - 10-Year TIPS

2. **Yahoo Finance**
   - Corporate bond ETFs (HYG, LQD, JNK) for market-implied credit risk
   - Individual corporate ticker fundamentals (debt-to-equity, market cap)

3. **Estimated CDS Spreads**
   - Corporate: derived from debt-to-equity ratios and sector
   - Sovereign: derived from credit ratings and safe-haven status
   - Note: Real CDS data requires premium feeds (Bloomberg, MarkIt)

## CLI Commands

### Via Direct Module
```bash
python modules/cds_spreads.py credit-spreads
python modules/cds_spreads.py cds AAPL
python modules/cds_spreads.py sovereign-risk Italy
```

### Via CLI Dispatcher
```bash
python cli.py spread-compare
python cli.py credit-risk-score TSLA
python cli.py sovereign-spreads Germany
python cli.py corporate-spreads
```

## API Endpoints

### Credit Market Dashboard
```
GET /api/v1/cds?action=credit-spreads
```
Returns comprehensive credit spread data across all ratings and FRED series.

### Corporate CDS Spread
```
GET /api/v1/cds?action=entity&ticker=AAPL
```
Returns estimated CDS spread for a corporate entity based on fundamentals.

### Sovereign Risk Analysis
```
GET /api/v1/cds?action=sovereign&country=Italy
```
Returns sovereign credit risk assessment with estimated CDS spread.

## Example Output

### Credit Spreads Dashboard
```json
{
  "timestamp": "2026-02-24T19:17:16.317158",
  "fred_spreads": {
    "BAMLH0A0HYM2": {
      "name": "ICE BofA US High Yield Option-Adjusted Spread",
      "value": 341.88,
      "date": "2026-02-24",
      "units": "Basis Points"
    }
  },
  "etf_proxies": {
    "HYG": {"price": 78.50, "return_30d": -1.2}
  },
  "summary": {
    "high_yield_spread_bps": 341.88,
    "investment_grade_spread_bps": 109.23,
    "hy_ig_ratio": 3.13,
    "risk_level": "NORMAL — Spreads within historical ranges",
    "market_stress": "LOW STRESS — Benign credit environment"
  }
}
```

### Corporate CDS
```json
{
  "entity": "AAPL",
  "name": "Apple Inc.",
  "type": "corporate",
  "estimated_cds_spread_bps": 250,
  "market_cap": 3995924955136,
  "debt_to_equity": 102.63,
  "sector": "Technology",
  "note": "Estimated from corporate fundamentals. Real CDS data requires premium feed."
}
```

### Sovereign Risk
```json
{
  "country": "Italy",
  "credit_rating": "BBB",
  "safe_haven_status": false,
  "estimated_cds_spread_bps": 200,
  "us_10y_yield": 4.25,
  "risk_assessment": "ELEVATED RISK — Investment grade floor, watch for downgrades"
}
```

## Risk Assessment Logic

### Market Stress Levels (High Yield Spreads)
- **< 300 bps:** LOW STRESS — Benign credit environment
- **300-400 bps:** NORMAL — Spreads within historical ranges
- **400-600 bps:** MODERATE — Spreads widening
- **600-800 bps:** HIGH STRESS — Elevated default risk
- **> 800 bps:** CRISIS — Distressed levels (2008, 2020 peaks)

### Sovereign Risk Assessment
- **AAA/AA + Safe Haven:** LOW RISK — Strong fiscal position
- **A ratings:** MODERATE RISK — Stable but monitor
- **BBB ratings:** ELEVATED RISK — Watch for downgrades
- **< BBB:** HIGH RISK — Speculative grade

### Corporate Credit Estimation
Based on debt-to-equity ratios:
- **< 100:** Base IG spread (100 bps)
- **100-200:** Moderate leverage (250 bps)
- **> 200:** High leverage (400 bps)

## Supported Sovereigns

US, Germany, Japan, Italy, Spain, Greece, Brazil, China, India, Mexico

## Integration Status

- ✅ Python module: `modules/cds_spreads.py`
- ✅ API route: `src/app/api/v1/cds/route.ts`
- ✅ Service registry: Added to `services.ts`
- ✅ Roadmap: Phase 30 marked as **done** with 486 LOC
- ✅ CLI dispatcher: Commands routed through `cli.py`

## Testing

All CLI commands tested and working:
```bash
✅ python cli.py spread-compare
✅ python cli.py credit-risk-score TSLA
✅ python cli.py sovereign-spreads Germany
```

## Future Enhancements

1. **Real CDS Data:** Integrate Bloomberg or MarkIt feeds (requires license)
2. **Historical Trends:** Add time-series analysis of spread widening/tightening
3. **Default Probability Models:** Merton model, reduced-form models
4. **Basis Trading Signals:** CDS vs bond spread arbitrage opportunities
5. **Credit Event Tracking:** Ratings changes, default events, restructurings

---

**Built by:** QUANTCLAW DATA Build Agent  
**Phase:** 30  
**Status:** ✅ DONE  
**Next Phase:** 31 — Fama-French Regression
