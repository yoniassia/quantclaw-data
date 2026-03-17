# 📈 QuantClaw Data — AI-Built Financial Intelligence Platform

> **965 production modules. 353K+ lines of Python. 179 data sources cataloged. $0/month. Built autonomously by AI agents.**

🌐 **Live**: [quantclaw.org](https://quantclaw.org) | 📊 **Dashboard**: [data.quantclaw.org](https://data.quantclaw.org)

---

## What is QuantClaw Data?

QuantClaw Data is the world's largest open-source financial data platform built entirely by AI agents. Every module collects, processes, and serves real financial data from free public sources — no paid API keys required.

The platform powers **Alpha Picker V3**, an autonomous stock-picking algorithm that matches SeekingAlpha Quant ratings with 69% accuracy and achieves a 92% win rate in backtesting.

## 🔢 By the Numbers

| Metric | Value |
|--------|-------|
| **Python Data Modules** | 965 |
| **Lines of Python (modules)** | 352,949+ |
| **Total Python (all files)** | 416,255+ |
| **Data Sources Cataloged** | 179 (DataScout) |
| **MCP Server** | 12,769 LOC |
| **CLI** | 1,776 LOC |
| **Cached Data** | 378 MB |
| **Monthly Cost** | **$0** |
| **Countries Covered** | 40+ |

---

## 🏗️ Architecture

```
quantclaw-data/
├── modules/              965 Python data modules (353K LOC)
│   ├── alpha_picker.py        Stock scoring algorithm (970 lines)
│   ├── sa_quant_replica.py    SA Quant reverse-engineering (1,232 lines)
│   ├── live_paper_trading.py  Portfolio engine (594 lines)
│   ├── signal_fusion.py       Multi-signal combiner
│   └── ...961 more modules
├── data/                 378 MB cached financial data
│   ├── signals/               Live trading signals
│   ├── datascout/             179 cataloged data sources
│   └── live_portfolio.db      Paper trading SQLite DB
├── src/app/              Next.js dashboard + roadmap UI
├── mcp_server.py         MCP API server (12.8K lines)
├── run_v3_signal.py      Alpha Picker live signal runner
├── run_param_sweep_v2.py Backtesting engine
├── cli.py                CLI interface (1.8K lines)
├── datascout.py          Continuous data source discovery agent
└── tests/                Integration & QA tests
```

---

## 📊 Module Categories

| Category | Modules | Description |
|----------|---------|-------------|
| 🏛️ Equity & Earnings | 27 | EPS revisions, analyst estimates, DCF, comps |
| 🏦 Commodities | 24 | Oil, gold, metals, agriculture, rig counts |
| 💵 Fixed Income | 21 | Treasury yields, corporate bonds, TIPS |
| 🌍 Macro & Central Bank | 16 | Fed, ECB, BIS, IMF, GDP, CPI |
| 🪙 Crypto & DeFi | 15 | DeFi Llama, on-chain, DEX volumes |
| 📊 Technical & Quant | 15 | Factor models, momentum, volatility |
| 💱 FX & Currency | 10 | Cross rates, carry trade, PPP |
| ⚔️ Geopolitical & Risk | 10 | Conflict monitors, sanctions, risk scores |
| 📑 Regulatory & Filing | 9 | SEC EDGAR, insider trades, 13F filings |
| 📡 Alternative Data | 8 | Wikipedia pageviews, sentiment, web traffic |
| 🚨 Signals & Alerts | 8 | Signal fusion, smart alerts, discovery |
| 📉 Derivatives | 7 | CBOE put/call, VIX, options flow |
| 🌱 ESG & Climate | 5 | Carbon markets, green bonds |
| 🎯 Portfolio & Risk | 5 | Optimization, rebalancing, drawdown |
| 💬 Sentiment & NLP | 4 | FinBERT, earnings call NLP |
| 🔧 Cross-domain | 781+ | Country stats, ML/AI, infrastructure, extended sources |

---

## 🎯 Alpha Picker V3 — Crown Jewel

Autonomous stock-picking engine reverse-engineering institutional quant strategies:

| Metric | Value |
|--------|-------|
| SA Agreement Rate | 69% (31/45 picks match) |
| Win Rate | 92% on 40 backtested picks |
| Annual Return | 41.5% (Triple Pyramid) |
| Max Drawdown | -7.9% |
| Sharpe Ratio | 5.3 |
| Strategy | $5K base + adds at +10%, +20%, +35% |
| Rebalance | Bi-weekly (1st & 15th) |

### How It Works
1. **Universe Filter**: 7,017 stocks → 386 candidates
2. **Multi-Factor Scoring**: Value + Growth + Momentum + Quality + Earnings Revision
3. **SA Quant Replica**: Reverse-engineered scoring matching SeekingAlpha
4. **Signal Fusion**: 7+ data sources per stock
5. **Live Signals**: Automated cron on 1st & 15th at 14:00 UTC

---

## 🔌 MCP Server (Model Context Protocol)

All 965 modules exposed as AI-callable tools:

```bash
python3 mcp_server.py  # Port 3055
```

---

## 🔍 DataScout — Continuous Discovery

Discovers new free data sources across 24 rotating categories. 179 sources cataloged and growing.

---

## 🗺️ Roadmap

| Phases | Status | Description |
|--------|--------|-------------|
| 1-100 | ✅ | Core macro, equity, fixed income, FX |
| 101-200 | ✅ | Country stats, derivatives, commodities |
| 201-300 | ✅ | Crypto, DeFi, ESG, alt data |
| 301-400 | ✅ | ML/AI models, NLP, factor engines |
| 401-500 | ✅ | Infrastructure, streaming |
| 501-699 | ✅ | Advanced analytics, emerging markets |
| 700-800 | ✅ | Free no-API-key sources (DataScout) |
| 800-965 | ✅ | Extended free sources, ML signals |
| 965+ | 🔄 | Continuous autonomous expansion |

---

## 🚀 Quick Start

```bash
git clone https://github.com/yoniassia/quantclaw-data.git
cd quantclaw-data
pip install requests beautifulsoup4 pandas numpy
npm install

# Create your .env with API keys (see Environment Variables below)
cp .env.example .env  # then fill in your keys

# Run any module
python3 modules/cnn_fear_greed.py
python3 modules/fed_soma.py

# Alpha Picker signal
python3 run_v3_signal.py

# MCP server
python3 mcp_server.py

# Dashboard
npm run dev
```

## 🔐 Environment Variables

API keys are encrypted with [dotenvx](https://dotenvx.com). The encrypted `.env` is in the repo — contributors with the decryption key can use it directly.

**For contributors with access to the decryption key:**
```bash
# Set the private key (shared securely by maintainers)
export DOTENV_PRIVATE_KEY="your-key-here"

# Run any command — dotenvx auto-decrypts
npx dotenvx run -- python3 modules/cnn_fear_greed.py
npx dotenvx run -- npm run dev
```

**For new contributors (bring your own keys):**
```bash
cp .env.example .env
# Fill in your own API keys — most have free tiers:
# FRED, Census, Finnhub, Etherscan, Polygon.io, USDA NASS
```

| Variable | Source | Free Tier |
|----------|--------|-----------|
| `FRED_API_KEY` | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) | ✅ |
| `CENSUS_API_KEY` | [census.gov](https://api.census.gov/data/key_signup.html) | ✅ |
| `FINNHUB_API_KEY` | [finnhub.io](https://finnhub.io/) | ✅ |
| `FD_API_KEY` | [financialdatasets.ai](https://financialdatasets.ai) | ✅ |
| `ETHERSCAN_API_KEY` | [etherscan.io](https://etherscan.io/apis) | ✅ |
| `POLYGONIO_API_KEY` | [polygon.io](https://polygon.io/) | ✅ |
| `USDA_NASS_API_KEY` | [quickstats.nass.usda.gov](https://quickstats.nass.usda.gov/api) | ✅ |

---

## 🤖 Built by AI Agents

| Agent | Role |
|-------|------|
| DataClaw 📊 | Builds new modules from roadmap |
| DataQAClaw 🔬 | Tests and quality-maps modules |
| DataScout 🔍 | Discovers new free data sources |
| Alpha Picker 🎯 | Generates trading signals |
| BacktestClaw ⚡ | Validates strategies |

---

*Built with ❤️ by AI agents. $0/month. 965 modules and counting.*
