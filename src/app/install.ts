export const installSteps = [
  {
    step: 1,
    title: "Clone the Repository",
    code: `git clone https://github.com/yoniassia/quantclaw-data.git
cd quantclaw-data`,
  },
  {
    step: 2,
    title: "Install Python Dependencies",
    code: `pip install yfinance numpy scipy pandas statsmodels pandas-datareader requests beautifulsoup4`,
  },
  {
    step: 3,
    title: "Verify Installation",
    code: `python cli.py price AAPL
# Should return real-time Apple stock price`,
  },
];

export const mcpConfig = {
  title: "MCP Server Configuration",
  description: "Add to your Claude Desktop or MCP client config:",
  config: `{
  "mcpServers": {
    "quantclaw-data": {
      "command": "node",
      "args": ["mcp-server.js"],
      "cwd": "/path/to/quantclaw-data",
      "env": {}
    }
  }
}`,
  apiBase: "https://data.quantclaw.org/api/v1",
};

export interface CLICommand {
  category: string;
  commands: { cmd: string; description: string }[];
}

export const cliReference: CLICommand[] = [
  {
    category: "📈 Market Data & Prices",
    commands: [
      { cmd: "price AAPL", description: "Real-time stock price" },
      { cmd: "price AAPL --history 30d", description: "Historical prices (30 days)" },
      { cmd: "crypto bitcoin", description: "Cryptocurrency price" },
      { cmd: "crypto ethereum --history 7d", description: "Crypto with history" },
      { cmd: "commodity gold", description: "Commodity price" },
      { cmd: "forex EUR/USD", description: "Forex pair" },
    ],
  },
  {
    category: "🔍 Company Research",
    commands: [
      { cmd: "profile AAPL", description: "Company profile & fundamentals" },
      { cmd: "ratings AAPL", description: "Analyst ratings & price targets" },
      { cmd: "ratings TSLA --history", description: "Rating history" },
      { cmd: "news AAPL --sentiment", description: "News with NLP sentiment" },
      { cmd: "earnings AAPL", description: "Earnings data" },
      { cmd: "earnings --upcoming 7d", description: "Upcoming earnings calendar" },
      { cmd: "dividends AAPL", description: "Dividend history" },
      { cmd: "dividends --aristocrats", description: "Dividend aristocrats" },
    ],
  },
  {
    category: "📊 Technical Analysis",
    commands: [
      { cmd: "technicals AAPL", description: "Full technical analysis (RSI, MACD, SMA, etc.)" },
      { cmd: "technicals TSLA --indicators rsi,macd", description: "Specific indicators" },
      { cmd: "mtf AAPL", description: "Multi-timeframe analysis (daily/weekly/monthly)" },
      { cmd: "trend-alignment TSLA", description: "Cross-timeframe trend check" },
      { cmd: "signal-confluence NVDA", description: "Signal agreement scoring" },
      { cmd: "kalman AAPL", description: "Kalman filter trend extraction" },
      { cmd: "adaptive-ma SPY --period 6mo", description: "Adaptive moving average" },
      { cmd: "regime-detect SPY", description: "Market regime detection (trending/mean-reverting)" },
      { cmd: "support-resistance AAPL --period 6mo", description: "Volume-based S/R levels" },
    ],
  },
  {
    category: "🎯 Options & Derivatives",
    commands: [
      { cmd: "options AAPL", description: "Options chain with Greeks" },
      { cmd: "options TSLA --expiry 2026-03-21", description: "Specific expiry" },
      { cmd: "options-flow AAPL", description: "Options flow analysis" },
      { cmd: "options-flow --unusual", description: "Unusual options activity" },
      { cmd: "gex SPY", description: "Gamma exposure (GEX) positioning" },
      { cmd: "pin-risk AAPL", description: "Options pin risk at strikes" },
      { cmd: "hedging-flow TSLA", description: "Dealer hedging pressure" },
    ],
  },
  {
    category: "🧮 Quantitative Models",
    commands: [
      { cmd: "factors AAPL", description: "Factor model scoring (momentum, value, quality)" },
      { cmd: "factor-zoo AAPL", description: "400+ academic factor scores" },
      { cmd: "fama-french AAPL", description: "Fama-French 3/5-factor regression" },
      { cmd: "factor-attribution TSLA", description: "Factor return attribution" },
      { cmd: "factor-returns --days 30", description: "Recent factor performance" },
      { cmd: "monte-carlo AAPL --simulations 10000 --days 252", description: "Monte Carlo simulation (GBM)" },
      { cmd: "var TSLA --confidence 0.95 0.99", description: "Value-at-Risk & CVaR" },
      { cmd: "scenario NVDA --days 90", description: "Bull/bear/crash scenarios" },
      { cmd: "black-litterman --tickers AAPL,MSFT,GOOGL --views AAPL:0.20", description: "Black-Litterman portfolio" },
      { cmd: "equilibrium-returns --tickers SPY,QQQ,IWM", description: "Market equilibrium returns" },
      { cmd: "portfolio-optimize --tickers AAPL,MSFT,GOOGL", description: "Mean-variance optimization" },
    ],
  },
  {
    category: "📉 Portfolio & Risk",
    commands: [
      { cmd: "portfolio-analyze portfolio.json", description: "Full portfolio analytics" },
      { cmd: "backtest --strategy momentum --period 1y", description: "Strategy backtesting" },
      { cmd: "walk-forward SPY --strategy sma-crossover", description: "Walk-forward optimization" },
      { cmd: "overfit-check AAPL", description: "Overfitting detection" },
      { cmd: "param-stability TSLA", description: "Parameter stability analysis" },
    ],
  },
  {
    category: "🔄 Pairs & Rotation",
    commands: [
      { cmd: "cointegration KO PEP", description: "Engle-Granger cointegration test" },
      { cmd: "pairs-scan beverage", description: "Scan sector for pairs" },
      { cmd: "spread-monitor AAPL MSFT --period 60d", description: "Z-score spread tracking" },
      { cmd: "sector-rotation 60", description: "Sector rotation signals" },
      { cmd: "sector-momentum 90", description: "Sector momentum rankings" },
      { cmd: "economic-cycle", description: "Economic cycle phase detection" },
    ],
  },
  {
    category: "📡 Market Microstructure",
    commands: [
      { cmd: "order-book AAPL --levels 10", description: "Simulated L2 order book" },
      { cmd: "bid-ask TSLA", description: "Bid-ask spread analysis" },
      { cmd: "liquidity SPY", description: "Liquidity score (0-100)" },
      { cmd: "imbalance NVDA --period 5d", description: "Order flow imbalance" },
      { cmd: "microstructure-spreads AAPL", description: "Microstructure spread analysis" },
      { cmd: "microstructure-flow TSLA", description: "Flow analytics" },
    ],
  },
  {
    category: "🏦 Fixed Income & Macro",
    commands: [
      { cmd: "bonds yield-curve", description: "Treasury yield curve" },
      { cmd: "bonds spread --rating BBB", description: "Credit spreads by rating" },
      { cmd: "cds AAPL", description: "CDS spread estimate" },
      { cmd: "credit-spreads", description: "HY/IG credit spread dashboard" },
      { cmd: "sovereign-risk Italy", description: "Sovereign risk assessment" },
      { cmd: "macro gdp", description: "GDP data" },
      { cmd: "macro cpi --history 5y", description: "CPI inflation history" },
    ],
  },
  {
    category: "🕵️ Alternative Data",
    commands: [
      { cmd: "social AAPL", description: "Social media sentiment" },
      { cmd: "social GME --source reddit", description: "Reddit sentiment" },
      { cmd: "congress AAPL", description: "Congressional trading disclosures" },
      { cmd: "short-interest AAPL", description: "Short interest data" },
      { cmd: "short-interest --squeeze", description: "Short squeeze candidates" },
      { cmd: "activists AAPL", description: "Activist investor tracking" },
      { cmd: "esg AAPL", description: "ESG composite scores" },
      { cmd: "patents AAPL", description: "Patent filing velocity" },
      { cmd: "jobs AAPL", description: "Job posting signals" },
      { cmd: "supply-chain AAPL", description: "Supply chain mapping" },
      { cmd: "13f 0001067983", description: "Hedge fund 13F holdings (Berkshire)" },
      { cmd: "smart-money AAPL", description: "Institutional flow analysis" },
      { cmd: "top-funds", description: "Top hedge funds directory" },
    ],
  },
  {
    category: "📑 SEC & Filings",
    commands: [
      { cmd: "sec AAPL", description: "Recent SEC filings" },
      { cmd: "sec TSLA --type 10-K", description: "Specific filing type" },
      { cmd: "sec-nlp AAPL --section risk", description: "NLP analysis of risk factors" },
      { cmd: "transcript AAPL --quarter Q1-2026", description: "Earnings call transcript" },
      { cmd: "research-report AAPL --output report.md", description: "AI-generated research report" },
    ],
  },
  {
    category: "🔔 Smart Alerts",
    commands: [
      { cmd: 'alert-create AAPL --condition "price>200"', description: "Create price alert" },
      { cmd: "alert-list", description: "List active alerts" },
      { cmd: "alert-check", description: "Check all alerts against live data" },
      { cmd: "alert-delete ALERT_ID", description: "Delete an alert" },
      { cmd: "alert-stats", description: "Alert trigger statistics" },
      { cmd: 'alert-backtest AAPL --condition "rsi<30" --period 1y', description: "Backtest alert strategy" },
      { cmd: "signal-quality TSLA --period 1y", description: "Signal quality scoring" },
      { cmd: 'dsl-eval AAPL "price > 200 AND rsi < 30"', description: "Evaluate DSL expression" },
      { cmd: 'dsl-scan "rsi < 25" --universe SP500', description: "Scan universe with DSL" },
      { cmd: "dsl-help", description: "DSL syntax reference" },
    ],
  },
  {
    category: "🏗️ Infrastructure",
    commands: [
      { cmd: "etf SPY", description: "ETF holdings & overlap" },
      { cmd: "etf QQQ --overlap SPY", description: "ETF overlap analysis" },
      { cmd: "ipos --upcoming", description: "Upcoming IPOs" },
      { cmd: "spacs --arbitrage", description: "SPAC arbitrage opportunities" },
      { cmd: "ma --active", description: "Active M&A deals" },
      { cmd: "weather --region midwest", description: "Agricultural weather data" },
    ],
  },
];

export const apiEndpoints = [
  { path: "/api/v1/gex?symbol=SPY", description: "Gamma exposure" },
  { path: "/api/v1/pairs?action=cointegration&symbol1=KO&symbol2=PEP", description: "Pairs trading" },
  { path: "/api/v1/fama-french?ticker=AAPL", description: "Fama-French regression" },
  { path: "/api/v1/monte-carlo?action=simulate&symbol=AAPL&simulations=1000&days=30", description: "Monte Carlo" },
  { path: "/api/v1/kalman?action=kalman&symbol=SPY", description: "Kalman filter" },
  { path: "/api/v1/black-litterman?action=equilibrium-returns&tickers=SPY,QQQ,IWM", description: "Black-Litterman" },
  { path: "/api/v1/sector-rotation?action=rotation&lookback=60", description: "Sector rotation" },
  { path: "/api/v1/walk-forward?action=walk-forward&symbol=SPY&strategy=sma-crossover", description: "Walk-forward" },
  { path: "/api/v1/multi-timeframe?action=mtf&symbol=AAPL", description: "Multi-timeframe" },
  { path: "/api/v1/order-book?action=liquidity&symbol=SPY", description: "Liquidity score" },
  { path: "/api/v1/alerts?action=list", description: "List alerts" },
  { path: "/api/v1/alert-backtest?action=backtest&symbol=AAPL&condition=rsi<30", description: "Alert backtest" },
  { path: '/api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price>200 AND rsi<30', description: "DSL eval" },
  { path: "/api/v1/cds?action=credit-spreads", description: "Credit spreads" },
  { path: "/api/v1/13f?cik=0001067983", description: "Hedge fund 13F" },
];
