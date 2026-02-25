# Earnings Surprise History — Phase 144 ✅

**Status:** COMPLETE  
**Category:** Equity  
**LOC:** 820 lines  
**Data Sources:** Yahoo Finance (earnings history, price data)

---

## Overview

Historical earnings surprise analysis tracking beat/miss patterns, whisper number estimates, and post-earnings announcement drift (PEAD). Provides comprehensive insights into a company's earnings track record and market reaction patterns.

---

## Features

### 1. **Earnings Surprise History** (`earnings-history`)
- Complete quarterly earnings surprise data
- Actual vs estimated EPS comparison
- Revenue surprise tracking (when available)
- Beat/miss/inline classification
- Post-earnings price drift (1d, 3d, 5d)
- Summary statistics (beat rate, average surprise)

### 2. **Surprise Pattern Analysis** (`surprise-patterns`)
- Beat/miss rate calculation
- Current streak tracking
- Longest beat/miss streaks
- Surprise consistency scoring (0-100)
- Surprise trend analysis (IMPROVING/DECLINING/STABLE)
- Median vs average surprise comparison

### 3. **Whisper Number Estimation** (`whisper-numbers`)
- Pre-earnings price drift analysis
- Estimated "whisper" number vs official estimate
- Beat whisper vs beat estimate tracking
- Confidence levels (HIGH/MEDIUM/LOW)
- Whisper accuracy rate

### 4. **Post-Earnings Drift (PEAD)** (`post-earnings-drift`)
- Price movement analysis (1d, 3d, 5d, 10d post-earnings)
- Volume spike detection
- Drift direction classification (POSITIVE/NEGATIVE/NEUTRAL)
- Drift strength scoring (STRONG/MODERATE/WEAK)
- Surprise-drift correlation analysis

### 5. **Earnings Quality Score** (`earnings-quality-score`)
- Composite quality score (0-100)
- Component scores:
  - Consistency score
  - Beat streak score
  - Surprise magnitude score
  - Guidance accuracy score
  - Revenue-EPS correlation
- Quality rating (EXCELLENT/GOOD/FAIR/POOR)
- Key strengths and weaknesses identification

### 6. **Comparative Analysis** (`compare-surprises`)
- Multi-ticker beat rate comparison
- Average surprise comparison
- Current streak comparison
- Sorted by beat rate

---

## CLI Commands

```bash
# Get complete earnings surprise history
python cli.py earnings-history AAPL 12

# Analyze beat/miss patterns
python cli.py surprise-patterns MSFT

# Estimate whisper numbers from price action
python cli.py whisper-numbers GOOGL 8

# Analyze post-earnings drift
python cli.py post-earnings-drift NVDA 12

# Calculate earnings quality score
python cli.py earnings-quality-score TSLA

# Compare multiple tickers
python cli.py compare-surprises AAPL MSFT GOOGL NVDA
```

---

## MCP Tools (6 tools)

1. **`earnings_surprise_history`** — Get historical earnings surprises
2. **`earnings_surprise_patterns`** — Analyze beat/miss patterns
3. **`earnings_whisper_numbers`** — Estimate whisper numbers
4. **`earnings_post_drift`** — Analyze post-earnings drift
5. **`earnings_quality_score`** — Calculate quality score
6. **`earnings_compare_surprises`** — Compare multiple tickers

---

## Example Output

### Earnings History (AAPL)
```json
{
  "ticker": "AAPL",
  "total_quarters": 4,
  "beats": 3,
  "misses": 0,
  "inline": 1,
  "beat_rate": 75.0,
  "avg_surprise_pct": 5.48,
  "avg_drift_1d": -1.28,
  "avg_drift_3d": -1.28,
  "avg_drift_5d": -1.07,
  "surprises": [...]
}
```

### Surprise Patterns (MSFT)
```json
{
  "ticker": "MSFT",
  "beat_rate": 80.0,
  "current_streak": 6,
  "current_streak_type": "BEAT",
  "longest_beat_streak": 6,
  "avg_surprise_pct": 8.43,
  "surprise_consistency": 0,
  "surprise_trend": "IMPROVING"
}
```

### Earnings Quality (TSLA)
```json
{
  "ticker": "TSLA",
  "quality_score": 55.6,
  "quality_rating": "FAIR",
  "key_strengths": [
    "Strong beat streak (8 quarters)"
  ],
  "key_weaknesses": [
    "Inconsistent surprises"
  ]
}
```

---

## Use Cases

### For Investors
- **Track earnings reliability:** Identify companies with consistent beat patterns
- **Pre-earnings positioning:** Use whisper numbers to gauge market expectations
- **Post-earnings strategy:** Understand typical price reaction patterns

### For Traders
- **PEAD trading:** Exploit post-earnings drift patterns
- **Earnings play timing:** Identify optimal entry/exit points around earnings
- **Volatility trading:** Anticipate earnings reaction magnitude

### For Analysts
- **Company quality assessment:** Earnings quality scoring
- **Peer comparison:** Compare earnings track records across competitors
- **Trend analysis:** Identify improving/declining earnings execution

---

## Data Quality Notes

1. **Yahoo Finance Limitations:**
   - Revenue estimates not always available (especially for older quarters)
   - Historical estimates may be revised
   - Some companies have incomplete earnings history

2. **Whisper Number Methodology:**
   - Estimates based on pre-earnings price drift (5 days before)
   - Not actual "street whispers" (those require paid services)
   - Confidence scoring based on drift magnitude

3. **PEAD Accuracy:**
   - Price drift calculated from close prices (not intraday)
   - Volume spikes calculated from daily volume data
   - Does not account for after-hours price movement

4. **Quality Score Components:**
   - Consistency: Variance-based scoring (lower variance = higher score)
   - Beat Streak: Weighted by beat rate + longest streak
   - Surprise Magnitude: Positive surprises weighted higher
   - Revenue-EPS Correlation: Available only when revenue data exists

---

## Research Foundation

### Academic Papers
1. **Post-Earnings Announcement Drift (PEAD)**
   - Bernard & Thomas (1989) — Original PEAD discovery
   - Ball & Brown (1968) — Earnings information content
   - Chan et al. (1996) — Momentum strategies

2. **Whisper Numbers**
   - Bagnoli et al. (2001) — Whisper forecasts vs analyst estimates
   - Matsumoto (2002) — Management's incentives for guidance

3. **Earnings Quality**
   - Richardson et al. (2005) — Accrual reliability
   - Dechow & Dichev (2002) — Earnings quality measurement

---

## Next Steps (Future Enhancements)

1. **Real Whisper Numbers:** Integrate paid data source (Estimize, etc.)
2. **Analyst Revision Tracking:** Link to Phase 145 (Analyst Target Price Tracker)
3. **Options IV Analysis:** Pre-earnings implied volatility vs realized
4. **Sector-Relative Surprises:** Compare surprise magnitude vs sector average
5. **Guidance Analysis:** Track management guidance accuracy separately
6. **Intraday PEAD:** Use minute-level data for more precise drift measurement

---

## Testing Results

All 6 CLI commands tested and working:
- ✅ `earnings-history AAPL 4`
- ✅ `surprise-patterns MSFT`
- ✅ `whisper-numbers NVDA 4`
- ✅ `post-earnings-drift NVDA 4`
- ✅ `earnings-quality-score TSLA`
- ✅ `compare-surprises AAPL MSFT GOOGL`

---

**Built by:** QUANTCLAW DATA Build Agent  
**Completed:** February 25, 2026  
**Phase:** 144 of 200  
**Status:** ✅ DONE
