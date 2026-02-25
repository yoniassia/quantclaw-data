# 📈 QuantClaw Data

**The open financial intelligence platform.** 200+ modules built, 400 planned, 210 CLI commands, 54 REST APIs, 210 MCP tools.

> Built autonomously by AI agents. 140,888 lines of code. 187 data sources. Zero API keys required for core features.

🌐 **Live:** [data.quantclaw.org](https://data.quantclaw.org)
📦 **ClawHub:** `clawhub install quantclaw-data`
📖 **GitHub:** [github.com/yoniassia/quantclaw-data](https://github.com/yoniassia/quantclaw-data)

---

## 📊 Stats

| Metric | Count |
|--------|-------|
| Lines of Code | 140,888+ |
| Python Modules | 181+ |
| Next.js API Routes | 54 |
| MCP Tools | 210 |
| CLI Commands | 210 |
| Unique Data Sources | 187 |
| Phases Complete | 207/400 |

---

## ⚡ Quick Start

```bash
# Install via ClawHub (for OpenClaw agents)
clawhub install quantclaw-data

# Or clone manually
git clone https://github.com/yoniassia/quantclaw-data.git
cd quantclaw-data

# Install dependencies
pip install yfinance numpy scipy pandas statsmodels pandas-datareader requests beautifulsoup4

# Try it
python cli.py price AAPL
python cli.py technicals TSLA
python cli.py monte-carlo SPY --simulations 10000
python cli.py fama-french NVDA
python cli.py screener --sector Technology --min-cap 10B
```

---

## 🔌 4 Access Methods

### 1. CLI (210 commands)
```bash
python cli.py price AAPL                    # Real-time price
python cli.py technicals TSLA               # RSI, MACD, Bollinger
python cli.py options AAPL                  # Options chain + Greeks
python cli.py monte-carlo SPY              # Monte Carlo simulation
python cli.py fama-french AAPL             # Factor regression
python cli.py congress AAPL                # Congressional trades
python cli.py bonds yield-curve            # Treasury yield curve
python cli.py crypto bitcoin               # Crypto prices
python cli.py forex EUR/USD                # Forex rates
python cli.py smart-money AAPL             # Institutional flow
```

### 2. REST API (54 endpoints)
```bash
# Base: https://data.quantclaw.org/api/v1
curl "https://data.quantclaw.org/api/v1/prices?ticker=AAPL"
curl "https://data.quantclaw.org/api/v1/monte-carlo?symbol=SPY&simulations=1000"
curl "https://data.quantclaw.org/api/v1/fama-french?ticker=NVDA"
curl "https://data.quantclaw.org/api/v1/pairs?symbol1=KO&symbol2=PEP"
curl "https://data.quantclaw.org/api/v1/cds?action=credit-spreads"
```

### 3. MCP Server (for AI agents)
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

### 4. Web Dashboard
Browse all modules with interactive cards at [data.quantclaw.org](https://data.quantclaw.org)

---

## 📦 Module Categories

| Category | Modules | Examples |
|----------|---------|---------|
| 📊 Core Market Data | 20+ | Prices, profiles, screener, technicals, multi-timeframe |
| 📈 Derivatives & Options | 15+ | Options flow, GEX, vol surface, Greeks, pin risk |
| 🧮 Quantitative | 30+ | Fama-French, Monte Carlo, Kalman, Black-Litterman, pairs |
| 🏦 Fixed Income & Macro | 25+ | Yield curves, CDS, Fed policy, inflation, PBOC, ECB |
| 🔍 Alternative Data | 25+ | Satellite, dark pool, insider, patents, Congress trades |
| 📰 Corporate Events | 15+ | Earnings, M&A, buybacks, activist, proxy fights |
| 🤖 Intelligence & NLP | 20+ | News sentiment, filing analysis, AI earnings, FinBERT |
| 🌍 Multi-Asset | 20+ | Crypto, FX cross rates, commodities, sector rotation |
| ⚙️ Infrastructure | 10+ | Alerts, backtest, reconciliation, PDF export, streaming |

---

## 📡 Data Sources (187)

**Top sources by reference count:**
| Source | Type | References |
|--------|------|-----------|
| FRED (St. Louis Fed) | Macro/rates | 654 |
| US Treasury | Fixed income | 265 |
| Yahoo Finance | Market data | 197 |
| OPEC | Commodities | 171 |
| IMF | Global macro | 108 |
| SEC EDGAR | Regulatory | 76 |
| USDA | Agriculture | 99 |
| Eurostat | EU macro | 50 |
| CFTC | Positioning | 32 |
| EIA | Energy | 31 |
| ECB | EU rates | 29 |
| Census Bureau | Demographics | 21 |
| BLS | Labor | 5 |

**Plus:** World Bank, CoinGecko, DeFi Llama, Binance, BOJ, PBOC, OECD, FAO, IEA, LME, arXiv, USPTO, NOAA, Polygon, Finnhub, Alpaca, MSRB, CAISO, and 150+ more.

---

## 🗺️ Roadmap

### ✅ Phases 1-200: COMPLETE
Foundation → Quant → Alt Data → ML/AI → Intelligence → Events → Global Macro → Equity Analysis → Fixed Income → Commodities → FX & Crypto → Alternative Data

### 🔨 Phases 201-400: BUILDING
| Range | Domain | Examples |
|-------|--------|---------|
| 201-220 | Real-Time & Streaming | WebSocket feeds, options flow, liquidation monitor |
| 221-240 | Quantitative Strategies | Stat arb, momentum, carry, risk parity, GARCH |
| 241-260 | Institutional Infrastructure | FIX gateway, attribution, TCA, margin calc |
| 261-280 | Global Macro Deep Dive | Taylor Rule, PPP, recession model, housing |
| 281-300 | AI/ML Models | Transformer predictor, RL agent, GNN, AutoML |
| 301-320 | Blockchain & Digital Assets | On-chain analytics, DEX feeds, MEV, RWA |
| 321-340 | Alternative Data v2 | Satellite, job postings, FDA, weather impact |
| 341-360 | Fixed Income Deep | CLO, ABS/MBS, muni, distressed debt |
| 361-380 | Commodities Deep | Crack spreads, OPEC compliance, rare earths |
| 381-400 | Next-Gen & Experimental | Prediction markets, CBDC, quantum, space economy |

Full roadmap: [ROADMAP_400.md](./ROADMAP_400.md)

---

## 🧪 Testing

```bash
# Run data integrity tests
python -m pytest tests/ -v

# Test individual module import
python -c "import modules.monte_carlo; print('OK')"

# Test API endpoint
curl -s "https://data.quantclaw.org/api/v1/prices?ticker=AAPL" | python -m json.tool

# Run full test suite
python tests/test_data_integrity.py
```

Tests validate:
- All modules import cleanly
- Core functions return expected data types
- API endpoints return valid JSON with correct schemas
- Data freshness (prices < 24h old on trading days)
- Cross-module consistency (same ticker returns consistent data)

---

## 🏗️ How It's Built

Built **autonomously by AI agents**:
1. Builder agent runs every 10 min, creates 5 modules per batch
2. Each module: Python + CLI + API route + MCP tool definition
3. Auto-builds, auto-tests, auto-deploys to data.quantclaw.org
4. Tester agent runs every 30 min, validates 10 random modules
5. Every 5 modules → auto-commit to GitHub + version bump

**Cost per module:** ~$0.04 (Claude Sonnet)
**Build rate:** ~30 modules/hour

---

## 📁 Project Structure

```
quantclaw-data/
├── cli.py                     # CLI dispatcher (210 commands)
├── modules/                   # Python modules (181+)
│   ├── monte_carlo.py
│   ├── fama_french.py
│   ├── black_litterman.py
│   ├── kalman_filter.py
│   ├── pairs_trading.py
│   ├── websocket_price_streamer.py
│   ├── crypto_liquidation_monitor.py
│   └── ... (181+ files)
├── tests/                     # Data integrity tests
│   └── test_data_integrity.py
├── src/app/
│   ├── page.tsx               # Dashboard UI
│   ├── services.ts            # Module registry (210 services)
│   ├── roadmap.ts             # Roadmap with status tracking
│   ├── install.ts             # Install docs & CLI reference
│   └── api/v1/                # REST API routes (54)
├── skill/SKILL.md             # ClawHub skill definition
├── ROADMAP_400.md             # Full 400-phase roadmap
├── package.json
└── README.md
```

---

## 🤝 Part of the QuantClaw Ecosystem

- [QuantClaw Data](https://data.quantclaw.org) — Financial Intelligence Platform
- [TerminalX](https://terminal.quantclaw.org) — Bloomberg-style CIO Console
- [AgentX](https://agentx.moneyclaw.com) — Personal AI Trading Agents
- [ClawX](https://x.quantclaw.org) — AI Social Trading
- [GoodWallet](https://wallet.quantclaw.org) — DeFi + Predictions

---

## 📜 License

MIT — use it, fork it, build on it.

---

**Built with 🦞 by [QuantClaw](https://quantclaw.org) — Autonomous Financial Intelligence**
