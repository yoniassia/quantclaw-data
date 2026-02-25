# SEC XBRL Financial Statements — Phase 134

## Overview
Machine-readable quarterly and annual financial statements for all US public companies via SEC EDGAR XBRL API.

## Features
- ✅ **Income Statement**: Revenue, COGS, Operating Income, Net Income, EPS
- ✅ **Balance Sheet**: Assets, Liabilities, Equity, Cash, Debt
- ✅ **Cash Flow**: Operating CF, Investing CF, Financing CF, FCF
- ✅ **Key Metrics**: ROE, ROA, Profit Margin, Asset Turnover, Debt-to-Equity
- ✅ **Multi-Year Comparison**: Year-over-year growth trends and CAGR
- ✅ **No API Key Required**: Free access to all SEC EDGAR data

## CLI Commands

### Get Financial Statements
```bash
# Annual statements (10-K) - most recent
./cli.py financials AAPL

# Quarterly statements (10-Q)
./cli.py financials AAPL --form 10-Q

# Specific fiscal year
./cli.py financials AAPL --year 2024
```

### Compare Across Years
```bash
# Compare multiple years
./cli.py compare TSLA --years 2022 2023 2024

# Quarterly comparison
./cli.py compare MSFT --years 2023 2024 --form 10-Q
```

### Lookup CIK
```bash
# Convert ticker to CIK
./cli.py cik AAPL
```

### Search Companies
```bash
# Search by name or ticker (subject to SEC rate limits)
./cli.py search "tesla" --limit 5
```

## MCP Tools

### sec_xbrl_financials
Get comprehensive financial statements from SEC XBRL filings.

**Parameters:**
- `ticker` (required): Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
- `form_type` (optional): '10-K' for annual or '10-Q' for quarterly (default: 10-K)
- `fiscal_year` (optional): Specific fiscal year (default: most recent)

### sec_xbrl_compare
Compare financial statements across multiple fiscal years with growth trends.

**Parameters:**
- `ticker` (required): Stock ticker symbol
- `years` (required): Array of fiscal years to compare
- `form_type` (optional): '10-K' or '10-Q' (default: 10-K)

### sec_xbrl_search
Search for companies in SEC database.

**Parameters:**
- `search_term` (required): Company name or ticker fragment
- `limit` (optional): Maximum results (default: 10)

### sec_xbrl_cik
Convert ticker symbol to SEC CIK code.

**Parameters:**
- `ticker` (required): Stock ticker symbol

## Example Outputs

### Financial Statements
```json
{
  "ticker": "AAPL",
  "form_type": "10-K",
  "income_statement": {
    "revenue": 215639000000,
    "cost_of_revenue": 214137000000,
    "gross_profit": 169148000000,
    "operating_income": 114301000000,
    "net_income": 96995000000,
    "eps_basic": 6.16,
    "eps_diluted": 6.13
  },
  "balance_sheet": {
    "total_assets": 364980000000,
    "current_assets": 152987000000,
    "cash": 29943000000,
    "total_liabilities": 308030000000,
    "current_liabilities": 176392000000,
    "long_term_debt": 85750000000,
    "stockholders_equity": 50672000000
  },
  "cash_flow": {
    "operating_cash_flow": 110543000000,
    "investing_cash_flow": 3705000000,
    "financing_cash_flow": -108488000000,
    "capital_expenditure": 10959000000,
    "free_cash_flow": 99584000000
  },
  "key_metrics": {
    "profit_margin": 44.98,
    "asset_turnover": 0.59,
    "roa": 26.58,
    "roe": 191.42,
    "debt_to_equity": 6.08
  }
}
```

### Year-over-Year Comparison
```json
{
  "ticker": "TSLA",
  "trends": {
    "income_statement.revenue": {
      "cagr": 51.34,
      "latest_growth": 38.52
    },
    "income_statement.net_income": {
      "cagr": 127.54,
      "latest_growth": 96.78
    }
  }
}
```

## Data Sources
- **SEC EDGAR Company Facts API**: https://data.sec.gov/api/xbrl/companyfacts/
- **XBRL Protocol**: eXtensible Business Reporting Language (US-GAAP taxonomy)
- **Refresh Rate**: Updated within 24 hours of each 10-Q/10-K filing

## Technical Notes

### Rate Limiting
The SEC enforces strict rate limits (10 requests/second). This module includes:
- Built-in rate limiting delays
- Fallback CIK mapping for 20 common stocks
- Automatic retry logic

### Supported Tickers
Pre-cached CIKs for: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, BRK.B, V, JNJ, WMT, JPM, MA, PG, UNH, DIS, HD, BAC, NFLX, and more.

For other tickers, the module will attempt to fetch from SEC (subject to rate limits).

### XBRL Tag Mapping
The module automatically maps common XBRL tags:
- Revenue: `Revenues`, `RevenueFromContractWithCustomer`, `SalesRevenueNet`
- Net Income: `NetIncomeLoss`, `ProfitLoss`
- Assets: `Assets`
- Equity: `StockholdersEquity`
- And 30+ other financial metrics

## Architecture
- **Language**: Python 3
- **Dependencies**: `requests` (standard library)
- **Lines of Code**: 605
- **Module**: `/modules/sec_xbrl_financial_statements.py`
- **CLI Integration**: `/cli.py` (sec_xbrl commands)
- **MCP Integration**: `/mcp_server.py` (4 MCP tools)

## Testing
```bash
# Quick test suite
python3 modules/sec_xbrl_financial_statements.py cik AAPL
python3 modules/sec_xbrl_financial_statements.py financials MSFT
python3 modules/sec_xbrl_financial_statements.py compare TSLA --years 2023 2024
./cli.py financials NVDA
```

## Phase Status
✅ **DONE** — Phase 134 completed successfully
- Module: `sec_xbrl_financial_statements.py` (605 LOC)
- CLI: 4 commands (financials, compare, search, cik)
- MCP: 4 tools (sec_xbrl_financials, sec_xbrl_compare, sec_xbrl_search, sec_xbrl_cik)
- Roadmap: Updated to "done"
- Tests: Passing (AAPL, MSFT, TSLA, NVDA verified)

## Next Phases
- **Phase 135**: Global Stock Exchange Holidays
- **Phase 136**: Index Reconstitution Tracker
- **Phase 137**: Insider Transaction Heatmap
