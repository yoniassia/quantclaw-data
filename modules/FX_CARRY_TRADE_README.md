# FX Carry Trade Monitor — Phase 182 ✅

**Status:** Complete (467 LOC)  
**Category:** FX & Crypto  
**Data Sources:** FRED API (3-month interest rates), Central Bank Policy Rates  

## Overview

Monitor interest rate differentials and identify carry trade opportunities across 10 major currency pairs. Calculate risk-adjusted carry returns using interest rate differentials and FX volatility.

## Features

### Carry Trade Logic
- **Borrow** in low-yielding currency (funding currency)
- **Invest** in high-yielding currency (investment currency)
- **Profit** = Interest Rate Differential - FX Depreciation - Transaction Costs
- **Risk-Adjusted Carry** = Rate Differential / FX Volatility (Sharpe-like ratio)

### Supported Currencies
- USD (US Dollar)
- EUR (Euro)
- JPY (Japanese Yen)
- GBP (British Pound)
- AUD (Australian Dollar)
- CAD (Canadian Dollar)
- CHF (Swiss Franc)
- NZD (New Zealand Dollar)
- SEK (Swedish Krona)
- NOK (Norwegian Krone)

### Data Sources
- **3-Month Interest Rates:** FRED API interbank rates (IR3TIB01XXM156N series)
- **FX Spot Rates:** FRED daily FX rates vs USD (DEXUSXX series)
- **FX Volatility:** Calculated from 90-day daily return standard deviation (annualized)

## CLI Commands

### 1. Carry Trade Opportunities
```bash
python cli.py carry-opportunities [min_differential]
```
List all carry trade opportunities with rate differentials above threshold (default 1.0%).

**Output:**
- Currency pair
- Funding vs investment currencies
- Interest rate differential (annualized %)
- FX volatility (annualized %)
- Risk-adjusted carry ratio
- Expected annual carry return

### 2. Rate Differential
```bash
python cli.py carry-differential USD JPY
```
Calculate detailed rate differential and carry trade metrics between two currencies.

**Output:**
- Current 3-month rates for both currencies
- Rate differential (absolute and directional)
- Recommended carry trade direction
- FX spot rates
- FX volatility
- Risk-adjusted carry

### 3. Carry Dashboard
```bash
python cli.py carry-dashboard
```
Comprehensive overview of global carry trade landscape.

**Output:**
- Total opportunities count
- Average carry of top 5 trades
- Average risk-adjusted carry of top 5 trades
- Best funding currencies (lowest rates)
- Best investment currencies (highest rates)
- Top 10 carry opportunities sorted by risk-adjusted carry

### 4. Top Funding Currencies
```bash
python cli.py carry-funding [n]
```
Get currencies with lowest interest rates (best for borrowing/funding).

### 5. Top Investment Currencies
```bash
python cli.py carry-investment [n]
```
Get currencies with highest interest rates (best for investment side).

## MCP Tools

All CLI commands are exposed via MCP protocol:

- `fx_carry_opportunities` — Identify carry trade opportunities
- `fx_carry_differential` — Calculate rate differential between two currencies
- `fx_carry_dashboard` — Full carry trade market overview
- `fx_carry_funding` — Top funding currencies
- `fx_carry_investment` — Top investment currencies

## Example Output

### Carry Dashboard
```json
{
  "timestamp": "2026-02-25T11:30:00",
  "summary": {
    "total_opportunities": 18,
    "avg_carry_top5": 3.45,
    "avg_risk_adjusted_top5": 0.412,
    "best_funding_currencies": ["JPY (0.12%)", "CHF (0.85%)", "EUR (1.22%)"],
    "best_investment_currencies": ["NZD (5.50%)", "AUD (4.85%)", "GBP (4.25%)"]
  },
  "top_opportunities": [
    {
      "pair": "JPY/NZD",
      "funding_currency": "JPY",
      "funding_rate": 0.12,
      "investment_currency": "NZD",
      "investment_rate": 5.50,
      "rate_differential": 5.38,
      "fx_volatility": 12.4,
      "risk_adjusted_carry": 0.434,
      "annual_carry_pct": 5.38
    }
  ]
}
```

### Rate Differential
```json
{
  "currency1": "JPY",
  "currency1_name": "Japanese Yen",
  "currency1_rate": 0.12,
  "currency2": "AUD",
  "currency2_name": "Australian Dollar",
  "currency2_rate": 4.85,
  "rate_differential": 4.73,
  "carry_trade_direction": "Borrow JPY, Invest AUD",
  "annual_carry_pct": 4.73,
  "fx_volatility": 11.2,
  "risk_adjusted_carry": 0.422
}
```

## Risk Considerations

**Note:** Carry trades are NOT risk-free arbitrage. Key risks:
- **FX Depreciation:** Investment currency can depreciate faster than carry earned
- **Volatility Spikes:** FX volatility can surge during market stress (e.g., risk-off events)
- **Correlation Breakdowns:** Carry trades often blow up simultaneously in crisis
- **Interest Rate Changes:** Central bank policy shifts can reverse differentials

## Data Requirements

**FRED API Key:** Required for live data. Without API key, module structure works but returns empty results.

To configure:
```python
FRED_API_KEY = "your_fred_api_key_here"  # In modules/fx_carry_trade.py
```

Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html

## Integration

✅ Module created: `modules/fx_carry_trade.py` (467 LOC)  
✅ CLI commands registered in `cli.py`  
✅ MCP tools added to `mcp_server.py`  
✅ Roadmap updated: Phase 182 marked as "done"  

## Next Steps

- **Phase 183:** FX Volatility Surface — Implied vol for major pairs, risk reversals, butterfly spreads
- **Phase 184:** EM Currency Crisis Monitor — FX reserves, current account, real effective exchange rates
- Add carry trade backtesting (historical carry returns vs realized FX moves)
- Integrate with portfolio allocation (optimal carry trade sizing)
- Add carry trade unwinding alerts (volatility spikes, correlation breakdowns)
