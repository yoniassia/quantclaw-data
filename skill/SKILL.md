---
name: quantclaw-data
description: "Comprehensive financial intelligence platform — 90+ modules covering market data, quant models, options analytics, alt data, fixed income, smart alerts, and more. 100+ CLI commands, REST API, MCP-ready. All free data sources."
metadata: {"openclaw":{"config":{"requiredEnv":[],"stateDirs":[".cache/quantclaw-data"],"example":"# No API keys required for core functionality\n# Optional: FRED_API_KEY for macro data\n"}}}
---

# QuantClaw Data Skill

Financial intelligence platform with 90+ modules. Bloomberg Terminal-level capabilities through CLI and REST API — powered entirely by free data sources.

**GitHub:** https://github.com/yoniassia/quantclaw-data
**Live:** https://data.quantclaw.org

## When to Use

Use this skill when the user asks about:
- Stock prices, crypto, commodities, forex
- Technical analysis (RSI, MACD, Bollinger, multi-timeframe)
- Options analysis (chains, Greeks, GEX, flow, pin risk)
- Quantitative models (Fama-French, Black-Litterman, Monte Carlo, Kalman)
- Alternative data (congress trades, social sentiment, 13F, patents, short interest)
- Portfolio analytics (Sharpe, VaR, backtesting, walk-forward)
- Fixed income (yield curves, credit spreads, CDS)
- Smart alerts with custom DSL expressions
- Pairs trading, sector rotation, regime detection
- SEC filings, earnings transcripts, NLP analysis
- Hedge fund holdings replication

## Setup

```bash
# Clone the repo
git clone https://github.com/yoniassia/quantclaw-data.git /tmp/quantclaw-data

# Install Python dependencies
pip install yfinance numpy scipy pandas statsmodels pandas-datareader requests beautifulsoup4

# Set the path (add to your shell profile)
export QUANTCLAW_DATA="/tmp/quantclaw-data"
```

## CLI Usage

All commands follow the pattern: `python $QUANTCLAW_DATA/cli.py <command> [args]`

### Market Data & Prices
```bash
python cli.py price AAPL                    # Real-time stock price
python cli.py price AAPL --history 30d       # Historical prices
python cli.py crypto bitcoin                 # Cryptocurrency
python cli.py commodity gold                 # Commodities
python cli.py forex EUR/USD                  # Forex pairs
```

### Technical Analysis
```bash
python cli.py technicals AAPL                # Full TA (RSI, MACD, SMA, etc.)
python cli.py mtf AAPL                       # Multi-timeframe (daily/weekly/monthly)
python cli.py kalman SPY                     # Kalman filter trend extraction
python cli.py adaptive-ma AAPL               # Adaptive moving average
python cli.py regime-detect SPY              # Market regime detection
python cli.py support-resistance AAPL        # Volume-based S/R levels
```

### Options & Derivatives
```bash
python cli.py options AAPL                   # Options chain with Greeks
python cli.py gex SPY                        # Gamma exposure (GEX)
python cli.py pin-risk AAPL                  # Pin risk at strikes
python cli.py hedging-flow TSLA              # Dealer hedging pressure
python cli.py options-flow --unusual         # Unusual options activity
```

### Quantitative Models
```bash
python cli.py fama-french AAPL               # Fama-French 3/5-factor regression
python cli.py factor-attribution TSLA        # Factor return decomposition
python cli.py monte-carlo AAPL --simulations 10000 --days 252  # Monte Carlo GBM
python cli.py var TSLA --confidence 0.95 0.99  # Value at Risk + CVaR
python cli.py scenario NVDA --days 90        # Bull/bear/crash scenarios
python cli.py black-litterman --tickers AAPL,MSFT,GOOGL --views AAPL:0.20  # Portfolio optimization
python cli.py equilibrium-returns --tickers SPY,QQQ,IWM  # Market equilibrium
python cli.py portfolio-optimize --tickers AAPL,MSFT,GOOGL  # Mean-variance
```

### Pairs Trading & Rotation
```bash
python cli.py cointegration KO PEP          # Engle-Granger test
python cli.py pairs-scan beverage            # Scan sector for pairs
python cli.py spread-monitor AAPL MSFT       # Z-score spread
python cli.py sector-rotation 60             # Sector rotation signals
python cli.py sector-momentum 90             # Momentum rankings
python cli.py economic-cycle                 # Economic cycle phase
```

### Alternative Data
```bash
python cli.py congress AAPL                  # Congressional trades
python cli.py social GME --source reddit     # Social sentiment
python cli.py 13f 0001067983                 # Hedge fund 13F (Berkshire)
python cli.py smart-money AAPL               # Institutional flow
python cli.py top-funds                      # Hedge fund directory
python cli.py activists AAPL                 # Activist investors
python cli.py short-interest --squeeze       # Short squeeze candidates
python cli.py patents AAPL                   # Patent filing velocity
python cli.py esg AAPL                       # ESG scores
python cli.py jobs AAPL                      # Job posting signals
```

### Portfolio & Risk
```bash
python cli.py portfolio-analyze portfolio.json  # Full analytics
python cli.py backtest --strategy momentum --period 1y  # Backtesting
python cli.py walk-forward SPY --strategy sma-crossover  # Walk-forward
python cli.py overfit-check AAPL             # Overfitting detection
```

### Smart Alerts (DSL)
```bash
python cli.py alert-create AAPL --condition "price>200"  # Create alert
python cli.py alert-list                     # List active alerts
python cli.py alert-check                    # Check all alerts
python cli.py alert-backtest AAPL --condition "rsi<30" --period 1y  # Backtest
python cli.py dsl-eval AAPL "price > 200 AND rsi < 30"  # Evaluate expression
python cli.py dsl-scan "rsi < 25" --universe SP500  # Scan with DSL
```

### Fixed Income & Macro
```bash
python cli.py bonds yield-curve              # Treasury yield curve
python cli.py credit-spreads                 # HY/IG credit spreads
python cli.py sovereign-risk Italy           # Sovereign CDS estimate
python cli.py macro gdp                      # GDP data
python cli.py fed-watch                      # Fed policy analysis
python cli.py rate-probability               # Rate hike probability
```

### SEC & Research
```bash
python cli.py sec AAPL                       # Recent SEC filings
python cli.py sec-nlp AAPL --section risk    # NLP risk factor analysis
python cli.py transcript AAPL                # Earnings transcript
python cli.py research-report AAPL           # AI-generated report
python cli.py earnings-tone AAPL             # Earnings call NLP
```

## REST API

Base URL: `https://data.quantclaw.org/api/v1` (or `http://localhost:3055/api/v1` locally)

```bash
# Examples
curl "https://data.quantclaw.org/api/v1/gex?symbol=SPY"
curl "https://data.quantclaw.org/api/v1/fama-french?ticker=AAPL"
curl "https://data.quantclaw.org/api/v1/monte-carlo?action=simulate&symbol=AAPL&simulations=1000&days=30"
curl "https://data.quantclaw.org/api/v1/pairs?action=cointegration&symbol1=KO&symbol2=PEP"
curl "https://data.quantclaw.org/api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price>200"
```

## MCP Configuration

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

## Data Sources (All Free)

- **Yahoo Finance** — Prices, options, fundamentals
- **SEC EDGAR** — Filings, 13F, insider trades
- **CoinGecko** — Crypto prices
- **FRED** — Macro indicators, yield curves
- **Kenneth French Library** — Academic factor returns
- **Google News** — Sentiment analysis
- **USPTO** — Patent data
- **NOAA** — Weather/agriculture

## Notes

- All commands output JSON for easy piping: `python cli.py price AAPL | jq .`
- No API keys required for core functionality
- Optional: `FRED_API_KEY` for enhanced macro data
- Cache directory: `.cache/quantclaw-data/` (auto-created)
- Rate limits: Yahoo Finance ~2000 req/hr, SEC EDGAR ~10 req/sec
