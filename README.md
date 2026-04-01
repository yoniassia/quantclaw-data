# QuantClaw Data — 1,056 Financial Data Modules

> The world's most comprehensive open financial data platform.
> 1,056 Python modules • MCP server • REST API • Natural Language Query • Terminal UI

**Live:** https://data.quantclaw.org · **Port:** 3055 · **PM2:** quantclaw-data

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Categories](#data-categories)
- [Module Catalog](#module-catalog)
- [MCP Server](#mcp-server)
- [REST API](#rest-api)
- [Natural Language Queries (DCC)](#natural-language-queries-dcc)
- [Terminal UI](#terminal-ui)
- [Data Sources & API Keys](#data-sources--api-keys)
- [Caching Layer](#caching-layer)
- [Development Phases](#development-phases)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Deployment](#deployment)

---

## Overview

QuantClaw Data is a massive financial data aggregation platform that unifies 1,056 Python data modules behind a single API. It provides real-time and historical data across equities, options, fixed income, crypto, commodities, forex, macro, alternative data, and quantitative analytics. The platform serves as the data backbone for the entire MoneyClawX ecosystem (AgentX, TerminalX, PICentral, VIP Signals).

**Key numbers:**
- **1,056** Python data modules
- **9** data categories (Core Market, Derivatives, Alt Data, Multi-Asset, Quant, Fixed Income, Events, Intelligence, Infrastructure)
- **47** completed development phases
- **30+** external API integrations
- **MCP protocol** support for AI agent tool calling
- **Natural language** query engine (DCC — Data Command Center)
- **Terminal-grade UI** with draggable panel grid

**How it's used:**
- AgentX signal generator fetches quotes, technicals, ratings, alpha scores
- TerminalX research views pull from 435+ modules
- PICentral research terminal uses 16 QuantClaw functions
- VIP Signals engine queries technicals and external signals

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 15.x |
| Language | TypeScript (web) + Python (modules) | 5.x / 3.14 |
| UI | React + Tailwind CSS | 19.x / 4.x |
| State | Zustand | 5.x |
| Charts | Lightweight Charts + Recharts | 5.x / 3.x |
| Tables | TanStack React Table | 8.x |
| Layout | react-grid-layout | 2.x |
| Database | PostgreSQL | 8.x |
| Process | PM2 | — |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Terminal UI (Next.js)                           │
│  ├── Draggable panel grid (TerminalGrid)        │
│  ├── Module browser (1,056 modules)             │
│  ├── Chart panels (TradingView-style)           │
│  ├── Ticker panels (real-time prices)           │
│  ├── News panels                                │
│  ├── Heatmap panels                             │
│  └── DCC Natural Language Query interface        │
├─────────────────────────────────────────────────┤
│  Next.js API Layer                               │
│  ├── /api/data?tool=X&params=Y (MCP proxy)      │
│  ├── /api/v1/{module}?params (REST API)          │
│  └── /api/dcc (natural language queries)         │
├─────────────────────────────────────────────────┤
│  MCP Server (Model Context Protocol)             │
│  ├── Tool definitions for all 1,056 modules      │
│  ├── AI agent interface (AgentX, PICentral)      │
│  └── callTool(), batchCall() patterns            │
├─────────────────────────────────────────────────┤
│  1,056 Python Modules                            │
│  ├── Each module = self-contained data fetcher   │
│  ├── Standardized input/output interface         │
│  ├── Built-in caching (file + memory)            │
│  └── Error handling + fallback logic             │
├─────────────────────────────────────────────────┤
│  External APIs                                   │
│  ├── FRED, Yahoo Finance, Financial Datasets     │
│  ├── Finnhub, CoinGecko, Etherscan              │
│  ├── SEC EDGAR, Census, EIA, USDA               │
│  ├── Polygon, Alpha Vantage, GuruFocus          │
│  └── 20+ more sources                            │
└─────────────────────────────────────────────────┘
```

---

## Data Categories

| Category | Icon | Modules | Description |
|----------|------|---------|-------------|
| Core Market Data | 📊 | ~150 | Prices, profiles, screeners, technicals, microstructure |
| Derivatives & Options | 📈 | ~80 | Options chains, Greeks, GEX tracking, flow scanner, volatility surface |
| Alternative Data | 🔍 | ~200 | Patents, job postings, supply chain, congress trades, social sentiment, satellite |
| Multi-Asset | 🌍 | ~120 | Crypto, commodities, forex, global indices, ETFs |
| Quantitative | 🧮 | ~150 | Factor models, portfolio analytics, backtesting, correlation, VaR |
| Fixed Income & Macro | 🏦 | ~100 | Yield curves, credit spreads, FRED macro data, central bank rates |
| Corporate Events | 📰 | ~80 | IPOs, SPACs, M&A, activist campaigns, earnings, dividends |
| Intelligence & NLP | 🤖 | ~80 | SEC NLP, earnings transcripts, AI research reports, news sentiment |
| Infrastructure | ⚙️ | ~60 | Data quality monitoring, streaming, alerts, caching |

---

## Module Catalog (Selected Highlights)

### Core Market Data
`prices`, `company_profile`, `screener`, `technicals`, `market_microstructure`, `analyst_ratings`, `market_quote`, `alpha_picker`

### Derivatives
`options_chain`, `options_flow`, `options_gex_tracker`, `cboe_put_call`, `volatility_surface`, `implied_volatility`

### Alternative Data
`congress_trades`, `patent_tracking`, `job_posting_signals`, `supply_chain_mapping`, `reddit_sentiment`, `insider_trades`, `short_interest`, `satellite_data`, `web_traffic_estimator`, `whale_wallet_tracker`

### Multi-Asset
`crypto_onchain`, `coingecko`, `commodity_prices`, `forex_rates`, `etf_holdings`, `adr_gdr_arbitrage`, `baltic_dry_index`

### Quantitative
`factor_model`, `portfolio_analytics`, `backtesting`, `correlation_heatmap`, `quant_factor_zoo`, `xgboost_alpha`, `monte_carlo`, `kelly_criterion`

### Fixed Income & Macro
`yield_curve`, `credit_spreads`, `fred_enhanced`, `central_bank_rates`, `treasury_curve`, `inflation_linked_bonds`, `fed_funds_futures`

### Corporate Events
`ipo_tracker`, `spac_tracker`, `ma_deal_flow`, `activist_investor`, `earnings_calendar`, `dividend_tracker`, `regulatory_calendar`

### Intelligence & NLP
`sec_nlp`, `earnings_transcripts`, `ai_research_reports`, `news_sentiment`, `ml_earnings_predictor`

### Government Statistics & Central Banks (Autobuilder Batches 1–7)

Thirty-two modules covering 22 countries across Europe, Scandinavia, Central Europe, British Isles, North America, Asia-Pacific, Middle East, Oceania, and Southeast Europe with 620+ macroeconomic indicators from official government statistical offices, central banks, and financial regulators:

| Module | Source | Country | API | Key Indicators |
|--------|--------|---------|-----|----------------|
| `bundesbank_sdmx` | Deutsche Bundesbank | Germany / Euro Area | `https://api.statistiken.bundesbank.de/rest` | Bund yields (1Y–30Y), ECB policy rates, MFI lending rates, M2/M3 monetary aggregates, current account, trade balance |
| `insee_france` | INSEE (National Statistics) | France | `https://bdm.insee.fr/series/sdmx` | GDP growth, CPI/HICP inflation, unemployment rate, industrial production, consumer confidence, household consumption, exports/imports |
| `banque_de_france` | Banque de France Webstat | France | `https://webstat.banque-france.fr/api/explore/v2.1` | EUR/USD/GBP/JPY/CHF/CNY FX rates, credit to NFCs & households, MFI interest rates, BoP, SME credit, business climate |
| `istat_italy` | ISTAT (National Statistics) | Italy | `http://sdmx.istat.it/SDMXWS/rest` | GDP quarterly accounts, CPI NIC & HICP, unemployment rate, industrial production, consumer & business confidence (IESI) |
| `cbs_netherlands` | CBS StatLine | Netherlands | `https://opendata.cbs.nl/ODataApi/odata` | GDP growth (YoY/QoQ), CPI, unemployment, house prices, trade balance, gov balance/debt (% GDP), consumer/producer confidence |
| `statistics_denmark` | Statistics Denmark (DST) | Denmark | `https://api.statbank.dk/v1` | GDP (nominal/real), CPI/HICP, unemployment, foreign trade, housing prices, consumer confidence, industrial production |
| `scb_sweden` | SCB (Statistics Sweden) | Sweden | `https://api.scb.se/OV0104/v1/doris/en/ssd` | GDP (QoQ + monthly indicator), CPI/CPIF, unemployment/employment rate, housing prices, production index, trade balance, govt debt |
| `riksbank_sweden` | Sveriges Riksbank | Sweden | `https://api.riksbank.se/swea/v1` | Policy/deposit/lending rates, SEK FX crosses (EUR/USD/GBP/JPY/CHF/NOK/DKK), KIX index, govt bond yields (2Y–10Y), T-bills, mortgage bonds |
| `banco_de_espana` | Banco de España | Spain / Euro Area | `https://app.bde.es/bierest/resources/srdatosapp` | Euribor (1W–12M), mortgage/consumer/NFC lending rates, deposit rates, IRPH, BoP (current/capital/financial account), housing prices (new/used/avg EUR/m²) |
| `banco_de_portugal` | Banco de Portugal (BPstat) | Portugal | `https://bpstat.bportugal.pt/data/v1` | MFI lending rates (NFC/housing/consumer), deposit rates (agreed maturity/overnight), new business rates, BoP (current/capital/goods/services/primary income), EUR FX crosses (USD/GBP/JPY/CHF/CNY), banking KPIs (ROA, CET1, NPL ratio, loan-to-deposit), FSI (Tier 1/RWA, liquidity) |
| `ons_uk` | ONS (Office for National Statistics) | United Kingdom | `https://api.beta.ons.gov.uk/v1` | Monthly GDP (all industries/services/production/manufacturing), CPIH inflation (all items/food/housing/transport), retail sales (volume/value), trade in goods (total/EU exports, imports), construction output (all/new work), private housing rental (index/YoY), labour market (unemployment/employment/inactivity rates) |
| `statcan_canada` | Statistics Canada (WDS) | Canada | `https://www150.statcan.gc.ca/t1/wds/rest` | GDP (quarterly current/real + monthly all industries), CPI (all items/food/shelter/energy), labour force survey (unemployment/employment/full-time/participation/employment rates), merchandise trade (exports/imports/balance), retail sales, housing starts (CMHC SAAR), new housing price index |
| `estat_japan` | e-Stat (Government of Japan) | Japan | `https://api.e-stat.go.jp/rest/3.0/app` | CPI (all items, core ex-fresh food), GDP (nominal/real quarterly SNA), unemployment rate, labour force population, industrial production index, trade statistics (exports/imports), housing starts, machinery orders (private ex. volatile) |
| `nbp_poland` | National Bank of Poland (NBP) | Poland | `https://api.nbp.pl/api` | PLN FX mid rates for 32+ major currencies (Table A), minor/exotic rates for 116 currencies (Table B, weekly), bid/ask dealer spreads for 13 currencies (Table C), gold price (PLN/gram), full table snapshots |
| `cbc_taiwan` | Central Bank of R.O.C. (Taiwan) | Taiwan | `https://cpx.cbc.gov.tw/API/DataAPI/Get` | TWD/USD spot FX (buy/sell/close), CBC policy rates (discount/secured/unsecured), five major bank deposit & lending rates, monetary aggregates (reserve money, M1A, M1B, M2 — daily avg + end-of-month), weighted-average interest rates (quarterly) |
| `nbb_belgium` | National Bank of Belgium (NBB.Stat) | Belgium / Euro Area | `https://nsidisseminate-stat.nbb.be/rest` | Balance of payments (current/goods/services/primary income/capital/financial accounts), HICP inflation (total/core/energy/services + index), financial accounts (household wealth, total economy), IIP (net position, portfolio investment), government finance (net lending, liabilities, debt securities), monetary aggregates (M1, M3 Euro Area), business surveys (synthetic, manufacturing, trade, services) |
| `central_bank_ireland` | Central Bank of Ireland | Ireland / Euro Area | `https://opendata.centralbank.ie/api/3/action` | ECB policy rates (deposit/refi/marginal), €STR & Euribor (3M/12M), retail new-business rates (mortgage/consumer/NFC lending, deposits), outstanding stock rates (household/NFC deposits & loans, mortgages), PDH mortgage rates (fixed >3Y, tracker), gross national debt (EUR mn), official external reserves (total/FX/gold) |
| `cso_ireland` | CSO Ireland (PxStat) | Ireland | `https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset` | GDP/GNP (quarterly constant & current prices), CPI (index/YoY/MoM), ILO unemployment/employment/participation rates, retail sales (volume/value index), residential property prices (index/YoY), merchandise trade (exports/imports/balance) |
| `statistics_finland` | Statistics Finland (Tilastokeskus) | Finland | `https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/` | GDP (QoQ/YoY/current prices), CPI index (2015=100), unemployment rate (SA + youth 15-24), employment rate & employed persons, industrial output (total/manufacturing/YoY), foreign trade (exports/imports), housing prices (index/YoY/EUR per m²) |
| `danmarks_nationalbank` | Danmarks Nationalbank | Denmark | `https://api.statbank.dk/v1` | DN policy rates (discount/current-account/lending/CD), DKK FX rates (EUR/USD/GBP/JPY/CHF/NOK/SEK), government bond yields (average/10Y), mortgage bond yields, balance of payments (current account/goods/services/primary income), MFI lending (total/NFC/households + avg lending rate), government debt securities |
|| `cnb_czech` | Czech National Bank (CNB) | Czech Republic | `https://www.cnb.cz` (TXT feeds) + `https://www.cnb.cz/aradb/api/v1` (ARAD) | CZK daily FX fixing (USD/EUR/GBP/CHF/JPY/CAD/AUD/PLN/HUF/SEK/NOK/CNY), PRIBOR interbank rates (O/N, 1W, 2W, 1M, 3M, 6M, 1Y), CNB monetary policy rates (2W repo, discount, Lombard) |
|| `destatis_germany` | Destatis (Statistisches Bundesamt) | Germany | `https://www-genesis.destatis.de/genesisWS/rest/2020` | GDP (annual/quarterly), CPI/HICP (monthly/annual), employment, foreign trade (exports/imports), industrial production index, PPI (monthly/annual), construction activity |
|| `uae_data` | CBUAE + World Bank | United Arab Emirates | `https://www.centralbank.ae` + `https://api.worldbank.org/v2` | AED FX rates (USD/EUR/GBP/JPY/CHF/SAR/CNY/INR/KWD/EGP — 76 currencies), GDP (current USD/growth), CPI inflation, broad money M2, FX reserves, exports/imports, current account, GDP per capita |
|| `edinet_japan` | EDINET (FSA Japan) | Japan | `https://api.edinet-fsa.go.jp/api/v2` | Annual securities reports (Yuho), quarterly reports, semi-annual reports, large shareholding reports (5%+), tender offer filings, securities registration (IPOs), company search, XBRL/PDF/CSV document downloads |
|| `fca_uk` | FCA Financial Services Register | United Kingdom | `https://register.fca.org.uk/services/V0.1` | Authorized firm search/details (by FRN), individual search (by IRN), fund/CIS search, firm permissions, disciplinary history, passports, requirements, addresses, regulated markets |
|| `abs_australia_sdmx` | ABS (Australian Bureau of Statistics) | Australia | `https://data.api.abs.gov.au/rest` | GDP (chain volume/growth/per capita), terms of trade, household saving ratio, CPI (index/quarterly change/annual monthly indicator), unemployment/employment/participation rate, labour force, current account, goods balance, retail trade, building approvals, trade balance, exports |
|| `rba_enhanced` | Reserve Bank of Australia (RBA) | Australia / International | `https://www.rba.gov.au/statistics/tables/csv` | Cash rate target, overnight cash rate, 3M BABs/OIS/T-note, AU govt bond yields (2Y–10Y + indexed), housing loan rates (variable/discounted/3Y fixed), credit card rate, SME lending rate, AUD FX (USD/EUR/GBP/JPY/CNY + TWI), international official rates (Fed/BOJ/ECB/BOE/BOC/RBA), credit growth (housing/total MoM & YoY), M3 growth, broad money, real & nominal GDP, terms of trade |
|| `bank_of_canada_valet` | Bank of Canada (Valet API) | Canada | `https://www.bankofcanada.ca/valet` | BoC overnight rate, bank rate, CORRA, GoC benchmark bond yields (2Y–30Y + RRB), marketable bond avg yields, T-bill yields (1M–1Y), CAD FX rates (26 currency pairs), prime rate, posted mortgage rates (1Y/3Y/5Y), GIC rates, GoC yield volatility, ACM term premiums (2Y/5Y/10Y), BCPI commodity index, BOS survey indicator |
|| `ine_spain` | INE (Instituto Nacional de Estadística) | Spain | `https://servicios.ine.es/wstempus/js/EN/` | GDP (current prices/QoQ/YoY growth), CPI (index/MoM/YoY), unemployment rate (total + youth <25), active population, employed persons, industrial production index (SA total + MoM), housing price index (HPI general/YoY/QoQ), exports & imports volume indices + YoY growth |
|| `dnb_netherlands` | De Nederlandsche Bank (DNB) | Netherlands | `https://api.dnb.nl/statpub-intapi-prd/v1` | Financial stability indicators (quarterly/yearly), banking structure (domestic/foreign/EU/non-EU), insurance & pension fund balance sheets, insurer cash flows, payment transactions & infrastructure, monetary aggregates (M1/M2/M3 Dutch contribution), household deposit & lending rates |
|| `bnr_romania` | National Bank of Romania (BNR) | Romania | `https://www.bnr.ro/nbrfxrates.xml` | RON daily reference FX rates for 37 currencies (EUR/USD/GBP/CHF/JPY/AUD/CAD/CNY/CZK/DKK/HUF/PLN/SEK/NOK/TRY/ZAR/KRW/INR/BRL/MXN/SGD/HKD/NZD/THB/PHP/MYR/IDR/ILS/EGP/MDL/RSD/RUB/UAH/ISK/AED + gold XAU + IMF SDR XDR), 10-day history |
|| `statbel_belgium` | Statbel (Statistics Belgium) | Belgium | `https://opendata-api.statbel.fgov.be` | CPI index (base 2013=100), CPI inflation (YoY), health index, CPI excl. energy, HICP by COICOP (food/housing/transport/restaurants), unemployment by age & sex (male/female × youth/prime), retail trade turnover index, Gini coefficient (income inequality), birth rate, death rate |

#### Global Coverage Map

```
🇩🇪 Germany      — Bundesbank (yields, ECB rates, monetary, trade)
🇫🇷 France       — INSEE (macro) + Banque de France (FX, credit, BoP)
🇮🇹 Italy        — ISTAT (GDP, inflation, labour, industry, confidence)
🇳🇱 Netherlands  — CBS StatLine (GDP, CPI, housing, trade, govt finance)
🇩🇰 Denmark      — DST StatBank (GDP, CPI, labour, trade, housing)
🇸🇪 Sweden       — SCB (macro) + Riksbank (rates, FX, bonds)
🇪🇸 Spain        — Banco de España (Euribor, lending rates, BoP, housing)
🇵🇹 Portugal     — BPstat (lending/deposit rates, BoP, FX, banking FSI)
🇬🇧 United Kingdom — ONS (GDP, CPIH, retail, trade, construction, labour)
🇨🇦 Canada       — StatCan (GDP, CPI, labour, trade, retail, housing)
🇯🇵 Japan        — e-Stat (CPI, GDP, unemployment, trade, industry, housing)
🇵🇱 Poland       — NBP (PLN FX rates Table A/B/C, bid/ask spreads, gold)
🇹🇼 Taiwan       — CBC (TWD/USD FX, policy rates, monetary aggregates, bank rates)
🇧🇪 Belgium      — NBB.Stat (BoP, HICP, financial accounts, IIP, govt finance, M1/M3, business surveys)
🇮🇪 Ireland      — CBI (ECB rates, Euribor, retail rates, mortgages, debt, reserves) + CSO (GDP/GNP, CPI, labour, retail, housing, trade)
🇫🇮 Finland        — Statistics Finland (GDP, CPI, unemployment, industrial output, trade, housing)
🇨🇿 Czech Republic — CNB (CZK FX fixing 12 currencies, PRIBOR term structure, 2W repo/discount/Lombard rates)
🇦🇺 Australia      — ABS SDMX (GDP, CPI, labour force, BoP, retail trade, building approvals, trade)
🇦🇪 UAE            — CBUAE (76-currency FX rates) + World Bank (GDP, CPI, M2, reserves, trade)
🇩🇪 Germany (ext)  — Destatis GENESIS (GDP, CPI/HICP, employment, trade, IPI, PPI, construction)
🇯🇵 Japan (ext)    — EDINET (annual/quarterly securities filings, large shareholding, tender offers)
🇬🇧 UK (ext)       — FCA Register (authorized firms, individuals, permissions, disciplinary, markets)
🇦🇺 Australia (ext) — RBA Enhanced (cash rate, money market, govt bonds, lending rates, AUD FX, intl rates, credit, GDP)
🇨🇦 Canada (ext)    — Bank of Canada Valet (overnight/bank rate, CORRA, GoC yield curve, T-bills, 26 FX pairs, mortgage rates, BCPI)
🇪🇸 Spain (ext)     — INE Tempus3 (GDP, CPI, EPA unemployment, IPI, housing prices, trade)
🇳🇱 Netherlands (ext) — DNB (FSIs, banking structure, insurance/pension, payments, monetary aggregates, household rates)
🇷🇴 Romania         — BNR (37-currency daily FX reference rates + gold + SDR, 10-day history)
🇧🇪 Belgium (ext)   — Statbel (CPI/health index, HICP by COICOP, unemployment by demographics, retail, Gini, demographics)
```

#### Usage Examples — Government Statistics Modules

**CLI:**
```bash
# Europe
python3 modules/bundesbank_sdmx.py BUND_10Y
python3 modules/insee_france.py GDP_GROWTH
python3 modules/banque_de_france.py EUR_USD
python3 modules/istat_italy.py CPI_NIC
python3 modules/cbs_netherlands.py GDP_GROWTH_YOY
python3 modules/statistics_denmark.py CPI_YOY
python3 modules/scb_sweden.py CPIF_ANNUAL_CHANGE
python3 modules/riksbank_sweden.py POLICY_RATE
python3 modules/banco_de_espana.py EURIBOR_12M
python3 modules/banco_de_portugal.py IR_LOANS_HOUSING
# UK, Canada, Japan
python3 modules/ons_uk.py GDP_MONTHLY
python3 modules/statcan_canada.py UNEMPLOYMENT_RATE
python3 modules/estat_japan.py CPI_ALL_ITEMS
# Poland, Taiwan
python3 modules/nbp_poland.py FX_EUR_PLN
python3 modules/cbc_taiwan.py TWD_USD_CLOSE
# Belgium, Ireland, Finland, Denmark (Batch 4)
python3 modules/nbb_belgium.py HICP_TOTAL_YOY
python3 modules/central_bank_ireland.py ECB_DEPOSIT_RATE
python3 modules/cso_ireland.py GDP_QUARTERLY
python3 modules/statistics_finland.py GDP_QOQ
python3 modules/danmarks_nationalbank.py DN_DISCOUNT_RATE
# Czech Republic (Batch 5)
python3 modules/cnb_czech.py FX_EUR
python3 modules/cnb_czech.py PRIBOR_3M
python3 modules/cnb_czech.py CNB_2W_REPO
python3 modules/cnb_czech.py pribor-curve
python3 modules/cnb_czech.py policy-rates
# Australia, UAE, Germany (ext), Japan (ext), UK (ext) — Batch 6–7
python3 modules/abs_australia_sdmx.py GDP_GROWTH
python3 modules/abs_australia_sdmx.py UNEMPLOYMENT_RATE
python3 modules/abs_australia_sdmx.py dashboard
python3 modules/uae_data.py FX_USD
python3 modules/uae_data.py GDP_GROWTH
python3 modules/uae_data.py fx
python3 modules/destatis_germany.py GDP_QUARTERLY
python3 modules/destatis_germany.py CPI_MONTHLY
python3 modules/destatis_germany.py INDUSTRIAL_PRODUCTION
python3 modules/edinet_japan.py ANNUAL_REPORTS
python3 modules/edinet_japan.py search "Toyota"
python3 modules/fca_uk.py FIRM_SEARCH "barclays"
python3 modules/fca_uk.py REGULATED_MARKETS
# RBA Australia Enhanced — Batch 7
python3 modules/rba_enhanced.py F1_CASH_RATE_TARGET
python3 modules/rba_enhanced.py F2_GOVT_10Y
python3 modules/rba_enhanced.py F5_HOUSING_VARIABLE
python3 modules/rba_enhanced.py F11_AUD_USD
python3 modules/rba_enhanced.py F13_US_FED_FUNDS
python3 modules/rba_enhanced.py yield-curve
python3 modules/rba_enhanced.py rates
python3 modules/rba_enhanced.py fx
# Bank of Canada Enhanced, INE Spain, DNB Netherlands, BNR Romania, Statbel Belgium — Batch 8
python3 modules/bank_of_canada_valet.py GOC_10Y
python3 modules/bank_of_canada_valet.py OVERNIGHT_RATE
python3 modules/bank_of_canada_valet.py FX_USD_CAD
python3 modules/bank_of_canada_valet.py yield-curve
python3 modules/bank_of_canada_valet.py fx-rates
python3 modules/bank_of_canada_valet.py policy-rates
python3 modules/ine_spain.py GDP_QOQ
python3 modules/ine_spain.py CPI_YOY
python3 modules/ine_spain.py UNEMPLOYMENT_RATE
python3 modules/ine_spain.py HPI_INDEX
python3 modules/dnb_netherlands.py FINANCIAL_STABILITY_Q
python3 modules/dnb_netherlands.py HOUSEHOLD_RATES
python3 modules/dnb_netherlands.py MONETARY_AGGREGATES
python3 modules/bnr_romania.py RON_EUR
python3 modules/bnr_romania.py RON_USD
python3 modules/bnr_romania.py rates
python3 modules/bnr_romania.py history
python3 modules/statbel_belgium.py CPI_INDEX
python3 modules/statbel_belgium.py CPI_INFLATION
python3 modules/statbel_belgium.py HICP_FOOD
python3 modules/statbel_belgium.py GINI_COEFFICIENT
```

**REST API:**
```
GET /api/v1/bundesbank-sdmx?indicator=BUND_10Y
GET /api/v1/insee-france?indicator=GDP_GROWTH
GET /api/v1/riksbank-sweden?indicator=POLICY_RATE
GET /api/v1/banco-de-espana?indicator=EURIBOR_12M
GET /api/v1/banco-de-portugal?indicator=BOP_CURRENT_ACCOUNT
GET /api/v1/ons-uk?indicator=GDP_MONTHLY
GET /api/v1/statcan-canada?indicator=GDP_REAL
GET /api/v1/estat-japan?indicator=GDP_NOMINAL
GET /api/v1/nbp-poland?indicator=FX_EUR_PLN
GET /api/v1/cbc-taiwan?indicator=CBC_DISCOUNT_RATE
GET /api/v1/nbb-belgium?indicator=HICP_TOTAL_YOY
GET /api/v1/central-bank-ireland?indicator=ECB_DEPOSIT_RATE
GET /api/v1/cso-ireland?indicator=CPI_YOY
GET /api/v1/statistics-finland?indicator=UNEMPLOYMENT_RATE
GET /api/v1/danmarks-nationalbank?indicator=FX_EUR_DKK
GET /api/v1/cnb-czech?indicator=FX_EUR
GET /api/v1/cnb-czech?indicator=PRIBOR_3M
GET /api/v1/cnb-czech?indicator=CNB_2W_REPO
GET /api/v1/abs-australia-sdmx?indicator=GDP_GROWTH
GET /api/v1/abs-australia-sdmx?indicator=UNEMPLOYMENT_RATE
GET /api/v1/uae-data?indicator=FX_USD
GET /api/v1/uae-data?indicator=GDP_CURRENT_USD
GET /api/v1/destatis-germany?indicator=CPI_MONTHLY
GET /api/v1/destatis-germany?indicator=GDP_QUARTERLY
GET /api/v1/edinet-japan?indicator=ANNUAL_REPORTS&start_date=2026-04-01
GET /api/v1/fca-uk?indicator=FIRM_SEARCH&query=barclays
GET /api/v1/fca-uk?indicator=REGULATED_MARKETS
GET /api/v1/rba-enhanced?indicator=F1_CASH_RATE_TARGET
GET /api/v1/rba-enhanced?indicator=F2_GOVT_10Y
GET /api/v1/rba-enhanced?indicator=F5_HOUSING_VARIABLE
GET /api/v1/rba-enhanced?indicator=F11_AUD_USD
GET /api/v1/rba-enhanced?indicator=H1_REAL_GDP_GROWTH
GET /api/v1/bank-of-canada-valet?indicator=GOC_10Y
GET /api/v1/bank-of-canada-valet?indicator=OVERNIGHT_RATE
GET /api/v1/bank-of-canada-valet?indicator=FX_USD_CAD
GET /api/v1/bank-of-canada-valet?indicator=PRIME_RATE
GET /api/v1/ine-spain?indicator=GDP_QOQ
GET /api/v1/ine-spain?indicator=CPI_YOY
GET /api/v1/ine-spain?indicator=UNEMPLOYMENT_RATE
GET /api/v1/dnb-netherlands?indicator=FINANCIAL_STABILITY_Q
GET /api/v1/dnb-netherlands?indicator=HOUSEHOLD_RATES
GET /api/v1/bnr-romania?indicator=RON_EUR
GET /api/v1/bnr-romania?indicator=RON_USD
GET /api/v1/statbel-belgium?indicator=CPI_INDEX
GET /api/v1/statbel-belgium?indicator=GINI_COEFFICIENT
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'ons_uk',
    params: { indicator: 'CPIH_ALL' }
  })
});
```

**Batch MCP — Cross-Country Comparison:**
```typescript
const results = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'fred_enhanced', params: { series: 'UNRATE' } },
      { tool: 'ons_uk', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'statcan_canada', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'estat_japan', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'insee_france', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'nbp_poland', params: { indicator: 'FX_USD_PLN' } }
    ]
  })
});
```

**Batch MCP — Interbank Rate Comparison (New in Batch 5):**
```typescript
const interbankRates = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'cnb_czech', params: { indicator: 'PRIBOR_3M' } },
      { tool: 'banco_de_espana', params: { indicator: 'EURIBOR_3M' } },
      { tool: 'central_bank_ireland', params: { indicator: 'EURIBOR_3M' } },
      { tool: 'riksbank_sweden', params: { indicator: 'POLICY_RATE' } },
      { tool: 'Danmarks_nationalbank', params: { indicator: 'DN_DISCOUNT_RATE' } }
    ]
  })
});
```

**Batch MCP — FX Rate Comparison (New in Batch 3):**
```typescript
const fxRates = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'cbc_taiwan', params: { indicator: 'TWD_USD_CLOSE' } },
      { tool: 'nbp_poland', params: { indicator: 'FX_USD_PLN' } },
      { tool: 'riksbank_sweden', params: { indicator: 'SEK_USD' } },
      { tool: 'banque_de_france', params: { indicator: 'EUR_USD' } },
      { tool: 'banco_de_portugal', params: { indicator: 'FX_EUR_USD' } }
    ]
  })
});
```

#### Batch 3: Asia & Eastern Europe Expansion

Batch 3 extends government data coverage to **12 countries** with two new modules:

**CBC Taiwan** (`cbc_taiwan`) — Central Bank of the Republic of China (Taiwan):
- TWD/USD spot exchange rates (daily close, bank buy/sell rates)
- CBC monetary policy rates: discount rate, secured & unsecured accommodation rates
- Five major domestic banks: 1-year fixed deposit, savings deposit, base lending rates
- Monetary aggregates: Reserve Money, M1A, M1B, M2 (daily averages + end-of-month)
- Weighted-average deposit and lending rates (all banks, quarterly)
- **18 indicators** covering FX, rates, and monetary policy
- API: `https://cpx.cbc.gov.tw/API/DataAPI/Get` (REST/JSON, open access, no auth)

**NBP Poland** (`nbp_poland`) — National Bank of Poland:
- PLN exchange rates against 32+ major currencies (Table A, daily mid rates)
- Minor/exotic currency rates for 116 currencies (Table B, published weekly on Wednesdays)
- Bid/ask dealer spreads for 13 key currencies (Table C, daily)
- Gold price in PLN per gram (daily, 1000 fineness)
- Full table snapshots: fetch all rates for any NBP table in a single API call
- Date-range queries with automatic chunking (handles NBP's 93-day API limit)
- **21 indicators** covering FX mid rates, bid/ask spreads, and gold
- API: `https://api.nbp.pl/api` (REST/JSON, open access, no auth, no rate limit)

**Coverage totals after Batch 3:**
- 15 government/central bank modules
- 13 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼
- 250+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates, policy rates, monetary aggregates, GDP, CPI, unemployment, trade, housing, banking FSIs, gold

#### Batch 4: Western Europe & Nordics Expansion

Batch 4 adds **5 new modules** covering Belgium, Ireland, Finland, and Danish central bank data, bringing total coverage to **16 countries** and **20 government/central bank modules** with **350+ indicators**.

**NBB Belgium** (`nbb_belgium`) — National Bank of Belgium:
- Balance of payments: current account, goods, services, primary income, capital & financial accounts (monthly)
- HICP inflation: total, core (ex food & energy), energy, services, plus index level (monthly)
- Financial accounts: household net financial wealth, total economy net financial position (quarterly)
- International investment position: net IIP, portfolio investment net position (quarterly)
- Government finance: net lending/borrowing, total financial liabilities, debt securities outstanding (quarterly)
- Monetary aggregates: M1 and M3 for the Euro Area (monthly)
- Business surveys: NBB synthetic confidence curve, manufacturing, trade, business services (monthly, SA)
- **24 indicators** across BoP, inflation, financial stability, government, monetary, and surveys
- API: `https://nsidisseminate-stat.nbb.be/rest` (SDMX 2.1 REST/JSON, open access, requires Origin header)

**Central Bank of Ireland** (`central_bank_ireland`) — CBI Open Data:
- Eurosystem official rates: ECB deposit facility, main refinancing, marginal lending rates (monthly)
- Interbank rates: €STR, 3-month & 12-month Euribor (monthly)
- Retail new-business rates: mortgage, consumer credit, NFC lending, household & NFC deposits (monthly)
- Outstanding stock rates: household overnight & term deposits, overdrafts, mortgages >5Y (monthly)
- Mortgage rates by type: PDH fixed >3Y, tracker mortgages (quarterly)
- Gross national debt outstanding in EUR millions (quarterly)
- Official external reserves: total reserve assets, foreign exchange, monetary gold (monthly)
- **22 indicators** covering ECB/interbank rates, retail banking, sovereign debt, and reserves
- API: `https://opendata.centralbank.ie/api/3/action` (CKAN Datastore REST, open access CC-BY-4.0)

**CSO Ireland** (`cso_ireland`) — Central Statistics Office:
- GDP & GNP at constant and current market prices, seasonally adjusted (quarterly)
- Consumer prices: CPI index (Dec 2023=100), year-on-year and month-on-month changes (monthly)
- Labour force: ILO unemployment, employment, and participation rates (quarterly)
- Retail sales: volume and value indices, seasonally adjusted (monthly, 2015=100)
- Residential property prices: national index and annual percentage change (monthly)
- Merchandise trade: total exports, imports, and trade balance in EUR millions (monthly)
- **16 indicators** covering the Irish economy's key macro dimensions
- API: `https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset` (PxStat JSON-stat 2.0, open access)

**Statistics Finland** (`statistics_finland`) — Tilastokeskus PxWeb:
- GDP: quarter-on-quarter and year-on-year volume changes, current prices in EUR millions (quarterly)
- CPI index with 2015 base year (monthly)
- Labour market: unemployment rate (SA), youth unemployment 15-24, employment rate 15-64, employed persons (monthly)
- Industrial output: total (BCD) and manufacturing (NACE C) volume indices, YoY working-day adjusted (monthly)
- Foreign trade: exports and imports of goods & services in EUR millions (quarterly)
- Housing: old dwelling price index (2020=100), annual change, and average EUR per m² (quarterly)
- **17 indicators** with PxWeb POST-based queries
- API: `https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/` (PxWeb REST, open access)

**Danmarks Nationalbank** (`danmarks_nationalbank`) — Danish Central Bank:
- Policy rates: discount rate, current-account deposits, lending rate, certificates of deposit (monthly)
- FX rates: DKK against EUR (ERM II peg ~746), USD, GBP, JPY, CHF, NOK, SEK (monthly average)
- Government bond yields: average redemption yield, 10-year benchmark, mortgage bond yields (monthly)
- Balance of payments: current account, goods, services, primary income — DKK mn, SA (monthly)
- MFI lending: total, NFC, household outstanding loans, average lending rate (monthly)
- Government securities: total debt securities and government bonds outstanding in DKK mn (monthly)
- **22 indicators** via StatBank Denmark's JSON-Stat API
- API: `https://api.statbank.dk/v1` (REST/JSON-Stat, open access)

**Coverage totals after Batch 4:**
- 20 government/central bank modules
- 16 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮
- 350+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates, policy rates, monetary aggregates, GDP, CPI/HICP, unemployment, trade, housing, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts

#### Batch 5: Central Europe — Czech Republic

Batch 5 adds the **Czech National Bank (CNB)** module, extending coverage to **17 countries** and **21 government/central bank modules** with **370+ indicators**.

**CNB Czech Republic** (`cnb_czech`) — Czech National Bank:
- CZK daily FX fixing rates for 12 major currencies: USD, EUR, GBP, CHF, JPY, CAD, AUD, PLN, HUF, SEK, NOK, CNY (published each business day ~14:15 CET)
- PRIBOR interbank term structure: overnight, 1-week, 2-week, 1-month, 3-month, 6-month, and 1-year maturities (daily, 48h delay)
- CNB official monetary policy rates: 2-week repo rate (main policy instrument), discount rate (corridor floor), Lombard rate (corridor ceiling) — full history since Czech independence (1993)
- Optional ARAD time-series API for deeper macroeconomic data (requires free API key)
- **22 indicators** across FX fixing, interbank rates, and monetary policy
- APIs: FX/PRIBOR via `https://www.cnb.cz` (open TXT/CSV feeds, no auth); ARAD via `https://www.cnb.cz/aradb/api/v1` (JSON, free key required)
- Cache TTL: 1h for FX/PRIBOR, 24h for policy rates

**Example response — `FX_EUR`:**
```json
{
  "success": true,
  "indicator": "FX_EUR",
  "name": "CZK/EUR Daily Fixing",
  "latest_value": 25.135,
  "latest_period": "01 Apr 2026",
  "period_change": -0.012,
  "period_change_pct": -0.0477,
  "unit": "CZK",
  "frequency": "daily",
  "data_points": [{"period": "01.04.2026", "value": 25.135}, "..."],
  "total_observations": 65
}
```

**Example — PRIBOR term structure:**
```bash
python3 modules/cnb_czech.py pribor-curve
# Returns: {"curve": [{"maturity": "1 day", "rate_pct": 3.69}, {"maturity": "1 week", "rate_pct": 3.72}, ...]}
```

**Coverage totals after Batch 5:**
- 21 government/central bank modules
- 17 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿
- 370+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates, policy rates, interbank rates (PRIBOR/Euribor), monetary aggregates, GDP, CPI/HICP, unemployment, trade, housing, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts

#### Batch 6: Asia-Pacific, Middle East, Extended Europe & Regulatory

Batch 6 adds **5 new modules** expanding to **Australia, UAE, and deeper German/Japanese/UK** data, bringing total coverage to **21 countries** and **26 government/central bank/regulatory modules** with **460+ indicators**.

**ABS Australia Enhanced** (`abs_australia_sdmx`) — Australian Bureau of Statistics:
- GDP chain volume measures, quarterly growth, and GDP per capita (seasonally adjusted)
- Terms of trade index, household saving ratio (quarterly)
- CPI all groups index (quarterly), annual % change (monthly indicator), quarterly % change
- Labour force survey: unemployment rate, employed persons, participation rate, total labour force (monthly, SA)
- Balance of payments: current account balance, goods balance (quarterly)
- Retail trade total turnover (monthly, SA), building approvals — total residential dwellings (monthly)
- International trade in goods: trade balance, total goods exports (monthly, SA)
- **19 indicators** via SDMX 2.1 REST with SDMX-JSON 2.0 parsing
- API: `https://data.api.abs.gov.au/rest` (SDMX 2.1, open access, no auth)

**UAE Open Data** (`uae_data`) — Central Bank of UAE + World Bank:
- CBUAE official FX rates for 76 currencies (daily, Arabic-to-ISO mapping, AED base)
- Major FX pairs: AED/USD (pegged ~3.6725), AED/EUR, AED/GBP, AED/JPY, AED/CHF, AED/SAR, AED/CNY, AED/INR, AED/KWD, AED/EGP
- Historical FX rates via date-based CBUAE API queries
- World Bank macro indicators: GDP (current USD, growth %), CPI inflation, CPI index (2010=100), broad money M2, total reserves incl. gold, exports/imports of goods & services, current account balance, GDP per capita
- **20 indicators** across daily FX and annual macroeconomic series
- APIs: CBUAE FX via `https://www.centralbank.ae` (Surface API, open access); World Bank via `https://api.worldbank.org/v2` (REST JSON, open)

**Destatis Germany** (`destatis_germany`) — Statistisches Bundesamt (GENESIS-Online):
- GDP: annual and quarterly gross domestic product and gross value added (nominal and price-adjusted)
- Consumer prices: CPI monthly and annual (2020=100), HICP monthly and annual (2015=100)
- Labour market: employment, unemployment, economically active population (annual)
- Foreign trade: exports and imports monthly and annual in EUR millions
- Industrial production index (manufacturing, monthly, 2021=100)
- Producer prices: PPI monthly and annual (2021=100)
- Construction sector: establishments, persons employed, hours worked, turnover (monthly)
- GENESIS table search: free-text search across 2,000+ Destatis statistical tables
- **13 indicators** via GENESIS-Online REST API with flat-file CSV parsing
- API: `https://www-genesis.destatis.de/genesisWS/rest/2020` (REST POST, free registration at https://www-genesis.destatis.de)

**EDINET Japan** (`edinet_japan`) — FSA Electronic Disclosure Network:
- Annual securities reports (有価証券報告書, Yuho) — comprehensive financial disclosures from all listed companies
- Quarterly and semi-annual financial reports
- Large shareholding reports (大量保有報告書) — 5%+ ownership disclosures
- Tender offer notifications (公開買付届出書) — takeover bid filings
- Securities registration statements — IPO and new offering filings
- Company search across filings by name, EDINET code, or securities code
- Document download: XBRL ZIP, PDF, attachments, English translations, CSV extracts
- **7 indicators** (filing categories) + search + document download
- API: `https://api.edinet-fsa.go.jp/api/v2` (REST JSON/ZIP, requires free Subscription-Key)

**FCA UK** (`fca_uk`) — Financial Conduct Authority Register:
- Firm search and detailed profiles: FCA-authorized firms by name or FRN (Firm Reference Number)
- Individual search: approved and prohibited persons by name or IRN
- Fund/CIS search: collective investment schemes by name or PRN
- Firm regulatory details: status, business type, Companies House number, effective dates
- Firm permissions: regulated activities and permissions granted
- Firm individuals: approved persons and controlled functions
- Firm passports: cross-border EEA passporting permissions
- Firm disciplinary history: enforcement actions, fines, and sanctions
- Firm requirements, addresses, PSD2 exclusions
- UK regulated markets: FCA-recognized exchanges and trading venues
- **13 indicators** across firm/individual/fund search and regulatory data
- API: `https://register.fca.org.uk/services/V0.1` (REST JSON, free API key + email at https://register.fca.org.uk/Developer/s/)

**Coverage totals after Batch 6:**
- 26 government/central bank/regulatory modules
- 21 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇩🇪+ 🇯🇵+ 🇬🇧+
- 460+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates, policy rates, interbank rates, monetary aggregates, GDP, CPI/HICP/PPI, unemployment, trade, housing, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade

#### Batch 7: Australia Central Bank — Reserve Bank of Australia

Batch 7 adds the **Reserve Bank of Australia (RBA) Enhanced** module, providing comprehensive coverage of all major RBA statistical tables. This is the deepest Australian financial data module in the platform, complementing the ABS macro statistics module added in Batch 6 with central bank rates, bond yields, lending rates, FX, credit aggregates, and GDP from the RBA's own statistical publications.

**RBA Australia Enhanced** (`rba_enhanced`) — Reserve Bank of Australia:
- **Table F1 — Money Market:** RBA cash rate target, interbank overnight cash rate, 3-month BABs/NCDs, 3-month OIS, 3-month Treasury note yield (daily)
- **Table F2 — Capital Market Yields:** Australian government bond yields at 2Y, 3Y, 5Y, 10Y maturities + 10Y indexed bond yield (daily, % p.a.)
- **Table F5 — Indicator Lending Rates:** Housing loan rates (variable standard, variable discounted, 3-year fixed for owner-occupiers), credit card standard rate, small business variable term lending rate (monthly)
- **Table F11 — Exchange Rates:** AUD/USD, AUD/EUR, AUD/GBP, AUD/JPY, AUD/CNY exchange rates + AUD Trade-Weighted Index (TWI, May 1970=100) (monthly)
- **Table F13 — International Official Interest Rates:** US Fed Funds max target, Bank of Japan policy rate, ECB refinancing rate, UK Bank Rate, Bank of Canada overnight target, RBA target cash rate — enabling cross-country rate comparisons (monthly)
- **Table D1 — Financial Aggregates Growth:** Housing credit (MoM & 12M), total credit (MoM & 12M), M3 monetary aggregate (MoM & 12M), broad money 12M growth — all seasonally adjusted incl. securitisations (monthly)
- **Table H1 — GDP and Income:** Real GDP (chain volume, AUD mn), real GDP year-ended growth (%), nominal GDP (current price, AUD mn), nominal GDP year-ended growth (%), terms of trade index (quarterly, SA)
- **39 indicators** across 7 RBA statistical tables (F1, F2, F5, F11, F13, D1, H1)
- **Special commands:** `yield-curve` (AU govt bond yield curve), `rates` (all interest/policy rates), `fx` (all AUD exchange rates)
- API: `https://www.rba.gov.au/statistics/tables/csv` (direct CSV download, open access, no auth)
- Cache TTL: 1h for daily tables (F1/F2), 24h for monthly/quarterly tables (F5/F11/F13/D1/H1)

**Example response — `F1_CASH_RATE_TARGET`:**
```json
{
  "success": true,
  "indicator": "F1_CASH_RATE_TARGET",
  "name": "RBA Cash Rate Target (%)",
  "description": "Official RBA cash rate target",
  "unit": "%",
  "frequency": "daily",
  "latest_value": 4.10,
  "latest_period": "2026-03-31",
  "period_change": 0.0,
  "period_change_pct": 0.0,
  "data_points": [{"period": "2026-03-31", "value": 4.10}, "..."],
  "total_observations": 250,
  "source": "https://www.rba.gov.au/statistics/tables/csv/f1-data.csv"
}
```

**Example — Australian government bond yield curve:**
```bash
python3 modules/rba_enhanced.py yield-curve
# Returns: {"curve": [{"maturity": "2Y", "yield_pct": 3.85}, {"maturity": "3Y", "yield_pct": 3.92}, {"maturity": "5Y", "yield_pct": 4.01}, {"maturity": "10Y", "yield_pct": 4.28}, {"maturity": "INDEXED", "yield_pct": 1.65}]}
```

**Batch MCP — Central Bank Rate Comparison (New in Batch 7):**
```typescript
const centralBankRates = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'rba_enhanced', params: { indicator: 'F1_CASH_RATE_TARGET' } },
      { tool: 'rba_enhanced', params: { indicator: 'F13_US_FED_FUNDS' } },
      { tool: 'rba_enhanced', params: { indicator: 'F13_ECB_REFI' } },
      { tool: 'rba_enhanced', params: { indicator: 'F13_UK_BANK_RATE' } },
      { tool: 'rba_enhanced', params: { indicator: 'F13_JAPAN_RATE' } },
      { tool: 'riksbank_sweden', params: { indicator: 'POLICY_RATE' } },
      { tool: 'cnb_czech', params: { indicator: 'CNB_2W_REPO' } },
      { tool: 'Danmarks_nationalbank', params: { indicator: 'DN_DISCOUNT_RATE' } }
    ]
  })
});
```

**Coverage totals after Batch 7:**
- 27 government/central bank/regulatory modules
- 21 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇩🇪+ 🇯🇵+ 🇬🇧+
- 500+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates, policy rates, interbank rates, monetary aggregates, GDP, CPI/HICP/PPI, unemployment, trade, housing, lending rates, credit growth, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves)

#### Batch 8: Extended Coverage — Canada, Spain, Netherlands, Romania, Belgium

Batch 8 adds **5 new modules** deepening existing country coverage and expanding into **Romania** as the first Southeast European nation. This brings total coverage to **22 countries** and **32 government/central bank/regulatory modules** with **620+ indicators**.

**Bank of Canada Valet Enhanced** (`bank_of_canada_valet`) — Bank of Canada:
- Policy rates: BoC overnight rate, bank rate, CORRA (Canadian Overnight Repo Rate Average)
- GoC benchmark bond yield curve: 2Y, 3Y, 5Y, 7Y, 10Y, long-term (30Y), real return bonds
- Marketable bond average yields: 1–3Y, 3–5Y, 5–10Y, over-10Y
- Treasury bill yields: 1M, 3M, 6M, 1Y + 90-day mid rate
- Daily FX rates: CAD against 26 currencies (USD/EUR/GBP/JPY/CHF/AUD/NZD/CNY/HKD/INR/IDR/MYR/MXN/NOK/PEN/RUB/SAR/SGD/ZAR/KRW/SEK/TWD/THB/TRY/BRL/VND)
- Chartered bank posted rates: prime rate, mortgage rates (1Y/3Y/5Y fixed), GIC rates (1Y/5Y)
- Financial conditions: GoC yield volatility, ACM term premiums (2Y/5Y/10Y)
- Bank of Canada Commodity Price Index (BCPI): total, energy, metals & minerals
- Business Outlook Survey (BOS) composite indicator
- **44 indicators** across 9 groups (policy, bonds, T-bills, money market, FX, bank rates, financial conditions, commodities, surveys)
- API: `https://www.bankofcanada.ca/valet` (REST JSON, open access, no auth)

**INE Spain** (`ine_spain`) — Instituto Nacional de Estadística:
- GDP: current prices (EUR mn), QoQ growth (SA volume), YoY growth (SA volume)
- CPI: overall index (base 2024=100), monthly variation, annual inflation rate
- Labour market (EPA survey): unemployment rate (all ages), youth unemployment (<25), active population, employed persons
- Industrial production: IPI total SA (2021=100), monthly variation
- Housing: HPI general index (2015=100), YoY change, QoQ change
- Foreign trade: exports & imports volume indices + YoY growth (SA chain-linked)
- **19 indicators** via INE Tempus3 API with series-level data access
- API: `https://servicios.ine.es/wstempus/js/EN/` (REST JSON, open access, no auth)

**DNB Netherlands** (`dnb_netherlands`) — De Nederlandsche Bank:
- Financial stability indicators: quarterly and yearly FSIs for Dutch banking (capital adequacy, asset quality, profitability, liquidity)
- Banking structure: number of banks and balance sheet totals by type (domestic, foreign, EU, non-EU)
- Institutional investors: insurance corporation balance sheets, pension fund balance sheets, insurer cash flow statements
- Payment system: transaction volumes and values (card, credit transfer, direct debit), payment infrastructure units (POS, ATMs, cards)
- Monetary aggregates: Dutch contribution to Euro Area M1/M2/M3 (stocks and flows)
- Interest rates: MFI rates on household deposits, consumer credit, and mortgage loans
- **9 indicators** (resource-based datasets with multi-dimensional filtering)
- API: `https://api.dnb.nl/statpub-intapi-prd/v1` (REST JSON via Azure APIM, subscription key — `DNB_SUBSCRIPTION_KEY` env var, public fallback available)

**BNR Romania** (`bnr_romania`) — National Bank of Romania:
- Daily reference exchange rates for RON against 37 currencies: EUR, USD, GBP, CHF, JPY, AUD, CAD, CNY, CZK, DKK, EGP, HKD, HUF, IDR, ILS, INR, ISK, KRW, MDL, MXN, MYR, NOK, NZD, PHP, PLN, RSD, RUB, SEK, SGD, THB, TRY, UAH, ZAR, AED, BRL + gold (XAU) per troy oz + IMF SDR (XDR)
- 10-day historical rates via extended XML feed
- Multiplier-normalized values (HUF, IDR, ISK, JPY, KRW published per 100 units)
- Date-specific rate queries and full rate snapshots
- **37 indicators** covering all published BNR FX pairs + precious metals
- API: `https://www.bnr.ro/nbrfxrates.xml` (daily XML) + `nbrfxrates10days.xml` (10-day history), open access, no auth
- Cache TTL: 1h (rates updated ~13:00 EET on business days)

**Statbel Belgium** (`statbel_belgium`) — Statistics Belgium Open Data:
- Consumer Price Index: overall CPI (base 2013=100), YoY inflation rate, health index (excl. tobacco/alcohol/fuel), CPI excluding energy
- Harmonised Index of Consumer Prices (HICP) by COICOP division: food & beverages, housing/water/energy, transport, restaurants & hotels (2015=100)
- Labour force: unemployment rates by sex and age group (male/female × youth 15-24 / prime 25-54), national annual averages
- Retail trade: total turnover index (base 2021=100, non-adjusted, NACE G47)
- Income inequality: Gini coefficient of equivalised disposable income
- Demographics: crude birth rate, crude death rate per 1,000 population
- **15 indicators** via two data sources: CPI from pipe-delimited ZIP archive, all others via PostgREST HVD API
- APIs: CPI ZIP at `https://statbel.fgov.be/sites/default/files/...CPI%20All%20base%20years.zip`; HVD at `https://opendata-api.statbel.fgov.be` (PostgREST JSON, open access, CC BY 4.0)

**Example response — `RON_EUR`:**
```json
{
  "success": true,
  "indicator": "RON_EUR",
  "name": "RON/EUR (Euro)",
  "description": "BNR reference rate, 1 EUR in RON",
  "unit": "RON",
  "frequency": "daily",
  "latest_value": 4.9768,
  "latest_period": "2026-03-31",
  "period_change": 0.0012,
  "period_change_pct": 0.0241,
  "data_points": [{"period": "2026-03-31", "value": 4.9768}, "..."],
  "total_observations": 10,
  "source": "https://www.bnr.ro/nbrfxrates10days.xml"
}
```

**Batch MCP — Multi-Country Yield Curve Comparison (New in Batch 8):**
```typescript
const yieldCurves = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'bank_of_canada_valet', params: { indicator: 'GOC_2Y' } },
      { tool: 'bank_of_canada_valet', params: { indicator: 'GOC_10Y' } },
      { tool: 'bank_of_canada_valet', params: { indicator: 'GOC_LONG' } },
      { tool: 'rba_enhanced', params: { indicator: 'F2_GOVT_2Y' } },
      { tool: 'rba_enhanced', params: { indicator: 'F2_GOVT_10Y' } },
      { tool: 'bundesbank_sdmx', params: { indicator: 'BUND_10Y' } },
      { tool: 'riksbank_sweden', params: { indicator: 'GVB_10Y' } }
    ]
  })
});
```

**Batch MCP — European CPI Comparison (New in Batch 8):**
```typescript
const cpiComparison = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ine_spain', params: { indicator: 'CPI_YOY' } },
      { tool: 'statbel_belgium', params: { indicator: 'CPI_INFLATION' } },
      { tool: 'insee_france', params: { indicator: 'CPI_YOY' } },
      { tool: 'istat_italy', params: { indicator: 'CPI_NIC' } },
      { tool: 'destatis_germany', params: { indicator: 'CPI_MONTHLY' } },
      { tool: 'nbb_belgium', params: { indicator: 'HICP_TOTAL_YOY' } },
      { tool: 'statistics_finland', params: { indicator: 'CPI_INDEX' } }
    ]
  })
});
```

**Coverage totals after Batch 8:**
- 32 government/central bank/regulatory modules
- 22 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇩🇪+ 🇯🇵+ 🇬🇧+ 🇨🇦+ 🇪🇸+ 🇳🇱+ 🇧🇪+
- 620+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD), policy rates, interbank rates, monetary aggregates, GDP, CPI/HICP/PPI, unemployment (incl. by demographics), trade, housing prices, lending rates, mortgage rates, credit growth, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves incl. full GoC curve), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets

---

## MCP Server

QuantClaw Data serves as an MCP (Model Context Protocol) server, allowing AI agents to call any data module as a tool.

### Tool Calling Pattern
```typescript
// From any client (AgentX, PICentral, etc.)
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'market_quote',
    params: { ticker: 'AAPL' }
  })
});
```

### Batch Calling
```typescript
const results = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'market_quote', params: { ticker: 'AAPL' } },
      { tool: 'technicals', params: { ticker: 'AAPL' } },
      { tool: 'ratings', params: { ticker: 'AAPL' } }
    ]
  })
});
```

### Common Tools Used by Platform

| Tool | Used By | Description |
|------|---------|-------------|
| `market_quote` | AgentX, TerminalX, PICentral | Real-time price + fundamentals |
| `technicals` | AgentX, VIP Signals | RSI, MACD, Bollinger, SMA |
| `ratings` | AgentX, PICentral | Analyst consensus + target prices |
| `alpha_picker` | AgentX | AI-generated alpha score |
| `news` | All | Latest news + sentiment |
| `smart_money` | AgentX, TerminalX | Institutional flow tracking |
| `short_interest` | TerminalX, PICentral | Short interest data |
| `earnings` | AgentX, PICentral | Earnings calendar + surprises |
| `screener` | PICentral | Multi-criteria stock screener |
| `profile` | All | Company overview + fundamentals |

---

## REST API

### Module Execution
```
GET /api/v1/{module-name}?param1=value1&param2=value2
POST /api/data?tool={module_name}&params={json}
```

### Auto-Generated Endpoints
Each of the 1,056 modules gets an auto-generated REST endpoint:
```
/api/v1/prices?ticker=AAPL
/api/v1/technicals?ticker=AAPL&indicators=rsi,macd
/api/v1/screener?min-cap=10B&sector=Technology
/api/v1/options-chain?ticker=AAPL&expiration=2026-04-17
/api/v1/fred-enhanced?series=GDP&start=2020-01-01
```

---

## Natural Language Queries (DCC)

The Data Command Center (DCC) allows natural language queries against all 1,056 modules:

### Architecture
- `src/lib/nl-query-engine.ts` — Query understanding + module routing
- `src/lib/nl-query-db.ts` — Query history + caching
- `src/lib/nl-conversations.ts` — Conversation context management
- `src/lib/schema-catalog.ts` — Module schema registry

### Example Queries
```
"What's the current price of Apple?"           → prices module
"Show me RSI and MACD for Tesla"               → technicals module
"Which stocks have insider buying this week?"   → insider_trades module
"Compare yields on 2Y vs 10Y treasuries"       → yield_curve module
"Find tech stocks with PE under 15"            → screener module
```

---

## Terminal UI

### Panel System
The terminal UI uses a draggable grid layout with multiple panel types:

| Panel | Description |
|-------|-------------|
| **ModuleBrowserPanel** | Browse and search all 1,056 modules by category |
| **DataModulePanel** | Execute a module and display results |
| **ChartPanel** | TradingView-style candlestick/line charts |
| **TickerPanel** | Real-time price ticker |
| **WatchlistPanel** | Multi-ticker watchlist |
| **NewsPanel** | Financial news feed |
| **HeatmapPanel** | Market heatmap visualization |
| **StatusPanel** | System health and API status |
| **WelcomePanel** | Onboarding + getting started |

### Command Bar
Terminal-style command input for quick module execution:
```
price AAPL
technicals TSLA --indicators rsi,macd
screen --min-cap 10B --sector Technology
```

### Access Control
- Login page with access code (default: `QuantData2026!`)
- Session-based authentication

---

## Data Sources & API Keys

| Source | Key Required | Free Tier | Data |
|--------|-------------|-----------|------|
| FRED | Yes | Unlimited | 800K+ macro time series |
| Yahoo Finance | No | — | Prices, quotes, history |
| Financial Datasets | Yes | Limited | Fundamentals, insider, filings |
| Finnhub | Yes | 60/min | Real-time quotes, IPOs |
| CoinGecko | No | 30/min | Crypto data |
| Etherscan | Yes | 5/sec | Ethereum on-chain |
| SEC EDGAR | No | 10/sec | Filings, ownership |
| Census Bureau | Yes | Unlimited | Economic indicators |
| EIA | Yes | Unlimited | Energy data |
| Polygon | Yes | 5/min | Market data, options |
| USDA NASS | Yes | Unlimited | Agriculture data |
| Alpha Vantage | Optional | 25/day | Intl stocks, forex |
| Deutsche Bundesbank | No | Open | German yields, ECB rates, monetary aggregates |
| INSEE France | No | 30/min | French GDP, CPI, unemployment, trade |
| Banque de France | Yes (free) | Open | EUR FX rates, credit, BoP, business climate |
| ISTAT Italy | No | 5/min | Italian GDP, CPI, unemployment, industry |
| CBS Netherlands | No | Open | Dutch GDP, CPI, housing, trade, govt finance |
| Statistics Denmark | No | Open | Danish GDP, CPI, labour, trade, housing |
| SCB Sweden | No | Open | Swedish GDP, CPI/CPIF, labour, trade |
| Sveriges Riksbank | No | Rate-limited | SEK FX, policy rates, govt bond yields |
| Banco de España | No | Open | Euribor, lending rates, BoP, housing prices |
| Banco de Portugal (BPstat) | No | Open | MFI interest rates, BoP, FX rates, banking FSIs |
| ONS UK (CMD beta) | No | Open (beta) | UK GDP, CPIH, retail sales, trade, labour market |
| Statistics Canada (WDS) | No | 25 req/s per IP | Canadian GDP, CPI, labour, trade, housing |
| e-Stat Japan | Yes (free) | Open | Japanese GDP, CPI, unemployment, trade, industry |
| NBP Poland | No | Open (no limit) | PLN FX rates (32+ currencies), bid/ask spreads, gold price |
| CBC Taiwan | No | Open | TWD/USD FX rates, CBC policy rates, monetary aggregates, bank rates |
| NBB Belgium (NBB.Stat) | No | Open (Origin hdr) | Belgian BoP, HICP, financial accounts, IIP, govt finance, M1/M3, business surveys |
| Central Bank of Ireland | No | Open (CC-BY-4.0) | ECB/Euribor rates, Irish retail lending/deposit rates, mortgages, national debt, reserves |
| CSO Ireland (PxStat) | No | Open | Irish GDP/GNP, CPI, unemployment, retail sales, housing prices, trade |
| Statistics Finland | No | Open | Finnish GDP, CPI, unemployment, industrial output, trade, housing prices |
| Danmarks Nationalbank | No | Open | DN policy rates, DKK FX, govt bond yields, BoP, MFI lending, govt securities |
| Czech National Bank (CNB) | No (ARAD: free key) | Open | CZK FX fixing (12 currencies), PRIBOR interbank rates (7 tenors), CNB policy rates (2W repo, discount, Lombard) |
| ABS Australia (SDMX) | No | Open | GDP, CPI, labour force, BoP, retail trade, building approvals, trade |
| CBUAE / World Bank (UAE) | No | Open | AED FX rates (76 currencies), UAE GDP, CPI, M2, reserves, trade |
| Destatis GENESIS (Germany) | Yes (free) | Open | German GDP, CPI/HICP, employment, trade, IPI, PPI, construction |
| EDINET Japan (FSA) | Yes (free) | Open | Japanese securities filings, annual/quarterly reports, shareholding, M&A |
| FCA UK Register | Yes (free) | Open | UK authorized firms, individuals, permissions, disciplinary, regulated markets |
| RBA Australia (CSV) | No | Open | RBA cash rate, money market, AU govt bond yields, lending rates, AUD FX/TWI, international official rates, credit growth, M3, GDP |
| Bank of Canada (Valet) | No | Open | BoC overnight/bank rate, CORRA, GoC bond yields (2Y–30Y), T-bills, 26 FX pairs, prime/mortgage/GIC rates, yield volatility, term premiums, BCPI, BOS |
| INE Spain (Tempus3) | No | Open | Spanish GDP, CPI, EPA unemployment (total+youth), IPI, housing prices, trade (exports/imports) |
| DNB Netherlands (APIM) | Optional (fallback key) | Open | Dutch FSIs, banking structure, insurance/pension balance sheets, payments, monetary aggregates, household rates |
| BNR Romania (XML) | No | Open | RON FX rates for 37 currencies + gold + SDR, daily & 10-day history |
| Statbel Belgium (PostgREST) | No | Open (CC BY 4.0) | Belgian CPI/health index, HICP by COICOP, unemployment by demographics, retail turnover, Gini, birth/death rates |

---

## Caching Layer

```
cache/
├── {module_name}/
│   └── {cache_key}.json    # Module-level file cache
├── .cache/
│   └── alpha_picker/
│       └── yfinance_cache.db  # SQLite cache for yfinance
```

- Each module implements its own caching strategy
- Default TTL varies by data type (1 min for prices, 24h for fundamentals)
- Cache invalidation on module re-execution with `force=true`

---

## Development Phases

47 phases completed across 9 categories:

| Phase Range | Category | Highlights |
|-------------|----------|------------|
| 1–4 | Foundation | Prices, options, sentiment, multi-asset, screener |
| 5–10 | Intelligence & Infra | NLP, options flow, factor models, portfolio analytics, backtesting, alerts |
| 11–16 | Alt Data & Fixed Income | Patents, jobs, supply chain, weather, bonds, SEC NLP |
| 17–20 | Events & ESG | IPO/SPAC, M&A, activist, ESG scoring |
| 21–25 | Quant & Streaming | Factor Zoo (400+ factors), microstructure, AI reports, data quality, WebSocket |
| 26–30 | ML & Advanced | ML earnings predictor, correlation regime detection, GEX, 13F replication, dark pool |
| 31–40 | Sector-Specific | Real estate, energy, shipping, climate, demographics, healthcare, agriculture |
| 41–47 | Global & Specialized | APAC data (BOJ, BOK, NBS), Israel CBS, Euro, central banks, EM, nuclear |

---

## Project Structure

```
quantclaw-data/
├── modules/                          # 1,056 Python data modules
│   ├── prices.py                     # Stock prices (Yahoo Finance)
│   ├── technicals.py                 # Technical analysis indicators
│   ├── alpha_picker.py               # AI alpha scoring
│   ├── options_chain.py              # Options data
│   ├── fred_enhanced.py              # FRED macro data
│   ├── congress_trades.py            # Congressional trading
│   ├── insider_trades.py             # Insider buying/selling
│   ├── bundesbank_sdmx.py            # Deutsche Bundesbank (SDMX)
│   ├── insee_france.py               # INSEE France macro statistics
│   ├── banque_de_france.py           # Banque de France Webstat
│   ├── istat_italy.py                # ISTAT Italy statistics
│   ├── cbs_netherlands.py            # CBS Netherlands StatLine
│   ├── statistics_denmark.py         # Statistics Denmark (DST)
│   ├── scb_sweden.py                 # SCB Sweden (Statistics Sweden)
│   ├── riksbank_sweden.py            # Sveriges Riksbank
│   ├── banco_de_espana.py            # Banco de España
│   ├── banco_de_portugal.py          # Banco de Portugal (BPstat)
│   ├── ons_uk.py                     # UK Office for National Statistics
│   ├── statcan_canada.py             # Statistics Canada (WDS)
│   ├── estat_japan.py                # e-Stat Japan (Government Statistics)
│   ├── nbp_poland.py                 # National Bank of Poland (FX, gold)
│   ├── cbc_taiwan.py                 # CBC Taiwan (FX, rates, monetary)
│   ├── nbb_belgium.py                # NBB Belgium (BoP, HICP, govt, surveys)
│   ├── central_bank_ireland.py       # CBI Ireland (ECB rates, mortgages, debt)
│   ├── cso_ireland.py                # CSO Ireland (GDP, CPI, labour, trade)
│   ├── statistics_finland.py         # Statistics Finland (GDP, CPI, industry)
│   ├── danmarks_nationalbank.py      # Danmarks Nationalbank (rates, FX, bonds)
│   ├── cnb_czech.py                 # Czech National Bank (FX, PRIBOR, policy rates)
│   ├── abs_australia_sdmx.py        # ABS Australia (GDP, CPI, labour, trade)
│   ├── uae_data.py                  # UAE CBUAE FX + World Bank macro
│   ├── destatis_germany.py          # Destatis GENESIS-Online (GDP, CPI, trade)
│   ├── edinet_japan.py              # EDINET Japan securities filings
│   ├── fca_uk.py                    # FCA UK Financial Services Register
│   ├── rba_enhanced.py              # Reserve Bank of Australia (7 statistical tables)
│   ├── bank_of_canada_valet.py      # Bank of Canada Valet (yields, FX, rates)
│   ├── ine_spain.py                 # INE Spain (GDP, CPI, labour, housing, trade)
│   ├── dnb_netherlands.py           # DNB Netherlands (FSI, banking, payments, monetary)
│   ├── bnr_romania.py               # BNR Romania (37-currency FX + gold + SDR)
│   ├── statbel_belgium.py           # Statbel Belgium (CPI, HICP, unemployment, demographics)
│   ├── ... (1,056 modules total)
│   └── zillow_zhvi.py               # Zillow home values
├── src/
│   ├── app/
│   │   ├── page.tsx                  # Main terminal UI
│   │   ├── layout.tsx                # Root layout
│   │   ├── globals.css               # Terminal dark theme
│   │   ├── terminal-theme.css        # Terminal-specific styles
│   │   ├── login/page.tsx            # Access code login
│   │   ├── tutorial/page.tsx         # Getting started guide
│   │   ├── services.ts              # Service/module catalog
│   │   ├── roadmap.ts               # 47 development phases
│   │   ├── install.ts               # Module dependency installer
│   │   └── dcc/                     # Data Command Center
│   │       ├── page.tsx             # DCC view
│   │       ├── layout.tsx           # DCC layout
│   │       └── nl-query-view.tsx    # Natural language query UI
│   ├── components/
│   │   ├── panels/
│   │   │   ├── ChartPanel.tsx       # TradingView-style charts
│   │   │   ├── DataModulePanel.tsx  # Module execution panel
│   │   │   ├── HeatmapPanel.tsx     # Market heatmap
│   │   │   ├── ModuleBrowserPanel.tsx # Module catalog browser
│   │   │   ├── NewsPanel.tsx        # News feed
│   │   │   ├── StatusPanel.tsx      # System status
│   │   │   ├── TickerPanel.tsx      # Price ticker
│   │   │   ├── WatchlistPanel.tsx   # Watchlist
│   │   │   └── WelcomePanel.tsx     # Welcome/onboarding
│   │   └── terminal/
│   │       ├── CommandBar.tsx       # Terminal command input
│   │       ├── Panel.tsx            # Base panel component
│   │       └── TerminalGrid.tsx     # Draggable grid layout
│   ├── lib/
│   │   ├── db.ts                    # PostgreSQL client
│   │   ├── nl-query-engine.ts       # NL query engine
│   │   ├── nl-query-db.ts          # Query history DB
│   │   ├── nl-conversations.ts     # Conversation context
│   │   ├── schema-catalog.ts       # Module schema registry
│   │   └── sapi-db.ts              # Structured API database
│   ├── store/
│   │   ├── terminal-store.ts       # Terminal UI state
│   │   └── dcc-store.ts           # DCC state
│   └── middleware.ts               # Auth + security
├── cache/                           # Module response cache
├── backups_api_migration/           # Migration backups
├── .env.example
├── .github/workflows/
│   ├── ci.yml
│   └── weekly-test.yml
├── DSL_QUICK_REFERENCE.md
├── API_KEYS_QUICKSTART.md
├── package.json
└── tsconfig.json
```

---

## Environment Variables

```bash
# API Keys (most have free tiers)
FRED_API_KEY=                        # Federal Reserve Economic Data
EIA_API_KEY=                         # Energy Information Administration
CENSUS_API_KEY=                      # US Census Bureau
FINANCIAL_DATASETS_API_KEY=          # Financial Datasets (fundamentals)
FINNHUB_API_KEY=                     # Finnhub (real-time quotes)
ETHERSCAN_API_KEY=                   # Etherscan (Ethereum data)
POLYGON_API_KEY=                     # Polygon.io (market data)
USDA_NASS_API_KEY=                   # USDA agriculture data

# Optional
ALPHA_VANTAGE_API_KEY=               # International stocks
FMP_API_KEY=                         # Financial Modeling Prep
BOK_API_KEY=                         # Bank of Korea
COMTRADE_API_KEY=                    # UN trade data
BANQUE_DE_FRANCE_API_KEY=            # Banque de France Webstat (free registration)
ESTAT_JAPAN_APP_ID=                  # e-Stat Japan (free at https://www.e-stat.go.jp/api/)
ARAD_API_KEY=                        # CNB Czech ARAD API (free at https://www.cnb.cz/aradb/)
DESTATIS_USER=                       # Destatis GENESIS-Online (free at https://www-genesis.destatis.de)
DESTATIS_PASSWORD=                   # Destatis GENESIS-Online password
EDINET_API_KEY=                      # EDINET Japan filings (free at https://disclosure.edinet-fsa.go.jp)
FCA_API_KEY=                         # FCA UK Register (free at https://register.fca.org.uk/Developer/s/)
FCA_API_EMAIL=                       # FCA UK Register signup email
DNB_SUBSCRIPTION_KEY=                # DNB Netherlands Statistics (optional, public fallback available)

# App
ACCESS_CODE=QuantData2026!           # Login access code
DATABASE_URL=                        # PostgreSQL connection
```

---

## Getting Started

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (for data modules)
pip install -r requirements.txt  # or per-module as needed

# Copy environment
cp .env.example .env
# Fill in API keys (most have free tiers)

# Start development server
npm run dev
# → http://localhost:3055

# Build for production
npm run build
npm run start
```

---

## Deployment

- **Server:** Hostinger VPS (76.13.147.35), 8 vCPU
- **Process:** PM2 (`quantclaw-data`)
- **Nginx:** SSL, reverse proxy → port 3055
- **DNS:** Cloudflare → data.quantclaw.org
- **CI:** GitHub Actions + weekly automated tests

```bash
cd /home/quant/apps/quantclaw-data
git pull
npm install
NODE_OPTIONS="--max-old-space-size=2048" npm run build
pm2 restart quantclaw-data
```

*1,056 modules • 47 phases • 22 countries (11 EU + UK + Canada + Japan + Poland + Taiwan + Ireland + Czech Republic + Australia + UAE + Romania) • 32 government/central bank modules • 620+ macro indicators • The data layer powering the MoneyClawX ecosystem*
