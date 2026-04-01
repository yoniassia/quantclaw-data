# QuantClaw Data — 1,034 Financial Data Modules

> The world's most comprehensive open financial data platform.
> 1,034 Python modules • MCP server • REST API • Natural Language Query • Terminal UI

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

QuantClaw Data is a massive financial data aggregation platform that unifies 1,034 Python data modules behind a single API. It provides real-time and historical data across equities, options, fixed income, crypto, commodities, forex, macro, alternative data, and quantitative analytics. The platform serves as the data backbone for the entire MoneyClawX ecosystem (AgentX, TerminalX, PICentral, VIP Signals).

**Key numbers:**
- **1,034** Python data modules
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
│  ├── Module browser (1,034 modules)             │
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
│  ├── Tool definitions for all 1,034 modules      │
│  ├── AI agent interface (AgentX, PICentral)      │
│  └── callTool(), batchCall() patterns            │
├─────────────────────────────────────────────────┤
│  1,034 Python Modules                            │
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

### European Government Statistics & Central Banks (Autobuilder Batch 1)

Nine new modules covering 7 European countries with 130+ macroeconomic indicators from official government statistical offices and central banks:

| Module | Source | Country | API | Key Indicators |
|--------|--------|---------|-----|----------------|
| `bundesbank_sdmx` | Deutsche Bundesbank | Germany / Euro Area | `https://api.statistiken.bundesbank.de/rest` | Bund yields (1Y–30Y), ECB policy rates, MFI lending rates, M2/M3 monetary aggregates, current account, trade balance |
| `insee_france` | INSEE (National Statistics) | France | `https://bdm.insee.fr/series/sdmx` | GDP growth, CPI/HICP inflation, unemployment rate, industrial production, consumer confidence, household consumption, exports/imports |
| `banque_de_france` | Banque de France Webstat | France | `https://webstat.banque-france.fr/api/explore/v2.1` | EUR/USD/GBP/JPY/CHF/CNY FX rates, credit to NFCs & households, MFI interest rates, BoP, SME credit, business climate |
| `istat_italy` | ISTAT (National Statistics) | Italy | `http://sdmx.istat.it/SDMXWS/rest` | GDP quarterly accounts, CPI NIC & HICP, unemployment rate, industrial production, consumer & business confidence (IESI) |
| `cbs_netherlands` | CBS StatLine | Netherlands | `https://opendata.cbs.nl/ODataApi/odata` | GDP growth (YoY/QoQ), CPI, unemployment, house prices, trade balance, gov balance/debt (% GDP), consumer/producer confidence |
| `statistics_denmark` | Statistics Denmark (DST) | Denmark | `https://api.statbank.dk/v1` | GDP (nominal/real), CPI/HICP, unemployment, foreign trade, housing prices, consumer confidence, industrial production |
| `scb_sweden` | SCB (Statistics Sweden) | Sweden | `https://api.scb.se/OV0104/v1/doris/en/ssd` | GDP (QoQ + monthly indicator), CPI/CPIF, unemployment/employment rate, housing prices, production index, trade balance, govt debt |
| `riksbank_sweden` | Sveriges Riksbank | Sweden | `https://api.riksbank.se/swea/v1` | Policy/deposit/lending rates, SEK FX crosses (EUR/USD/GBP/JPY/CHF/NOK/DKK), KIX index, govt bond yields (2Y–10Y), T-bills, mortgage bonds |
| `banco_de_espana` | Banco de España | Spain / Euro Area | `https://app.bde.es/bierest/resources/srdatosapp` | Euribor (1W–12M), mortgage/consumer/NFC lending rates, deposit rates, IRPH, BoP (current/capital/financial account), housing prices (new/used/avg EUR/m²) |

#### European Coverage Map

```
🇩🇪 Germany    — Bundesbank (yields, ECB rates, monetary, trade)
🇫🇷 France     — INSEE (macro) + Banque de France (FX, credit, BoP)
🇮🇹 Italy      — ISTAT (GDP, inflation, labour, industry, confidence)
🇳🇱 Netherlands — CBS StatLine (GDP, CPI, housing, trade, govt finance)
🇩🇰 Denmark    — DST StatBank (GDP, CPI, labour, trade, housing)
🇸🇪 Sweden     — SCB (macro) + Riksbank (rates, FX, bonds)
🇪🇸 Spain      — Banco de España (Euribor, lending rates, BoP, housing)
```

#### Usage Examples — European Modules

**CLI:**
```bash
python3 modules/bundesbank_sdmx.py BUND_10Y
python3 modules/insee_france.py GDP_GROWTH
python3 modules/banque_de_france.py EUR_USD
python3 modules/istat_italy.py CPI_NIC
python3 modules/cbs_netherlands.py GDP_GROWTH_YOY
python3 modules/statistics_denmark.py CPI_YOY
python3 modules/scb_sweden.py CPIF_ANNUAL_CHANGE
python3 modules/riksbank_sweden.py POLICY_RATE
python3 modules/banco_de_espana.py EURIBOR_12M
```

**REST API:**
```
GET /api/v1/bundesbank-sdmx?indicator=BUND_10Y
GET /api/v1/insee-france?indicator=GDP_GROWTH
GET /api/v1/riksbank-sweden?indicator=POLICY_RATE
GET /api/v1/banco-de-espana?indicator=EURIBOR_12M
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'bundesbank_sdmx',
    params: { indicator: 'BUND_10Y' }
  })
});
```

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
Each of the 1,034 modules gets an auto-generated REST endpoint:
```
/api/v1/prices?ticker=AAPL
/api/v1/technicals?ticker=AAPL&indicators=rsi,macd
/api/v1/screener?min-cap=10B&sector=Technology
/api/v1/options-chain?ticker=AAPL&expiration=2026-04-17
/api/v1/fred-enhanced?series=GDP&start=2020-01-01
```

---

## Natural Language Queries (DCC)

The Data Command Center (DCC) allows natural language queries against all 1,034 modules:

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
| **ModuleBrowserPanel** | Browse and search all 1,034 modules by category |
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
| Deutsche Bundesbank | No | Open | German yields, ECB rates, monetary aggregates |
| INSEE France | No | 30/min | French GDP, CPI, unemployment, trade |
| Banque de France | Yes (free) | Open | EUR FX rates, credit, BoP, business climate |
| ISTAT Italy | No | 5/min | Italian GDP, CPI, unemployment, industry |
| CBS Netherlands | No | Open | Dutch GDP, CPI, housing, trade, govt finance |
| Statistics Denmark | No | Open | Danish GDP, CPI, labour, trade, housing |
| SCB Sweden | No | Open | Swedish GDP, CPI/CPIF, labour, trade |
| Sveriges Riksbank | No | Rate-limited | SEK FX, policy rates, govt bond yields |
| Banco de España | No | Open | Euribor, lending rates, BoP, housing prices |

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
├── modules/                          # 1,034 Python data modules
│   ├── prices.py                     # Stock prices (Yahoo Finance)
│   ├── technicals.py                 # Technical analysis indicators
│   ├── alpha_picker.py               # AI alpha scoring
│   ├── options_chain.py              # Options data
│   ├── fred_enhanced.py              # FRED macro data
│   ├── congress_trades.py            # Congressional trading
│   ├── insider_trades.py             # Insider buying/selling
│   ├── bundesbank_sdmx.py            # Deutsche Bundesbank (SDMX)
│   ├── insee_france.py               # INSEE France macro statistics
│   ├── banque_de_france.py           # Banque de France Webstat
│   ├── istat_italy.py                # ISTAT Italy statistics
│   ├── cbs_netherlands.py            # CBS Netherlands StatLine
│   ├── statistics_denmark.py         # Statistics Denmark (DST)
│   ├── scb_sweden.py                 # SCB Sweden (Statistics Sweden)
│   ├── riksbank_sweden.py            # Sveriges Riksbank
│   ├── banco_de_espana.py            # Banco de España
│   ├── ... (1,034 modules total)
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
BANQUE_DE_FRANCE_API_KEY=            # Banque de France Webstat (free registration)

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

*1,034 modules • 47 phases • 7 European countries • The data layer powering the MoneyClawX ecosystem*
