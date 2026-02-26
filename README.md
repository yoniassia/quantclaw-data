# 📈 QuantClaw Data — AI-Built Financial Intelligence Platform

> **699 modules. 112 data sources. 354K+ lines of code. $0/month. Built autonomously by AI agents.**

🌐 **Live**: [quantclaw.org](https://quantclaw.org) | 📊 **Dashboard**: [data.quantclaw.org](https://data.quantclaw.org)

---

## What is QuantClaw Data?

QuantClaw Data is an open financial intelligence platform where AI agents build, test, and deploy data modules autonomously. Every 30 minutes, a build agent creates new modules, expanding the platform's capabilities without human intervention.

## 🔢 By the Numbers

| Metric | Value |
|--------|-------|
| **Modules** | 699 |
| **Data Sources** | 112 (40+ countries) |
| **Lines of Code** | 354,050 |
| **REST API Endpoints** | 235+ |
| **Cost** | $0/month |
| **API Keys Required** | 0 |

## 🌍 Global Coverage

Central banks & statistics agencies from 40+ countries:

🇺🇸 US (FRED, SEC, BLS, Census) · 🇪🇺 EU (ECB, Eurostat) · 🇯🇵 Japan (BOJ, e-Stat, JPX) · 🇨🇳 China (PBOC, NBS, SSE, SZSE) · 🇮🇳 India (RBI, NSO, BSE/NSE) · 🇰🇷 Korea (BOK, KRX) · 🇦🇺 Australia (RBA, ABS, ASX) · 🇨🇦 Canada (BOC, StatCan) · 🇬🇧 UK (LSE) · 🇩🇪 Germany (Eurex) · 🇮🇱 Israel (BOI, CBS, TASE) · 🇷🇺 Russia (CBR, MOEX) · 🇧🇷 Brazil (BCB) · 🇲🇽 Mexico (Banxico, INEGI) · 🇸🇬 Singapore (MAS) · 🇭🇰 Hong Kong (HKMA) · 🇨🇭 Switzerland (SNB) · 🇿🇦 South Africa (SARB) · 🇸🇦 Saudi Arabia (SAMA) · 🇮🇩 Indonesia (BI) · 🇹🇼 Taiwan (CBC) · 🇵🇭 Philippines (BSP) · 🇨🇱 Chile · 🇨🇴 Colombia · 🇪🇬 Egypt · 🇲🇾 Malaysia · 🇻🇳 Vietnam · 🇹🇭 Thailand · 🇳🇬 Nigeria · 🇦🇷 Argentina · 🇵🇱 Poland

Plus: IMF, World Bank, OECD, BIS, WTO, ILO, FAO, WHO, IEA, UNCTAD, UNIDO, IRENA

## 📦 Module Categories

- **Market Data** — Prices, options, technicals, screeners
- **Fixed Income** — Treasuries, corporates, munis, repo rates
- **Derivatives** — CME, Cboe, ICE, DTCC, options analytics
- **Crypto** — CoinGecko, DeFi Llama, Glassnode, L2Beat
- **Global Macro** — FRED, central banks, yield curves
- **Country Stats** — 40+ national statistics agencies
- **Exchange Data** — JPX, LSE, SSE, SZSE, KRX, ASX, MOEX, TASE
- **Alt Data** — Satellite, shipping, flights, patents, congress trades
- **ESG & Climate** — CDP, carbon credits, EU taxonomy, deforestation
- **Quant** — Fama-French, Monte Carlo, backtesting, optimization
- **Intelligence** — NLP, sentiment, research synthesis
- **Commodities** — Oil, gas, agriculture, metals, rare earths

## 🔌 Integration

### MCP (AI Agents)
```json
{
  "mcpServers": {
    "quantclaw-data": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": { "CACHE_DIR": "/tmp/quantclaw-cache" }
    }
  }
}
```

### REST API
```
GET https://data.quantclaw.org/api/v1/{tool}?ticker={SYMBOL}
```
No authentication required.

### CLI
```bash
python cli.py prices AAPL
python cli.py monte-carlo SPY --simulations 10000
python cli.py congress-trades --days 30
python cli.py options TSLA --expiry 2026-03
```

## 🤖 AI Discovery

- **LLMs.txt**: [quantclaw.org/llms.txt](https://quantclaw.org/llms.txt)
- **AI Plugin**: [quantclaw.org/.well-known/ai-plugin.json](https://quantclaw.org/.well-known/ai-plugin.json)

## 🏗️ How It's Built

QuantClaw Data is self-evolving. An AI build agent runs on a cron schedule:
1. Reads the current roadmap
2. Builds the next module (Python + tests)
3. Registers it as CLI command + REST endpoint + MCP tool
4. Suggests 3 new features based on what it just built
5. Updates the roadmap and repeats

Started at 24 phases. Now at 699. The platform compounds its own capabilities.

## 🔗 Ecosystem

- [quantclaw.org](https://quantclaw.org) — Main site
- [data.quantclaw.org](https://data.quantclaw.org) — Interactive dashboard
- [terminal.quantclaw.org](https://terminal.quantclaw.org) — Bloomberg-style terminal
- [moneyclaw.com](https://moneyclaw.com) — Parent ecosystem

## 📄 License

Open source. Free to use.

---

*Built by [QuantClaw](https://quantclaw.org) — Autonomous Financial Intelligence*
