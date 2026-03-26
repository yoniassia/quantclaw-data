# QuantClaw Data — 1,000+ Financial Data Modules

> The world's most comprehensive open financial data platform.
> 1,023 Python modules • MCP server • REST API • Natural Language Query • Terminal UI

**Live:** https://data.quantclaw.org · **Port:** 3055 · **PM2:** quantclaw-data

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Categories](#data-categories)
- [Module Catalog](#module-catalog)
- [MCP Server](#mcp-server)
- [REST API](#rest-api)
- [Natural Language Queries (DCC)](#natural-language-queries-dcc)
- [Terminal UI](#terminal-ui)
- [Data Sources & API Keys](#data-sources--api-keys)
- [Caching Layer](#caching-layer)
- [Development Phases](#development-phases)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Deployment](#deployment)

---

## Overview

QuantClaw Data is a massive financial data aggregation platform that unifies 1,023 Python data modules behind a single API. It provides real-time and historical data across equities, options, fixed income, crypto, commodities, forex, macro, alternative data, and quantitative analytics. The platform serves as the data backbone for the entire MoneyClawX ecosystem (AgentX, TerminalX, PICentral, VIP Signals).

**Key numbers:**
- **1,023** Python data modules
- **9** data categories (Core Market, Derivatives, Alt Data, Multi-Asset, Quant, Fixed Income, Events, Intelligence, Infrastructure)
- **47** completed development phases
- **30+** external API integrations
- **MCP protocol** support for AI agent tool calling
- **Natural language** query engine (DCC — Data Command Center)
- **Terminal-grade UI** with draggable panel grid

**How it's used:**
- AgentX signal generator fetches quotes, technicals, ratings, alpha scores
- TerminalX research views pull from 435+ modules
- PICentral research terminal uses 16 QuantClaw functions
- VIP Signals engine queries technicals and external signals

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 15.x |
| Language | TypeScript (web) + Python (modules) | 5.x / 3.14 |
| UI | React + Tailwind CSS | 19.x / 4.x |
| State | Zustand | 5.x |
| Charts | Lightweight Charts + Recharts | 5.x / 3.x |
| Tables | TanStack React Table | 8.x |
| Layout | react-grid-layout | 2.x |
| Database | PostgreSQL | 8.x |
| Process | PM2 | — |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Terminal UI (Next.js)                           │
│  ├── Draggable panel grid (TerminalGrid)        │
│  ├── Module browser (1,023 modules)             │
│  ├── Chart panels (TradingView-style)           │
│  ├── Ticker panels (real-time prices)           │
│  ├── News panels                                │
│  ├── Heatmap panels                             │
│  └── DCC Natural Language Query interface        │
├─────────────────────────────────────────────────┤
│  Next.js API Layer                               │
│  ├── /api/data?tool=X&params=Y (MCP proxy)      │
│  ├── /api/v1/{module}?params (REST API)          │
│  └── /api/dcc (natural language queries)         │
├─────────────────────────────────────────────────┤
│  MCP Server (Model Context Protocol)             │
│  ├── Tool definitions for all 1,023 modules      │
│  ├── AI agent interface (AgentX, PICentral)      │
│  └── callTool(), batchCall() patterns            │
├─────────────────────────────────────────────────┤
│  1,023 Python Modules                            │
│  ├── Each module = self-contained data fetcher   │
│  ├── Standardized input/output interface         │
│  ├── Built-in caching (file + memory)            │
│  └── Error handling + fallback logic             │
├─────────────────────────────────────────────────┤
│  External APIs                                   │
│  ├── FRED, Yahoo Finance, Financial Datasets     │
│  ├── Finnhub, CoinGecko, Etherscan              │
│  ├── SEC EDGAR, Census, EIA, USDA               │
│  ├── Polygon, Alpha Vantage, GuruFocus          │
│  └── 20+ more sources                            │
└─────────────────────────────────────────────────┘
```

---

## Data Categories

| Category | Icon | Modules | Description |
|----------|------|---------|-------------|
| Core Market Data | 📊 | ~150 | Prices, profiles, screeners, technicals, microstructure |
| Derivatives & Options | 📈 | ~80 | Options chains, Greeks, GEX tracking, flow scanner, volatility surface |
| Alternative Data | 🔍 | ~200 | Patents, job postings, supply chain, congress trades, social sentiment, satellite |
| Multi-Asset | 🌍 | ~120 | Crypto, commodities, forex, global indices, ETFs |
| Quantitative | 🧮 | ~150 | Factor models, portfolio analytics, backtesting, correlation, VaR |
| Fixed Income & Macro | 🏦 | ~100 | Yield curves, credit spreads, FRED macro data, central bank rates |
| Corporate Events | 📰 | ~80 | IPOs, SPACs, M&A, activist campaigns, earnings, dividends |
| Intelligence & NLP | 🤖 | ~80 | SEC NLP, earnings transcripts, AI research reports, news sentiment |
| Infrastructure | ⚙️ | ~60 | Data quality monitoring, streaming, alerts, caching |

---

## Module Catalog (Selected Highlights)

### Core Market Data
`prices`, `company_profile`, `screener`, `technicals`, `market_microstructure`, `analyst_ratings`, `market_quote`, `alpha_picker`

### Derivatives
`options_chain`, `options_flow`, `options_gex_tracker`, `cboe_put_call`, `volatility_surface`, `implied_volatility`

### Alternative Data
`congress_trades`, `patent_tracking`, `job_posting_signals`, `supply_chain_mapping`, `reddit_sentiment`, `insider_trades`, `short_interest`, `satellite_data`, `web_traffic_estimator`, `whale_wallet_tracker`

### Multi-Asset
`crypto_onchain`, `coingecko`, `commodity_prices`, `forex_rates`, `etf_holdings`, `adr_gdr_arbitrage`, `baltic_dry_index`

### Quantitative
`factor_model`, `portfolio_analytics`, `backtesting`, `correlation_heatmap`, `quant_factor_zoo`, `xgboost_alpha`, `monte_carlo`, `kelly_criterion`

### Fixed Income & Macro
`yield_curve`, `credit_spreads`, `fred_enhanced`, `central_bank_rates`, `treasury_curve`, `inflation_linked_bonds`, `fed_funds_futures`

### Corporate Events
`ipo_tracker`, `spac_tracker`, `ma_deal_flow`, `activist_investor`, `earnings_calendar`, `dividend_tracker`, `regulatory_calendar`

### Intelligence & NLP
`sec_nlp`, `earnings_transcripts`, `ai_research_reports`, `news_sentiment`, `ml_earnings_predictor`

---

## MCP Server

QuantClaw Data serves as an MCP (Model Context Protocol) server, allowing AI agents to call any data module as a tool.

### Tool Calling Pattern
```typescript
// From any client (AgentX, PICentral, etc.)
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'market_quote',
    params: { ticker: 'AAPL' }
  })
});
```

### Batch Calling
```typescript
const results = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'market_quote', params: { ticker: 'AAPL' } },
      { tool: 'technicals', params: { ticker: 'AAPL' } },
      { tool: 'ratings', params: { ticker: 'AAPL' } }
    ]
  })
});
```

### Common Tools Used by Platform

| Tool | Used By | Description |
|------|---------|-------------|
| `market_quote` | AgentX, TerminalX, PICentral | Real-time price + fundamentals |
| `technicals` | AgentX, VIP Signals | RSI, MACD, Bollinger, SMA |
| `ratings` | AgentX, PICentral | Analyst consensus + target prices |
| `alpha_picker` | AgentX | AI-generated alpha score |
| `news` | All | Latest news + sentiment |
| `smart_money` | AgentX, TerminalX | Institutional flow tracking |
| `short_interest` | TerminalX, PICentral | Short interest data |
| `earnings` | AgentX, PICentral | Earnings calendar + surprises |
| `screener` | PICentral | Multi-criteria stock screener |
| `profile` | All | Company overview + fundamentals |

---

## REST API

### Module Execution
```
GET /api/v1/{module-name}?param1=value1&param2=value2
POST /api/data?tool={module_name}&params={json}
```

### Auto-Generated Endpoints
Each of the 1,023 modules gets an auto-generated REST endpoint:
```
/api/v1/prices?ticker=AAPL
/api/v1/technicals?ticker=AAPL&indicators=rsi,macd
/api/v1/screener?min-cap=10B&sector=Technology
/api/v1/options-chain?ticker=AAPL&expiration=2026-04-17
/api/v1/fred-enhanced?series=GDP&start=2020-01-01
```

---

## Natural Language Queries (DCC)

The Data Command Center (DCC) allows natural language queries against all 1,023 modules:

### Architecture
- `src/lib/nl-query-engine.ts` — Query understanding + module routing
- `src/lib/nl-query-db.ts` — Query history + caching
- `src/lib/nl-conversations.ts` — Conversation context management
- `src/lib/schema-catalog.ts` — Module schema registry

### Example Queries
```
"What's the current price of Apple?"           → prices module
"Show me RSI and MACD for Tesla"               → technicals module
"Which stocks have insider buying this week?"   → insider_trades module
"Compare yields on 2Y vs 10Y treasuries"       → yield_curve module
"Find tech stocks with PE under 15"            → screener module
```

---

## Terminal UI

### Panel System
The terminal UI uses a draggable grid layout with multiple panel types:

| Panel | Description |
|-------|-------------|
| **ModuleBrowserPanel** | Browse and search all 1,023 modules by category |
| **DataModulePanel** | Execute a module and display results |
| **ChartPanel** | TradingView-style candlestick/line charts |
| **TickerPanel** | Real-time price ticker |
| **WatchlistPanel** | Multi-ticker watchlist |
| **NewsPanel** | Financial news feed |
| **HeatmapPanel** | Market heatmap visualization |
| **StatusPanel** | System health and API status |
| **WelcomePanel** | Onboarding + getting started |

### Command Bar
Terminal-style command input for quick module execution:
```
price AAPL
technicals TSLA --indicators rsi,macd
screen --min-cap 10B --sector Technology
```

### Access Control
- Login page with access code (default: `QuantData2026!`)
- Session-based authentication

---

## Data Sources & API Keys

| Source | Key Required | Free Tier | Data |
|--------|-------------|-----------|------|
| FRED | Yes | Unlimited | 800K+ macro time series |
| Yahoo Finance | No | — | Prices, quotes, history |
| Financial Datasets | Yes | Limited | Fundamentals, insider, filings |
| Finnhub | Yes | 60/min | Real-time quotes, IPOs |
| CoinGecko | No | 30/min | Crypto data |
| Etherscan | Yes | 5/sec | Ethereum on-chain |
| SEC EDGAR | No | 10/sec | Filings, ownership |
| Census Bureau | Yes | Unlimited | Economic indicators |
| EIA | Yes | Unlimited | Energy data |
| Polygon | Yes | 5/min | Market data, options |
| USDA NASS | Yes | Unlimited | Agriculture data |
| Alpha Vantage | Optional | 25/day | Intl stocks, forex |

---

## Caching Layer

```
cache/
├── {module_name}/
│   └── {cache_key}.json    # Module-level file cache
├── .cache/
│   └── alpha_picker/
│       └── yfinance_cache.db  # SQLite cache for yfinance
```

- Each module implements its own caching strategy
- Default TTL varies by data type (1 min for prices, 24h for fundamentals)
- Cache invalidation on module re-execution with `force=true`

---

## Development Phases

47 phases completed across 9 categories:

| Phase Range | Category | Highlights |
|-------------|----------|------------|
| 1–4 | Foundation | Prices, options, sentiment, multi-asset, screener |
| 5–10 | Intelligence & Infra | NLP, options flow, factor models, portfolio analytics, backtesting, alerts |
| 11–16 | Alt Data & Fixed Income | Patents, jobs, supply chain, weather, bonds, SEC NLP |
| 17–20 | Events & ESG | IPO/SPAC, M&A, activist, ESG scoring |
| 21–25 | Quant & Streaming | Factor Zoo (400+ factors), microstructure, AI reports, data quality, WebSocket |
| 26–30 | ML & Advanced | ML earnings predictor, correlation regime detection, GEX, 13F replication, dark pool |
| 31–40 | Sector-Specific | Real estate, energy, shipping, climate, demographics, healthcare, agriculture |
| 41–47 | Global & Specialized | APAC data (BOJ, BOK, NBS), Israel CBS, Euro, central banks, EM, nuclear |

---

## Project Structure

```
quantclaw-data/
├── modules/                          # 1,023 Python data modules
│   ├── prices.py                     # Stock prices (Yahoo Finance)
│   ├── technicals.py                 # Technical analysis indicators
│   ├── alpha_picker.py               # AI alpha scoring
│   ├── options_chain.py              # Options data
│   ├── fred_enhanced.py              # FRED macro data
│   ├── congress_trades.py            # Congressional trading
│   ├── insider_trades.py             # Insider buying/selling
│   ├── ... (1,023 modules total)
│   └── zillow_zhvi.py               # Zillow home values
├── src/
│   ├── app/
│   │   ├── page.tsx                  # Main terminal UI
│   │   ├── layout.tsx                # Root layout
│   │   ├── globals.css               # Terminal dark theme
│   │   ├── terminal-theme.css        # Terminal-specific styles
│   │   ├── login/page.tsx            # Access code login
│   │   ├── tutorial/page.tsx         # Getting started guide
│   │   ├── services.ts              # Service/module catalog
│   │   ├── roadmap.ts               # 47 development phases
│   │   ├── install.ts               # Module dependency installer
│   │   └── dcc/                     # Data Command Center
│   │       ├── page.tsx             # DCC view
│   │       ├── layout.tsx           # DCC layout
│   │       └── nl-query-view.tsx    # Natural language query UI
│   ├── components/
│   │   ├── panels/
│   │   │   ├── ChartPanel.tsx       # TradingView-style charts
│   │   │   ├── DataModulePanel.tsx  # Module execution panel
│   │   │   ├── HeatmapPanel.tsx     # Market heatmap
│   │   │   ├── ModuleBrowserPanel.tsx # Module catalog browser
│   │   │   ├── NewsPanel.tsx        # News feed
│   │   │   ├── StatusPanel.tsx      # System status
│   │   │   ├── TickerPanel.tsx      # Price ticker
│   │   │   ├── WatchlistPanel.tsx   # Watchlist
│   │   │   └── WelcomePanel.tsx     # Welcome/onboarding
│   │   └── terminal/
│   │       ├── CommandBar.tsx       # Terminal command input
│   │       ├── Panel.tsx            # Base panel component
│   │       └── TerminalGrid.tsx     # Draggable grid layout
│   ├── lib/
│   │   ├── db.ts                    # PostgreSQL client
│   │   ├── nl-query-engine.ts       # NL query engine
│   │   ├── nl-query-db.ts          # Query history DB
│   │   ├── nl-conversations.ts     # Conversation context
│   │   ├── schema-catalog.ts       # Module schema registry
│   │   └── sapi-db.ts              # Structured API database
│   ├── store/
│   │   ├── terminal-store.ts       # Terminal UI state
│   │   └── dcc-store.ts           # DCC state
│   └── middleware.ts               # Auth + security
├── cache/                           # Module response cache
├── backups_api_migration/           # Migration backups
├── .env.example
├── .github/workflows/
│   ├── ci.yml
│   └── weekly-test.yml
├── DSL_QUICK_REFERENCE.md
├── API_KEYS_QUICKSTART.md
├── package.json
└── tsconfig.json
```

---

## Environment Variables

```bash
# API Keys (most have free tiers)
FRED_API_KEY=                        # Federal Reserve Economic Data
EIA_API_KEY=                         # Energy Information Administration
CENSUS_API_KEY=                      # US Census Bureau
FINANCIAL_DATASETS_API_KEY=          # Financial Datasets (fundamentals)
FINNHUB_API_KEY=                     # Finnhub (real-time quotes)
ETHERSCAN_API_KEY=                   # Etherscan (Ethereum data)
POLYGON_API_KEY=                     # Polygon.io (market data)
USDA_NASS_API_KEY=                   # USDA agriculture data

# Optional
ALPHA_VANTAGE_API_KEY=               # International stocks
FMP_API_KEY=                         # Financial Modeling Prep
BOK_API_KEY=                         # Bank of Korea
COMTRADE_API_KEY=                    # UN trade data

# App
ACCESS_CODE=QuantData2026!           # Login access code
DATABASE_URL=                        # PostgreSQL connection
```

---

## Getting Started

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (for data modules)
pip install -r requirements.txt  # or per-module as needed

# Copy environment
cp .env.example .env
# Fill in API keys (most have free tiers)

# Start development server
npm run dev
# → http://localhost:3055

# Build for production
npm run build
npm run start
```

---

## Deployment

- **Server:** Hostinger VPS (76.13.147.35), 8 vCPU
- **Process:** PM2 (`quantclaw-data`)
- **Nginx:** SSL, reverse proxy → port 3055
- **DNS:** Cloudflare → data.quantclaw.org
- **CI:** GitHub Actions + weekly automated tests

```bash
cd /home/quant/apps/quantclaw-data
git pull
npm install
NODE_OPTIONS="--max-old-space-size=2048" npm run build
pm2 restart quantclaw-data
```

*1,023 modules • 47 phases • The data layer powering the MoneyClawX ecosystem*
