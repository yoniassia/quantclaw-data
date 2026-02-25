# 📈 QuantClaw Data

**The open financial intelligence platform.** 42 modules built, 93 planned, 100+ CLI commands, REST API, MCP-ready.

> Built autonomously by AI agents. 5 modules built in parallel every ~7 minutes. Self-evolving roadmap.

🌐 **Live:** [data.quantclaw.org](https://data.quantclaw.org)
📖 **CLI Reference:** [data.quantclaw.org/#install](https://data.quantclaw.org/#install)

---

## 📦 Install via ClawHub (for OpenClaw agents)

```bash
clawhub install quantclaw-data
```

Or manually:

---

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/yoniassia/quantclaw-data.git
cd quantclaw-data

# Install dependencies
pip install yfinance numpy scipy pandas statsmodels pandas-datareader requests beautifulsoup4

# Try it
python cli.py price AAPL
python cli.py technicals TSLA
python cli.py fama-french NVDA
python cli.py monte-carlo SPY --simulations 10000 --days 252
```

---

## 🧠 What Is This?

QuantClaw Data is a **comprehensive financial data platform** that gives you Bloomberg Terminal-level capabilities through a simple CLI and REST API — powered entirely by free data sources.

It covers:
- **Real-time prices** for stocks, crypto, commodities, forex
- **Quantitative models** — Fama-French, Black-Litterman, Monte Carlo, Kalman Filter
- **Options analytics** — Greeks, GEX, pin risk, flow analysis
- **Alternative data** — Congressional trades, social sentiment, patent filings, satellite proxies
- **Fixed income** — Yield curves, credit spreads, CDS estimates
- **Smart alerts** — Custom DSL for complex multi-condition rules
- **SEC filings** — NLP analysis, earnings transcripts, 13F replication

**All free. No API keys required for core functionality.**

---

## 📊 Module Status

| Status | Count | Description |
|--------|-------|-------------|
| ✅ Done | 42 | Production-ready, tested |
| 🔧 Building | 5 | Agents working right now |
| 📋 Planned | 46 | In the autonomous pipeline |

### ✅ Built Modules (42/93)

#### Foundation (Phases 1-4)
| # | Module | What It Does |
|---|--------|-------------|
| 1 | Core Market Data | Real-time prices, SEC EDGAR, news sentiment, caching |
| 2 | Enhanced Data | Options chains with Greeks, earnings, macro, dividends, ETF holdings |
| 3 | Alternative Data | Social sentiment (Reddit/StockTwits), congress trades, short interest, TA |
| 4 | Multi-Asset | Cryptocurrency (CoinGecko), commodities, forex, analyst ratings, screener |

#### Intelligence (Phases 5-10)
| # | Module | What It Does |
|---|--------|-------------|
| 5 | Earnings Transcripts NLP | Parse 8-K transcripts, extract quotes, guidance changes, sentiment |
| 6 | Options Flow Scanner | Unusual activity alerts, dark pool prints, sweep detection |
| 7 | Factor Model Engine | Momentum, value, quality, size, volatility scoring |
| 8 | Portfolio Analytics | Sharpe, Sortino, max drawdown, correlation matrix, VaR |
| 9 | Backtesting Framework | Event-driven backtester with slippage, fills, commissions |
| 10 | Smart Alerts | Price/volume/RSI alerts with multi-channel delivery |

#### Advanced Analytics (Phases 11-27)
| # | Module | What It Does |
|---|--------|-------------|
| 11 | Patent Tracking | USPTO filings, R&D velocity, innovation index |
| 12 | Job Posting Signals | Hiring velocity as leading indicator, dept growth |
| 13 | Supply Chain Mapping | SEC NLP for supplier/customer relationships |
| 14 | Weather & Agriculture | NOAA data, crop conditions, energy demand signals |
| 15 | Bond Analytics | Yield curves, credit spreads, duration, convexity |
| 16 | SEC NLP Analysis | Risk factor extraction, MD&A sentiment, change detection |
| 17 | IPO & SPAC Tracker | Upcoming IPOs, SPAC arbitrage, lock-up expiries |
| 18 | M&A Deal Flow | Announced deals, merger arb spreads, completion probability |
| 19 | Activist Investor Tracking | 13D filings, campaign tracking, target identification |
| 20 | ESG Scoring | Environmental, social, governance composite scores |
| 21 | Quant Factor Zoo | 400+ published academic factors with validation |
| 22 | Market Microstructure | Bid-ask spreads, order flow, liquidity scoring |
| 23 | AI Research Reports | LLM-generated equity research from all data sources |
| 24 | Data Quality Monitor | Staleness checks, source health, broken feed alerts |
| 25 | Real-time Streaming | WebSocket feeds (Polygon, Finnhub, Alpaca), L2 quotes |
| 26 | ML Earnings Predictor | RF + XGBoost ensemble, 77% accuracy on beats/misses |
| 27 | Correlation Heatmaps | Cross-asset regime detection, 22 ETFs, Z-score anomalies |

#### Quantitative Models (Phases 28-42)
| # | Module | What It Does |
|---|--------|-------------|
| 28 | Options GEX Tracker | Dealer gamma exposure, pin risk, hedging flow |
| 29 | Hedge Fund 13F Replication | Clone top fund positions, quarterly changes, smart money |
| 30 | CDS Spreads | Sovereign & corporate credit risk signals |
| 31 | Fama-French Regression | 3-factor & 5-factor models, statistical attribution |
| 32 | Pairs Trading Signals | Cointegration (Engle-Granger), z-score spreads, half-life |
| 33 | Sector Rotation Model | Economic cycle indicators, relative strength rotation |
| 34 | Monte Carlo Simulation | GBM, bootstrap, VaR/CVaR, scenario analysis |
| 35 | Kalman Filter Trends | Adaptive MA, regime detection, state-space models |
| 36 | Black-Litterman Allocation | Equilibrium returns + investor views, portfolio construction |
| 37 | Walk-Forward Optimization | Rolling windows, overfitting detection, param stability |
| 38 | Multi-Timeframe Analysis | Daily/weekly/monthly signal confluence |
| 39 | Order Book Depth | L2 simulation, bid-ask imbalance, liquidity scoring |
| 40 | Smart Alert Delivery | Multi-channel notifications with rate limiting |
| 41 | Alert Backtesting | Historical signal quality, hit rates, profit factor |
| 42 | Custom Alert DSL | `price > 200 AND rsi < 30` expression language |

---

## 🖥️ CLI Commands

### Market Data
```bash
python cli.py price AAPL                          # Real-time price
python cli.py price AAPL --history 30d             # Historical
python cli.py crypto bitcoin                       # Crypto
python cli.py commodity gold                       # Commodities
python cli.py forex EUR/USD                        # Forex
```

### Technical Analysis
```bash
python cli.py technicals AAPL                      # Full TA (RSI, MACD, SMA)
python cli.py mtf AAPL                             # Multi-timeframe
python cli.py kalman SPY                           # Kalman filter trend
python cli.py regime-detect TSLA                   # Market regime
python cli.py support-resistance AAPL              # Volume-based S/R
```

### Options
```bash
python cli.py options AAPL                         # Options chain + Greeks
python cli.py gex SPY                              # Gamma exposure
python cli.py pin-risk AAPL                        # Pin risk analysis
python cli.py options-flow --unusual               # Unusual activity
```

### Quantitative Models
```bash
python cli.py fama-french AAPL                     # Factor regression
python cli.py monte-carlo AAPL --simulations 10000 # Monte Carlo
python cli.py var TSLA --confidence 0.95 0.99      # Value at Risk
python cli.py black-litterman --tickers AAPL,MSFT,GOOGL  # Portfolio optimization
python cli.py cointegration KO PEP                 # Pairs trading
python cli.py sector-rotation 60                   # Sector rotation signals
python cli.py walk-forward SPY --strategy sma-crossover  # Walk-forward test
```

### Alternative Data
```bash
python cli.py congress AAPL                        # Congressional trades
python cli.py social GME --source reddit           # Social sentiment
python cli.py 13f 0001067983                       # Hedge fund holdings (Berkshire)
python cli.py smart-money AAPL                     # Institutional flow
python cli.py top-funds                            # Top hedge funds
python cli.py activists AAPL                       # Activist investors
python cli.py short-interest --squeeze             # Short squeeze candidates
python cli.py patents AAPL                         # Patent velocity
```

### Smart Alerts
```bash
python cli.py alert-create AAPL --condition "price>200"  # Create alert
python cli.py alert-list                           # List active
python cli.py alert-check                          # Check against live data
python cli.py alert-backtest AAPL --condition "rsi<30" --period 1y  # Backtest
python cli.py dsl-eval AAPL "price > 200 AND rsi < 30"  # DSL expression
python cli.py dsl-scan "rsi < 25" --universe SP500      # Scan universe
```

### Fixed Income & Macro
```bash
python cli.py bonds yield-curve                    # Treasury yield curve
python cli.py credit-spreads                       # HY/IG spreads
python cli.py sovereign-risk Italy                 # Sovereign CDS
python cli.py macro gdp                            # GDP data
python cli.py macro cpi --history 5y               # Inflation
```

---

## 🌐 REST API

Base URL: `https://data.quantclaw.org/api/v1`

```bash
# Gamma exposure
curl "https://data.quantclaw.org/api/v1/gex?symbol=SPY"

# Fama-French regression
curl "https://data.quantclaw.org/api/v1/fama-french?ticker=AAPL"

# Monte Carlo simulation
curl "https://data.quantclaw.org/api/v1/monte-carlo?action=simulate&symbol=AAPL&simulations=1000&days=30"

# Pairs trading
curl "https://data.quantclaw.org/api/v1/pairs?action=cointegration&symbol1=KO&symbol2=PEP"

# Alert DSL
curl "https://data.quantclaw.org/api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price>200%20AND%20rsi<30"

# Credit spreads
curl "https://data.quantclaw.org/api/v1/cds?action=credit-spreads"

# Hedge fund 13F
curl "https://data.quantclaw.org/api/v1/13f?cik=0001067983"
```

All endpoints return JSON.

---

## 🤖 MCP Server (for AI Agents)

Add to your Claude Desktop or MCP client config:

```json
{
  "mcpServers": {
    "quantclaw-data": {
      "command": "node",
      "args": ["mcp-server.js"],
      "cwd": "/path/to/quantclaw-data"
    }
  }
}
```

---

## 📡 Data Sources (All Free)

| Source | Type | Modules |
|--------|------|---------|
| Yahoo Finance | Market Data | Prices, options, technicals, fundamentals |
| SEC EDGAR | Regulatory | 10-K, 10-Q, 8-K, insider trades, 13F |
| CoinGecko | Crypto | Prices, market cap, volume |
| FRED | Macro | GDP, CPI, rates, yield curves |
| Google News RSS | News | Real-time aggregation + NLP |
| USPTO | Alt Data | Patent filings, R&D velocity |
| NOAA | Alt Data | Weather, crop conditions |
| Reddit/StockTwits | Social | Retail sentiment |
| Congressional Disclosures | Alt Data | Politician trades |
| Polygon.io | Streaming | Real-time WebSocket |
| Finnhub | Streaming | Multi-market data |
| Alpaca | Streaming | Commission-free feeds |
| Kenneth French Library | Academic | Fama-French factor returns |

---

## 🗺️ Full Roadmap

### ✅ Done (42 phases)
Phases 1-42 — see module table above.

### 🔧 In Progress
| # | Module | Description |
|---|--------|-------------|
| 43 | Crypto On-Chain Analytics | Whale tracking, token flows, DEX volume, gas fees |
| 44 | Commodity Futures Curves | Contango/backwardation, roll yields, term structure |
| 45 | Fed Policy Prediction | FOMC analysis, dot plot, rate probability |
| 46 | Satellite Imagery Proxies | Foot traffic, shipping, construction activity |
| 47 | Earnings Call NLP | Tone, confidence, question-dodging detection |

### 📋 Planned (46 phases)
| # | Module | Description |
|---|--------|-------------|
| 48 | Peer Network Analysis | Interconnected company relationships, systemic risk |
| 49 | Political Risk Scoring | Geopolitical events, sanctions, regulatory impact |
| 50 | Product Launch Tracker | Social buzz, pre-order velocity, review sentiment |
| 51 | Executive Compensation | Pay-for-performance, peer comparison |
| 52 | Revenue Quality Analysis | Cash flow vs earnings divergence, channel stuffing |
| 53 | Peer Earnings Comparison | Beat/miss patterns, guidance trends |
| 54 | Crypto Correlation Indicators | BTC dominance, altcoin seasonality, DeFi TVL |
| 55 | Tax Loss Harvesting | Opportunities, wash sale rules, tax savings |
| 56 | Share Buyback Analysis | Authorization vs execution, dilution impact |
| 57 | Dividend Sustainability | Payout ratio, FCF coverage, cut probability |
| 58 | Institutional Ownership | 13F changes, whale accumulation/distribution |
| 59 | Earnings Quality Metrics | Accruals ratio, Beneish M-Score, Altman Z-Score |
| 60 | Sector Performance Attribution | Allocation vs selection effect decomposition |
| 61 | Dark Pool Tracker | Block trades, institutional accumulation |
| 62 | Estimate Revision Tracker | Analyst upgrade/downgrade velocity |
| 63 | Corporate Action Calendar | Ex-dates, splits, spin-offs, rights offerings |
| 64 | Convertible Bond Arbitrage | Conversion premium, implied vol, delta hedging |
| 65 | Short Squeeze Detector | High SI + low float + technical signals |
| 66 | Market Regime Detection | Volatility clustering, correlation breakdowns |
| 67 | Activist Success Predictor | ML model on historical campaign outcomes |
| 68 | 13D/13G Filing Alerts | Real-time webhook for activist filings |
| 69 | Proxy Fight Tracker | ISS/Glass Lewis recommendations, voting |
| 70 | Greenwashing Detection | ESG report vs actual metrics analysis |
| 71 | Sustainability-Linked Bonds | SLB issuance, KPI achievement |
| 72 | Climate Risk Scoring | Physical risk, transition risk, scenarios |
| 73 | Factor Timing Model | Regime detection for when factors work |
| 74 | ML Factor Discovery | Automated predictive factor engineering |
| 75 | Transaction Cost Analysis | Market impact, bid-ask modeling |
| 76 | AI Earnings Call Analyzer | Real-time tone via LLM |
| 77 | Cross-Exchange Arbitrage | Price discrepancies across exchanges |
| 78 | Regulatory Event Calendar | FOMC/CPI/GDP with reaction backtests |
| 79 | PDF Report Exporter | Markdown → professional PDF + email |
| 80 | Alert Backtesting Dashboard | Visual performance with Sharpe ratio |
| 81 | Portfolio Construction Tool | MPT, BL, ESG constraints, tax-aware |
| 82 | Live Earnings Transcription | Stream + transcribe + extract signals |
| 83 | Smart Data Prefetching | ML predicts next request, preloads |
| 84 | Multi-Source Reconciliation | Compare sources, confidence voting |
| 85 | Neural Price Prediction | LSTM/Transformer with uncertainty |
| 86 | Order Book Imbalance | L3 data, short-term price prediction |
| 87 | Correlation Anomaly Detector | Unusual correlation breakdowns |
| 88 | Deep Learning Sentiment | FinBERT for filings, news, calls |
| 89 | Volatility Surface Modeling | IV smile/skew, vol arbitrage |
| 90 | ML Stock Screening | Multi-factor ML ranking |
| 91 | Insider Trading Network | Coordinated buying/selling clusters |
| 92 | Earnings Quality Forensics | Deep accounting red flag detection |
| 93 | Social Sentiment Spike Detector | Real-time surge detection, pump alerts |

---

## 🏗️ How It's Built

This platform is built **autonomously by AI agents**:

1. **5 sub-agents run in parallel**, each building one module (~5-7 min each)
2. Each agent reads existing patterns, creates Python module + CLI + API route
3. When a batch of 5 completes → deploy → launch next 5
4. At phase 80 → a research agent discovers new data sources
5. At phase 93 → pipeline self-terminates

**Cost per module:** ~$0.04 (Claude Sonnet)
**Total platform cost:** ~$4 for all 93 modules
**Build time:** ~2 hours for the full platform

---

## 📁 Project Structure

```
quantclaw-data/
├── cli.py                    # Main CLI dispatcher
├── modules/                  # Python modules (one per phase)
│   ├── alert_backtest.py
│   ├── alert_dsl.py
│   ├── black_litterman.py
│   ├── cds_spreads.py
│   ├── kalman_filter.py
│   ├── monte_carlo.py
│   ├── multi_timeframe.py
│   ├── order_book.py
│   ├── pairs_trading.py
│   ├── sector_rotation.py
│   ├── smart_alerts.py
│   └── walk_forward.py
├── src/app/
│   ├── page.tsx              # Dashboard UI
│   ├── services.ts           # Module registry
│   ├── roadmap.ts            # Full roadmap with status
│   ├── install.ts            # Install instructions & CLI reference
│   └── api/v1/               # REST API routes
├── package.json
└── README.md
```

---

## 🤝 Part of the MoneyClaw Ecosystem

- [MoneyClaw](https://moneyclaw.com) — AI Trading Agents
- [TerminalX](https://terminal.quantclaw.org) — Bloomberg-style Terminal
- [ClawX](https://x.quantclaw.org) — AI Trading Assistant
- [GoodWallet](https://wallet.quantclaw.org) — DeFi + Predictions

---

## 📜 License

MIT — use it, fork it, build on it.

---

**Built with 🦞 by [QuantClaw](https://quantclaw.org) — Autonomous Financial Intelligence**
