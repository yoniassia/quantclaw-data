---
name: quantclaw-data
description: "QuantClaw Data — 452 financial data modules with CLI, REST API, and MCP interfaces. Real-time prices, technicals, options, macro, alt data, AI/ML models, fixed income, commodities, crypto, and more. 259 data sources including FRED, Yahoo Finance, SEC EDGAR, Treasury, IMF, ECB, OPEC. Bloomberg Terminal alternative built on free sources."
metadata:
  openclaw:
    requires:
      bins: ["python3"]
    install:
      - id: quantclaw-deps
        kind: shell
        command: "pip install yfinance numpy scipy pandas statsmodels pandas-datareader requests beautifulsoup4"
        label: "Install Python dependencies"
---

# QuantClaw Data — Financial Intelligence Platform

452 financial data modules. 259 data sources. Bloomberg Terminal alternative built on FREE sources.
167K+ lines of Python. $0/month operating cost.

---

## Access Methods

### 1. REST API (Live — No Auth Required)

**Internal:** `http://localhost:3055/api/v1` (from the server)
**External:** `https://data.moneyclaw.com/api/v1` (via nginx/cloudflare)

Available endpoints:

| Endpoint | Description | Example |
|----------|-------------|---------|
| `/price` | Real-time stock price + market cap | `?ticker=AAPL` |
| `/options` | Options chain data | `?ticker=TSLA` |
| `/technicals` | Technical indicators (RSI, MACD, BB, etc.) | `?ticker=NVDA` |
| `/news` | Latest news + sentiment | `?ticker=MSFT` |
| `/earnings` | Earnings data | `?ticker=GOOGL` |
| `/dividends` | Dividend history | `?ticker=KO` |
| `/macro` | Macro indicators (GDP, CPI, rates) | `?indicator=gdp` |
| `/crypto` | Crypto prices | `?symbol=BTC` |
| `/commodity` | Commodity prices | `?symbol=gold` |
| `/forex` | FX rates | `?pair=EURUSD` |
| `/profile` | Company profile | `?ticker=META` |
| `/ratings` | Analyst ratings | `?ticker=AMZN` |
| `/sec` | SEC filings | `?ticker=AAPL` |
| `/social` | Social sentiment | `?ticker=GME` |
| `/short-interest` | Short interest data | `?ticker=TSLA` |
| `/etf-holdings` | ETF constituent holdings | `?ticker=SPY` |
| `/screener` | Stock screener | `?sector=Technology&limit=10` |
| `/esg` | ESG scores | `?ticker=MSFT` |
| `/fama-french` | Fama-French factor analysis | `?ticker=AAPL` |
| `/factor-attribution` | Factor return attribution | `?ticker=NVDA` |
| `/factor-returns` | Factor return data | ` ` |
| `/13f` | Institutional 13F holdings | `?ticker=AAPL` |
| `/13f-changes` | 13F quarter-over-quarter changes | `?ticker=TSLA` |
| `/smart-money` | Smart money flow tracking | `?ticker=MSFT` |
| `/top-funds` | Top fund holdings | ` ` |
| `/gex` | Gamma exposure (GEX) | `?ticker=SPY` |
| `/pin-risk` | Options pinning risk | `?ticker=AAPL` |
| `/hedging-flow` | Hedging flow analysis | `?ticker=QQQ` |

**Example with curl:**
```bash
curl "https://data.moneyclaw.com/api/v1/price?ticker=AAPL"
# → {"ticker":"AAPL","price":265.36,"market_cap":3900241428058,"currency":"USD","exchange":"NMS"}

curl "https://data.moneyclaw.com/api/v1/technicals?ticker=TSLA"
curl "https://data.moneyclaw.com/api/v1/screener?sector=Technology&limit=5"
curl "https://data.moneyclaw.com/api/v1/13f?ticker=NVDA"
```

### 2. MCP HTTP Server (Remote Access)

**URL:** `http://localhost:3056` (port 3056, PM2 managed as `quantclaw-mcp`)

30 tools exposed over HTTP. No auth required (internal network).

**Endpoints:**
- `GET /health` — health check + tool count
- `GET /tools` — list all available tools
- `GET /tool/<name>?param=val` — call a tool via GET
- `POST /mcp/call` — call a tool via POST JSON
- `POST /mcp/batch` — batch multiple tool calls
- `POST /rpc` — JSON-RPC interface

**Examples:**
```bash
# GET style
curl "http://localhost:3056/tool/market_quote?symbol=AAPL"
curl "http://localhost:3056/tool/news?ticker=MSFT"
curl "http://localhost:3056/tool/screener?sector=Technology&limit=5"

# POST style
curl -X POST http://localhost:3056/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool":"market_quote","arguments":{"symbol":"TSLA"}}'

# Batch
curl -X POST http://localhost:3056/mcp/batch \
  -H "Content-Type: application/json" \
  -d '[{"tool":"market_quote","arguments":{"symbol":"AAPL"}},{"tool":"market_quote","arguments":{"symbol":"MSFT"}}]'

# JSON-RPC
curl -X POST http://localhost:3056/rpc \
  -H "Content-Type: application/json" \
  -d '{"method":"call_tool","params":{"tool":"market_quote","args":{"symbol":"NVDA"}}}'
```

### 3. MCP Server (stdio mode — local only)

For agents running on the same machine:
```json
{
  "mcpServers": {
    "quantclaw-data": {
      "command": "python3",
      "args": ["/home/quant/apps/quantclaw-data/mcp_server.py"]
    }
  }
}
```

### 3. CLI (210 commands)

```bash
cd /home/quant/apps/quantclaw-data

# Prices
python3 -c "from modules.price import get_price; print(get_price('AAPL'))"

# Technicals
python3 -c "from modules.technicals import get_technicals; print(get_technicals('TSLA'))"

# Screener
python3 -c "from modules.screener import run_screener; print(run_screener(sector='Technology', limit=5))"

# Monte Carlo simulation
python3 -c "from modules.monte_carlo import run_simulation; print(run_simulation('SPY', simulations=10000))"

# Fama-French factor model
python3 -c "from modules.fama_french import analyze; print(analyze('NVDA'))"

# Alpha Picker (stock scoring)
python3 -c "from modules.alpha_picker import score_stock; print(score_stock('AAPL'))"

# Options chain
python3 -c "from modules.options import get_options_chain; print(get_options_chain('TSLA'))"

# 13F institutional holdings
python3 -c "from modules.institutional_13f import get_13f; print(get_13f('AAPL'))"
```

### 4. Direct Python Import

All 452 modules are in `/home/quant/apps/quantclaw-data/modules/`. Import any module directly:

```python
import sys
sys.path.insert(0, '/home/quant/apps/quantclaw-data/modules')

from price import get_price
from technicals import get_technicals
from screener import run_screener
from alpha_picker import score_stock
from fama_french import analyze
from monte_carlo import run_simulation
from ai_research_reports import generate_research_report
```

---

## Module Categories (452 total)

**Market Data:** prices, options, technicals, forex, crypto, commodities
**Fundamentals:** earnings, dividends, profiles, SEC filings, financial statements
**Quant Models:** Fama-French, Black-Litterman, Monte Carlo, Kalman filter, pairs trading
**Alternative Data:** social sentiment, satellite imagery, web traffic, patent filings
**Institutional:** 13F holdings, smart money, hedge fund tracking, insider trading
**Macro:** FRED, World Bank, Eurostat, IMF, ECB, OPEC, BLS, Census
**Options:** GEX, pin risk, hedging flow, options chain, IV surface
**Fixed Income:** Treasury yields, corporate bonds, credit spreads
**AI/ML:** Research reports, stock scoring (Alpha Picker), signal fusion

---

## Data Sources (259)

Yahoo Finance, FRED, SEC EDGAR, U.S. Treasury, IMF, ECB, OPEC, BLS, Census Bureau, World Bank, Eurostat, CIA Factbook, FinViz, Seeking Alpha, Tipranks, OpenInsider, WhaleWisdom, and 240+ more. All free, no API keys needed.

---

## Dashboard

Web dashboard: https://data.moneyclaw.com
Shows roadmap progress, module status, and data source map.
