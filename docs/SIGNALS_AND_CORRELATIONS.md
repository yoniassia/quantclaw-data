# 📡 QuantClaw Data — Signal Discovery & Correlation APIs

> **Version:** 1.6.0 | **Modules:** 208 | **Data Sources:** 162 | **Last Updated:** 2026-02-26

The signal and correlation layer is QuantClaw Data's most powerful feature — it turns raw financial data into actionable trading signals by finding hidden relationships across 208 modules and 162 data sources.

---

## 🔍 Signal Discovery Modules

### 1. Signal Discovery Engine
**Module:** `signal_discovery_engine` | **Category:** quant

Automatically scans across all data modules to find statistically significant predictive signals.

| Function | Description |
|----------|-------------|
| `discover_signals(ticker)` | Scan all available data for predictive signals on a given ticker |
| `test_signal_correlation(signal, returns)` | Test if a signal has statistically significant correlation with future returns |
| `get_price_data(ticker, period)` | Fetch price data for signal testing |

**CLI:**
```bash
python cli.py signal-discover AAPL
python cli.py signal-test AAPL --signal earnings_surprise --horizon 5d
```

**REST API:**
```
GET /api/v1/signal-discovery-engine?ticker=AAPL
```

**MCP Tool:** `signal_discovery_engine`

**Update Frequency:** On-demand (runs live analysis)

---

### 2. Signal Fusion
**Module:** `signal_fusion` | **Category:** quant

Combines signals from multiple sources (technical, fundamental, sentiment, smart money) into a single weighted composite signal with confidence scoring.

| Function | Description |
|----------|-------------|
| `get_signal_fusion(ticker)` | Get composite signal combining all available signals |
| `get_technical_signal(ticker)` | RSI, MACD, Bollinger, momentum signals |
| `get_fundamental_signal(ticker)` | Earnings quality, valuation, growth signals |
| `get_sentiment_signal(ticker)` | News sentiment, social media, analyst revisions |
| `get_smart_money_signal(ticker)` | Institutional flow, insider trades, dark pool activity |

**CLI:**
```bash
python cli.py signal-fusion AAPL
python cli.py signal-technical TSLA
python cli.py signal-fundamental MSFT
python cli.py signal-sentiment NVDA
python cli.py signal-smart-money META
```

**REST API:**
```
GET /api/v1/signal-fusion?ticker=AAPL
```

**MCP Tool:** `signal_fusion`

**Update Frequency:** Real-time (aggregates live data from 4+ signal sources)

---

### 3. Cross-Correlate
**Module:** `cross_correlate` | **Category:** quant

Finds leading/lagging relationships between any two data series — the core of macro-to-equity signal discovery.

| Function | Description |
|----------|-------------|
| `correlate_series(series_a, series_b, lags)` | Cross-correlate two time series with multiple lag periods |
| `find_leading_indicators(target, candidates, lags)` | Find which series leads the target with highest correlation |
| `calculate_correlation_numpy(a, b)` | Fast numpy-based correlation |

**CLI:**
```bash
python cli.py cross-correlate SPY VIX --lags 30
python cli.py leading-indicators AAPL --candidates CPI,PMI,YIELD_10Y
```

**REST API:**
```
GET /api/v1/cross-correlate?series1=SPY&series2=VIX&lags=30
```

**MCP Tool:** `cross_correlate`

**Update Frequency:** On-demand

---

### 4. Correlation Anomaly Detector
**Module:** `correlation_anomaly` | **Category:** quant

Detects when correlations between assets break from historical norms — a powerful regime change and arbitrage signal.

| Function | Description |
|----------|-------------|
| `CorrelationAnomalyDetector` | Class that monitors correlation breakdowns in real-time |
| `zscore(current_corr, historical_mean, historical_std)` | Compute z-score of current correlation vs history |

**CLI:**
```bash
python cli.py corr-breakdown --ticker1 AAPL --ticker2 MSFT
python cli.py corr-scan --tickers SPY,TLT,GLD,QQQ
python cli.py corr-arbitrage --tickers XLF,XLK,XLE
```

**REST API:**
```
GET /api/v1/correlation-anomaly?tickers=SPY,TLT,GLD,QQQ
```

**MCP Tool:** `correlation_anomaly`

**Update Frequency:** Daily (recommended) or real-time

---

### 5. Regime Correlation
**Module:** `regime_correlation` | **Category:** quant

Detects market regime shifts (risk-on/risk-off/crisis) by analyzing correlation patterns across asset classes.

| Function | Description |
|----------|-------------|
| `detect_regime(data)` | Classify current market regime from cross-asset correlations |
| `get_correlation_matrix(tickers, period)` | Build rolling correlation matrix |
| `get_asset_data(ticker, period)` | Fetch asset data for regime analysis |

**CLI:**
```bash
python cli.py market-regime
python cli.py regime-history
python cli.py risk-dashboard
python cli.py correlation-regime
python cli.py corr-regime --tickers SPY,TLT,GLD,DBC
```

**REST API:**
```
GET /api/v1/market-regime?action=current
GET /api/v1/market-regime?action=correlation
GET /api/v1/market-regime?action=dashboard
GET /api/v1/market-regime?action=history
```

**MCP Tool:** `regime_correlation`

**Update Frequency:** Daily

---

### 6. Cointegration Pair Finder
**Module:** `cointegration_pair_finder` | **Category:** quant

Finds statistically cointegrated pairs for pairs trading / stat arb strategies using Engle-Granger tests.

| Function | Description |
|----------|-------------|
| `scan_universe(tickers)` | Scan a universe of stocks for cointegrated pairs |
| `engle_granger_test(series_a, series_b)` | Run Engle-Granger cointegration test on two series |
| `get_pair_spread_signals(ticker1, ticker2)` | Generate buy/sell signals from pair spread z-scores |

**CLI:**
```bash
python cli.py pairs-scan Technology --limit 20
python cli.py cointegration KO PEP --lookback 252
python cli.py spread-monitor KO PEP --period 1y
```

**REST API:**
```
GET /api/v1/cointegration-pair-finder?action=scan_universe&tickers=AAPL,MSFT,GOOGL,META
GET /api/v1/cointegration-pair-finder?action=get_pair_spread_signals&ticker1=KO&ticker2=PEP
```

**MCP Tool:** `cointegration_pair_finder`

**Update Frequency:** Weekly (relationships are slow-moving)

---

### 7. ML Factor Discovery
**Module:** `ml_factor_discovery` | **Category:** ml_ai

Uses machine learning (random forests, gradient boosting) to discover which factors actually predict returns in the current regime.

| Function | Description |
|----------|-------------|
| `cmd_discover_factors(tickers)` | Discover predictive factors for a stock universe |
| `cmd_factor_ic(top_n)` | Compute information coefficient of discovered factors |
| `cmd_factor_backtest(factor_name)` | Backtest a specific factor's predictive power |
| `cmd_feature_importance(horizon)` | Rank features by importance for return prediction |

**CLI:**
```bash
python cli.py discover-factors AAPL,MSFT,GOOGL,AMZN,META
python cli.py factor-ic --top-n 30
python cli.py factor-backtest momentum_3m
python cli.py feature-importance --horizon 5d
```

**REST API:**
```
GET /api/v1/ml-factor-discovery?action=discover&tickers=AAPL,MSFT,GOOGL
```

**MCP Tool:** `ml_factor_discovery`

**Update Frequency:** Weekly

---

## 📈 Quantitative Strategy Modules (Signal Generators)

### 8. Dispersion Trade
**Module:** `dispersion_trade` | **Category:** quant

Trade the spread between index implied volatility and constituent implied volatilities.

| Function | Description |
|----------|-------------|
| `calculate_implied_correlation(index_iv, constituent_ivs)` | Compute implied correlation from vol surface |
| `scan_dispersion_opportunities()` | Find profitable dispersion trade setups |
| `dispersion_trade_pnl(positions)` | Calculate P&L of dispersion positions |

**Update Frequency:** Daily (options data changes daily)

---

### 9. Cross-Sectional Momentum
**Module:** `cross_sectional_momentum` | **Category:** quant

Jegadeesh-Titman momentum factor — rank stocks by trailing returns, go long winners, short losers.

| Function | Description |
|----------|-------------|
| `compute_momentum_scores(universe, lookback)` | Rank universe by momentum |
| `construct_long_short_portfolio(scores, top_n, bottom_n)` | Build L/S portfolio from rankings |
| `momentum_backtest(universe, lookback, holding_period)` | Full momentum strategy backtest |

**Update Frequency:** Monthly (rebalance signal)

---

### 10. Time-Series Momentum (TSMOM)
**Module:** `time_series_momentum` | **Category:** quant

Moskowitz-Ooi-Pedersen absolute momentum — go long assets with positive trailing returns, short negative.

| Function | Description |
|----------|-------------|
| `tsmom_signal(ticker, lookback)` | Generate TSMOM signal (+1/-1) for single asset |
| `tsmom_portfolio(tickers, lookback)` | Multi-asset vol-scaled TSMOM portfolio |
| `tsmom_backtest(tickers, lookback, holding)` | Full TSMOM backtest with Sharpe/drawdown |

**Update Frequency:** Monthly

---

### 11. Betting Against Beta (BAB)
**Module:** `betting_against_beta` | **Category:** quant

Frazzini-Pedersen factor — leveraged low-beta stocks outperform high-beta stocks.

| Function | Description |
|----------|-------------|
| `estimate_beta(ticker, market, window)` | Vasicek-shrinkage beta estimate |
| `construct_bab_portfolio(universe)` | Build BAB long-short portfolio |
| `bab_factor_return(portfolio)` | Compute BAB factor return |

**Update Frequency:** Monthly

---

### 12. Quality Minus Junk (QMJ)
**Module:** `quality_minus_junk` | **Category:** quant

Asness quality factor — long high-quality (profitable, safe, growing), short low-quality.

| Function | Description |
|----------|-------------|
| `composite_quality_score(ticker)` | Combined profitability + safety + growth score |
| `compute_profitability_score(ticker)` | Gross margin, ROE, ROA, cash flow |
| `compute_safety_score(ticker)` | Low leverage, low volatility, low beta |
| `rank_universe_by_quality(universe)` | Rank stocks by composite quality |
| `construct_qmj_portfolio(rankings)` | Build QMJ long-short portfolio |

**Update Frequency:** Quarterly (driven by earnings)

---

### 13. Mean Reversion Scanner
**Module:** `mean_reversion_scanner` | **Category:** quant

Finds oversold/overbought stocks using z-scores and Bollinger Bands across multiple timeframes.

| Function | Description |
|----------|-------------|
| `scan_universe(tickers)` | Scan for mean reversion opportunities |
| `compute_z_score(ticker, lookback)` | Current z-score vs historical mean |
| `multi_timeframe_zscore(ticker)` | Z-scores across daily, weekly, monthly |
| `bollinger_band_analysis(ticker)` | Bollinger Band squeeze/expansion signals |

**Update Frequency:** Daily

---

### 14. Statistical Arbitrage Engine
**Module:** `stat_arb_engine` | **Category:** quant

Full stat arb framework — spread modeling, z-score signals, entry/exit rules.

| Function | Description |
|----------|-------------|
| `compute_spread_zscore(pair)` | Z-score of current pair spread |
| `engle_granger_test(series_a, series_b)` | Cointegration test for pair validity |
| `generate_signals(pair, z_entry, z_exit)` | Generate entry/exit signals from spread |

**Update Frequency:** Daily

---

### 15. Factor Timing
**Module:** `factor_timing` | **Category:** quant

Time factor exposures based on macro regime — overweight momentum in bull markets, quality in bear markets.

| Function | Description |
|----------|-------------|
| `cmd_factor_timing()` | Current factor timing recommendations |
| `cmd_factor_rotation()` | Factor rotation signals based on regime |
| `cmd_factor_performance(period)` | Factor performance over given period |
| `cmd_factor_regime_history(days)` | Historical regime-factor mapping |

**CLI:**
```bash
python cli.py factor-timing
python cli.py factor-rotation
python cli.py factor-performance 6m
python cli.py factor-regime-history --days 90
```

**Update Frequency:** Monthly

---

## 🔗 Correlation Data Sources (Zvec-Indexed)

The Zvec database indexes all 208 modules and automatically discovers cross-module correlations. Here are the highest-value correlation clusters:

### Top Shared Data Sources for Signal Building

| Data Source | Modules Connected | Signal Opportunity |
|-------------|-------------------|-------------------|
| **FRED (api.stlouisfed.org)** | 38 modules | Macro → equity signals. Fed funds rate, yield curve, credit spreads → stock returns |
| **SEC (www.sec.gov)** | 27 modules | Insider + institutional + filing signals → price prediction |
| **Yahoo Finance** | 15 modules | Cross-asset price correlations, multi-timeframe analysis |
| **FRED alt (fred.stlouisfed.org)** | 11 modules | Bond-equity rotation, macro leading indicators |
| **CoinGecko** | 7 modules | Crypto-equity correlation, DeFi TVL vs crypto prices |
| **ECB** | 3 modules | EUR rates → European equity signals |
| **EIA Energy** | 5 modules | Oil supply/demand → energy sector, inflation signals |
| **World Bank** | 6 modules | EM macro → emerging market equity signals |

### Highest-Value Cross-Category Correlations

| Correlation Pair | Why It Matters |
|-----------------|----------------|
| **Macro ↔ Equity** (5 shared sources) | PMI → sector rotation, yield curve → bank stocks, CPI → TIPS vs nominal |
| **Equity ↔ Commodities** (5 shared sources) | Oil → airlines/transport, copper → industrials, gold → miners |
| **Macro ↔ Commodities** (3 shared sources) | Dollar strength → commodity weakness, rates → gold, GDP → base metals |
| **Equity ↔ Crypto** (2 shared sources) | Risk-on/off correlation, BTC as tech proxy, DeFi TVL → crypto |
| **Fixed Income ↔ Macro** (2 shared sources) | Yield curve shape → recession probability, credit spreads → equity vol |
| **Macro ↔ Alt Data** (2 shared sources) | Shipping volumes → GDP, satellite imagery → retail sales |

---

## 📊 Complete Data Module Catalog

### Update Frequency Guide

| Frequency | When to Refresh | Signal Type |
|-----------|----------------|-------------|
| **Real-time** | Every 1-60 seconds | Price, order flow, liquidations |
| **Intraday** | Every 1-4 hours | Sentiment, news, social media |
| **Daily** | End of day | Technical signals, spreads, z-scores |
| **Weekly** | End of week | Macro indicators, fund flows, COT |
| **Monthly** | End of month | Factor rebalance, PMI, employment |
| **Quarterly** | After earnings | Fundamentals, quality scores |
| **Annual** | Yearly | Demographics, structural indicators |

### Full Module Table

| # | Module | Category | Functions | Update Freq | Signal Use Case |
|---|--------|----------|-----------|-------------|-----------------|
| 1 | `abs` | macro | 21 | Monthly | Australian macro → AUD pairs, ASX |
| 2 | `academic_papers` | other | 5 | Weekly | Research alpha — new factor papers |
| 3 | `activist_success_predictor` | equity | 8 | Daily | Activist 13D filings → target stock rally |
| 4 | `adr_gdr_arbitrage` | equity | 6 | Daily | ADR-ordinary spread → arb signals |
| 5 | `agricultural_commodities` | commodities | 8 | Daily | Crop futures → food stocks, inflation |
| 6 | `ai_earnings_analyzer` | equity | 7 | Quarterly | NLP earnings analysis → post-earnings drift |
| 7 | `airport_traffic_aviation` | alt_data | 9 | Monthly | Air traffic → airlines, tourism, GDP proxy |
| 8 | `alert_backtest` | other | 5 | On-demand | Backtest alert strategies historically |
| 9 | `alert_dashboard` | other | 6 | Real-time | Monitor active alerts across all signals |
| 10 | `alert_dsl` | other | 5 | On-demand | Define custom alert rules with DSL |
| 11 | `analyst_target_price` | equity | 6 | Daily | Consensus target → mean reversion signal |
| 12 | `anomaly_scanner` | equity | 6 | Daily | Price/volume anomalies → breakout detection |
| 13 | `argentina_indec` | macro | 11 | Monthly | Argentina macro → EM signals, ARS |
| 14 | `auto_sales_ev` | alt_data | 7 | Monthly | Auto sales + EV adoption → TSLA, F, GM |
| 15 | `backtesting_framework` | other | 8 | On-demand | Backtest any strategy with PIT data |
| 16 | `bankruptcy_tracker` | equity | 7 | Daily | Bankruptcy risk scoring → short signals |
| 17 | `bcb` | macro | 8 | Monthly | Brazil central bank → BRL, Bovespa |
| 18 | `betting_against_beta` | quant | 3 | Monthly | BAB factor long-short portfolio |
| 19 | `bis_banking` | macro | 10 | Quarterly | Global banking flows → systemic risk |
| 20 | `black_litterman` | quant | 5 | Monthly | Optimal portfolio with views overlay |
| 21 | `bls` | macro | 7 | Monthly | US employment + CPI → Fed signals |
| 22 | `boj` | macro | 7 | Monthly | Japan macro → JPY, Nikkei |
| 23 | `bond_new_issue` | fixed_income | 6 | Daily | New issue calendar → spread compression |
| 24 | `carbon_credits` | commodities | 6 | Daily | Carbon price → energy transition stocks |
| 25 | `cds_spreads` | fixed_income | 8 | Daily | Credit risk premium → equity vol prediction |
| 26 | `census` | macro | 6 | Monthly | US demographics → housing, retail |
| 27 | `central_bank_balance` | macro | 6 | Weekly | QE/QT tracking → liquidity signal |
| 28 | `central_bank_rates` | macro | 7 | Monthly | Global rates → FX carry, bond rotation |
| 29 | `cftc_cot` | derivatives | 7 | Weekly | Commitment of Traders → positioning signal |
| 30 | `china_nbs` | macro | 8 | Monthly | China PMI, GDP → commodities, EM |
| 31 | `cia_factbook` | macro | 7 | Annual | Country fundamentals → EM allocation |
| 32 | `climate_risk` | equity | 6 | Quarterly | Physical + transition risk → ESG alpha |
| 33 | `clo_abs` | fixed_income | 7 | Monthly | Structured credit → systemic risk |
| 34 | `cointegration_pair_finder` | quant | 3 | Weekly | Stat arb pair identification |
| 35 | `commercial_paper` | fixed_income | 5 | Daily | CP rates → money market stress |
| 36 | `commodity_futures` | commodities | 7 | Daily | Futures curves → contango/backwardation |
| 37 | `comparable_companies` | equity | 6 | Quarterly | Relative valuation → mispricing |
| 38 | `comtrade` | macro | 7 | Monthly | Global trade flows → EM, commodities |
| 39 | `container_port_throughput` | alt_data | 7 | Monthly | Port volumes → global trade proxy |
| 40 | `convertible_bonds` | fixed_income | 8 | Daily | Convertible arb signals |
| 41 | `corporate_actions` | equity | 6 | Daily | Splits, spinoffs → event-driven alpha |
| 42 | `corporate_bond_spreads` | fixed_income | 7 | Daily | IG/HY spreads → equity risk signal |
| 43 | `correlation_anomaly` | quant | 2 | Daily | Correlation breakdown → regime change |
| 44 | `cross_chain_bridge_monitor` | crypto | 5 | Real-time | Bridge flows → cross-chain alpha |
| 45 | `cross_correlate` | quant | 6 | On-demand | Find leading indicators for any series |
| 46 | `cross_exchange_arb` | crypto | 5 | Real-time | CEX price discrepancies → arb |
| 47 | `cross_sectional_momentum` | quant | 3 | Monthly | Jegadeesh-Titman long-short momentum |
| 48 | `crude_oil_fundamentals` | commodities | 7 | Weekly | Supply/demand → oil price direction |
| 49 | `crypto_correlation` | crypto | 6 | Daily | BTC dominance, altcoin season signals |
| 50 | `crypto_derivatives` | derivatives | 7 | Real-time | Funding rates, OI → crypto direction |
| 51 | `crypto_exchange_flow` | crypto | 6 | Daily | Exchange inflows → sell pressure |
| 52 | `crypto_liquidation_monitor` | derivatives | 5 | Real-time | Liquidation cascades → reversal signal |
| 53 | `crypto_onchain` | crypto | 7 | Daily | On-chain metrics → BTC/ETH signals |
| 54 | `currency_intervention_detector` | macro | 5 | Daily | Central bank FX intervention signals |
| 55 | `dark_pool` | equity | 7 | Daily | Dark pool prints → institutional intent |
| 56 | `data_reconciliation` | other | 6 | Daily | Multi-source data quality scoring |
| 57 | `dcf_valuation` | equity | 7 | Quarterly | Intrinsic value → mispricing signal |
| 58 | `deep_learning_sentiment` | ml_ai | 8 | Intraday | NLP sentiment → short-term momentum |
| 59 | `defi_tvl_yield` | crypto | 7 | Daily | DeFi TVL trends → crypto rotation |
| 60 | `dispersion_trade` | quant | 3 | Daily | Index vs constituent vol → dispersion arb |
| 61 | `dividend_history` | equity | 6 | Quarterly | Dividend growth → income stock selection |
| 62 | `dividend_sustainability` | equity | 7 | Quarterly | Payout safety → avoid dividend cuts |
| 63 | `earnings_forensics` | equity | 7 | Quarterly | Accounting red flags → short signals |
| 64 | `earnings_nlp` | equity | 7 | Quarterly | Earnings call tone → post-earnings drift |
| 65 | `earnings_quality` | equity | 6 | Quarterly | Accruals, cash conversion → quality factor |
| 66 | `earnings_surprise_history` | equity | 6 | Quarterly | Surprise patterns → PEAD trading |
| 67 | `ecb` | macro | 7 | Monthly | ECB policy → EUR, European equities |
| 68 | `eia_energy` | commodities | 7 | Weekly | US energy inventory → oil/gas prices |
| 69 | `em_currency_crisis` | macro | 6 | Daily | EM crisis indicators → risk-off signal |
| 70 | `em_sovereign_spreads` | fixed_income | 6 | Daily | EM spreads → emerging market equities |
| 71 | `equity_screener` | equity | 7 | Daily | Multi-factor stock screening |
| 72 | `estimate_revision_tracker` | equity | 6 | Daily | Earnings revisions → momentum signal |
| 73 | `etf_flow_tracker` | equity | 7 | Daily | ETF flows → sector rotation signal |
| 74 | `eurostat` | macro | 8 | Monthly | European macro → EUR, Euro Stoxx |
| 75 | `exec_compensation` | equity | 6 | Annual | CEO pay alignment → governance alpha |
| 76 | `executive_comp` | equity | 6 | Annual | Executive compensation analysis |
| 77 | `factor_timing` | quant | 4 | Monthly | Factor rotation based on regime |
| 78 | `fed_policy` | macro | 7 | Weekly | Fed balance sheet, rates → all assets |
| 79 | `filing_alerts` | equity | 6 | Daily | SEC filing alerts → event trading |
| 80 | `fred_enhanced` | macro | 8 | Daily | 800K+ economic series from FRED |
| 81 | `fx_carry_trade` | derivatives | 7 | Daily | Interest rate differentials → FX carry |
| 82 | `fx_volatility_surface` | derivatives | 6 | Daily | FX vol surface → options signals |
| 83 | `garch_volatility` | derivatives | 5 | Daily | GARCH vol forecast → options pricing |
| 84 | `global_bonds` | fixed_income | 7 | Daily | Global bond yields → rate differentials |
| 85 | `global_debt` | macro | 7 | Quarterly | Sovereign debt levels → crisis risk |
| 86 | `global_electricity_demand` | commodities | 6 | Monthly | Power demand → industrial activity proxy |
| 87 | `global_equity_index_returns` | equity | 6 | Daily | Global index returns → correlation regime |
| 88 | `global_fx_rates` | macro | 7 | Daily | Major + EM FX rates → carry, momentum |
| 89 | `global_inflation` | macro | 7 | Monthly | Inflation → bonds, TIPS, gold, rates |
| 90 | `global_pmi` | macro | 8 | Monthly | 30+ country PMIs → growth signal |
| 91 | `global_real_estate` | macro | 7 | Quarterly | Property prices → REITs, construction |
| 92 | `global_shipping` | macro | 7 | Daily | Baltic Dry → global trade proxy |
| 93 | `global_stock_exchange_holidays` | other | 5 | Annual | Exchange calendar → holiday effect |
| 94 | `global_tourism_statistics` | macro | 7 | Monthly | Tourism → airlines, hotels, EM |
| 95 | `gold_precious_metals` | commodities | 7 | Daily | Gold, silver → safe haven, inflation |
| 96 | `greenwashing_detection` | equity | 5 | Quarterly | ESG greenwashing risk scoring |
| 97 | `health_impact` | macro | 6 | Monthly | Health crises → pharma, risk-off |
| 98 | `heston_stochastic` | derivatives | 4 | Daily | Stochastic vol model → options pricing |
| 99 | `hidden_markov_regime` | ml_ai | 4 | Daily | HMM regime detection → allocation |
| 100 | `high_yield_bonds` | fixed_income | 6 | Daily | HY spreads → equity risk appetite |
| 101 | `ilo_labor` | macro | 6 | Quarterly | Global labor market → EM signals |
| 102 | `imf_weo` | macro | 7 | Semi-annual | IMF forecasts → macro positioning |
| 103 | `index_reconstitution_tracker` | equity | 5 | Monthly | Index adds/drops → event alpha |
| 104 | `industrial_metals` | commodities | 7 | Daily | Copper, aluminum → industrial cycle |
| 105 | `inegi` | macro | 7 | Monthly | Mexico macro → MXN, Bolsa |
| 106 | `inflation_linked_bonds` | fixed_income | 6 | Daily | TIPS breakeven → inflation expectations |
| 107 | `insider_network` | equity | 6 | Daily | Insider trade clusters → conviction signal |
| 108 | `insider_transaction_heatmap` | equity | 6 | Daily | Insider buy/sell heatmap → directional |
| 109 | `institutional_ownership` | equity | 6 | Quarterly | 13F filings → smart money tracking |
| 110 | `israel_cbs` | macro | 7 | Monthly | Israel macro → ILS, TASE |
| 111 | `jump_diffusion` | derivatives | 4 | Daily | Jump risk modeling → tail risk |
| 112 | `kalman_filter` | quant | 5 | Daily | Adaptive trend + regime detection |
| 113 | `kelly_criterion_sizer` | quant | 4 | On-demand | Optimal position sizing |
| 114 | `kosis` | macro | 7 | Monthly | South Korea macro → KRW, KOSPI |
| 115 | `live_earnings` | real_time | 7 | Real-time | Live earnings call transcription + signals |
| 116 | `live_forex_cross_rates` | real_time | 5 | Real-time | Live FX cross rates matrix |
| 117 | `live_transcription` | real_time | 5 | Real-time | Audio → text → signal extraction |
| 118 | `livestock_meat` | commodities | 6 | Daily | Livestock futures → food inflation |
| 119 | `lng_gas` | commodities | 7 | Daily | Natural gas + LNG → energy signals |
| 120 | `macro_leading_index` | macro | 6 | Monthly | Composite leading indicator → recession |
| 121 | `market_regime` | equity | 6 | Daily | Risk-on/off classification |
| 122 | `mean_reversion_scanner` | quant | 5 | Daily | Z-score extremes → reversion trades |
| 123 | `minimum_variance_portfolio` | quant | 4 | Monthly | Min-vol portfolio construction |
| 124 | `ml_factor_discovery` | ml_ai | 4 | Weekly | ML-driven factor discovery |
| 125 | `ml_stock_screening` | ml_ai | 5 | Weekly | ML-ranked stock screen |
| 126 | `mmf_flows` | equity | 7 | Weekly | Money market flows → risk appetite |
| 127 | `momentum_factor_backtest` | quant | 3 | Monthly | XS + TS momentum backtest |
| 128 | `monte_carlo` | other | 6 | On-demand | Monte Carlo simulation + VaR/CVaR |
| 129 | `multi_source` | other | 5 | Daily | Multi-source data reconciliation |
| 130 | `multi_timeframe` | other | 5 | Daily | MTF signal confluence |
| 131 | `muni_bonds` | fixed_income | 6 | Daily | Muni spreads → tax-adjusted yields |
| 132 | `mutual_fund_flow_analysis` | equity | 6 | Monthly | Mutual fund flows → sector rotation |
| 133 | `natural_gas_supply_demand` | commodities | 7 | Weekly | Gas S/D balance → price direction |
| 134 | `neural_prediction` | ml_ai | 5 | Daily | Neural net price predictions |
| 135 | `nft_market` | crypto | 6 | Daily | NFT market metrics → crypto sentiment |
| 136 | `nigeria_nbs` | macro | 6 | Monthly | Nigeria macro → NGN, frontier markets |
| 137 | `oecd` | macro | 7 | Monthly | OECD indicators → developed markets |
| 138 | `opec` | commodities | 7 | Monthly | OPEC production → oil price |
| 139 | `optimal_f_calculator` | quant | 4 | On-demand | Optimal fraction position sizing |
| 140 | `options_flow_scanner` | derivatives | 7 | Real-time | Unusual options activity → directional |
| 141 | `order_book` | real_time | 6 | Real-time | L2 order book analysis |
| 142 | `orderbook_imbalance` | derivatives | 5 | Real-time | Bid/ask imbalance → short-term direction |
| 143 | `pairs_trading` | quant | 3 | Daily | Pairs trading signals |
| 144 | `patent_tracking` | equity | 6 | Monthly | Patent filings → innovation alpha |
| 145 | `pdf_exporter` | other | 4 | On-demand | Export reports to PDF |
| 146 | `pe_vc_deals` | equity | 7 | Monthly | PE/VC deal flow → sector sentiment |
| 147 | `peer_earnings` | equity | 6 | Quarterly | Peer group earnings comparison |
| 148 | `peer_network` | equity | 5 | Quarterly | Supply chain + peer network mapping |
| 149 | `poland_gus` | macro | 6 | Monthly | Poland macro → PLN, WSE |
| 150 | `political_risk` | macro | 6 | Monthly | Geopolitical risk → safe havens |
| 151 | `portfolio_construction` | quant | 7 | Monthly | Multi-factor portfolio construction |
| 152 | `product_launches` | equity | 6 | Weekly | Product launches → company momentum |
| 153 | `proxy_fights` | equity | 5 | Monthly | Proxy contests → activist alpha |
| 154 | `quality_minus_junk` | quant | 5 | Quarterly | QMJ factor long-short |
| 155 | `rare_earths` | commodities | 6 | Monthly | Rare earth prices → tech supply chain |
| 156 | `rbi` | macro | 6 | Monthly | India macro → INR, Nifty |
| 157 | `realtime_sector_heatmap` | real_time | 5 | Real-time | Live sector performance heatmap |
| 158 | `regime_correlation` | quant | 3 | Daily | Regime-conditional correlations |
| 159 | `regulatory_calendar` | macro | 6 | Weekly | Regulatory events → sector impact |
| 160 | `relative_valuation` | equity | 6 | Quarterly | Cross-sector valuation comparison |
| 161 | `repo_rate_monitor` | fixed_income | 5 | Daily | Repo rates → funding stress signal |
| 162 | `revenue_quality` | equity | 6 | Quarterly | Revenue sustainability scoring |
| 163 | `risk_parity_portfolio` | quant | 5 | Monthly | Risk parity allocation signals |
| 164 | `satellite_proxies` | alt_data | 6 | Monthly | Satellite data → retail/oil storage proxy |
| 165 | `saudi_arabia_gastat` | macro | 6 | Monthly | Saudi macro → SAR, Tadawul |
| 166 | `sec_xbrl_financial_statements` | equity | 7 | Quarterly | Structured financials from XBRL |
| 167 | `secondary_offering_monitor` | equity | 5 | Daily | Secondary offerings → dilution signal |
| 168 | `sector_performance_attribution` | equity | 6 | Daily | Sector attribution → rotation signals |
| 169 | `sector_rotation` | equity | 7 | Monthly | Economic cycle → sector allocation |
| 170 | `semiconductor_chip` | equity | 7 | Monthly | Chip cycle → semis, tech supply chain |
| 171 | `share_buyback` | equity | 6 | Quarterly | Buyback activity → shareholder return |
| 172 | `share_float_and_ownership_structure` | equity | 6 | Quarterly | Float changes → supply/demand signal |
| 173 | `short_squeeze` | equity | 7 | Daily | Short interest + borrow cost → squeeze |
| 174 | `signal_discovery_engine` | quant | 3 | On-demand | Automated signal discovery |
| 175 | `signal_fusion` | quant | 5 | Real-time | Multi-source signal combination |
| 176 | `singapore_dos` | macro | 6 | Monthly | Singapore macro → SGD, STI |
| 177 | `slb` | equity | 6 | Monthly | Stock lending → short demand signal |
| 178 | `smart_alerts` | other | 5 | Real-time | Configurable alert system |
| 179 | `smart_money_tracker` | equity | 7 | Daily | Institutional flow tracking |
| 180 | `smart_prefetch` | other | 4 | On-demand | Predictive data caching |
| 181 | `social_sentiment_spikes` | equity | 6 | Intraday | Reddit/social sentiment spikes |
| 182 | `south_africa_reserve_bank` | macro | 7 | Monthly | South Africa macro → ZAR, JSE |
| 183 | `sovereign_rating_tracker` | macro | 7 | Daily | Rating changes → EM bond impact |
| 184 | `spac_lifecycle` | equity | 7 | Daily | SPAC arb → trust value vs price |
| 185 | `stablecoin_supply` | crypto | 5 | Daily | Stablecoin minting → crypto inflow |
| 186 | `stat_arb_engine` | quant | 3 | Daily | Statistical arbitrage signals |
| 187 | `stock_loan_borrow_costs` | equity | 6 | Daily | Borrow cost → hard-to-borrow signal |
| 188 | `stock_split_corporate_events` | equity | 6 | Daily | Corporate events calendar |
| 189 | `sustainability_bonds` | fixed_income | 6 | Monthly | Green/social bond issuance trends |
| 190 | `swap_rate_curves` | fixed_income | 6 | Daily | Swap curves → rate expectations |
| 191 | `swf_tracker` | equity | 7 | Quarterly | Sovereign wealth fund holdings |
| 192 | `switzerland_snb` | macro | 6 | Monthly | Swiss macro → CHF, SMI |
| 193 | `tax_loss_harvesting` | quant | 4 | Annual | Tax-loss selling → January effect |
| 194 | `tick_trade_tape` | real_time | 5 | Real-time | Trade-by-trade tape analysis |
| 195 | `time_series_momentum` | quant | 3 | Monthly | TSMOM absolute momentum |
| 196 | `tips_breakeven` | fixed_income | 5 | Daily | Inflation breakevens → TIPS signals |
| 197 | `transaction_cost` | other | 5 | Daily | Transaction cost analysis (TCA) |
| 198 | `treasury_auctions` | macro | 6 | Weekly | Auction demand → rate direction |
| 199 | `treasury_curve` | macro | 5 | Daily | Yield curve shape → recession signal |
| 200 | `turkish_institute` | macro | 6 | Monthly | Turkey macro → TRY, BIST |
| 201 | `usda_agriculture` | macro | 7 | Monthly | Crop reports → agricultural futures |
| 202 | `variance_swap` | derivatives | 4 | Daily | Variance swap levels → vol trading |
| 203 | `vix_term_structure` | derivatives | 6 | Daily | VIX contango/backwardation → vol carry |
| 204 | `volatility_surface` | derivatives | 6 | Daily | Options vol surface → skew signals |
| 205 | `walk_forward` | other | 4 | On-demand | Walk-forward optimization framework |
| 206 | `websocket_price_streamer` | real_time | 4 | Real-time | WebSocket price streaming |
| 207 | `worldbank` | macro | 7 | Annual | World Bank development indicators |
| 208 | `wto_trade` | macro | 6 | Quarterly | WTO trade stats → globalization signals |

---

## 🧠 How to Use Zvec for Signal Discovery

The Zvec database (port 4010) indexes all modules and correlations. Use it to find signals by semantic search:

```bash
# Search for modules related to a concept
bash memclawz/search.sh "leading indicator for recession"
bash memclawz/search.sh "insider buying signal"
bash memclawz/search.sh "crude oil supply demand imbalance"
bash memclawz/search.sh "correlation breakdown detection"
```

### Example Signal Discovery Workflow

1. **Hypothesis:** "Does copper price predict equity market direction?"
2. **Search Zvec:** `bash memclawz/search.sh "copper equity correlation"`
3. **Find modules:** `industrial_metals` + `global_equity_index_returns` + `cross_correlate`
4. **Run cross-correlation:**
   ```bash
   python cli.py cross-correlate COPPER SPY --lags 30
   ```
5. **Check regime context:**
   ```bash
   python cli.py market-regime
   python cli.py correlation-regime
   ```
6. **If signal found, backtest:**
   ```bash
   python cli.py backtest SPY --strategy copper_lead --start 2020-01-01
   ```

---

## 🌐 API Access Summary

| Method | Base URL | Auth | Rate Limit |
|--------|----------|------|------------|
| **REST API** | `https://data.quantclaw.org/api/v1/` | None (public) | 100 req/min |
| **CLI** | `python cli.py <command>` | None | Unlimited |
| **MCP Server** | stdio via `python mcp_server.py` | None | Unlimited |
| **Web UI** | `https://data.quantclaw.org` | None | — |

### REST API — Signal Endpoints

```bash
# Signal Discovery
GET /api/v1/signal-discovery-engine?ticker=AAPL
GET /api/v1/signal-fusion?ticker=AAPL

# Correlations
GET /api/v1/cross-correlate?series1=SPY&series2=VIX&lags=30
GET /api/v1/correlation-anomaly?tickers=SPY,TLT,GLD,QQQ
GET /api/v1/market-regime?action=correlation

# Quant Strategies
GET /api/v1/cointegration-pair-finder?action=scan_universe&tickers=AAPL,MSFT
GET /api/v1/cross-sectional-momentum?action=momentum_backtest
GET /api/v1/time-series-momentum?action=tsmom_signal&ticker=SPY
GET /api/v1/betting-against-beta?action=construct_bab_portfolio
GET /api/v1/quality-minus-junk?action=rank_universe
GET /api/v1/dispersion-trade?action=scan_opportunities
GET /api/v1/mean-reversion-scanner?action=scan&tickers=SPY,QQQ,IWM
GET /api/v1/stat-arb-engine?action=generate_signals
GET /api/v1/factor-timing?action=rotation
GET /api/v1/ml-factor-discovery?action=discover

# Macro Signals
GET /api/v1/macro-leading-index
GET /api/v1/fed-policy
GET /api/v1/treasury-curve
GET /api/v1/global-pmi

# Smart Money
GET /api/v1/smart-money?ticker=AAPL
GET /api/v1/dark-pool?ticker=TSLA
GET /api/v1/insider-network?ticker=NVDA
GET /api/v1/etf-flow-tracker?ticker=SPY
GET /api/v1/options-flow-scanner?ticker=AAPL
```

---

*Built by QuantClaw. 208 modules. 162 data sources. Zero API keys required.*
*GitHub: github.com/yoniassia/quantclaw-data | ClawHub: clawhub install quantclaw-data*
