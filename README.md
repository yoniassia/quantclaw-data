# QuantClaw Data — AI-Built Financial Intelligence Platform

> **1,028 production modules. 362K+ lines of Python. 439 API routes. 179 data sources cataloged. $0/month. Built autonomously by AI agents.**

**Live Dashboard:** [data.quantclaw.org](https://data.quantclaw.org) | **Public Site:** [quantclaw.org](https://quantclaw.org)

---

## Table of Contents

- [What is QuantClaw Data?](#what-is-quantclaw-data)
- [By the Numbers](#by-the-numbers)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Data Modules](#data-modules)
- [Quality Tier System](#quality-tier-system)
- [Pipeline Framework (qcd_platform)](#pipeline-framework-qcd_platform)
- [MCP Server (Model Context Protocol)](#mcp-server-model-context-protocol)
- [HTTP API (Next.js)](#http-api-nextjs)
- [CLI Interface](#cli-interface)
- [DataScout — Continuous Discovery](#datascout--continuous-discovery)
- [Alpha Picker V3 — Crown Jewel](#alpha-picker-v3--crown-jewel)
- [Database Schema](#database-schema)
- [Infrastructure Stack](#infrastructure-stack)
- [Dashboard UI](#dashboard-ui)
- [CI/CD Pipeline](#cicd-pipeline)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Module Development Guide](#module-development-guide)
- [Data Sources](#data-sources)
- [Roadmap](#roadmap)
- [AI Agents](#ai-agents)

---

## What is QuantClaw Data?

QuantClaw Data (internally: **DCC — Data Collection Center**) is the world's largest open-source financial data platform built entirely by AI agents. It serves as the **single source of truth** for all financial data across the QuantClaw ecosystem.

Every downstream consumer — TerminalX (Bloomberg-style terminal), AgentX (autonomous trading agents), PICentral (Popular Investor dashboard), and Signal Centre — pulls data exclusively from DCC. No consumer app connects directly to upstream APIs.

The platform collects, cleans, validates, and serves data from 179+ free public sources through three access layers:
- **MCP Protocol** — AI agents call data tools natively via Model Context Protocol
- **REST API** — 439 endpoints for programmatic access
- **CLI** — Command-line interface for interactive exploration

---

## By the Numbers

```
Python Data Modules (v1)      1,028
Python Data Modules (v2)         43  (BaseModule pipeline pattern)
Lines of Python (modules)   362,716
MCP Server                   12,769 LOC
HTTP MCP Server                 746 LOC
CLI Dispatcher                1,776 LOC
DataScout Agent                 669 LOC
Next.js API Routes              439
Data Sources Cataloged          179  (and growing via DataScout)
Cached Data                   377 MB
Module Cache                  102 MB
Monthly Infrastructure Cost      $0
Countries Covered               40+
```

---

## System Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │         UPSTREAM DATA SOURCES       │
                                    │  FRED · Yahoo · eToro SAPI · SEC   │
                                    │  GuruFocus · Financial Datasets     │
                                    │  World Bank · OECD · Eurostat       │
                                    │  BLS · Census · EIA · 170+ more    │
                                    └─────────────┬───────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        QUANTCLAW DATA (DCC)                             │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  modules/     │  │ modules_v2/  │  │  DataScout   │  │  Pipeline  │  │
│  │  1,028 scripts│  │  43 BaseModule│  │  Discovery   │  │Orchestrator│  │
│  │  (v1 - file) │  │  (v2 - DB)   │  │  Agent       │  │            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  │
│         │                 │                  │                  │        │
│         ▼                 ▼                  ▼                  ▼        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     DATA LAYER                                     │  │
│  │  PostgreSQL + TimescaleDB │ Redis (hot cache) │ Kafka (event bus)  │  │
│  │  data_points (hypertable) │ latest values     │ topic-per-domain   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  MCP Server  │  │  REST API    │  │    CLI       │                   │
│  │  Port 3055   │  │  439 routes  │  │  cli.py      │                   │
│  │  mcp_server  │  │  Next.js API │  │              │                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
│         │                 │                  │                            │
└─────────┼─────────────────┼──────────────────┼────────────────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
  ┌───────────┐   ┌──────────────┐   ┌──────────────┐
  │ AI Agents │   │  TerminalX   │   │  Developers  │
  │ AgentX    │   │  PICentral   │   │  & Scripts   │
  │ OpenClaw  │   │ Signal Centre│   │              │
  └───────────┘   └──────────────┘   └──────────────┘
```

---

## Repository Structure

```
quantclaw-data/
├── modules/                 # 1,028 Python data modules (v1 — standalone scripts)
│   ├── alpha_picker.py          # Stock scoring algorithm (970 lines)
│   ├── sa_quant_replica.py      # SeekingAlpha Quant reverse-engineering
│   ├── live_paper_trading.py    # Paper trading portfolio engine
│   ├── signal_fusion.py         # Multi-signal combiner
│   ├── cnn_fear_greed.py        # CNN Fear & Greed Index
│   ├── fed_soma.py              # Fed SOMA holdings
│   ├── worldbank.py             # World Bank indicators
│   └── ...1,021 more modules
│
├── modules_v2/              # 43 v2 modules (BaseModule class, DB-integrated)
│   ├── gurufocus_fundamentals.py
│   ├── etoro_sapi_instruments.py  # eToro SAPI integration (3,571+ symbols)
│   ├── financial_datasets_prices.py
│   ├── scrapling_earnings_calendar.py
│   └── ...39 more modules
│
├── qcd_platform/            # Production pipeline framework
│   ├── pipeline/
│   │   ├── base_module.py       # Abstract base class (Bronze→Silver→Gold→Platinum)
│   │   ├── orchestrator.py      # Cadence-based scheduler with retry logic
│   │   ├── db.py                # PostgreSQL interface
│   │   ├── kafka_producer.py    # Event publishing to Kafka topics
│   │   ├── redis_cache.py       # Hot cache + pub/sub
│   │   └── v1_adapter.py        # Wraps v1 modules into BaseModule interface
│   ├── config/
│   │   └── settings.py          # DB, Kafka, Redis, pipeline configuration
│   ├── schema.sql               # Full database DDL (TimescaleDB)
│   ├── migrations/              # Schema migrations
│   │   ├── 003_materialized_views.sql
│   │   ├── 004_platinum_records_grants.sql
│   │   └── gurufocus_tables.sql
│   ├── scripts/
│   │   ├── run_pipeline.py      # Manual pipeline runner
│   │   ├── run_batch.py         # Batch execution
│   │   ├── bulk_register.py     # Register all modules in DB
│   │   ├── analyze_modules.py   # Module analysis/stats
│   │   ├── alert_notifier.py    # WhatsApp alert integration
│   │   ├── cadence_cron.sh      # Cron schedule setup
│   │   └── overnight_run.sh     # Nightly batch processing
│   └── module_manifest.json     # Module registry manifest
│
├── mcp_server.py            # MCP Protocol server (12,769 LOC)
├── mcp_http_server.py       # HTTP MCP server — 30 tools, port 3056
├── cli.py                   # CLI dispatcher (1,776 LOC)
├── datascout.py             # Data source discovery agent (Grok 4 powered)
│
├── src/app/                 # Next.js 15 dashboard + API
│   ├── page.tsx                 # Terminal-style dashboard UI
│   ├── layout.tsx               # Root layout
│   ├── login/                   # Password-protected login
│   ├── tutorial/                # Interactive tutorial
│   ├── api/
│   │   ├── v1/                  # 439 REST API routes
│   │   │   ├── [tool]/route.ts  # Dynamic tool routing
│   │   │   ├── abs/             # Australian Bureau of Statistics
│   │   │   ├── fred-enhanced/   # Federal Reserve data
│   │   │   ├── sector-rotation/ # Sector analysis
│   │   │   ├── monte-carlo/     # Simulation endpoints
│   │   │   ├── signal-fusion/   # Combined signals
│   │   │   └── ...435 more
│   │   ├── auth/                # Authentication (login/logout)
│   │   └── dcc/                 # DCC management endpoints
│   │       ├── modules/         # Module registry
│   │       ├── pipeline/        # Pipeline status/control
│   │       ├── quality/         # Quality reports
│   │       ├── stats/           # Platform statistics
│   │       ├── alerts/          # Alert management
│   │       └── sources/         # Data source catalog
│   └── services.ts              # API client services
│
├── data/                    # 377 MB cached data
│   ├── signals/                 # Live trading signals
│   ├── datascout/               # 179 cataloged data sources
│   ├── alerts/                  # Alert history
│   ├── reports/                 # Generated reports
│   ├── live_portfolio.db        # Paper trading SQLite DB
│   ├── price_cache/             # Price history cache
│   └── search-index/            # Module search index
│
├── scripts/                 # Utility scripts
│   ├── signal_pipeline.py       # Signal generation pipeline
│   ├── search_modules.py        # Module search utility
│   ├── validate_module.py       # Module validation
│   ├── refresh_price_cache.py   # Price cache refresh
│   └── ci-test.sh               # CI test runner
│
├── tests/                   # Test suite
│   └── test_data_integrity.py   # Data integrity checks
│
├── .github/workflows/       # CI/CD
│   ├── ci.yml                   # Push/PR: test, build, deploy
│   └── weekly-test.yml          # Monday 6am: full test + API health
│
├── package.json             # Node.js deps (Next.js 15, React 19)
├── requirements.txt         # Python deps
├── .env.example             # Environment variable template
└── .env                     # Encrypted env (dotenvx)
```

---

## Data Modules

### v1 Modules (1,028 in `modules/`)

Standalone Python scripts that fetch, process, and return data. Each module is self-contained with its own API calls, parsing logic, and output formatting. Executed directly or via CLI/MCP server.

**Categories:**

```
Equity & Earnings         ~27 modules   EPS, analyst estimates, DCF, comps
Commodities               ~24 modules   Oil, gold, metals, agriculture, rig counts
Fixed Income              ~21 modules   Treasury yields, corporate bonds, TIPS, munis
Macro & Central Bank      ~16 modules   Fed, ECB, BIS, IMF, GDP, CPI, employment
Crypto & DeFi             ~15 modules   DeFi Llama, on-chain, DEX, stablecoins
Technical & Quant         ~15 modules   Factor models, momentum, volatility, Kalman
FX & Currency             ~10 modules   Cross rates, carry trade, PPP
Geopolitical & Risk       ~10 modules   Conflict monitors, sanctions, risk scores
Regulatory & Filing        ~9 modules   SEC EDGAR, insider trades, 13F filings
Alternative Data           ~8 modules   Wikipedia pageviews, sentiment, web traffic
Signals & Alerts           ~8 modules   Signal fusion, smart alerts, discovery
Derivatives                ~7 modules   CBOE put/call, VIX, options flow
ESG & Climate              ~5 modules   Carbon markets, green bonds
Portfolio & Risk           ~5 modules   Optimization, rebalancing, drawdown
Sentiment & NLP            ~4 modules   FinBERT, earnings call NLP
Cross-domain             780+ modules   Country stats, ML/AI, infrastructure, extended
```

### v2 Modules (43 in `modules_v2/`)

Production-grade modules inheriting from `BaseModule`. Integrated with PostgreSQL, Kafka, and Redis. Support the full Bronze → Silver → Gold → Platinum pipeline.

Key v2 modules include:
- **etoro_sapi_instruments.py** — eToro SAPI integration covering 3,571+ symbols
- **etoro_sapi_platinum_bridge.py** — Platinum-tier enrichment for eToro data
- **gurufocus_fundamentals.py** — GuruFocus financial statements and ratios
- **financial_datasets_prices.py** — Primary price data source
- **scrapling_earnings_calendar.py** — Web-scraped earnings calendar
- **cnn_fear_greed.py** — CNN Fear & Greed Index (v2 pipeline)

---

## Quality Tier System

Every data point is classified into a quality tier, promoting through the pipeline as validation checks pass:

```
BRONZE (Raw)        Score: 0+     Data as-is from source. Module runs and returns data.
   │
   ▼
SILVER (Cleaned)    Score: 50+    Nulls handled, types validated, deduplicated,
   │                              timestamps normalized to UTC.
   ▼
GOLD (Validated)    Score: 80+    Completeness >95%, timeliness within cadence window,
   │                              cross-source consistency checks pass, schema valid.
   ▼
PLATINUM (Enriched) Score: 95+    Cross-module joins, forward-filled, composite
                                  indicators. Requires 2+ successful runs, zero
                                  consecutive failures.
```

Quality checks run automatically on every pipeline execution:
- **Completeness** — percentage of non-null payload fields
- **Timeliness** — data freshness relative to cadence (e.g., daily data should be <48h old)
- **Accuracy** — value range and format validation
- **Consistency** — cross-source agreement
- **Schema validity** — payload matches expected structure

---

## Pipeline Framework (qcd_platform)

The production pipeline framework lives in `qcd_platform/` and provides the runtime for v2 modules.

### BaseModule

Every v2 module inherits from `BaseModule` and implements three methods:

```python
from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport

class AaiiSentiment(BaseModule):
    name = "aaii_sentiment"
    display_name = "AAII Investor Sentiment Survey"
    cadence = "weekly"
    granularity = "market"
    tags = ["Sentiment", "US Equities"]

    def fetch(self, symbols=None) -> list[DataPoint]:
        """Bronze: fetch raw data from external source."""
        # Your data collection logic here
        return [DataPoint(ts=datetime.now(), payload={"bull": 38.2, "bear": 28.1})]

    def clean(self, raw_points) -> list[DataPoint]:
        """Silver: validate, clean, normalize. Base class provides default implementation."""
        return super().clean(raw_points)

    def validate(self, clean_points) -> QualityReport:
        """Gold: run quality checks. Base class provides default implementation."""
        return super().validate(clean_points)
```

Calling `module.run()` executes the full pipeline: fetch → clean → validate → store → publish events.

### Pipeline Orchestrator

The orchestrator (`qcd_platform/pipeline/orchestrator.py`) handles:
- **Cadence scheduling** — discovers modules due for execution based on their configured cadence
- **Concurrent execution** — runs up to 4 modules in parallel via ThreadPoolExecutor
- **Retry logic** — 3 retries with 60-second delays for transient failures
- **Health monitoring** — publishes module health to Redis and Kafka
- **Error escalation** — after 3 consecutive failures, triggers WhatsApp alerts

### Event Flow

```
Module.run()
  → Bronze: fetch() → store in PostgreSQL (tier=bronze) → publish to Kafka bronze topic
  → Silver: clean() → store (tier=silver) → publish to Kafka silver topic
  → Gold:   validate() → if score ≥ 80: store (tier=gold) → publish to Kafka gold topic
  → Platinum: if score ≥ 95 AND run_count ≥ 2 AND no failures → promote to platinum
  → Quality checks recorded in quality_checks table
  → Module stats updated (last_run, quality_score, tier)
  → Latest values cached in Redis
  → Errors: retry 3x → alert → human queue
```

---

## MCP Server (Model Context Protocol)

**File:** `mcp_server.py` (12,769 LOC) | **Port:** 3055

Exposes all 1,028+ modules as AI-callable tools via the Model Context Protocol. AI agents (OpenClaw, AgentX, etc.) call data tools natively without REST.

```bash
python3 mcp_server.py
```

The MCP server imports functions from all modules and maps them to standardized tool signatures with typed parameters and descriptions.

### HTTP MCP Server

**File:** `mcp_http_server.py` (746 LOC) | **Port:** 3056

A lightweight HTTP wrapper exposing 30 high-frequency tools for direct HTTP access:

```bash
python3 mcp_http_server.py

# Example calls
curl "http://localhost:3056/tool/market_quote?symbol=AAPL"
curl "http://localhost:3056/tool/profile?symbol=MSFT"
curl "http://localhost:3056/tool/fear_greed"
```

---

## HTTP API (Next.js)

**Framework:** Next.js 15 | **Port:** 3055 | **Routes:** 439

All REST API routes live under `src/app/api/v1/`. Each route wraps a Python module via subprocess call and returns JSON.

### Core Endpoints

```
GET /api/v1/prices?ticker=AAPL              # Real-time quotes
GET /api/v1/fred-enhanced?series=GDP         # FRED economic data
GET /api/v1/sector-rotation                  # Sector momentum analysis
GET /api/v1/monte-carlo?ticker=AAPL&sims=1000  # Monte Carlo simulation
GET /api/v1/signal-fusion?ticker=AAPL        # Multi-signal combination
GET /api/v1/anomaly-scanner                  # Market anomaly detection
GET /api/v1/regime-correlation               # Regime-based correlations
GET /api/v1/macro-leading                    # Leading indicators
GET /api/v1/cds?entity=US                    # Credit default swaps
GET /api/v1/backtest?strategy=momentum       # Strategy backtesting
```

### DCC Management Endpoints

```
GET  /api/v1/dcc/modules                     # List all registered modules
GET  /api/v1/dcc/pipeline                    # Pipeline status
GET  /api/v1/dcc/quality                     # Quality reports
GET  /api/v1/dcc/stats                       # Platform statistics
GET  /api/v1/dcc/alerts                      # Active alerts
GET  /api/v1/dcc/sources                     # Data source catalog
POST /api/v1/dcc/pipeline                    # Trigger pipeline run
```

### Authentication

The dashboard and API are protected by a simple access code via `/api/auth/login`. Session-based auth via cookies.

---

## CLI Interface

**File:** `cli.py` (1,776 LOC)

Central dispatcher routing commands to the appropriate module. Supports 400+ commands across all domains.

```bash
# Market data
python3 cli.py quote AAPL
python3 cli.py historical MSFT --period 1y

# Technical analysis
python3 cli.py kalman AAPL
python3 cli.py mtf NVDA
python3 cli.py walk-forward SPY

# Trading signals
python3 cli.py alpha-score AAPL
python3 cli.py alpha-picks --top 20
python3 cli.py signal-fusion TSLA

# Portfolio
python3 cli.py monte-carlo AAPL --sims 10000
python3 cli.py black-litterman --tickers AAPL,MSFT,GOOGL
python3 cli.py backtest momentum --start 2024-01-01

# Alerts
python3 cli.py alert-create --ticker AAPL --condition "price > 200"
python3 cli.py alert-check

# Macro
python3 cli.py fred GDP
python3 cli.py bls unemployment
python3 cli.py eurostat DE inflation
```

---

## DataScout — Continuous Discovery

**File:** `datascout.py` (669 LOC) | **Powered by:** Grok 4 (xai/grok-4)

An autonomous agent that discovers new free financial data sources. Runs hourly via cron, rotating through 24 categories:

- Macro / Central Banks
- Satellite & Geospatial
- Social & Sentiment
- Commodities & Energy
- Crypto & DeFi
- ESG & Climate
- And 18 more categories...

For each category, DataScout performs web searches and X/Twitter searches, evaluates discovered sources for quality and relevance, and logs them to `data/datascout/`. Currently **179 sources cataloged** and growing.

---

## Alpha Picker V3 — Crown Jewel

The autonomous stock-picking engine that reverse-engineers institutional quant strategies:

```
SA Quant Agreement Rate     69% (31/45 picks match SeekingAlpha)
Win Rate                    92% on 40 backtested picks
Annual Return               41.5% (Triple Pyramid strategy)
Max Drawdown                -7.9%
Sharpe Ratio                5.3
Base Position               $5K + adds at +10%, +20%, +35%
Rebalance Frequency         Bi-weekly (1st & 15th of month)
```

### How It Works

1. **Universe Filter** — 7,017 stocks → 386 candidates (market cap, volume, price filters)
2. **Multi-Factor Scoring** — Value + Growth + Momentum + Quality + Earnings Revision
3. **SA Quant Replica** — Reverse-engineered scoring matching SeekingAlpha's quant model
4. **Signal Fusion** — 7+ data sources per stock combined into a single score
5. **Live Signals** — Automated cron on 1st & 15th at 14:00 UTC

### Related Modules

- `modules/alpha_picker.py` — Core scoring algorithm
- `modules/sa_quant_replica.py` — SeekingAlpha reverse-engineering
- `modules/signal_fusion.py` — Multi-source signal combiner
- `modules/live_paper_trading.py` — Paper trading portfolio engine
- `scripts/signal_pipeline.py` — Signal generation pipeline

---

## Database Schema

**Database:** `quantclaw_data` | **Engine:** PostgreSQL 14 + TimescaleDB

### Core Tables

```
symbol_universe      Instrument registry (symbol, asset class, exchange, eToro ID)
modules              Registry of all 1,028+ modules (cadence, tier, quality score, run stats)
tag_definitions      Hierarchical taxonomy (asset_class, data_type, region, frequency)
module_tags          Many-to-many: modules ↔ tags
data_points          Time-series data (TimescaleDB hypertable, chunked by month)
pipeline_runs        Execution audit trail (status, duration, rows, errors)
quality_checks       Per-run validation results (completeness, timeliness, accuracy)
alerts               Error queue + notifications (severity, category, resolution status)
```

### Key Design Decisions

- **TimescaleDB hypertables** for `data_points` with 1-month chunk intervals — enables efficient time-range queries and automatic partitioning
- **JSONB payload** — flexible schema per module, with GIN indexes for fast JSON path queries
- **Source hash** — SHA-256 deduplication prevents storing identical data points
- **Forward-fill via `locf()`** — cross-cadence joins at query time (e.g., daily prices joined with weekly sentiment)
- **Trigger-based stats** — `update_module_stats()` automatically updates module run counts and failure tracking

### Kafka Topics

```
quantclaw.pipeline.bronze.{domain}     Raw data ingested
quantclaw.pipeline.silver.{domain}     Cleaned data
quantclaw.pipeline.gold.{domain}       Validated data
quantclaw.pipeline.errors              All failures
quantclaw.pipeline.alerts              Material alerts → WhatsApp
quantclaw.pipeline.status              Module status changes
```

Domains: `us_equities`, `sentiment`, `earnings`, `fundamentals`, `corporate_actions`, `macro`, `crypto`, `fx`, `commodities`

### Redis Keys

```
qcd:latest:{module}:{symbol}    Latest data point (hot cache)
qcd:health:{module}             Module health status
qcd:queue:retry                 Retry queue for failed modules
qcd:updates (pub/sub)           Real-time dashboard updates
qcd:ratelimit:{source}          API source throttling
```

---

## Infrastructure Stack

```
PostgreSQL 14 + TimescaleDB     Primary data store, hypertables for time-series
Apache Kafka                    Message bus, topic-per-domain event streaming
Redis                           Hot cache (latest values), pub/sub, rate limiting
Next.js 15                      Dashboard UI + REST API (port 3055)
PM2                             Process management (quantclaw-data service)
Python 3.12                     Module runtime, pipeline framework
Node.js                         Next.js server
dotenvx                         Encrypted environment variables
```

### Server

- **Host:** Hostinger VPS (ID 1340294), 8 vCPU
- **OS:** Linux 5.15
- **Port:** 3055 (dashboard + API), 3056 (HTTP MCP)
- **Process Manager:** PM2 (`quantclaw-data`)

---

## Dashboard UI

The dashboard at `data.quantclaw.org` features a retro terminal-style interface with:

- **Live Market Ticker** — SPY, QQQ, DIA, IWM, AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, BTC, ETH
- **Interactive Terminal** — Execute any CLI command directly from the browser
- **Data Source Browser** — Search and explore all 179+ cataloged data sources
- **Module Statistics** — Real-time counts, quality scores, pipeline status
- **Responsive Design** — Mobile-friendly with tab-based navigation

**Tech Stack:** Next.js 15 · React 19 · TailwindCSS 4 · Recharts · TradingView Lightweight Charts · Zustand · TanStack Table

---

## CI/CD Pipeline

### On Push/PR (`.github/workflows/ci.yml`)

```
1. Test Python Modules     Import-test all 1,028 modules (fail threshold: >5 broken)
2. Build Next.js           Production build with NODE_OPTIONS=--max-old-space-size=2048
3. Project Stats            Count modules, routes, LOC → GitHub Step Summary
4. Deploy (main only)      SSH → git pull → npm ci → build → pm2 restart
```

### Weekly Full Test (`.github/workflows/weekly-test.yml`)

```
Monday 6am UTC:
1. Full module import test
2. Data integrity checks
3. API health check (hit live endpoints, verify 200 responses)
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/shayhe-tr/quantclaw-data.git
cd quantclaw-data

# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for dashboard + API)
npm install

# Copy environment template
cp .env.example .env
# Fill in your API keys (most have free tiers)

# Run any module directly
python3 modules/cnn_fear_greed.py
python3 modules/fed_soma.py
python3 modules/worldbank.py

# Run via CLI
python3 cli.py quote AAPL
python3 cli.py alpha-picks --top 10

# Start MCP server
python3 mcp_server.py

# Start HTTP MCP server
python3 mcp_http_server.py

# Start dashboard + API
npm run dev          # Development (hot reload)
npm run build        # Production build
npm run start        # Production server (port 3055)

# Run pipeline (requires PostgreSQL + TimescaleDB)
python3 qcd_platform/scripts/run_pipeline.py
```

---

## Environment Variables

API keys are encrypted with [dotenvx](https://dotenvx.com). The encrypted `.env` is in the repo.

**With the decryption key (for authorized contributors):**
```bash
export DOTENV_PRIVATE_KEY="your-key-here"
npx dotenvx run -- python3 modules/cnn_fear_greed.py
npx dotenvx run -- npm run dev
```

**Bring your own keys:**
```bash
cp .env.example .env
# Fill in your keys — most have free tiers
```

### Available API Keys

```
FRED_API_KEY                Federal Reserve Economic Data       Free ✅
EIA_API_KEY                 US Energy Information Admin          Free ✅
CENSUS_API_KEY              US Census Bureau                     Free ✅
FINANCIAL_DATASETS_API_KEY  financialdatasets.ai                 Free ✅
FINNHUB_API_KEY             Finnhub real-time market data        Free ✅
ETHERSCAN_API_KEY           Ethereum blockchain data             Free ✅
POLYGON_API_KEY             Polygon.io market data               Free ✅
USDA_NASS_API_KEY           USDA agricultural statistics         Free ✅
```

Optional (uncomment in .env):
```
BOK_API_KEY                 Bank of Korea
COMTRADE_API_KEY            UN Comtrade trade data
ALPHA_VANTAGE_API_KEY       Alpha Vantage market data
FMP_API_KEY                 Financial Modeling Prep
```

### Database Configuration (for pipeline)

```
QCD_DB_HOST                 PostgreSQL host (default: localhost)
QCD_DB_PORT                 PostgreSQL port (default: 5432)
QCD_DB_NAME                 Database name (default: quantclaw_data)
QCD_DB_USER                 Database user (default: quantclaw_user)
QCD_DB_PASS                 Database password
QCD_KAFKA_SERVERS           Kafka brokers (default: localhost:9092)
QCD_REDIS_HOST              Redis host (default: localhost)
QCD_REDIS_PORT              Redis port (default: 6379)
QCD_REDIS_DB                Redis database number (default: 2)
```

---

## Module Development Guide

### Creating a v2 Module

1. Create a new file in `modules_v2/`:

```python
"""
my_new_source.py — Description of what this module fetches
"""
from datetime import datetime, timezone
from typing import List, Optional
import requests

from qcd_platform.pipeline.base_module import BaseModule, DataPoint, QualityReport


class MyNewSource(BaseModule):
    name = "my_new_source"
    display_name = "My New Data Source"
    cadence = "daily"           # realtime|1min|5min|15min|1h|4h|daily|weekly|monthly|quarterly
    granularity = "symbol"      # symbol|market|macro|global
    tags = ["US Equities", "Fundamentals"]

    def fetch(self, symbols: List[str] = None) -> List[DataPoint]:
        """Bronze: collect raw data from source."""
        response = requests.get("https://api.example.com/data")
        data = response.json()

        points = []
        for item in data:
            points.append(DataPoint(
                ts=datetime.now(timezone.utc),
                symbol=item["ticker"],
                cadence=self.cadence,
                payload=item,
            ))
        return points

    def clean(self, raw_points: List[DataPoint]) -> List[DataPoint]:
        """Silver: custom cleaning logic (optional — base class has defaults)."""
        cleaned = super().clean(raw_points)
        for p in cleaned:
            if "price" in p.payload:
                p.payload["price"] = float(p.payload["price"])
        return cleaned

    def validate(self, clean_points: List[DataPoint]) -> QualityReport:
        """Gold: custom validation (optional — base class has defaults)."""
        report = super().validate(clean_points)
        # Add custom checks
        for p in clean_points:
            if p.payload.get("price", 0) <= 0:
                report.issues.append(f"Invalid price for {p.symbol}")
                report.accuracy -= 10
        report.compute_overall()
        return report
```

2. Register the module: `python3 qcd_platform/scripts/bulk_register.py`

3. Test: `python3 -c "from modules_v2.my_new_source import MyNewSource; print(MyNewSource().run())"`

### Creating a v1 Module (standalone)

Simply add a `.py` file to `modules/`. It should be self-contained and either:
- Define importable functions (for MCP server integration)
- Print JSON to stdout when run directly (for CLI integration)

---

## Data Sources

### Primary Sources

```
eToro SAPI              3,571+ instruments, real-time prices, sentiment
Financial Datasets      Insider trades, holdings, SEC filings, financials
GuruFocus               Fundamentals, rankings, guru portfolios, valuations
FRED                    800K+ macroeconomic time-series
Yahoo Finance           Fallback pricing, fundamentals, earnings
SEC EDGAR               10-K, 10-Q, 13F filings, insider transactions
```

### Government & International

```
World Bank              Development indicators, 40+ countries
OECD                    CLI, housing, productivity, 38 member countries
Eurostat                EU economic data, 27+ countries
BLS                     US employment, CPI, wages
US Census               Retail sales, housing starts, trade deficit
EIA                     Energy prices, petroleum, natural gas
USDA                    Agricultural commodities, crop stats
UN Comtrade             International trade flows
IMF                     World Economic Outlook, global indicators
BIS                     Banking statistics, cross-border claims
```

### Alternative & Sentiment

```
CNN Fear & Greed Index  Market sentiment composite
AAII Sentiment Survey   Retail investor bullish/bearish readings
Wikipedia Pageviews     Company attention proxy
Congressional Trades    US congressional stock transactions
Web Traffic             Site traffic estimates as business proxy
```

### Crypto & DeFi

```
DeFi Llama             TVL, protocol revenue, yield farming
Etherscan              Ethereum on-chain data, gas prices
CoinGecko              Crypto prices, market cap, volume
DEX Aggregators         Decentralized exchange volumes
Stablecoin Monitors     Supply, depegging alerts
```

---

## Roadmap

```
Phase 1-100       ✅ Complete    Core macro, equity, fixed income, FX
Phase 101-200     ✅ Complete    Country stats, derivatives, commodities
Phase 201-300     ✅ Complete    Crypto, DeFi, ESG, alternative data
Phase 301-400     ✅ Complete    ML/AI models, NLP, factor engines
Phase 401-500     ✅ Complete    Infrastructure, streaming
Phase 501-699     ✅ Complete    Advanced analytics, emerging markets
Phase 700-800     ✅ Complete    Free no-API-key sources (DataScout)
Phase 800-965     ✅ Complete    Extended free sources, ML signals
Phase 965-1028    ✅ Complete    Additional modules, v2 migration
Phase 1028+       🔄 Ongoing    Continuous autonomous expansion via DataScout
```

---

## AI Agents

QuantClaw Data is built and maintained entirely by AI agents:

```
DataClaw       📊  Builds new data modules from the roadmap
DataQAClaw     🔬  Tests, validates, and quality-maps modules
DataScout      🔍  Discovers new free data sources (Grok 4 powered)
Alpha Picker   🎯  Generates trading signals from combined data
BacktestClaw   ⚡  Validates strategies via backtesting
Quant          📈  Orchestrator — coordinates all agents and infrastructure
```

---

## Architecture Principles

1. **DCC-first** — All data ingestion goes through DCC before reaching any consumer app. No direct pipeline-to-frontend wiring.
2. **Primary/fallback** — Financial Datasets is the primary price source; Yahoo Finance is the fallback.
3. **Quality over quantity** — Every data point must pass through the Bronze → Gold pipeline before being served to production consumers.
4. **Free-first** — Maximize coverage using free-tier APIs. $0/month infrastructure cost target.
5. **AI-native** — MCP protocol as the primary access layer for AI agents. REST API for traditional consumers.
6. **Immutable audit trail** — Every pipeline run, quality check, and alert is recorded in PostgreSQL.

---

*Built with precision by AI agents. 1,028 modules. $0/month. Always growing.*
