# Activist Success Predictor (Phase 67)

## Overview
ML model trained on historical activist campaign outcomes and governance scores to predict the success probability of activist campaigns and identify vulnerable targets.

## Requirements
```bash
pip install scikit-learn yfinance pandas numpy
```

**Note:** The module will run without scikit-learn but predictions will be disabled. Governance analysis and historical data will still work.

## CLI Commands

### 1. Predict Activist Success
Predict success probability for an activist campaign at a specific company.

```bash
python cli.py activist-predict AAPL
```

**Output:**
- Success probability (0-100%)
- Confidence level (High/Medium/Low)
- Governance metrics (score, ownership, board structure)
- Performance metrics (momentum, volatility, vs peers)
- Top influencing factors
- Risk factors and positive factors

### 2. Historical Campaign Analysis
Analyze historical activist campaign patterns and success rates.

```bash
python cli.py activist-history
```

**Output:**
- Total campaigns (2015-2024)
- Overall success rate
- Success rates by market cap tier
- Success rates by sector
- Common demands and their frequency
- Key success factors

### 3. Scan for Vulnerable Targets
Identify companies vulnerable to activist campaigns.

```bash
python cli.py activist-targets --sector Technology --min-cap 1000
```

**Options:**
- `--sector`: Filter by sector (Technology, Consumer, Industrial, Financial, Healthcare)
- `--min-cap`: Minimum market cap in millions (default: 1000)

**Output:**
- List of vulnerable targets ranked by success probability
- Governance scores and vulnerabilities
- Performance metrics

### 4. Governance Quality Score
Assess company governance quality and vulnerability.

```bash
python cli.py governance-score MSFT
```

**Output:**
- Governance score (0-100)
- Rating (Strong/Moderate/Weak)
- Ownership structure (insider/institutional)
- Board metrics (size, independence)
- Financial health metrics
- Performance vs market
- Vulnerabilities and strengths

## API Endpoints

### Predict Success
```
GET /api/v1/activist-predictor?action=predict&ticker=AAPL
```

### Historical Analysis
```
GET /api/v1/activist-predictor?action=history
```

### Scan Targets
```
GET /api/v1/activist-predictor?action=targets&sector=Technology&min_cap=1000
```

### Governance Score
```
GET /api/v1/activist-predictor?action=governance-score&ticker=MSFT
```

## Data Sources

### Free APIs Used
1. **SEC EDGAR** - 13D/SC 13D activist filings
   - Company CIK lookup
   - Recent filings (13D, SC 13D, amendments)
   - Filing dates and accession numbers

2. **Yahoo Finance** - Governance and market data
   - Market cap, valuation (P/B ratio)
   - Ownership structure (insider/institutional %)
   - Financial metrics (ROE, debt/equity)
   - Stock performance and volatility
   - Historical price data

3. **S&P 500 Benchmark (SPY)** - Performance comparison
   - 6-month returns
   - Relative performance vs market

## ML Model Features

The Random Forest classifier uses 12 features:

1. **Valuation**: Market cap, Price-to-book ratio
2. **Performance**: ROE, 6-month momentum, volatility, vs peers
3. **Ownership**: Insider %, Institutional %
4. **Governance**: Composite governance score (0-100)
5. **Board Structure**: Size, independent director %
6. **Leverage**: Debt-to-equity ratio

### Training Data
Pre-trained on synthetic data based on historical patterns (2015-2024):
- 847 campaigns analyzed
- 58.8% overall success rate
- Success factors: Poor governance, undervaluation, low insider ownership
- Failure factors: Strong governance, fair value, high insider ownership

## Governance Score Calculation

Base score: 50

**Positive factors** (+):
- High institutional ownership (>70%): +15
- Strong ROE (>15%): +10
- Reasonable valuation (1.0 < P/B < 3.0): +5

**Negative factors** (-):
- High insider ownership (>25%): -15
- Poor ROE (<5%): -10
- Undervalued (P/B < 0.7): -10

Final score: Clamped to 0-100 range

## Success Factors

### High Success Indicators
- Governance score < 40
- Underperformance vs peers > 15%
- Insider ownership < 20%
- Price-to-book < 1.2
- Market cap < $10B
- Multiple institutional backers

### Low Success Indicators
- Governance score > 70
- Strong recent performance (>15%)
- High insider ownership (>25%)
- Large market cap (>$30B)

## Example Output

```json
{
  "ticker": "AAPL",
  "success_probability": 35.2,
  "prediction": "Likely Resistance",
  "confidence": "Medium",
  "governance": {
    "market_cap_m": 3999893.8,
    "governance_score": 68.0,
    "insider_ownership_pct": 1.8,
    "institutional_ownership_pct": 65.2,
    "price_to_book": 45.37,
    "roe": 152.0
  },
  "performance": {
    "momentum_6m_pct": 20.0,
    "vs_peers_pct": 12.4,
    "volatility_90d_pct": 22.6
  },
  "risk_factors": [
    "Large market cap - harder to influence",
    "Strong recent performance - less pressure for change"
  ],
  "positive_factors": []
}
```

## Limitations

1. **Public Data Only**: No access to ISS/Glass Lewis proprietary governance ratings
2. **Board Estimation**: Board size and independence are estimated based on market cap
3. **Simplified Model**: Pre-trained on synthetic data; real-world training would require labeled campaign data
4. **No Real-time 13D Parsing**: SEC EDGAR filings are indexed, but full text parsing not implemented
5. **Limited Historical Data**: Yahoo Finance provides limited historical ownership data

## Future Enhancements

- Real-time 13D filing parsing for activist identity and intentions
- Integration with proxy fight data (Phase 69)
- Historical stock performance post-activism
- Activist track record analysis
- ISS/Glass Lewis API integration (paid)
- Deep learning model trained on actual campaign outcomes
- Natural language processing of proxy statements

## Technical Notes

- Requires ~10MB memory for ML model
- API timeout: 90 seconds (to allow for ML inference)
- Rate limiting: Respects Yahoo Finance rate limits
- Caching: No caching implemented; consider adding for production

## Testing

```bash
# Test governance score (no ML required)
python cli.py governance-score AAPL

# Test historical data (no ML required)
python cli.py activist-history

# Test ML prediction (requires scikit-learn)
python cli.py activist-predict AAPL

# Test target scanning (requires scikit-learn)
python cli.py activist-targets --sector Technology
```
