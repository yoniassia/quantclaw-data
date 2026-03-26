# QuantClaw Data

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776ab)](https://www.python.org/)

**QuantClaw Data** (internal name: **DCC — Data Collection Center**) is a financial data pipeline and API platform: **1,000+ Python data modules** in `modules/`, **40+ pipeline-integrated modules** in `modules_v2/`, covering market data, fundamentals, macro, sentiment, alternatives, crypto, and more. Downstream QuantClaw apps consume this layer instead of calling upstream providers directly.

**Live:** [data.quantclaw.org](https://data.quantclaw.org) · **Site:** [quantclaw.org](https://quantclaw.org)

---

## Tech stack

| Layer | Stack |
|--------|--------|
| **Web & API** | Next.js 15, React 19, TypeScript, Tailwind CSS 4 |
| **UI** | TanStack Table, Recharts, Lightweight Charts, React Grid Layout, Zustand |
| **Data / API** | Node `pg` (PostgreSQL), route handlers invoking Python (`cli.py` / `modules/*.py`) |
| **Python** | pandas, NumPy, SciPy, statsmodels, yfinance, pandas-datareader, requests, aiohttp, BeautifulSoup |
| **Pipeline (optional)** | PostgreSQL 14 + TimescaleDB, Redis, Kafka (`qcd_platform/`) |
| **Agent access** | MCP (`mcp_server.py`), optional HTTP MCP (`mcp_http_server.py`) |
| **Secrets** | [dotenvx](https://dotenvx.com) (encrypted `.env` in repo for authorized deploys) |

---

## Features

- **Large module catalog** — 1,000+ standalone collectors/analytics in `modules/`; v2 modules use `BaseModule` (Bronze → Silver → Gold → Platinum) in `modules_v2/`.
- **REST API** — 440+ routes under `/api/v1/*` (domain-specific paths: FRED, sector rotation, Monte Carlo, signal fusion, GuruFocus wrappers, backtests, paper trading, etc.) plus `/api/dcc/*` for registry, pipeline, quality, alerts, sources.
- **Natural language query** — DCC UI/API: NL → read-only SQL against `quantclaw_data` via Claude (requires `ANTHROPIC_API_KEY`). Endpoints: `POST /api/dcc/nl-query`, conversation APIs under `/api/dcc/nl-query/…`.
- **CLI** — `cli.py` dispatches hundreds of commands (quotes, macro, signals, backtests, alerts).
- **MCP** — `mcp_server.py` exposes tools over MCP (stdio); `mcp_http_server.py` serves a subset of tools over HTTP (default **3056** in that script).
- **Dashboard** — Terminal-style UI: tickers, embedded CLI, module/source browsing, DCC stats (port **3055** in `package.json`).
- **DataScout** — `datascout.py` catalogs candidate free data sources under `data/datascout/`.
- **CI** — Module import sweep, Next.js build, optional data-integrity tests (`.github/workflows/`).

---

## Architecture (overview)

```
Upstream APIs & scrapers (FRED, SEC, Yahoo, eToro SAPI, GuruFocus, …)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  Python: modules/  │  modules_v2/  │  cli.py             │
│  Optional: qcd_platform (orchestrator, DB, Kafka, Redis)  │
└─────────────────────────────┬─────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   PostgreSQL            MCP server            Next.js API + UI
   (TimescaleDB)         (agents)              /api/v1, /api/dcc
```

- **v1** — Self-contained scripts; many are importable for MCP or invoked by CLI/API subprocesses.
- **v2** — Registered pipeline modules: fetch → clean → validate → store → events (see `qcd_platform/pipeline/`).
- **Next.js** — Serves the dashboard and bridges HTTP to Python; some routes use a fixed repo path — adjust for your host if needed.

---

## Getting started

### Prerequisites

- **Node.js** 20+ (matches CI)
- **Python** 3.12+
- **PostgreSQL + TimescaleDB** — only if you run the full pipeline or NL SQL features against a real DCC database

### Install

```bash
git clone https://github.com/shayhe-tr/quantclaw-data.git
cd quantclaw-data

pip install -r requirements.txt
npm install
```

### Environment

```bash
cp .env.example .env
# Fill API keys (many sources have free tiers).
```

| Variable | Purpose |
|----------|---------|
| `FRED_API_KEY`, `EIA_API_KEY`, `CENSUS_API_KEY`, … | See `.env.example` |
| `ANTHROPIC_API_KEY` | Natural language → SQL (DCC NL query) |
| `QCD_DB_*`, `QCD_KAFKA_SERVERS`, `QCD_REDIS_*` | Pipeline / DB-backed features (`qcd_platform/config`) |

For encrypted team `.env`, use `dotenvx` as documented in your internal runbooks.

### Run

```bash
# Dashboard + HTTP API (dev)
npm run dev          # http://localhost:3055

# Production build
npm run build && npm run start

# Examples — Python
python3 modules/cnn_fear_greed.py
python3 cli.py quote AAPL
python3 mcp_server.py
```

Pipeline (requires DB stack):

```bash
python3 qcd_platform/scripts/run_pipeline.py
```

---

## Project structure

```
quantclaw-data/
├── modules/              # 1,000+ v1 data modules (Python)
├── modules_v2/           # Pipeline modules (BaseModule)
├── qcd_platform/         # Orchestrator, schema, migrations, Redis/Kafka helpers
├── mcp_server.py         # MCP entrypoint
├── mcp_http_server.py    # HTTP MCP tools
├── cli.py                # CLI dispatcher
├── datascout.py          # Source discovery agent
├── src/
│   ├── app/              # Next.js App Router: pages, layout, dashboard, DCC
│   └── lib/              # DB client, NL query engine, schema catalog, etc.
├── data/                 # Local caches, datascout logs, signals, search index
├── scripts/              # Maintenance, validation, pipelines
├── tests/
└── .github/workflows/    # CI: module imports, Next build, stats
```

---

## API surface

- **`/api/v1/*`** — Tool-specific JSON endpoints (prices, macro, backtests, GuruFocus proxies, signal-centre, platinum dashboard, etc.). Discovery: browse `src/app/api/v1/`.
- **`/api/dcc/*`** — Operational DCC APIs: modules registry, pipeline/quality/stats/alerts, data sources, config health, SAPI helpers, **NL query**.
- **`/api/auth/*`** — Login/logout for the dashboard (session/cookies).

Representative patterns (exact query params vary by route):

- `GET /api/v1/fred-enhanced?series=GDP`
- `GET /api/v1/signal-fusion?ticker=AAPL`
- `GET /api/v1/monte-carlo?ticker=AAPL&sims=1000`
- `GET /api/dcc/modules`, `GET /api/dcc/sources`

> **Deploy note:** Many handlers assume the project root and `python3` on `PATH`, or a hardcoded install path. For a new server, search `src/app/api` for path constants and align them with your layout.

---

## Data sources (representative)

Government & macro: **FRED**, **BLS**, **Census**, **EIA**, **USDA**, **World Bank**, **OECD**, **Eurostat**, **UN Comtrade**, **IMF**, **BIS**, **SEC EDGAR**.  
Markets & fundamentals: **Yahoo Finance**, **Financial Datasets**, **GuruFocus**, **eToro SAPI**, **Finnhub**, **Polygon** (as configured).  
Alternatives: **CNN Fear & Greed**, **AAII**, on-chain/scraped feeds, DeFi and commodity specialists — see `modules/` and `data/datascout/` for the full surface.

---

## Deployment notes

- **Process:** Common pattern is `npm run build` + `npm run start` (port **3055**) behind a reverse proxy; PM2 or systemd for supervision.
- **CI (`.github/workflows/ci.yml`):** On PR/main — import-test `modules/*.py` (failure threshold >5 broken imports), `npm ci` + `npm run build` on Node 20.
- **Build:** `next.config.ts` may ignore TypeScript/ESLint errors during build; fix types/lint locally before relying on strict CI elsewhere.
- **Python deps:** Root `requirements.txt` is minimal; individual modules may need extra packages — add as you enable more routes.

---

## Contributing / modules

- **New v1 module:** Add `modules/your_module.py` (callable/importable or CLI-friendly).
- **New v2 module:** Subclass `BaseModule` in `modules_v2/`, register via `qcd_platform` scripts; see `qcd_platform/pipeline/base_module.py`.

---

*QuantClaw Data — consolidated financial data access for terminals, agents, and research workflows.*
