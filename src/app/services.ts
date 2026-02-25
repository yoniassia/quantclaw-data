export interface Service {
  id: string;
  name: string;
  phase: number;
  category: string;
  description: string;
  commands: string[];
  mcpTool: string;
  params: string;
  icon: string;
}

export const categories = [
  { id: "core", name: "Core Market Data", icon: "📊", color: "#13C636" },
  { id: "derivatives", name: "Derivatives & Options", icon: "📈", color: "#00BFFF" },
  { id: "alt-data", name: "Alternative Data", icon: "🔍", color: "#FFD700" },
  { id: "multi-asset", name: "Multi-Asset", icon: "🌍", color: "#FF6B6B" },
  { id: "quant", name: "Quantitative", icon: "🧮", color: "#C0E8FD" },
  { id: "fixed-income", name: "Fixed Income & Macro", icon: "🏦", color: "#9B59B6" },
  { id: "events", name: "Corporate Events", icon: "📰", color: "#E67E22" },
  { id: "intelligence", name: "Intelligence & NLP", icon: "🤖", color: "#1ABC9C" },
  { id: "infrastructure", name: "Infrastructure", icon: "⚙️", color: "#95A5A6" },
];

export const services: Service[] = [
  // Core Market Data
  { id: "prices", name: "Real-Time Prices", phase: 1, category: "core", description: "Live stock prices, historical OHLCV, after-hours data via Yahoo Finance", commands: ["price AAPL", "price AAPL --history 30d"], mcpTool: "get_price", params: "ticker, period?", icon: "💰" },
  { id: "company_profile", name: "Company Profile", phase: 4, category: "core", description: "Company overview, sector, employees, market cap, description", commands: ["profile AAPL"], mcpTool: "get_company_profile", params: "ticker", icon: "🏢" },
  { id: "screener", name: "Stock Screener", phase: 4, category: "core", description: "Filter stocks by market cap, P/E, sector, dividend yield, volume", commands: ["screen --min-cap 10B --sector Technology"], mcpTool: "screen_stocks", params: "filters{}", icon: "🔎" },
  { id: "technicals", name: "Technical Analysis", phase: 3, category: "core", description: "RSI, MACD, Bollinger Bands, moving averages, support/resistance", commands: ["technicals AAPL", "technicals TSLA --indicators rsi,macd"], mcpTool: "get_technicals", params: "ticker, indicators?", icon: "📉" },
  { id: "market_microstructure", name: "Market Microstructure", phase: 22, category: "core", description: "Bid-ask spreads, order flow imbalance, liquidity scoring, market maker activity", commands: ["microstructure-spreads AAPL", "microstructure-flow TSLA", "microstructure-compare AAPL MSFT GOOGL"], mcpTool: "get_microstructure", params: "ticker, analysis_type", icon: "🔬" },

  // Derivatives & Options
  { id: "options", name: "Options Chain", phase: 2, category: "derivatives", description: "Full options chain with Greeks, put/call ratio, implied volatility", commands: ["options AAPL", "options TSLA --expiry 2026-03-21"], mcpTool: "get_options", params: "ticker, expiry?", icon: "📋" },
  { id: "options_flow_scanner", name: "Options Flow Scanner", phase: 6, category: "derivatives", description: "Unusual activity alerts, dark pool prints, sweep detection", commands: ["options-flow AAPL", "options-flow --unusual"], mcpTool: "scan_options_flow", params: "ticker?, unusual_only?", icon: "🌊" },
  { id: "options_gex", name: "Options GEX Tracker", phase: 28, category: "derivatives", description: "Dealer gamma exposure positioning, pin risk at major strikes, hedging flow analysis", commands: ["gex SPY", "pin-risk AAPL", "hedging-flow TSLA"], mcpTool: "get_gex", params: "ticker, analysis_type?", icon: "⚡" },

  // Alternative Data
  { id: "news_sentiment", name: "News & Sentiment", phase: 1, category: "alt-data", description: "Aggregated news with NLP sentiment scoring from multiple sources", commands: ["news AAPL", "news TSLA --sentiment"], mcpTool: "get_news_sentiment", params: "ticker, sources?", icon: "📰" },
  { id: "social_sentiment", name: "Social Sentiment", phase: 3, category: "alt-data", description: "Reddit, StockTwits, Twitter sentiment tracking and trends", commands: ["social AAPL", "social GME --source reddit"], mcpTool: "get_social_sentiment", params: "ticker, source?", icon: "💬" },
  { id: "congress_trades", name: "Congress Trades", phase: 3, category: "alt-data", description: "Congressional trading disclosures, politician portfolios, insider timing", commands: ["congress AAPL", "congress --recent 30d"], mcpTool: "get_congress_trades", params: "ticker?, days?", icon: "🏛️" },
  { id: "short_interest", name: "Short Interest", phase: 3, category: "alt-data", description: "Short interest ratio, days to cover, short squeeze candidates", commands: ["short-interest AAPL", "short-interest --squeeze"], mcpTool: "get_short_interest", params: "ticker", icon: "📊" },
  { id: "patent_tracking", name: "Patent Tracking", phase: 11, category: "alt-data", description: "USPTO patent filings, R&D velocity scoring, innovation index", commands: ["patents AAPL", "patents --top-filers"], mcpTool: "get_patents", params: "ticker, limit?", icon: "💡" },
  { id: "job_posting_signals", name: "Job Posting Signals", phase: 12, category: "alt-data", description: "Hiring velocity as leading indicator, department growth, geo expansion", commands: ["jobs AAPL", "jobs TSLA --trend"], mcpTool: "get_job_signals", params: "ticker", icon: "👔" },
  { id: "supply_chain_mapping", name: "Supply Chain Mapping", phase: 13, category: "alt-data", description: "Supplier/customer relationships via SEC NLP, dependency graphs", commands: ["supply-chain AAPL"], mcpTool: "get_supply_chain", params: "ticker", icon: "🔗" },
  { id: "weather_agriculture", name: "Weather & Agriculture", phase: 14, category: "alt-data", description: "NOAA weather data, crop conditions, energy demand signals", commands: ["weather --region midwest", "weather --crop corn"], mcpTool: "get_weather_ag", params: "region?, crop?", icon: "🌾" },
  { id: "activist_investor_tracking", name: "Activist Investors", phase: 19, category: "alt-data", description: "13D filings, campaign tracking, activist targets", commands: ["activists AAPL", "activists --recent"], mcpTool: "get_activist_investors", params: "ticker?", icon: "🎯" },
  { id: "esg_scoring", name: "ESG Scoring", phase: 20, category: "alt-data", description: "Environmental, social, governance metrics and composite scores", commands: ["esg AAPL", "esg --compare AAPL MSFT"], mcpTool: "get_esg_score", params: "ticker", icon: "🌱" },
  { id: "hedge_fund_13f", name: "Hedge Fund 13F", phase: 29, category: "alt-data", description: "Clone top fund positions, track quarterly changes, smart money flow analysis", commands: ["13f 0001067983", "13f-changes 0001067983", "smart-money AAPL", "top-funds"], mcpTool: "get_13f_holdings", params: "fund?, ticker?, action?", icon: "🏦" },

  // Multi-Asset
  { id: "crypto", name: "Cryptocurrency", phase: 4, category: "multi-asset", description: "Real-time crypto prices, market cap, volume via CoinGecko", commands: ["crypto bitcoin", "crypto ethereum --history 7d"], mcpTool: "get_crypto", params: "coin, period?", icon: "₿" },
  { id: "commodities", name: "Commodities", phase: 4, category: "multi-asset", description: "Gold, silver, oil, natural gas, agricultural futures", commands: ["commodity gold", "commodity oil --history 30d"], mcpTool: "get_commodity", params: "commodity, period?", icon: "🛢️" },
  { id: "forex", name: "Forex", phase: 4, category: "multi-asset", description: "Currency pairs, cross rates, historical exchange rates", commands: ["forex EUR/USD", "forex GBP/JPY --history 90d"], mcpTool: "get_forex", params: "pair, period?", icon: "💱" },

  // Quantitative
  { id: "factor_model", name: "Factor Model", phase: 7, category: "quant", description: "Momentum, value, quality, size, volatility factor scoring", commands: ["factors AAPL", "factors --top momentum"], mcpTool: "get_factor_scores", params: "ticker, factors?", icon: "📐" },
  { id: "factor_zoo", name: "Factor Zoo", phase: 21, category: "quant", description: "400+ published academic factors replicated and scored", commands: ["factor-zoo AAPL", "factor-zoo --category value"], mcpTool: "get_factor_zoo", params: "ticker, category?", icon: "🦁" },
  { id: "portfolio_analytics", name: "Portfolio Analytics", phase: 8, category: "quant", description: "Sharpe, Sortino, max drawdown, correlation matrix, VaR", commands: ["portfolio-analyze portfolio.json"], mcpTool: "analyze_portfolio", params: "holdings[]", icon: "📊" },
  { id: "backtesting", name: "Backtesting", phase: 9, category: "quant", description: "Event-driven backtester with realistic fills, slippage, commission", commands: ["backtest --strategy momentum --period 1y"], mcpTool: "run_backtest", params: "strategy, period, params?", icon: "⏪" },
  { id: "fama_french", name: "Fama-French Regression", phase: 31, category: "quant", description: "Statistical factor attribution and multi-factor risk decomposition with FF 3-factor and 5-factor models", commands: ["fama-french AAPL", "factor-attribution TSLA", "factor-returns --days 30"], mcpTool: "run_fama_french", params: "ticker, model?, period?", icon: "📐" },
  { id: "pairs_trading", name: "Pairs Trading Signals", phase: 32, category: "quant", description: "Cointegration detection, mean reversion opportunities, spread monitoring", commands: ["pairs-scan beverage", "cointegration KO PEP", "spread-monitor AAPL MSFT --period 60d"], mcpTool: "pairs_trading", params: "action, symbols, params?", icon: "🔗" },
  { id: "sector_rotation", name: "Sector Rotation Model", phase: 33, category: "quant", description: "Economic cycle indicators, relative strength rotation strategies", commands: ["sector-rotation 60", "sector-momentum 90", "economic-cycle"], mcpTool: "sector_rotation", params: "action, lookback?", icon: "🔄" },
  { id: "monte_carlo", name: "Monte Carlo Simulation", phase: 34, category: "quant", description: "Scenario analysis, probabilistic forecasting, tail risk modeling with GBM and bootstrap methods", commands: ["monte-carlo AAPL --simulations 10000 --days 252", "var TSLA --confidence 0.95 0.99", "scenario NVDA --days 90"], mcpTool: "monte_carlo", params: "action, ticker, params?", icon: "🎲" },
  { id: "kalman_filter", name: "Kalman Filter Trends", phase: 35, category: "quant", description: "Smooth price trend extraction using state-space models", commands: ["kalman AAPL", "kalman TSLA --period 1y"], mcpTool: "kalman_filter", params: "ticker, period?", icon: "📡" },
  { id: "adaptive_ma", name: "Adaptive Moving Average", phase: 35, category: "quant", description: "Self-adjusting moving averages with crossover signals", commands: ["adaptive-ma AAPL", "adaptive-ma SPY --period 6mo"], mcpTool: "adaptive_ma", params: "ticker, period?", icon: "📊" },
  { id: "regime_detect", name: "Regime Detection", phase: 35, category: "quant", description: "Market regime changes via innovation variance (trending vs mean-reverting)", commands: ["regime-detect SPY", "regime-detect TSLA --window 30"], mcpTool: "regime_detect", params: "ticker, period?, window?", icon: "🔀" },
  { id: "black_litterman", name: "Black-Litterman Allocation", phase: 36, category: "quant", description: "Combine market equilibrium with investor views for portfolio construction", commands: ["black-litterman --tickers AAPL,MSFT,GOOGL --views AAPL:0.20", "equilibrium-returns --tickers SPY,QQQ,IWM", "portfolio-optimize --tickers AAPL,MSFT,GOOGL"], mcpTool: "black_litterman", params: "action, tickers, views?, params?", icon: "⚖️" },
  { id: "walk_forward", name: "Walk-Forward Optimization", phase: 37, category: "quant", description: "Out-of-sample strategy tuning with rolling windows to prevent overfitting", commands: ["walk-forward SPY --strategy sma-crossover", "overfit-check AAPL", "param-stability TSLA"], mcpTool: "walk_forward_optimize", params: "action, ticker, strategy?, params?", icon: "⏩" },
  { id: "multi_timeframe", name: "Multi-Timeframe Analysis", phase: 38, category: "quant", description: "Combine signals from daily/weekly/monthly charts for confirmation", commands: ["mtf AAPL", "trend-alignment TSLA", "signal-confluence NVDA"], mcpTool: "multi_timeframe_analysis", params: "action, ticker", icon: "📊" },
  { id: "order_book", name: "Order Book Depth", phase: 39, category: "quant", description: "Level 2 data analysis, bid-ask imbalance, hidden liquidity detection", commands: ["order-book AAPL --levels 10", "bid-ask TSLA", "liquidity SPY", "imbalance NVDA --period 5d", "support-resistance AAPL --period 6mo"], mcpTool: "order_book_analysis", params: "action, ticker, params?", icon: "📖" },

  // Fixed Income & Macro
  { id: "macro", name: "Macro Indicators", phase: 2, category: "fixed-income", description: "GDP, CPI, unemployment, interest rates, Fed funds", commands: ["macro gdp", "macro cpi --history 5y"], mcpTool: "get_macro", params: "indicator, period?", icon: "🏦" },
  { id: "bond_analytics", name: "Bond Analytics", phase: 15, category: "fixed-income", description: "Yield curves, credit spreads, duration, convexity analysis", commands: ["bonds yield-curve", "bonds spread --rating BBB"], mcpTool: "get_bond_analytics", params: "analysis_type, params?", icon: "📜" },
  { id: "cds_spreads", name: "CDS Spreads", phase: 30, category: "fixed-income", description: "Sovereign and corporate credit risk signals from credit default swap markets", commands: ["cds AAPL", "cds --credit-spreads", "cds --sovereign Italy"], mcpTool: "get_cds_spreads", params: "entity?, action?", icon: "💳" },

  // Corporate Events
  { id: "sec_edgar", name: "SEC Filings", phase: 1, category: "events", description: "10-K, 10-Q, 8-K filings from SEC EDGAR with full text", commands: ["sec AAPL", "sec TSLA --type 10-K"], mcpTool: "get_sec_filings", params: "ticker, form_type?", icon: "📑" },
  { id: "sec_nlp", name: "SEC NLP Analysis", phase: 16, category: "events", description: "Risk factor extraction, MD&A sentiment, change detection", commands: ["sec-nlp AAPL --section risk", "sec-nlp TSLA --diff"], mcpTool: "analyze_sec_filing", params: "ticker, section?, diff?", icon: "🔬" },
  { id: "earnings", name: "Earnings Calendar", phase: 2, category: "events", description: "Upcoming earnings dates, EPS estimates, beat/miss history", commands: ["earnings AAPL", "earnings --upcoming 7d"], mcpTool: "get_earnings", params: "ticker?, period?", icon: "📅" },
  { id: "earnings_transcripts", name: "Earnings Transcripts", phase: 5, category: "events", description: "Full call transcripts with NLP — key quotes, guidance, sentiment", commands: ["transcript AAPL --quarter Q1-2026"], mcpTool: "get_earnings_transcript", params: "ticker, quarter?", icon: "🎤" },
  { id: "dividends", name: "Dividends", phase: 2, category: "events", description: "Dividend history, yield, payout ratio, ex-dates, growth rate", commands: ["dividends AAPL", "dividends --aristocrats"], mcpTool: "get_dividends", params: "ticker", icon: "💎" },
  { id: "analyst_ratings", name: "Analyst Ratings", phase: 4, category: "events", description: "Consensus ratings, price targets, upgrades/downgrades", commands: ["ratings AAPL", "ratings TSLA --history"], mcpTool: "get_analyst_ratings", params: "ticker", icon: "⭐" },
  { id: "ipo_spac_tracker", name: "IPO & SPAC Tracker", phase: 17, category: "events", description: "Upcoming IPOs, SPAC arbitrage, lock-up expiry dates", commands: ["ipos --upcoming", "spacs --arbitrage"], mcpTool: "get_ipo_spac", params: "type, filter?", icon: "🚀" },
  { id: "ma_deal_flow", name: "M&A Deal Flow", phase: 18, category: "events", description: "Announced deals, merger arb spreads, completion probability", commands: ["ma --active", "ma ATVI --spread"], mcpTool: "get_ma_deals", params: "ticker?, active_only?", icon: "🤝" },
  { id: "etf_holdings", name: "ETF Holdings", phase: 2, category: "events", description: "ETF constituents, sector weights, overlap analysis", commands: ["etf SPY", "etf QQQ --overlap SPY"], mcpTool: "get_etf_holdings", params: "ticker, compare?", icon: "🗂️" },

  // Intelligence
  { id: "research_reports", name: "Research Reports", phase: 23, category: "intelligence", description: "AI-generated equity research with LLM synthesis across all data sources", commands: ["research-report AAPL --output report.md"], mcpTool: "generate_research_report", params: "ticker, format?", icon: "📝" },
  { id: "alerts", name: "Smart Alerts", phase: 10, category: "infrastructure", description: "Price alerts, volume spikes, RSI thresholds, earnings triggers", commands: ["alert set AAPL --price-above 250", "alert list"], mcpTool: "manage_alerts", params: "action, ticker?, conditions?", icon: "🔔" },
  { id: "smart_alert_delivery", name: "Smart Alert Delivery", phase: 40, category: "infrastructure", description: "Multi-channel notifications (email, SMS, Discord, Telegram) with rate limiting, cooldown periods, and delivery tracking", commands: ["alert-create AAPL --condition 'price>200'", "alert-check --symbols AAPL,TSLA", "alert-history --symbol AAPL"], mcpTool: "manage_smart_alerts", params: "action, params?", icon: "📬" },
  { id: "alert_dsl", name: "Custom Alert DSL", phase: 42, category: "infrastructure", description: "Domain-specific language for complex multi-condition alert rules", commands: ["dsl-eval AAPL \"price > 200 AND rsi < 30\"", "dsl-scan \"rsi < 25\" --universe SP500", "dsl-help"], mcpTool: "evaluate_alert_dsl", params: "expression, ticker?, universe?", icon: "🔧" },
  { id: "alert_backtest", name: "Alert Backtesting", phase: 41, category: "infrastructure", description: "Test alert strategies historically, measure signal quality, false positive rates", commands: ["alert-backtest AAPL --condition 'rsi<30'"], mcpTool: "backtest_alert", params: "ticker, condition, period?", icon: "🎯" },
  { id: "signal_quality", name: "Signal Quality Analysis", phase: 41, category: "infrastructure", description: "Rank alert conditions by quality score, hit rate, profit factor", commands: ["signal-quality AAPL --period 1y"], mcpTool: "analyze_signal_quality", params: "ticker, period?", icon: "🏆" },
  { id: "alert_potential", name: "Alert Potential", phase: 41, category: "infrastructure", description: "Measure alert trigger frequency and volatility metrics", commands: ["alert-potential AAPL --period 1y"], mcpTool: "get_alert_potential", params: "ticker, period?", icon: "📊" },
];
