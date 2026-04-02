# QuantClaw Data — 1,080 Financial Data Modules

> The world's most comprehensive open financial data platform.
> 1,080 Python modules • MCP server • REST API • Natural Language Query • Terminal UI

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

QuantClaw Data is a massive financial data aggregation platform that unifies 1,080 Python data modules behind a single API. It provides real-time and historical data across equities, options, fixed income, crypto, commodities, forex, macro, alternative data, and quantitative analytics. The platform serves as the data backbone for the entire MoneyClawX ecosystem (AgentX, TerminalX, PICentral, VIP Signals).

**Key numbers:**
- **1,080** Python data modules
- **9** data categories (Core Market, Derivatives, Alt Data, Multi-Asset, Quant, Fixed Income, Events, Intelligence, Infrastructure)
- **49** completed development phases
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
│  ├── Module browser (1,080 modules)             │
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
│  ├── Tool definitions for all 1,080 modules      │
│  ├── AI agent interface (AgentX, PICentral)      │
│  └── callTool(), batchCall() patterns            │
├─────────────────────────────────────────────────┤
│  1,080 Python Modules                            │
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

### Government Statistics, Central Banks, International Institutions & Alt-Data (Autobuilder Batches 1–16)

Fifty-six modules covering 39 countries plus EU-wide and global data (190+ IMF member nations, 38 OECD members) across Western Europe, Scandinavia, Central Europe, Alpine, Baltic, British Isles, Southeast Europe, Balkans, Mediterranean, North America, Central America, South America, Asia-Pacific, Southeast Asia, Middle East, Oceania, and international institutions with 1,020+ macroeconomic, geopolitical, patent, seismic, and entity-registry indicators from official government statistical offices, central banks, international institutions, financial regulators, global event databases, patent offices, and scientific agencies:

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
|| `statistics_austria` | Statistik Austria (OGD) | Austria | `https://data.statistik.gv.at` | GDP (nominal quarterly/annual, real quarterly), CPI (2015=100), PPI (2021=100), wholesale price index, employed/unemployed persons, total imports/exports, tourism overnight stays & turnover index, new car registrations, industrial production index, construction production index, household consumption, gross fixed capital formation |
|| `czso_czech` | CZSO (Czech Statistical Office) | Czech Republic | `https://vdb.czso.cz/pll/eweb` | GDP (nominal/real/YoY growth), GVA, GFCF, CPI (YoY/MoM/index 2015=100, food, housing, transport), unemployment & employment rates, employed/unemployed persons, IPI total & automotive, construction output index, foreign trade (exports/imports/balance CZK mn) |
|| `statistics_estonia` | Statistics Estonia (PxWeb) | Estonia | `https://andmed.stat.ee/api/v1/en/stat` | GDP (nominal quarterly/real YoY growth), CPI (annual/monthly YoY), HICP annual, employment & unemployment rates (15-74), labour force, exports & imports of goods & services, industrial production index (2021=100) & YoY |
|| `ecb_enhanced` | European Central Bank (SDMX) | Euro Area (EA20) | `https://data-api.ecb.europa.eu/service` | M1/M2/M3 monetary aggregates (EUR mn), MFI loans to households/NFCs/housing, composite cost of borrowing (NFC & HH housing), NFC new loan rates (short/long), HH deposit rate, HICP headline/core/food annual rates |
|| `eurostat_enhanced` | Eurostat (JSON-stat 2.0) | EU27 + Members | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data` | Gov deficit/surplus & debt (% GDP), gov expenditure & revenue, energy production/consumption/dependency, renewable energy share (total/electricity/transport/heating), GHG emissions (total/energy/industry/transport/agriculture), environmental taxes (total/energy/transport), digital economy (internet access/use/e-commerce) |
|| `bis_enhanced` | BIS (Bank for International Settlements) | Global / 60+ countries | `https://stats.bis.org/api/v2` | OTC derivatives outstanding (total notional/swaps/GMV/NFC counterparties), exchange-traded derivatives OI (FX/IR/equity/commodity) & turnover, FX spot & OTC IR derivatives turnover (triennial), international debt securities (US/GB/JP/CN/DE), CPMI cashless payments, CPMI macro indicators |
|| `imf_enhanced` | IMF (5 Databases: FAS, FSI, CPIS, CDIS, GFS) | Global / 190+ countries | `https://api.db.nomics.world/v22` | Financial Access Survey (ATMs, branches, deposit accounts, mobile money per capita), Financial Soundness Indicators (NPL ratio, regulatory capital, CET1, ROA, ROE), Coordinated Portfolio Investment Survey (total/equity/debt assets), Coordinated Direct Investment Survey (inward/outward FDI equity & debt), Government Finance Statistics (revenue, expense, tax, expenditure, social benefits, interest, investment, liabilities) |
|| `oecd_enhanced` | OECD (5 Dataflows: CLI, KEI, REV, PAG, MSTI) | 38 OECD members + partners | `https://sdmx.oecd.org/public/rest/data` | Composite Leading Indicators (USA/GBR/DEU/JPN/FRA/OECD), Business & Consumer Confidence (BCI/CCI), Key Economic Indicators (unemployment/CPI YoY/GDP/short-term & long-term interest rates), Revenue Statistics (total tax/income tax/corporate tax/SSC/goods & services as % GDP for USA/GBR/DEU), Pensions at a Glance (gross replacement rates, life expectancy, employment rates), Main Science & Technology Indicators (GERD/BERD/HERD R&D expenditure) |
|| `boe_iadb_enhanced` | Bank of England (IADB) | United Kingdom | `https://www.bankofengland.co.uk/boeapps/iadb` | Gilt zero-coupon yields (5Y/10Y/20Y nominal + 3M moving averages), Bank Rate, M4 outstanding & lending (12M/1M/3M growth rates), mortgage SVR, consumer credit (excl. cards total & flow + 1M growth), GBP FX crosses (USD/EUR/JPY/CHF), Sterling Effective Exchange Rate (EER narrow & broad) |
|| `mnb_hungary` | Magyar Nemzeti Bank (MNB) | Hungary | `http://www.mnb.hu/arfolyamok.asmx` | MNB base rate (policy rate history), HUF FX crosses (EUR/USD/GBP/CHF/JPY/CZK/PLN/RON/SEK/CNY/TRY/CAD), CEE equal-weight basket (CZK+PLN+RON+HUF vs EUR), G4 basket (USD+EUR+GBP+JPY vs HUF) |
|| `eu_small_central_banks` | 9 EU Central Banks + ECB SDMX | BG, HR, CY, LV, LT, LU, MT, SK, SI | ECB: `https://data-api.ecb.europa.eu/service/data` + national APIs | HICP annual inflation for all 9 countries, MFI lending & deposit rates (household) for all 9, FX rates (EUR/USD/GBP/CHF) for BG/HR/LT/SK/SI from national central banks (BNB/HNB/Lietuvos bankas/NBS/BSI), Slovenia extras (domestic & EU inflation, ECB deposit/refi/marginal rates) |
|| `eu_small_statistics` | Eurostat (batch for 12 smaller EU NSOs) | BG, HR, CY, EL, HU, LV, LT, LU, MT, RO, SK, SI | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data` | GDP (nominal/real/growth/per capita), CPI (overall YoY/food/energy/index level), unemployment rate (total + youth), employment rate, government debt & deficit (% GDP), GVA manufacturing, current account balance — all filterable by country |
|| `ine_portugal` | INE (Instituto Nacional de Estatística) | Portugal | `https://www.ine.pt/ine/json_indicador/pindica.jsp` | GDP real growth YoY, GDP nominal, GDP per capita growth, CPI YoY, CPI index (2025=100), HICP YoY, unemployment rate, employed population, activity rate, tourism overnight stays, exports/imports of goods, trade coverage rate, construction cost index, construction cost YoY |
|| `ibge_brazil` | IBGE (Instituto Brasileiro de Geografia e Estatística) | Brazil | `https://servicodados.ibge.gov.br/api/v3/agregados` | GDP YoY/QoQ growth, IPCA monthly/12M cumulative/YTD/index (Dec 1993=100), PNAD unemployment rate, PIM-PF industrial production index (2022=100), PMC broad retail sales YoY |
|| `gdelt_global_events` | GDELT Project (Global Database of Events) | Global (100+ languages) | `https://api.gdeltproject.org/api/v2/doc/doc` | Protest/military/terror/armed conflict volume & sentiment, inflation/interest rate/trade/stock market/bankruptcy media coverage, sanctions media volume, country risk scores, bilateral tension scores, topic sentiment, article search |
|| `patentsview_uspto` | USPTO Open Data Portal (PatentsView) | United States | `https://api.uspto.gov/api/v1` | Patent application search, patent grants by assignee (ticker-to-company mapping for 35+ tickers), top assignees ranking, technology trends by CPC class (22 named classes incl. AI/ML, semiconductors, pharma), single patent detail |
|| `inegi_mexico` | INEGI (Banco de Información Económica) | Mexico | `https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR` | GDP quarterly growth, CPI headline inflation, core inflation (ex food & energy), unemployment rate, industrial production index, exports/imports of goods, consumer confidence index, automotive production volume |
|| `gleif_lei` | GLEIF (Global LEI Foundation) | Global (100+ jurisdictions) | `https://api.gleif.org/api/v1` | Total active/lapsed LEIs, entity counts by country (US/GB/DE/JP/FR/CN/CA/LU), entity search, LEI lookup, corporate hierarchy traversal |
|| `bank_of_thailand` | Bank of Thailand (BOT) | Thailand | `https://gateway.api.bot.or.th` | BOT policy rate, BIBOR (1W/3M/6M/1Y), govt bond yields (1Y/5Y/10Y/20Y), GDP (real/nominal), CPI (headline/core YoY), current account, international reserves, THB FX, monetary aggregates (M1/broad), commercial bank balance sheet (assets/loans/deposits/LDR) |
|| `dane_colombia` | DANE (Departamento Nacional de Estadística) | Colombia | `https://sdmx.dane.gov.co/gateway/rest` | GDP production approach (COP bn), CPI index, unemployment rate (GEIH), industrial production (EMM), trade balance (USD mn), PPI, annual manufacturing survey |
|| `epo_ops` | European Patent Office (OPS) | Global (100+ patent authorities) | `https://ops.epo.org/3.2/rest-services` | Patent full-text search, applicant/company filings, patent family members, EP register status, IPC technology filing trends, recent EP grants |
|| `usgs_earthquake` | USGS Earthquake Hazards Program | Global + regional hotspots | `https://earthquake.usgs.gov/fdsnws/event/1` | Significant global events (M5+), recent M4+ worldwide, PAGER alerts, regional hotspots (Taiwan/Japan/Chile/Turkey/California), annual M5+ count, DYFI felt reports |
|| `kosis_korea` | KOSIS — Statistics Korea (KOSTAT) | South Korea | `https://kosis.kr/openapi/Param/statisticsParameterData.do` | GDP by expenditure (quarterly), CPI all items (2020=100), unemployment rate, industrial production index, merchandise exports, housing price index, semiconductor production index |
|| `ssb_norway` | Statistics Norway (SSB) | Norway | `https://data.ssb.no/api/v0/en/table` | GDP (nominal/volume growth), CPI (index 2015=100/12-month rate), unemployment rate (SA), goods exports/imports, house price index (raw/SA), petroleum deliveries, industrial output, gross value added |

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
🇦🇹 Austria          — Statistik Austria (GDP nom/real, CPI, PPI, wholesale prices, employment, trade, tourism, industry, construction, investment)
🇨🇿 Czech Rep. (ext) — CZSO (GDP/GVA/GFCF, CPI by component, labour market, IPI incl. automotive, construction, foreign trade)
🇪🇪 Estonia          — Statistics Estonia (GDP, CPI/HICP, employment/unemployment, labour force, trade, industrial production)
🇪🇺 Euro Area        — ECB Enhanced (M1/M2/M3 monetary aggregates, MFI credit, cost of borrowing, HICP headline/core/food)
🇪🇺 EU27             — Eurostat Enhanced (govt deficit/debt, energy balances, renewables, GHG emissions, env taxes, digital economy)
🌍 Global            — BIS Enhanced (OTC/exchange-traded derivatives, FX turnover, international debt securities, cashless payments)
🌐 190+ Countries    — IMF Enhanced (financial access, banking soundness, portfolio/FDI investment, government finance)
🇭🇺 Hungary          — MNB (base rate, HUF FX crosses, CEE/G4 baskets)
🇬🇧 UK (ext)         — BoE IADB (gilt yields, Bank Rate, M4/lending, mortgage SVR, consumer credit, GBP FX, sterling EER)
🇧🇬 Bulgaria         — ECB SDMX + BNB (HICP, MFI rates, FX USD/GBP/CHF)
🇭🇷 Croatia          — ECB SDMX + HNB (HICP, MFI rates, FX USD/GBP/CHF)
🇨🇾 Cyprus           — ECB SDMX (HICP, MFI lending & deposit rates)
🇱🇻 Latvia           — ECB SDMX (HICP, MFI lending & deposit rates)
🇱🇹 Lithuania        — ECB SDMX + Lietuvos bankas (HICP, MFI rates, FX)
🇱🇺 Luxembourg       — ECB SDMX (HICP, MFI lending & deposit rates)
🇲🇹 Malta            — ECB SDMX (HICP, MFI lending & deposit rates)
🇸🇰 Slovakia         — ECB SDMX + NBS (HICP, MFI rates, FX USD/GBP/CHF)
🇸🇮 Slovenia         — ECB SDMX + BSI (HICP, MFI rates, FX, domestic/EU inflation, ECB policy rates)
🇬🇷 Greece           — Eurostat batch (GDP, CPI, unemployment, govt finance, trade)
🌍 OECD (38 members) — OECD Enhanced (CLI, BCI/CCI, KEI, tax revenue, pensions, R&D/MSTI)
🇵🇹 Portugal (ext)    — INE Statistics (GDP real/nominal/per capita, CPI/HICP, unemployment, tourism, trade, construction)
🇧🇷 Brazil            — IBGE SIDRA (GDP YoY/QoQ, IPCA inflation, PNAD unemployment, PIM-PF industry, PMC retail)
🌐 Global (events)    — GDELT (protest/military/terror/conflict/economic media volume & sentiment, country risk, bilateral tension)
🇺🇸 US (patents)      — USPTO PatentsView (patent search, assignee filings, CPC tech trends, innovation intelligence)
🇲🇽 Mexico            — INEGI BIE (GDP quarterly, CPI, core inflation, unemployment, industrial production, trade, consumer confidence, auto production)
🌐 Global (LEI)       — GLEIF LEI Registry (active/lapsed entity counts, search, lookup, hierarchy — 100+ jurisdictions)
🇹🇭 Thailand          — Bank of Thailand (policy rate, BIBOR, govt bonds, GDP, CPI, BoP, reserves, THB FX, monetary aggregates, banking)
🇨🇴 Colombia          — DANE SDMX (GDP, CPI, unemployment, industrial production, trade, PPI, manufacturing survey)
🌐 Global (patents)   — EPO Open Patent Services (patent search, family members, EP register, IPC trends, recent grants — 100+ authorities)
🌐 Global (seismic)   — USGS Earthquake Hazards (significant events M5+, PAGER alerts, regional hotspots, felt reports — real-time 5min cache)
🇰🇷 South Korea       — KOSIS Statistics Korea (GDP, CPI, unemployment, industrial production, exports, housing prices, semiconductor index)
🇳🇴 Norway            — SSB Statistics Norway (GDP nom/growth, CPI index/12mo rate, unemployment SA, trade exports/imports, house prices, petroleum deliveries, industrial output, GVA)
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
# Austria (Batch 9)
python3 modules/statistics_austria.py GDP_NOMINAL_Q
python3 modules/statistics_austria.py GDP_REAL_Q
python3 modules/statistics_austria.py CPI
python3 modules/statistics_austria.py PRODUCER_PRICE_INDEX
python3 modules/statistics_austria.py EMPLOYED
python3 modules/statistics_austria.py EXPORTS_TOTAL
python3 modules/statistics_austria.py OVERNIGHT_STAYS
python3 modules/statistics_austria.py INDUSTRIAL_PRODUCTION_INDEX
python3 modules/statistics_austria.py list
python3 modules/statistics_austria.py catalog
# Czech Republic Extended, Estonia, ECB, Eurostat, BIS (Batch 10)
python3 modules/czso_czech.py GDP_NOMINAL
python3 modules/czso_czech.py CPI_YOY
python3 modules/czso_czech.py UNEMPLOYMENT_RATE
python3 modules/czso_czech.py IPI_TOTAL
python3 modules/czso_czech.py TRADE_BALANCE
python3 modules/statistics_estonia.py GDP_REAL_GROWTH
python3 modules/statistics_estonia.py CPI_MONTHLY
python3 modules/statistics_estonia.py UNEMPLOYMENT_RATE
python3 modules/statistics_estonia.py EXPORTS
python3 modules/statistics_estonia.py INDUSTRIAL_PRODUCTION_INDEX
python3 modules/ecb_enhanced.py M3_OUTSTANDING
python3 modules/ecb_enhanced.py LOANS_HH
python3 modules/ecb_enhanced.py HICP_HEADLINE
python3 modules/ecb_enhanced.py CCOB_NFC
python3 modules/ecb_enhanced.py monetary
python3 modules/eurostat_enhanced.py GOV_DEBT DE
python3 modules/eurostat_enhanced.py RENEWABLE_SHARE_TOTAL FR
python3 modules/eurostat_enhanced.py GHG_TOTAL DE
python3 modules/eurostat_enhanced.py compare GOV_DEBT
python3 modules/bis_enhanced.py OTC_NOTIONAL_TOTAL
python3 modules/bis_enhanced.py XTD_OI_IR
python3 modules/bis_enhanced.py DEBT_SEC_US
python3 modules/bis_enhanced.py derivatives
python3 modules/bis_enhanced.py debt-securities
# IMF Enhanced — 5 databases, 190+ countries (Batch 11)
python3 modules/imf_enhanced.py FSI_NPL_RATIO US
python3 modules/imf_enhanced.py FSI_CET1_RATIO DE
python3 modules/imf_enhanced.py FSI_ROE JP
python3 modules/imf_enhanced.py FAS_ATMS_PER_100K IN
python3 modules/imf_enhanced.py FAS_MOBILE_MONEY_ACTIVE KE
python3 modules/imf_enhanced.py CPIS_TOTAL_ASSETS US
python3 modules/imf_enhanced.py CDIS_INWARD_EQUITY GB
python3 modules/imf_enhanced.py GFS_REVENUE US
python3 modules/imf_enhanced.py GFS_EXPENSE DE
python3 modules/imf_enhanced.py fsi US
python3 modules/imf_enhanced.py fas BR
python3 modules/imf_enhanced.py gfs JP
python3 modules/imf_enhanced.py banking-health CN
python3 modules/imf_enhanced.py access NG
python3 modules/imf_enhanced.py list
# OECD Enhanced — 38 OECD members, CLI/KEI/tax/pensions/R&D (Batch 12)
python3 modules/oecd_enhanced.py CLI_USA
python3 modules/oecd_enhanced.py CLI_DEU
python3 modules/oecd_enhanced.py BCI_USA
python3 modules/oecd_enhanced.py KEI_GDP_USA
python3 modules/oecd_enhanced.py TAX_TOTAL_USA
python3 modules/oecd_enhanced.py PENSION_GRR_USA
python3 modules/oecd_enhanced.py RD_GERD_USA
python3 modules/oecd_enhanced.py list
# Bank of England IADB Enhanced (Batch 12)
python3 modules/boe_iadb_enhanced.py BANK_RATE
python3 modules/boe_iadb_enhanced.py GILT_NZC_10Y
python3 modules/boe_iadb_enhanced.py M4_OUTSTANDING
python3 modules/boe_iadb_enhanced.py GBP_USD
python3 modules/boe_iadb_enhanced.py STERLING_EER
python3 modules/boe_iadb_enhanced.py MORTGAGE_SVR
python3 modules/boe_iadb_enhanced.py CONSUMER_CREDIT_EXCL_CARD
# MNB Hungary (Batch 12)
python3 modules/mnb_hungary.py MNB_BASE_RATE
python3 modules/mnb_hungary.py FX_EUR_HUF
python3 modules/mnb_hungary.py FX_USD_HUF
python3 modules/mnb_hungary.py FX_CEE_BASKET
python3 modules/mnb_hungary.py FX_G4_BASKET
# EU Small Central Banks — 9 countries (Batch 12)
python3 modules/eu_small_central_banks.py BG_HICP
python3 modules/eu_small_central_banks.py HR_HICP
python3 modules/eu_small_central_banks.py SI_INFLATION_DOMESTIC
python3 modules/eu_small_central_banks.py BG_FX_USD
python3 modules/eu_small_central_banks.py SK_LENDING_RATE_HH
python3 modules/eu_small_central_banks.py list
# EU Small Statistics — 12 countries (Batch 12)
python3 modules/eu_small_statistics.py GDP_NOMINAL BG
python3 modules/eu_small_statistics.py CPI_YOY HU
python3 modules/eu_small_statistics.py UNEMPLOYMENT_RATE EL
python3 modules/eu_small_statistics.py GOV_DEBT HR
python3 modules/eu_small_statistics.py CURRENT_ACCOUNT LT
python3 modules/eu_small_statistics.py list
# INE Portugal — National Statistics (Batch 13)
python3 modules/ine_portugal.py GDP_GROWTH_YOY
python3 modules/ine_portugal.py CPI_YOY
python3 modules/ine_portugal.py HICP_YOY
python3 modules/ine_portugal.py UNEMPLOYMENT_RATE
python3 modules/ine_portugal.py TOURISM_OVERNIGHT_STAYS
python3 modules/ine_portugal.py EXPORTS
python3 modules/ine_portugal.py CONSTRUCTION_COST_INDEX
python3 modules/ine_portugal.py list
# IBGE Brazil — SIDRA Macro (Batch 13)
python3 modules/ibge_brazil.py GDP_YOY
python3 modules/ibge_brazil.py GDP_QOQ
python3 modules/ibge_brazil.py IPCA_MONTHLY
python3 modules/ibge_brazil.py IPCA_12M
python3 modules/ibge_brazil.py UNEMPLOYMENT
python3 modules/ibge_brazil.py INDUSTRIAL_PRODUCTION
python3 modules/ibge_brazil.py RETAIL_SALES
python3 modules/ibge_brazil.py gdp
python3 modules/ibge_brazil.py ipca
# GDELT Global Events — Geopolitical Risk (Batch 13)
python3 modules/gdelt_global_events.py PROTEST_ACTIVITY_GLOBAL
python3 modules/gdelt_global_events.py MILITARY_ACTIVITY_GLOBAL
python3 modules/gdelt_global_events.py INFLATION_MEDIA_VOL
python3 modules/gdelt_global_events.py STOCKMARKET_SENTIMENT
python3 modules/gdelt_global_events.py SANCTIONS_MEDIA_VOL
python3 modules/gdelt_global_events.py country_risk US
python3 modules/gdelt_global_events.py country_risk CN
python3 modules/gdelt_global_events.py tension US CN
python3 modules/gdelt_global_events.py topic "central bank"
python3 modules/gdelt_global_events.py articles "semiconductor tariff"
python3 modules/gdelt_global_events.py list
# USPTO PatentsView — Patent Innovation (Batch 13)
python3 modules/patentsview_uspto.py search "artificial intelligence"
python3 modules/patentsview_uspto.py patent_grants_by_assignee AAPL
python3 modules/patentsview_uspto.py patent_grants_by_assignee NVDA
python3 modules/patentsview_uspto.py tech_trends G06N
python3 modules/patentsview_uspto.py tech_trends H01L
python3 modules/patentsview_uspto.py top_assignees
python3 modules/patentsview_uspto.py detail 18123456
python3 modules/patentsview_uspto.py tickers
python3 modules/patentsview_uspto.py cpc_classes
python3 modules/patentsview_uspto.py list
# Mexico — INEGI National Statistics (Batch 14)
python3 modules/inegi_mexico.py GDP_QUARTERLY
python3 modules/inegi_mexico.py CPI
python3 modules/inegi_mexico.py CORE_INFLATION
python3 modules/inegi_mexico.py UNEMPLOYMENT
python3 modules/inegi_mexico.py INDUSTRIAL_PRODUCTION
python3 modules/inegi_mexico.py EXPORTS
python3 modules/inegi_mexico.py IMPORTS
python3 modules/inegi_mexico.py CONSUMER_CONFIDENCE
python3 modules/inegi_mexico.py AUTO_PRODUCTION
python3 modules/inegi_mexico.py list
# GLEIF LEI Registry — Global Entity Data (Batch 15)
python3 modules/gleif_lei.py TOTAL_ACTIVE
python3 modules/gleif_lei.py US_ENTITIES
python3 modules/gleif_lei.py DE_ENTITIES
python3 modules/gleif_lei.py JP_ENTITIES
python3 modules/gleif_lei.py search "Goldman Sachs"
python3 modules/gleif_lei.py lookup 5493001KJTIIGC8Y1R12
python3 modules/gleif_lei.py hierarchy 5493001KJTIIGC8Y1R12
python3 modules/gleif_lei.py list
# Bank of Thailand (Batch 15)
python3 modules/bank_of_thailand.py POLICY_RATE
python3 modules/bank_of_thailand.py BIBOR_3M
python3 modules/bank_of_thailand.py BOND_10Y
python3 modules/bank_of_thailand.py GDP_REAL
python3 modules/bank_of_thailand.py HEADLINE_CPI_YOY
python3 modules/bank_of_thailand.py CURRENT_ACCOUNT_USD
python3 modules/bank_of_thailand.py INTL_RESERVES_USD
python3 modules/bank_of_thailand.py fx_rates
python3 modules/bank_of_thailand.py list
# DANE Colombia — SDMX Macro (Batch 15)
python3 modules/dane_colombia.py GDP
python3 modules/dane_colombia.py CPI
python3 modules/dane_colombia.py UNEMPLOYMENT
python3 modules/dane_colombia.py INDUSTRIAL_PRODUCTION
python3 modules/dane_colombia.py TRADE_BALANCE
python3 modules/dane_colombia.py PPI
python3 modules/dane_colombia.py list
# EPO Open Patent Services (Batch 15)
python3 modules/epo_ops.py PATENT_SEARCH "battery solid state"
python3 modules/epo_ops.py APPLICANT_FILINGS "Samsung"
python3 modules/epo_ops.py PATENT_FAMILY EP3456789
python3 modules/epo_ops.py EP_REGISTER EP3456789
python3 modules/epo_ops.py IPC_TRENDS H01M
python3 modules/epo_ops.py RECENT_GRANTS
python3 modules/epo_ops.py list
# USGS Earthquake Hazards — Real-Time Seismic (Batch 15)
python3 modules/usgs_earthquake.py SIGNIFICANT_GLOBAL
python3 modules/usgs_earthquake.py RECENT_M4
python3 modules/usgs_earthquake.py PAGER_ALERTS
python3 modules/usgs_earthquake.py HOTSPOT_TAIWAN
python3 modules/usgs_earthquake.py HOTSPOT_JAPAN
python3 modules/usgs_earthquake.py HOTSPOT_CALIFORNIA
python3 modules/usgs_earthquake.py ANNUAL_M5_PLUS
python3 modules/usgs_earthquake.py FELT_REPORTS
python3 modules/usgs_earthquake.py list
# KOSIS South Korea — Statistics Korea (Batch 15)
python3 modules/kosis_korea.py GDP
python3 modules/kosis_korea.py CPI
python3 modules/kosis_korea.py UNEMPLOYMENT
python3 modules/kosis_korea.py INDUSTRIAL_PRODUCTION
python3 modules/kosis_korea.py EXPORTS
python3 modules/kosis_korea.py HOUSING
python3 modules/kosis_korea.py SEMICONDUCTORS
python3 modules/kosis_korea.py list
# SSB Norway — Statistics Norway (Batch 16)
python3 modules/ssb_norway.py GDP
python3 modules/ssb_norway.py GDP_GROWTH
python3 modules/ssb_norway.py CPI_INDEX
python3 modules/ssb_norway.py CPI_ANNUAL_RATE
python3 modules/ssb_norway.py UNEMPLOYMENT_RATE
python3 modules/ssb_norway.py TRADE_EXPORTS
python3 modules/ssb_norway.py TRADE_IMPORTS
python3 modules/ssb_norway.py HOUSE_PRICE_INDEX
python3 modules/ssb_norway.py PETROLEUM_DELIVERIES
python3 modules/ssb_norway.py INDUSTRIAL_OUTPUT
python3 modules/ssb_norway.py VALUE_ADDED
python3 modules/ssb_norway.py list
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
GET /api/v1/statistics-austria?indicator=GDP_NOMINAL_Q
GET /api/v1/statistics-austria?indicator=CPI
GET /api/v1/statistics-austria?indicator=PRODUCER_PRICE_INDEX
GET /api/v1/statistics-austria?indicator=EXPORTS_TOTAL
GET /api/v1/statistics-austria?indicator=INDUSTRIAL_PRODUCTION_INDEX
GET /api/v1/statistics-austria?indicator=OVERNIGHT_STAYS
GET /api/v1/czso-czech?indicator=GDP_NOMINAL
GET /api/v1/czso-czech?indicator=CPI_YOY
GET /api/v1/czso-czech?indicator=UNEMPLOYMENT_RATE
GET /api/v1/czso-czech?indicator=IPI_TOTAL
GET /api/v1/czso-czech?indicator=TRADE_BALANCE
GET /api/v1/statistics-estonia?indicator=GDP_REAL_GROWTH
GET /api/v1/statistics-estonia?indicator=CPI_MONTHLY
GET /api/v1/statistics-estonia?indicator=UNEMPLOYMENT_RATE
GET /api/v1/ecb-enhanced?indicator=M3_OUTSTANDING
GET /api/v1/ecb-enhanced?indicator=HICP_HEADLINE
GET /api/v1/ecb-enhanced?indicator=LOANS_HH
GET /api/v1/ecb-enhanced?indicator=CCOB_NFC
GET /api/v1/eurostat-enhanced?indicator=GOV_DEBT&geo=DE
GET /api/v1/eurostat-enhanced?indicator=RENEWABLE_SHARE_TOTAL&geo=FR
GET /api/v1/eurostat-enhanced?indicator=GHG_TOTAL&geo=DE
GET /api/v1/bis-enhanced?indicator=OTC_NOTIONAL_TOTAL
GET /api/v1/bis-enhanced?indicator=XTD_OI_IR
GET /api/v1/bis-enhanced?indicator=DEBT_SEC_US
GET /api/v1/bis-enhanced?indicator=FX_TURNOVER_TOTAL
GET /api/v1/imf-enhanced?indicator=FSI_NPL_RATIO&country=US
GET /api/v1/imf-enhanced?indicator=FSI_CET1_RATIO&country=DE
GET /api/v1/imf-enhanced?indicator=FSI_ROE&country=JP
GET /api/v1/imf-enhanced?indicator=FAS_ATMS_PER_100K&country=IN
GET /api/v1/imf-enhanced?indicator=FAS_MOBILE_MONEY_ACTIVE&country=KE
GET /api/v1/imf-enhanced?indicator=CPIS_TOTAL_ASSETS&country=US
GET /api/v1/imf-enhanced?indicator=CDIS_INWARD_EQUITY&country=GB
GET /api/v1/imf-enhanced?indicator=GFS_REVENUE&country=US
GET /api/v1/imf-enhanced?indicator=GFS_TAX_REVENUE&country=FR
GET /api/v1/oecd-enhanced?indicator=CLI_USA
GET /api/v1/oecd-enhanced?indicator=KEI_GDP_USA
GET /api/v1/oecd-enhanced?indicator=TAX_TOTAL_USA
GET /api/v1/oecd-enhanced?indicator=PENSION_GRR_GBR
GET /api/v1/oecd-enhanced?indicator=RD_GERD_DEU
GET /api/v1/boe-iadb-enhanced?indicator=BANK_RATE
GET /api/v1/boe-iadb-enhanced?indicator=GILT_NZC_10Y
GET /api/v1/boe-iadb-enhanced?indicator=M4_OUTSTANDING
GET /api/v1/boe-iadb-enhanced?indicator=GBP_USD
GET /api/v1/boe-iadb-enhanced?indicator=STERLING_EER
GET /api/v1/boe-iadb-enhanced?indicator=MORTGAGE_SVR
GET /api/v1/mnb-hungary?indicator=MNB_BASE_RATE
GET /api/v1/mnb-hungary?indicator=FX_EUR_HUF
GET /api/v1/mnb-hungary?indicator=FX_CEE_BASKET
GET /api/v1/eu-small-central-banks?indicator=BG_HICP
GET /api/v1/eu-small-central-banks?indicator=HR_FX_USD
GET /api/v1/eu-small-central-banks?indicator=SI_INFLATION_DOMESTIC
GET /api/v1/eu-small-statistics?indicator=GDP_NOMINAL&geo=BG
GET /api/v1/eu-small-statistics?indicator=CPI_YOY&geo=HU
GET /api/v1/eu-small-statistics?indicator=UNEMPLOYMENT_RATE&geo=EL
GET /api/v1/eu-small-statistics?indicator=GOV_DEBT&geo=HR
GET /api/v1/ine-portugal?indicator=GDP_GROWTH_YOY
GET /api/v1/ine-portugal?indicator=CPI_YOY
GET /api/v1/ine-portugal?indicator=UNEMPLOYMENT_RATE
GET /api/v1/ine-portugal?indicator=TOURISM_OVERNIGHT_STAYS
GET /api/v1/ine-portugal?indicator=EXPORTS
GET /api/v1/ibge-brazil?indicator=GDP_YOY
GET /api/v1/ibge-brazil?indicator=IPCA_12M
GET /api/v1/ibge-brazil?indicator=UNEMPLOYMENT
GET /api/v1/ibge-brazil?indicator=INDUSTRIAL_PRODUCTION
GET /api/v1/ibge-brazil?indicator=RETAIL_SALES
GET /api/v1/gdelt-global-events?indicator=PROTEST_ACTIVITY_GLOBAL
GET /api/v1/gdelt-global-events?indicator=MILITARY_ACTIVITY_GLOBAL
GET /api/v1/gdelt-global-events?indicator=INFLATION_MEDIA_VOL
GET /api/v1/gdelt-global-events?indicator=STOCKMARKET_SENTIMENT
GET /api/v1/gdelt-global-events?indicator=SANCTIONS_MEDIA_VOL
GET /api/v1/patentsview-uspto?indicator=PATENT_SEARCH&query=artificial+intelligence
GET /api/v1/patentsview-uspto?indicator=PATENT_GRANTS_BY_ASSIGNEE&assignee=AAPL
GET /api/v1/patentsview-uspto?indicator=TOP_ASSIGNEES
GET /api/v1/patentsview-uspto?indicator=TECH_TRENDS&cpc_class=G06N
GET /api/v1/inegi-mexico?indicator=GDP_QUARTERLY
GET /api/v1/inegi-mexico?indicator=CPI
GET /api/v1/inegi-mexico?indicator=CORE_INFLATION
GET /api/v1/inegi-mexico?indicator=UNEMPLOYMENT
GET /api/v1/inegi-mexico?indicator=INDUSTRIAL_PRODUCTION
GET /api/v1/inegi-mexico?indicator=EXPORTS
GET /api/v1/inegi-mexico?indicator=CONSUMER_CONFIDENCE
GET /api/v1/inegi-mexico?indicator=AUTO_PRODUCTION
GET /api/v1/gleif-lei?indicator=TOTAL_ACTIVE
GET /api/v1/gleif-lei?indicator=US_ENTITIES
GET /api/v1/gleif-lei?indicator=DE_ENTITIES
GET /api/v1/gleif-lei?indicator=JP_ENTITIES
GET /api/v1/bank-of-thailand?indicator=POLICY_RATE
GET /api/v1/bank-of-thailand?indicator=BIBOR_3M
GET /api/v1/bank-of-thailand?indicator=BOND_10Y
GET /api/v1/bank-of-thailand?indicator=GDP_REAL
GET /api/v1/bank-of-thailand?indicator=HEADLINE_CPI_YOY
GET /api/v1/bank-of-thailand?indicator=CURRENT_ACCOUNT_USD
GET /api/v1/bank-of-thailand?indicator=INTL_RESERVES_USD
GET /api/v1/dane-colombia?indicator=GDP
GET /api/v1/dane-colombia?indicator=CPI
GET /api/v1/dane-colombia?indicator=UNEMPLOYMENT
GET /api/v1/dane-colombia?indicator=TRADE_BALANCE
GET /api/v1/dane-colombia?indicator=PPI
GET /api/v1/epo-ops?indicator=PATENT_SEARCH&query=solid+state+battery
GET /api/v1/epo-ops?indicator=APPLICANT_FILINGS&applicant=Samsung
GET /api/v1/epo-ops?indicator=IPC_TRENDS&ipc_class=H01M
GET /api/v1/epo-ops?indicator=RECENT_GRANTS
GET /api/v1/usgs-earthquake?indicator=SIGNIFICANT_GLOBAL
GET /api/v1/usgs-earthquake?indicator=RECENT_M4
GET /api/v1/usgs-earthquake?indicator=PAGER_ALERTS
GET /api/v1/usgs-earthquake?indicator=HOTSPOT_TAIWAN
GET /api/v1/usgs-earthquake?indicator=HOTSPOT_JAPAN
GET /api/v1/usgs-earthquake?indicator=FELT_REPORTS
GET /api/v1/kosis-korea?indicator=GDP
GET /api/v1/kosis-korea?indicator=CPI
GET /api/v1/kosis-korea?indicator=UNEMPLOYMENT
GET /api/v1/kosis-korea?indicator=SEMICONDUCTORS
GET /api/v1/kosis-korea?indicator=EXPORTS
GET /api/v1/kosis-korea?indicator=HOUSING
GET /api/v1/ssb-norway?indicator=GDP
GET /api/v1/ssb-norway?indicator=GDP_GROWTH
GET /api/v1/ssb-norway?indicator=CPI_ANNUAL_RATE
GET /api/v1/ssb-norway?indicator=UNEMPLOYMENT_RATE
GET /api/v1/ssb-norway?indicator=PETROLEUM_DELIVERIES
GET /api/v1/ssb-norway?indicator=HOUSE_PRICE_INDEX
GET /api/v1/ssb-norway?indicator=TRADE_EXPORTS
GET /api/v1/ssb-norway?indicator=INDUSTRIAL_OUTPUT
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

#### Batch 9: Central Europe — Austria

Batch 9 adds the **Statistics Austria** module, extending coverage to **23 countries** and **33 government/central bank/regulatory modules** with **635+ indicators**. Austria is the first Alpine nation on the platform, providing comprehensive macroeconomic data from the Konjunkturmonitor (Economic Trend Monitor) — the Austrian government's flagship composite dataset aggregating national accounts, prices, labour, trade, tourism, and industrial output.

**Statistics Austria** (`statistics_austria`) — Statistik Austria (OGD Portal):
- GDP: nominal quarterly (EUR mn), nominal annual (EUR mn), real chain-linked quarterly (EUR mn) — seasonally unadjusted national accounts
- Consumer prices: CPI Verbraucherpreisindex (base 2015=100, monthly), with automatic year-on-year change extraction
- Producer prices: Erzeugerpreisindex industrial output price index (NACE B-E, 2021=100, monthly)
- Wholesale prices: Großhandelspreisindex wholesale trade price index (2025=100, monthly)
- Labour market: total employed persons in thousands (quarterly), total unemployed persons in thousands (quarterly)
- Foreign trade: total goods imports and exports in EUR (monthly customs data)
- Tourism: total tourist overnight stays (Nächtigungen, monthly), accommodation & food service turnover index (2021=100, quarterly)
- Automotive: new passenger car registrations (Pkw-Neuzulassungen, monthly)
- Industrial output: Produktionsindex Industrie working-day adjusted production index (2021=100, monthly)
- Construction: Produktionsindex Bau working-day adjusted construction production index (2021=100, monthly)
- Consumption & investment: private household consumption expenditure (EUR mn, quarterly), gross fixed capital formation / Bruttoanlageinvestitionen (EUR mn, quarterly)
- **15 indicators** with value, month-on-month change, and year-on-year % change for each series
- **Special commands:** `list` (all available indicators with metadata), `catalog` (OGD dataset metadata discovery)
- Data source: Konjunkturmonitor (OGD_konjunkturmonitor_KonMon_1) — semicolon-delimited CSV with European decimal format
- API: `https://data.statistik.gv.at` (OGD CSV download, open access, CC BY 4.0, no auth required)
- Cache TTL: 24h (data updated monthly/quarterly depending on indicator)

**Example response — `GDP_NOMINAL_Q`:**
```json
{
  "success": true,
  "indicator": "GDP_NOMINAL_Q",
  "name": "GDP Nominal, Quarterly (EUR mn)",
  "description": "Gross domestic product, nominal, quarterly, in million EUR",
  "unit": "EUR mn",
  "frequency": "quarterly",
  "latest_value": 128450.5,
  "latest_period": "2025-Q4",
  "period_change": 1230.2,
  "period_change_pct": 0.9672,
  "yoy_change_pct": 3.45,
  "data_points": [{"period": "2025-Q4", "value": 128450.5, "yoy_pct": 3.45}, "..."],
  "total_observations": 80,
  "source": "https://data.statistik.gv.at/data/OGD_konjunkturmonitor_KonMon_1.csv"
}
```

**Example — Full Austrian macro dashboard:**
```bash
python3 modules/statistics_austria.py
# Returns latest values for all 15 indicators: GDP, CPI, PPI, employment, trade, tourism, industry, construction, investment
```

**Batch MCP — European GDP Comparison (New in Batch 9):**
```typescript
const gdpComparison = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'statistics_austria', params: { indicator: 'GDP_NOMINAL_Q' } },
      { tool: 'destatis_germany', params: { indicator: 'GDP_QUARTERLY' } },
      { tool: 'insee_france', params: { indicator: 'GDP_GROWTH' } },
      { tool: 'istat_italy', params: { indicator: 'GDP_QUARTERLY' } },
      { tool: 'cbs_netherlands', params: { indicator: 'GDP_GROWTH_YOY' } },
      { tool: 'ine_spain', params: { indicator: 'GDP_QOQ' } },
      { tool: 'statbel_belgium', params: { indicator: 'CPI_INDEX' } },
      { tool: 'statistics_finland', params: { indicator: 'GDP_QOQ' } }
    ]
  })
});
```

**Batch MCP — European Industrial Production (New in Batch 9):**
```typescript
const industrialOutput = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'statistics_austria', params: { indicator: 'INDUSTRIAL_PRODUCTION_INDEX' } },
      { tool: 'destatis_germany', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'insee_france', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'istat_italy', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'ine_spain', params: { indicator: 'IPI_SA' } },
      { tool: 'statistics_finland', params: { indicator: 'IPI_TOTAL' } }
    ]
  })
});
```

**Coverage totals after Batch 9:**
- 33 government/central bank/regulatory modules
- 23 countries: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇩🇪+ 🇯🇵+ 🇬🇧+ 🇨🇦+ 🇪🇸+ 🇳🇱+ 🇧🇪+
- 635+ macroeconomic indicators from official government sources
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD), policy rates, interbank rates, monetary aggregates, GDP (incl. Austrian national accounts), CPI/HICP/PPI/wholesale prices, unemployment (incl. by demographics), trade, housing prices, lending rates, mortgage rates, credit growth, banking FSIs, gold, government debt, BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism (overnight stays, turnover), automotive registrations, investment (GFCF)

#### Batch 10: Extended Coverage — Czech Stats, Estonia, ECB Monetary, Eurostat Fiscal/Energy, BIS Derivatives

Batch 10 adds **5 new modules** expanding into Baltic statistics (Estonia), deeper Czech macroeconomic data beyond CNB's financial markets coverage, comprehensive Euro Area monetary statistics from the ECB, EU-wide fiscal/energy/environment data from Eurostat, and global derivatives/debt/payments data from the Bank for International Settlements. This brings total coverage to **24 countries** plus EU-wide and global datasets, with **38 government/institutional/regulatory modules** and **725+ indicators**.

**CZSO Czech Republic** (`czso_czech`) — Czech Statistical Office:
- GDP at current prices and constant 2020 prices, YoY growth rate (annual from national accounts)
- Gross value added (GVA) and gross fixed capital formation (GFCF) at current prices (annual)
- Consumer prices: CPI year-on-year change, month-on-month change, and index level (2015=100); food & beverages YoY, housing/water/energy YoY, transport YoY (monthly)
- Labour force survey: general unemployment rate, employment rate, employed and unemployed persons in thousands (quarterly)
- Industrial production: total industry (B+C+D) YoY change and motor vehicles (NACE 29) YoY (monthly)
- Construction output index: total output YoY at current prices (monthly)
- Foreign trade: total goods exports, imports, and trade balance in CZK mn (monthly)
- **20 indicators** across national accounts, prices, labour, industry, construction, and trade
- API: `https://vdb.czso.cz/pll/eweb` (Open Data CSV, no auth, CC BY 4.0)

**Statistics Estonia** (`statistics_estonia`) — Estonian National Statistics via PxWeb:
- GDP at current prices (quarterly, EUR mn) and real GDP growth YoY (chain-linked volume, quarterly)
- CPI inflation: annual and monthly year-on-year rates, all items
- HICP (Harmonised Index): annual rate of change, all items
- Labour force survey: employment rate (15-74), unemployment rate (15-74), labour force in thousands (quarterly)
- National accounts expenditure: exports and imports of goods & services in EUR mn (quarterly)
- Industrial production: calendar & seasonally adjusted volume index (2021=100, monthly) and YoY change (unadjusted)
- **13 indicators** via PxWeb POST-based JSON queries with dynamic time dimension resolution
- API: `https://andmed.stat.ee/api/v1/en/stat` (PxWeb REST, open access, no auth)

**ECB Enhanced** (`ecb_enhanced`) — European Central Bank SDMX:
- Monetary aggregates: M1, M2, and M3 outstanding amounts (Euro Area, seasonally adjusted, EUR mn)
- MFI credit: total loans to households, loans to non-financial corporations, housing loans to households (outstanding amounts, EUR mn)
- Composite cost of borrowing: NFC composite indicator, household housing loan composite indicator (% p.a.)
- MFI interest rates: NFC new loan rate (up to 1Y and over 5Y), household deposit rate (new business with agreed maturity)
- HICP inflation: headline annual rate, core (ex food & energy), food & non-alcoholic beverages
- **14 indicators** across 3 SDMX dataflows (BSI, MIR, ICP) covering monetary policy, credit, and inflation
- API: `https://data-api.ecb.europa.eu/service` (SDMX 2.1 REST, SDMX-JSON 1.0, open access)

**Eurostat Enhanced** (`eurostat_enhanced`) — EU Government Finance, Energy & Environment:
- Government finance: deficit/surplus (% GDP), Maastricht debt (% GDP), total expenditure (% GDP), total revenue (% GDP)
- Energy balance: total energy production and final consumption (KTOE), energy import dependency (%)
- Renewable energy: overall share, electricity share, transport share, heating/cooling share (%)
- Greenhouse gas emissions: total excl. memo items, energy sector, manufacturing/construction, transport, agriculture (Mt CO₂eq)
- Environmental taxes: total environmental taxes, energy taxes, transport taxes (all % of GDP)
- Digital economy: household internet access (%), individual internet use (%), e-commerce participation (%)
- **21 indicators** with per-country and EU-wide cross-country comparison support (27 Member States)
- API: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data` (JSON-stat 2.0, open access, ~100 req/hour)

**BIS Enhanced** (`bis_enhanced`) — Bank for International Settlements:
- OTC derivatives: total notional outstanding, swaps notional, gross market value, NFC counterparty notional (semiannual, USD bn)
- Exchange-traded derivatives: open interest in FX, interest rate, equity, and commodity contracts (quarterly, USD mn); FX turnover
- FX & OTC IR turnover survey: total FX daily average, FX spot daily average, OTC IR derivatives daily average (triennial, USD mn)
- International debt securities outstanding: US, UK, Japan, China, Germany (quarterly, USD bn)
- CPMI cashless payments: total value for US, UK, and China (annual)
- CPMI macro indicators: population and banknotes/coins in circulation (annual)
- **22 indicators** across 6 BIS SDMX dataflows (WS_OTC_DERIV2, WS_XTD_DERIV, WS_DER_OTC_TOV, WS_NA_SEC_DSS, WS_CPMI_CASHLESS, WS_CPMI_MACRO)
- API: `https://stats.bis.org/api/v2` (BIS SDMX REST v2, CSV output, open access, no auth)

**Example response — `ecb_enhanced` `HICP_HEADLINE`:**
```json
{
  "success": true,
  "indicator": "HICP_HEADLINE",
  "name": "HICP — All Items Annual Rate (%)",
  "description": "Harmonised Index of Consumer Prices, all items, annual rate of change",
  "unit": "%",
  "frequency": "monthly",
  "category": "inflation",
  "latest_value": 2.3,
  "latest_period": "2026-02",
  "period_change": -0.1,
  "period_change_pct": -4.1667,
  "data_points": [{"period": "2026-02", "value": 2.3}, "..."],
  "total_observations": 60,
  "source": "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR"
}
```

**Batch MCP — Euro Area Monetary Dashboard (New in Batch 10):**
```typescript
const monetaryDashboard = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ecb_enhanced', params: { indicator: 'M1_OUTSTANDING' } },
      { tool: 'ecb_enhanced', params: { indicator: 'M2_OUTSTANDING' } },
      { tool: 'ecb_enhanced', params: { indicator: 'M3_OUTSTANDING' } },
      { tool: 'ecb_enhanced', params: { indicator: 'LOANS_HH' } },
      { tool: 'ecb_enhanced', params: { indicator: 'LOANS_NFC' } },
      { tool: 'ecb_enhanced', params: { indicator: 'HICP_HEADLINE' } },
      { tool: 'ecb_enhanced', params: { indicator: 'HICP_CORE' } },
      { tool: 'ecb_enhanced', params: { indicator: 'CCOB_NFC' } }
    ]
  })
});
```

**Batch MCP — EU Government Debt Comparison (New in Batch 10):**
```typescript
const govDebt = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'DE' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'FR' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'IT' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'ES' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'NL' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'BE' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'AT' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'GOV_DEBT', geo: 'EE' } }
    ]
  })
});
```

**Batch MCP — Global Derivatives Overview (New in Batch 10):**
```typescript
const derivsOverview = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'bis_enhanced', params: { indicator: 'OTC_NOTIONAL_TOTAL' } },
      { tool: 'bis_enhanced', params: { indicator: 'OTC_GMV_TOTAL' } },
      { tool: 'bis_enhanced', params: { indicator: 'XTD_OI_IR' } },
      { tool: 'bis_enhanced', params: { indicator: 'XTD_OI_EQUITY' } },
      { tool: 'bis_enhanced', params: { indicator: 'FX_TURNOVER_TOTAL' } },
      { tool: 'bis_enhanced', params: { indicator: 'DEBT_SEC_US' } },
      { tool: 'bis_enhanced', params: { indicator: 'DEBT_SEC_CN' } }
    ]
  })
});
```

**Coverage totals after Batch 10:**
- 38 government/central bank/regulatory/institutional modules
- 24 countries + EU-wide + global: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇪🇺 🌍
- 725+ indicators from official government, central bank, and international institution sources
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED), policy rates, interbank rates, monetary aggregates (incl. EA M1/M2/M3), GDP (incl. Czech/Estonian national accounts), CPI/HICP/PPI/wholesale prices, unemployment (incl. by demographics), trade, housing prices, lending rates, mortgage rates, credit growth, MFI credit to households/NFCs, cost of borrowing indicators, banking FSIs, gold, government debt/deficit/surplus, fiscal accounts, BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism, automotive registrations, investment (GFCF), OTC/exchange-traded derivatives (notional/GMV/open interest), FX turnover surveys, international debt securities, energy production/consumption/dependency, renewable energy share, greenhouse gas emissions by sector, environmental taxes, digital economy indicators, cashless payments

#### Batch 11: International Monetary Fund — IMF Enhanced (5 Databases)

Batch 11 adds the **IMF Enhanced** module, integrating five specialized International Monetary Fund statistical databases (FAS, FSI, CPIS, CDIS, GFS) via the DBnomics API mirror. This is the first truly global module on the platform, providing country-level data for **190+ nations** across financial inclusion, banking soundness, cross-border investment flows, and government fiscal accounts. This brings total coverage to **24 countries + EU-wide + global + 190 IMF member nations**, with **39 government/institutional/regulatory modules** and **755+ indicators**.

**IMF Enhanced** (`imf_enhanced`) — International Monetary Fund (5 Databases via DBnomics):
- **Financial Access Survey (FAS):** ATMs per 100,000 adults, commercial bank branches per 100,000 adults, ATMs per 1,000 km², bank branches per 1,000 km², household deposit accounts per 1,000 adults, active mobile money accounts per 1,000 adults, registered mobile money accounts per 1,000 adults (annual, 190+ countries)
- **Financial Soundness Indicators (FSI):** Non-performing loans to total gross loans (NPL ratio), regulatory capital to risk-weighted assets, Common Equity Tier 1 (CET1) to RWA, return on assets (ROA), return on equity (ROE) — all for deposit-taking institutions (annual/quarterly, 190+ countries)
- **Coordinated Portfolio Investment Survey (CPIS):** Total cross-border portfolio investment assets vs world, portfolio equity assets, long-term debt securities assets (annual, USD)
- **Coordinated Direct Investment Survey (CDIS):** Inward FDI equity positions, inward FDI debt assets (gross), inward FDI debt liabilities (gross), outward FDI equity positions, outward FDI debt assets, outward FDI debt liabilities — all net/gross bilateral positions vs world (annual, USD mn)
- **Government Finance Statistics (GFS):** General government revenue, general government expense, tax revenue, total expenditure, social benefits expense, interest expense, net investment in nonfinancial assets, net incurrence of liabilities — all in domestic currency billions (annual)
- **29 indicators** across 5 IMF databases (FAS ×7, FSI ×5, CPIS ×3, CDIS ×6, GFS ×8)
- **Special commands:** `fas [COUNTRY]` (financial inclusion), `fsi [COUNTRY]` (banking health), `cpis [COUNTRY]` (portfolio investment), `cdis [COUNTRY]` (direct investment), `gfs [COUNTRY]` (government finance), `banking-health [COUNTRY]`, `access [COUNTRY]`, `list`
- Default country: US — pass any ISO2 country code (DE, JP, GB, CN, IN, BR, KE, NG, etc.) for any of 190+ nations
- API: `https://api.db.nomics.world/v22` (DBnomics mirror of IMF data, open access, no auth, rate-limited)
- Cache TTL: 24h (data updated annually for FAS/CPIS/CDIS/GFS, quarterly for FSI)

**Example response — `FSI_NPL_RATIO`:**
```json
{
  "success": true,
  "indicator": "FSI_NPL_RATIO",
  "country": "US",
  "name": "Non-performing Loans to Total Gross Loans",
  "description": "Core FSI: ratio of non-performing loans to total gross loans for deposit takers",
  "unit": "%",
  "frequency": "annual",
  "database": "FSI",
  "category": "fsi",
  "latest_value": 1.12,
  "latest_period": "2024",
  "period_change": -0.05,
  "period_change_pct": -4.27,
  "data_points": [{"period": "2024", "value": 1.12}, "..."],
  "total_observations": 15,
  "source": "IMF FSI via DBnomics",
  "series_key": "A.US.FSANL_PT"
}
```

**Example — Government Finance Statistics for Japan:**
```bash
python3 modules/imf_enhanced.py gfs JP
# Returns: {"success": true, "category": "gfs", "country": "JP", "indicators": {"GFS_REVENUE": {"value": 228.5, "period": "2023"}, "GFS_EXPENSE": {"value": 234.1, ...}, ...}}
```

**Batch MCP — Global Banking Health Comparison (New in Batch 11):**
```typescript
const bankingHealth = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'imf_enhanced', params: { indicator: 'FSI_NPL_RATIO', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_NPL_RATIO', country: 'DE' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_NPL_RATIO', country: 'JP' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_NPL_RATIO', country: 'GB' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_NPL_RATIO', country: 'CN' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_CET1_RATIO', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_CET1_RATIO', country: 'DE' } },
      { tool: 'imf_enhanced', params: { indicator: 'FSI_REGULATORY_CAPITAL', country: 'IN' } }
    ]
  })
});
```

**Batch MCP — Financial Inclusion Across Developing Economies (New in Batch 11):**
```typescript
const financialAccess = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'imf_enhanced', params: { indicator: 'FAS_ATMS_PER_100K', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_ATMS_PER_100K', country: 'IN' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_ATMS_PER_100K', country: 'BR' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_ATMS_PER_100K', country: 'NG' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_MOBILE_MONEY_ACTIVE', country: 'KE' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_MOBILE_MONEY_ACTIVE', country: 'NG' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_MOBILE_MONEY_ACTIVE', country: 'GH' } },
      { tool: 'imf_enhanced', params: { indicator: 'FAS_BRANCHES_PER_100K', country: 'JP' } }
    ]
  })
});
```

**Batch MCP — Government Fiscal Comparison: G7 (New in Batch 11):**
```typescript
const g7Fiscal = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'imf_enhanced', params: { indicator: 'GFS_REVENUE', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_REVENUE', country: 'JP' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_REVENUE', country: 'DE' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_REVENUE', country: 'GB' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_EXPENSE', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_EXPENSE', country: 'JP' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_SOCIAL_BENEFITS', country: 'FR' } },
      { tool: 'imf_enhanced', params: { indicator: 'GFS_INTEREST_EXPENSE', country: 'IT' } }
    ]
  })
});
```

**Batch MCP — Cross-Border Investment Flows (New in Batch 11):**
```typescript
const investmentFlows = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'imf_enhanced', params: { indicator: 'CPIS_TOTAL_ASSETS', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'CPIS_TOTAL_ASSETS', country: 'GB' } },
      { tool: 'imf_enhanced', params: { indicator: 'CPIS_EQUITY_ASSETS', country: 'JP' } },
      { tool: 'imf_enhanced', params: { indicator: 'CDIS_INWARD_EQUITY', country: 'US' } },
      { tool: 'imf_enhanced', params: { indicator: 'CDIS_INWARD_EQUITY', country: 'CN' } },
      { tool: 'imf_enhanced', params: { indicator: 'CDIS_OUTWARD_EQUITY', country: 'DE' } },
      { tool: 'imf_enhanced', params: { indicator: 'CDIS_OUTWARD_EQUITY', country: 'JP' } }
    ]
  })
});
```

**Coverage totals after Batch 11:**
- 39 government/central bank/regulatory/institutional modules
- 24 countries + EU-wide + global + 190 IMF member nations: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇪🇺 🌍 🌐
- 755+ indicators from official government, central bank, and international institution sources
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED), policy rates, interbank rates, monetary aggregates (incl. EA M1/M2/M3), GDP (incl. Czech/Estonian national accounts), CPI/HICP/PPI/wholesale prices, unemployment (incl. by demographics), trade, housing prices, lending rates, mortgage rates, credit growth, MFI credit to households/NFCs, cost of borrowing indicators, banking FSIs, gold, government debt/deficit/surplus, fiscal accounts (IMF GFS revenue/expenditure/tax/social benefits/interest/investment/borrowing), BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves incl. full GoC curve), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism, automotive registrations, investment (GFCF), OTC/exchange-traded derivatives (notional/GMV/open interest), FX turnover surveys, international debt securities, energy production/consumption/dependency, renewable energy share, greenhouse gas emissions by sector, environmental taxes, digital economy indicators, cashless payments, financial inclusion metrics (ATM/branch/account density, mobile money penetration), banking soundness indicators (NPL ratios, capital adequacy CET1/RWA, ROA/ROE), cross-border portfolio investment (CPIS equity/debt), foreign direct investment positions (CDIS inward/outward)

#### Batch 12: OECD, Bank of England, Hungary, EU Small States Expansion

Batch 12 adds **5 new modules** completing coverage of the broader European economic area and expanding into OECD-wide composite indicators, UK central bank statistical depth, Hungarian monetary policy, and unified data access for 9 smaller EU central banks plus 12 smaller EU statistical offices. This brings total coverage to **33 countries + EU-wide + global + 190 IMF member nations + 38 OECD members**, with **44 government/institutional/regulatory modules** and **885+ indicators**.

**OECD Enhanced** (`oecd_enhanced`) — Organisation for Economic Co-operation and Development:
- **Composite Leading Indicators (CLI):** Monthly CLI amplitude-adjusted for USA, GBR, DEU, JPN, FRA, and OECD total — designed to provide early signals of turning points in business cycles relative to trend
- **Business & Consumer Confidence:** Business Confidence Index (BCI) and Consumer Confidence Index (CCI) for USA — standardized to long-term average = 100
- **Key Economic Indicators (KEI/MEI):** Harmonised unemployment rate, CPI year-on-year, GDP volume at market prices, short-term interest rates, long-term interest rates — all for USA, comparable across OECD
- **Revenue Statistics (REV):** Total tax revenue, income tax, corporate tax, social security contributions, taxes on goods & services — all as % of GDP for USA, GBR, DEU; enables cross-country fiscal structure comparison
- **Pensions at a Glance (PAG):** Gross replacement rates (earnings-related pension/pre-retirement earnings), life expectancy at 65, employment rate 55-64 for USA, GBR, DEU — measures adequacy of pension systems
- **Main Science & Technology Indicators (MSTI):** Gross domestic expenditure on R&D (GERD), business enterprise R&D (BERD), higher education R&D (HERD) as % GDP for USA, DEU, JPN — tracks innovation investment
- **30 indicators** across 5 OECD SDMX dataflows with per-indicator country customization
- **Special commands:** `list` (all indicators with metadata), `cli` (leading indicators), `tax` (fiscal structure), `pension` (retirement adequacy), `rd` (R&D)
- API: `https://sdmx.oecd.org/public/rest/data` (SDMX 3.0 REST, open access, ~60 req/hr rate limit)
- Cache TTL: 24h (monthly for CLI/KEI, annual for REV/PAG/MSTI)

**Bank of England IADB Enhanced** (`boe_iadb_enhanced`) — Bank of England Interactive Analytical Database:
- **Gilt Yield Curve:** Zero-coupon nominal gilt yields at 5Y, 10Y, 20Y maturities + 3-month moving averages for each (daily, % p.a., Svensson method)
- **Monetary Policy:** Bank Rate — the BoE's official policy interest rate (monthly)
- **Money Supply:** M4 outstanding stock (seasonally adjusted, GBP mn); M4 lending outstanding; M4 lending growth rates (12-month, 1-month, 3-month annualized)
- **Mortgage & Consumer Credit:** Mortgage standard variable rate (monthly, %); consumer credit excluding credit cards (total outstanding & net monthly flow, GBP mn); consumer credit 1-month growth rate
- **FX Rates:** GBP/USD, GBP/EUR, GBP/JPY, GBP/CHF spot exchange rates (daily)
- **Effective Exchange Rates:** Sterling narrow EER index, sterling broad EER index (January 2005=100, daily)
- **22 indicators** across 7 categories (yield_curve, policy_rate, money_supply, mortgage, consumer_credit, fx_rates, eer)
- **Special commands:** `yield-curve` (gilt ZC yields), `monetary` (M4 + lending), `fx` (all GBP crosses + EER)
- API: `https://www.bankofengland.co.uk/boeapps/iadb/FromShowColumns.asp` (XML, open access, no auth)
- Cache TTL: 1h for daily (gilt yields, FX), 24h for monthly (M4, rates)

**MNB Hungary** (`mnb_hungary`) — Magyar Nemzeti Bank:
- **Policy Rate:** MNB base rate — Hungary's main policy instrument, with full historical series since 1999 (monthly)
- **FX Rates:** Official HUF exchange rates for 12 currencies: EUR/HUF, USD/HUF, GBP/HUF, CHF/HUF, JPY/HUF, CZK/HUF, PLN/HUF, RON/HUF, SEK/HUF, CNY/HUF, TRY/HUF, CAD/HUF (daily, MNB reference rates)
- **Regional Baskets:** CEE equal-weight basket (CZK+PLN+RON average rate vs HUF for regional comparison), G4 basket (USD+EUR+GBP+JPY average vs HUF for global comparison) — derived indicators
- **16 indicators** covering policy rates, FX crosses, and composite baskets
- API: SOAP web services at `http://www.mnb.hu/arfolyamok.asmx` (FX) and `http://www.mnb.hu/alapkamat.asmx` (base rate), open access
- Cache TTL: 1h (rates updated daily on business days)

**EU Small Central Banks** (`eu_small_central_banks`) — Unified access to 9 smaller Euro Area and EU central banks:
- **Coverage:** Bulgaria (BNB), Croatia (HNB), Cyprus (CBC), Latvia (BoL), Lithuania (Lietuvos bankas), Luxembourg (BCL), Malta (CBM), Slovakia (NBS), Slovenia (BSI)
- **HICP Inflation:** Annual rate of change for all 9 countries (monthly, via ECB SDMX ICP dataflow)
- **MFI Interest Rates:** Lending rate to households and deposit rate for households with agreed maturity, new business, for all 9 countries (monthly, via ECB SDMX MIR dataflow)
- **FX Rates:** Daily EUR/USD, EUR/GBP, EUR/CHF from national central bank feeds for Bulgaria, Croatia, Lithuania, Slovakia, and Slovenia — sourced from BNB XML, HNB JSON API, Lietuvos bankas SOAP, NBS CSV, and BSI REST respectively
- **Slovenia Extras:** Domestic inflation rate, EU-harmonised inflation, ECB deposit facility rate, ECB main refinancing rate, ECB marginal lending rate (via Banka Slovenije API)
- **47 indicators** (27 ECB macro + 15 national FX + 5 Slovenia-specific) from 6 distinct API sources
- APIs: ECB `https://data-api.ecb.europa.eu/service/data`; HNB `https://api.hnb.hr/tecajn-eur/v3`; BSI `https://api.bsi.si`; BNB `https://www.bnb.bg`; LB `https://www.lb.lt/webservices`; NBS `https://nbs.sk/export`
- Cache TTL: 6h for ECB SDMX data, 1h for national FX feeds

**EU Small Statistics** (`eu_small_statistics`) — Eurostat batch module for 12 smaller EU national statistical offices:
- **Coverage:** Bulgaria (NSI), Croatia (DZS), Cyprus (CYSTAT), Greece (ELSTAT), Hungary (KSH), Latvia (CSP), Lithuania (OSP), Luxembourg (STATEC), Malta (NSO), Romania (INS), Slovakia (SUSR), Slovenia (SURS)
- **GDP & National Accounts:** Nominal GDP, real GDP, GDP growth rate, GDP per capita in PPS (annual/quarterly)
- **Consumer Prices:** CPI year-on-year, food CPI YoY, energy CPI YoY, CPI index level (monthly/annual)
- **Labour Market:** Unemployment rate (total), youth unemployment rate (under 25), employment rate (20-64) — all ILO definitions (quarterly)
- **Government Finance:** General government gross debt (% GDP), general government deficit/surplus (% GDP) — Maastricht criteria (annual)
- **Industry & Trade:** GVA in manufacturing (EUR mn, annual), current account balance (% GDP, annual)
- **15 indicators** per country × 12 countries = 180 country-indicator combinations, unified interface with geo parameter
- API: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data` (JSON-stat 2.0, open access, ~100 req/hr)
- Cache TTL: 24h (quarterly/annual data from Eurostat)

**Example response — `oecd_enhanced` `CLI_USA`:**
```json
{
  "success": true,
  "indicator": "CLI_USA",
  "name": "Composite Leading Indicator — United States",
  "description": "OECD CLI amplitude adjusted, long-term trend = 100",
  "unit": "index",
  "frequency": "monthly",
  "category": "cli",
  "country": "USA",
  "latest_value": 100.85,
  "latest_period": "2026-01",
  "period_change": 0.12,
  "period_change_pct": 0.119,
  "data_points": [{"period": "2026-01", "value": 100.85}, "..."],
  "total_observations": 60,
  "source": "OECD CLI via SDMX"
}
```

**Example response — `boe_iadb_enhanced` `BANK_RATE`:**
```json
{
  "success": true,
  "indicator": "BANK_RATE",
  "name": "Bank of England Official Bank Rate",
  "description": "BoE policy rate — the rate paid on commercial bank reserves",
  "unit": "%",
  "frequency": "monthly",
  "category": "policy_rate",
  "latest_value": 4.50,
  "latest_period": "2026-03",
  "period_change": 0.0,
  "period_change_pct": 0.0,
  "data_points": [{"period": "2026-03", "value": 4.50}, "..."],
  "total_observations": 120,
  "source": "https://www.bankofengland.co.uk/boeapps/iadb"
}
```

**Example — MNB Hungary base rate + CEE basket:**
```bash
python3 modules/mnb_hungary.py MNB_BASE_RATE
# Returns: {"success": true, "indicator": "MNB_BASE_RATE", "latest_value": 6.50, "latest_period": "2026-03", ...}
python3 modules/mnb_hungary.py FX_CEE_BASKET
# Returns: {"success": true, "indicator": "FX_CEE_BASKET", "currencies": ["CZK","PLN","RON"], "basket_value": 95.42, ...}
```

**Batch MCP — OECD Leading Indicators vs Policy Rates (New in Batch 12):**
```typescript
const oecdDashboard = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'oecd_enhanced', params: { indicator: 'CLI_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'CLI_DEU' } },
      { tool: 'oecd_enhanced', params: { indicator: 'CLI_JPN' } },
      { tool: 'oecd_enhanced', params: { indicator: 'CLI_GBR' } },
      { tool: 'oecd_enhanced', params: { indicator: 'BCI_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'CCI_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'KEI_STIR_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'KEI_LTIR_USA' } }
    ]
  })
});
```

**Batch MCP — UK Financial Deep Dive (New in Batch 12):**
```typescript
const ukFinancial = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'boe_iadb_enhanced', params: { indicator: 'BANK_RATE' } },
      { tool: 'boe_iadb_enhanced', params: { indicator: 'GILT_NZC_10Y' } },
      { tool: 'boe_iadb_enhanced', params: { indicator: 'M4_OUTSTANDING' } },
      { tool: 'boe_iadb_enhanced', params: { indicator: 'MORTGAGE_SVR' } },
      { tool: 'boe_iadb_enhanced', params: { indicator: 'GBP_USD' } },
      { tool: 'boe_iadb_enhanced', params: { indicator: 'STERLING_EER' } },
      { tool: 'ons_uk', params: { indicator: 'GDP_MONTHLY' } },
      { tool: 'ons_uk', params: { indicator: 'CPIH_ALL' } }
    ]
  })
});
```

**Batch MCP — Central European Monetary Policy Comparison (New in Batch 12):**
```typescript
const ceeRates = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'mnb_hungary', params: { indicator: 'MNB_BASE_RATE' } },
      { tool: 'cnb_czech', params: { indicator: 'CNB_2W_REPO' } },
      { tool: 'riksbank_sweden', params: { indicator: 'POLICY_RATE' } },
      { tool: 'Danmarks_nationalbank', params: { indicator: 'DN_DISCOUNT_RATE' } },
      { tool: 'mnb_hungary', params: { indicator: 'FX_EUR_HUF' } },
      { tool: 'cnb_czech', params: { indicator: 'FX_EUR' } },
      { tool: 'bnr_romania', params: { indicator: 'RON_EUR' } },
      { tool: 'eu_small_central_banks', params: { indicator: 'HR_HICP' } }
    ]
  })
});
```

**Batch MCP — Small EU States GDP Comparison (New in Batch 12):**
```typescript
const smallEuGdp = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'BG' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'HR' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'HU' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'EL' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'RO' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GDP_GROWTH', geo: 'SI' } },
      { tool: 'eu_small_statistics', params: { indicator: 'UNEMPLOYMENT_RATE', geo: 'EL' } },
      { tool: 'eu_small_statistics', params: { indicator: 'GOV_DEBT', geo: 'EL' } }
    ]
  })
});
```

**Coverage totals after Batch 12:**
- 44 government/central bank/regulatory/institutional modules
- 33 countries + EU-wide + global + 190 IMF member nations + 38 OECD members: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇭🇺 🇧🇬 🇭🇷 🇨🇾 🇱🇻 🇱🇹 🇱🇺 🇲🇹 🇸🇰 🇸🇮 🇬🇷 🇪🇺 🌍 🌐
- 885+ indicators from official government, central bank, and international institution sources
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED, HUF 12-pair, GBP 4-pair + EER, EU small-state FX), policy rates (incl. MNB base rate, BoE Bank Rate), interbank rates, monetary aggregates (incl. EA M1/M2/M3, UK M4/M4 lending growth), GDP (incl. EU-12 small state accounts), CPI/HICP/PPI/wholesale prices, unemployment (incl. by demographics, EU-12 youth), trade, housing prices, lending rates, mortgage rates (incl. UK SVR), credit growth, MFI credit to households/NFCs, cost of borrowing indicators, banking FSIs, gold, government debt/deficit/surplus (Maastricht criteria for EU-12), fiscal accounts (IMF GFS, OECD REV tax structure), BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves incl. gilt ZC curve, GoC curve), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism, automotive registrations, investment (GFCF), OTC/exchange-traded derivatives, FX turnover surveys, international debt securities, energy/renewables/GHG/env taxes, digital economy, cashless payments, financial inclusion, banking soundness, portfolio/FDI investment, OECD leading indicators (CLI/BCI/CCI), pension adequacy metrics (replacement rates, life expectancy), R&D expenditure (GERD/BERD/HERD), consumer credit, gilt yield curves

#### Batch 13: Portugal Statistics, Brazil IBGE, GDELT Geopolitical Risk, USPTO PatentsView

Batch 13 adds **4 new modules** expanding into South American macroeconomic data (Brazil), deeper Portuguese national statistics beyond the existing central bank module, real-time global geopolitical risk monitoring via the GDELT event database, and US patent innovation tracking via the USPTO Open Data Portal. This brings total coverage to **34 countries + EU-wide + global + 190 IMF member nations + 38 OECD members**, with **48 government/institutional/regulatory/alt-data modules** and **930+ indicators**.

**INE Portugal** (`ine_portugal`) — Instituto Nacional de Estatística:
- GDP: real growth year-on-year (chained volume, Base 2021), nominal GDP at current prices (EUR), real GDP per capita annual growth rate
- Consumer prices: CPI year-on-year rate (Base 2025), CPI index level (Base 2025=100), HICP year-on-year rate (Base 2025)
- Labour market: unemployment rate (Series 2021, total population), employed population in thousands, activity rate of working-age population
- Tourism: total overnight stays in tourist accommodation establishments (monthly)
- Foreign trade: total exports of goods (EUR), total imports of goods (EUR), trade coverage rate (%)
- Construction: new housing construction cost index (Base 2021), construction cost annual average change (%)
- **15 indicators** across national accounts, prices, labour, tourism, trade, and construction
- **Special commands:** `list` (all available indicators with metadata)
- Multi-strategy API fetching: recent period codes → fallback to full dataset → dimension filtering in Python
- API: `https://www.ine.pt/ine/json_indicador/pindica.jsp` (REST JSON, open access, no auth required)
- Cache TTL: 24h (data updated monthly for CPI/tourism/construction, quarterly for GDP/labour, annually for trade)

**IBGE Brazil** (`ibge_brazil`) — Instituto Brasileiro de Geografia e Estatística (SIDRA):
- GDP: year-on-year quarterly growth rate vs same quarter previous year, quarter-on-quarter seasonally adjusted growth rate
- Inflation (IPCA): monthly percentage change, 12-month rolling cumulative rate, year-to-date accumulation, IPCA price index level (December 1993=100)
- Labour market: PNAD Contínua unemployment rate for population aged 14+ (monthly, from IBGE's continuous household survey)
- Industrial production: PIM-PF seasonally adjusted general industry index (CNAE 2.0, Base 2022=100)
- Retail sales: PMC broad retail sales volume, year-on-year monthly comparison
- **9 indicators** across GDP, inflation, employment, industry, and retail — core Brazilian macro dashboard
- **CLI aliases:** `gdp` (YoY+QoQ), `ipca` (monthly+12M), `inflation`, `unemployment`, `industry`, `retail`
- API: `https://servicodados.ibge.gov.br/api/v3/agregados` (SIDRA REST JSON, open access, no auth required)
- Cache TTL: 24h (data updated monthly for IPCA/PNAD/PIM-PF/PMC, quarterly for GDP)

**GDELT Global Events** (`gdelt_global_events`) — GDELT Project DOC 2.0 API:
- **Geopolitical risk indicators:** Global protest activity index, protest media sentiment, military activity index, terror threat index, armed conflict media volume — all as 7-day hourly time series with summary statistics (current, mean, median, min, max, std, 24h mean)
- **Economic media indicators:** Inflation media coverage volume & sentiment, interest rate media volume, trade policy media volume & sentiment, stock market media volume & sentiment, bankruptcy/default media volume, sanctions media volume
- **Country risk scoring:** Composite risk index (0–100 scale) for any of 35+ mapped countries, combining conflict volume Z-scores and sentiment tone — with risk interpretation (MINIMAL/LOW/MODERATE/HIGH/ELEVATED)
- **Bilateral tension analysis:** Tension scores between any two countries based on cross-media tone analysis — measures how Country A's media covers Country B and vice versa (0–100 scale with MINIMAL to SEVERE interpretation)
- **Topic sentiment:** Arbitrary keyword/topic tracking with volume + sentiment timelines + recent article extraction (e.g., "central bank", "tariffs", "semiconductor supply chain")
- **Article search:** Full-text search across global news articles with metadata (title, URL, date, domain, language, source country)
- **14 predefined indicators** + 4 special commands (country_risk, tension, topic, articles)
- Country resolution: accepts FIPS codes, ISO 3166, or country names (automatic mapping)
- API: `https://api.gdeltproject.org/api/v2/doc/doc` (REST JSON, fully open, no auth, fair-use ~5s between requests)
- Cache TTL: 1h (data updates every 15 minutes)

**PatentsView USPTO** (`patentsview_uspto`) — USPTO Open Data Portal:
- **Patent search:** Full Lucene/Solr query syntax against USPTO patent applications (keyword, assignee, CPC class, date range)
- **Patent grants by assignee:** Filing count and details for any company — supports 35+ ticker-to-assignee mappings (AAPL→Apple, MSFT→Microsoft, NVDA→NVIDIA, PFE→Pfizer, etc.), returns top CPC class distribution
- **Top assignees:** Most active patent filers from recent filings with ranked leaderboard
- **Technology trends by CPC class:** Patent activity for any of 22 named CPC classes (H01L=Semiconductors, G06N=AI/ML, A61K=Pharma, G06Q=Fintech, H01M=Batteries, B60L=EVs, C12N=Genetic Engineering, etc.) with top assignees per class
- **Patent detail:** Full metadata for a single patent by application or grant number (title, assignee, CPC classes, filing date, grant date, status)
- **5 indicators** covering patent search, corporate innovation pipelines, technology trends, and R&D tracking
- **Special commands:** `search`, `patent_grants_by_assignee`, `tech_trends`, `top_assignees`, `detail`, `tickers`, `cpc_classes`, `list`
- API: `https://api.uspto.gov/api/v1` (REST JSON, API key required — free registration at https://data.uspto.gov/apis/getting-started)
- Rate limit: 45 requests/minute with automatic retry on 429
- Cache TTL: 24h (patent data updated daily)

**Example response — `ine_portugal` `GDP_GROWTH_YOY`:**
```json
{
  "success": true,
  "indicator": "GDP_GROWTH_YOY",
  "name": "GDP Real Growth YoY (%)",
  "description": "Gross domestic product, chained volume, year-on-year growth rate (Base 2021)",
  "unit": "%",
  "frequency": "quarterly",
  "latest_value": 2.1,
  "latest_period": "4th Quarter 2025",
  "period_change": 0.3,
  "period_change_pct": 16.67,
  "data_points": [{"period": "4th Quarter 2025", "value": 2.1}, "..."],
  "total_observations": 24,
  "source": "INE Portugal (varcd=0013431)"
}
```

**Example response — `ibge_brazil` `IPCA_12M`:**
```json
{
  "success": true,
  "indicator": "IPCA_12M",
  "name": "IPCA 12-Month Cumulative (%)",
  "description": "IPCA consumer price index, 12-month rolling accumulation",
  "unit": "%",
  "frequency": "monthly",
  "latest_value": 5.48,
  "latest_period": "2026-02",
  "period_change": 0.12,
  "period_change_pct": 2.24,
  "data_points": [{"period": "2026-02", "value": 5.48}, "..."],
  "total_observations": 24,
  "source": "https://servicodados.ibge.gov.br/api/v3/agregados/1737/variaveis/2265"
}
```

**Example response — `gdelt_global_events` `PROTEST_ACTIVITY_GLOBAL`:**
```json
{
  "success": true,
  "indicator": "PROTEST_ACTIVITY_GLOBAL",
  "name": "Global Protest Activity Index",
  "description": "Volume intensity of protest-related media coverage worldwide",
  "unit": "volume %",
  "frequency": "hourly",
  "series": "timelinevol",
  "summary": {
    "current": 2.3456,
    "mean_7d": 2.1234,
    "median_7d": 2.0987,
    "min_7d": 0.8765,
    "max_7d": 4.5678,
    "std_7d": 0.6543,
    "mean_24h": 2.4567,
    "latest_date": "20260402000000",
    "data_points": 168
  },
  "timeline": [{"date": "20260401230000", "value": 2.3456}, "..."],
  "source": "GDELT Project DOC 2.0 API"
}
```

**Example — GDELT country risk index:**
```bash
python3 modules/gdelt_global_events.py country_risk CN
# Returns: {"success": true, "country": "CH", "country_name": "China", "risk_score": 58.42, "risk_interpretation": "MODERATE — normal range of geopolitical activity", ...}
python3 modules/gdelt_global_events.py tension US CN
# Returns: {"success": true, "pair": "US-CH", "tension_score": 62.35, "tension_interpretation": "HIGH — predominantly negative bilateral coverage", ...}
```

**Example — PatentsView corporate innovation:**
```bash
python3 modules/patentsview_uspto.py patent_grants_by_assignee NVDA
# Returns: {"success": true, "assignee": "NVIDIA", "total_filings": 15234, "top_cpc_classes": [{"cpc_class": "G06F", "name": "Digital Computing", "count": 12}, ...], ...}
python3 modules/patentsview_uspto.py tech_trends G06N
# Returns: {"success": true, "cpc_class": "G06N", "cpc_name": "AI & Machine Learning", "total_patents": 45678, "top_assignees_in_class": [...], ...}
```

**Batch MCP — Lusophone & Latin American Economy (New in Batch 13):**
```typescript
const lusophoneLatam = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ine_portugal', params: { indicator: 'GDP_GROWTH_YOY' } },
      { tool: 'ine_portugal', params: { indicator: 'CPI_YOY' } },
      { tool: 'ine_portugal', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'ibge_brazil', params: { indicator: 'GDP_YOY' } },
      { tool: 'ibge_brazil', params: { indicator: 'IPCA_12M' } },
      { tool: 'ibge_brazil', params: { indicator: 'UNEMPLOYMENT' } },
      { tool: 'banco_de_portugal', params: { indicator: 'IR_LOANS_HOUSING' } },
      { tool: 'banco_de_portugal', params: { indicator: 'BOP_CURRENT_ACCOUNT' } }
    ]
  })
});
```

**Batch MCP — Global Geopolitical Risk Dashboard (New in Batch 13):**
```typescript
const geopoliticalRisk = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'gdelt_global_events', params: { indicator: 'PROTEST_ACTIVITY_GLOBAL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'MILITARY_ACTIVITY_GLOBAL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'TERROR_THREAT_GLOBAL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'INFLATION_MEDIA_VOL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'TRADE_MEDIA_VOL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'STOCKMARKET_SENTIMENT' } },
      { tool: 'gdelt_global_events', params: { indicator: 'SANCTIONS_MEDIA_VOL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'BANKRUPTCY_MEDIA_VOL' } }
    ]
  })
});
```

**Batch MCP — Innovation Intelligence: Patent Leaders vs R&D Spend (New in Batch 13):**
```typescript
const innovationIntel = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'patentsview_uspto', params: { indicator: 'PATENT_GRANTS_BY_ASSIGNEE', assignee: 'AAPL' } },
      { tool: 'patentsview_uspto', params: { indicator: 'PATENT_GRANTS_BY_ASSIGNEE', assignee: 'MSFT' } },
      { tool: 'patentsview_uspto', params: { indicator: 'PATENT_GRANTS_BY_ASSIGNEE', assignee: 'NVDA' } },
      { tool: 'patentsview_uspto', params: { indicator: 'TECH_TRENDS', cpc_class: 'G06N' } },
      { tool: 'patentsview_uspto', params: { indicator: 'TECH_TRENDS', cpc_class: 'H01L' } },
      { tool: 'oecd_enhanced', params: { indicator: 'RD_GERD_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'RD_GERD_DEU' } },
      { tool: 'oecd_enhanced', params: { indicator: 'RD_GERD_JPN' } }
    ]
  })
});
```

**Coverage totals after Batch 13:**
- 48 government/central bank/regulatory/institutional/alt-data modules
- 34 countries + EU-wide + global + 190 IMF member nations + 38 OECD members: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇭🇺 🇧🇬 🇭🇷 🇨🇾 🇱🇻 🇱🇹 🇱🇺 🇲🇹 🇸🇰 🇸🇮 🇬🇷 🇧🇷 🇪🇺 🌍 🌐
- 930+ indicators from official government, central bank, international institution, geopolitical event, and patent innovation sources
- New in Batch 13: Portuguese national accounts/prices/labour/tourism/trade/construction, Brazilian GDP/IPCA/unemployment/industrial production/retail sales, global geopolitical risk monitoring (protest/military/terror/conflict/economic media sentiment), US patent innovation intelligence (company filings, CPC technology trends, assignee rankings)
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED, HUF 12-pair, GBP 4-pair + EER, EU small-state FX), policy rates (incl. MNB base rate, BoE Bank Rate), interbank rates, monetary aggregates (incl. EA M1/M2/M3, UK M4/M4 lending growth, Brazilian M2), GDP (incl. EU-12 small state accounts, Portuguese/Brazilian quarterly), CPI/HICP/IPCA/PPI/wholesale prices, unemployment (incl. by demographics, EU-12 youth, PNAD), trade, housing prices, construction costs, lending rates, mortgage rates (incl. UK SVR), credit growth, MFI credit to households/NFCs, cost of borrowing indicators, banking FSIs, gold, government debt/deficit/surplus, fiscal accounts (IMF GFS, OECD REV), BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism (incl. Portuguese overnight stays), automotive registrations, investment (GFCF), OTC/exchange-traded derivatives, FX turnover surveys, international debt securities, energy/renewables/GHG/env taxes, digital economy, cashless payments, financial inclusion, banking soundness, portfolio/FDI investment, OECD leading indicators (CLI/BCI/CCI), pension adequacy, R&D expenditure, consumer credit, gilt yield curves, geopolitical risk scores, bilateral tension indices, media sentiment (inflation/trade/equity/sanctions/bankruptcy), patent innovation metrics (company IP portfolios, technology CPC trends, industrial production indices)

#### Batch 14: Latin America Expansion — Mexico (INEGI)

Batch 14 adds the **INEGI Mexico** module, expanding the platform into Central/North America's second-largest economy. Mexico is the 12th-largest economy globally and a critical trading partner for the United States — making INEGI data essential for cross-border trade analysis, nearshoring assessments, and Latin American macro monitoring. This brings total coverage to **35 countries + EU-wide + global + 190 IMF member nations + 38 OECD members**, with **49 government/institutional/regulatory/alt-data modules** and **940+ indicators**.

**INEGI Mexico** (`inegi_mexico`) — Instituto Nacional de Estadística y Geografía:
- GDP: quarterly growth rate vs same quarter previous year (constant 2018 prices, seasonally adjusted)
- Consumer prices: headline CPI monthly rate (INPC, base Jul 2018=100), core inflation excluding food & energy (monthly)
- Labour market: national unemployment rate from the Encuesta Nacional de Ocupación y Empleo (ENOE, monthly)
- Industrial production: total manufacturing production index (base 2018=100, monthly, seasonally adjusted)
- Foreign trade: total merchandise exports and imports in USD millions (monthly, from customs data)
- Consumer confidence: INEGI/Banxico consumer confidence index (seasonally adjusted, monthly)
- Automotive industry: total motor vehicle production units (monthly, from AMIA data via INEGI aggregation) — Mexico is the world's 7th-largest auto producer
- **9 indicators** across GDP, prices, labour, industry, trade, sentiment, and automotive
- **Special commands:** `list` (all available indicators with metadata)
- **CLI aliases:** `gdp`, `inflation`, `trade`, `industry`, `auto`
- API: `https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR` (BIE REST JSON/XML, requires free API token)
- Auth: `INEGI_API_TOKEN` or `INEGI_TOKEN` environment variable (free at https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify)
- Cache TTL: 24h (data updated monthly for most indicators, quarterly for GDP)

**Example response — `inegi_mexico` `GDP_QUARTERLY`:**
```json
{
  "success": true,
  "indicator": "GDP_QUARTERLY",
  "name": "GDP Quarterly Growth (%)",
  "description": "Real GDP year-on-year quarterly growth rate (base 2018, seasonally adjusted)",
  "unit": "%",
  "frequency": "quarterly",
  "latest_value": 1.8,
  "latest_period": "2025-Q4",
  "period_change": -0.3,
  "period_change_pct": -14.29,
  "data_points": [{"period": "2025-Q4", "value": 1.8}, "..."],
  "total_observations": 24,
  "source": "INEGI BIE (indicator 493911)"
}
```

**Example response — `inegi_mexico` `AUTO_PRODUCTION`:**
```json
{
  "success": true,
  "indicator": "AUTO_PRODUCTION",
  "name": "Automotive Production (units)",
  "description": "Total motor vehicle production in Mexico",
  "unit": "units",
  "frequency": "monthly",
  "latest_value": 345678,
  "latest_period": "2026-02",
  "period_change": 12345,
  "period_change_pct": 3.70,
  "data_points": [{"period": "2026-02", "value": 345678}, "..."],
  "total_observations": 24,
  "source": "INEGI BIE (AMIA automotive)"
}
```

**Example — Mexican macro dashboard:**
```bash
python3 modules/inegi_mexico.py list
# Returns all 9 indicators with metadata, latest values, and data freshness
python3 modules/inegi_mexico.py gdp
# Returns: GDP_QUARTERLY latest value + 8-quarter history
python3 modules/inegi_mexico.py trade
# Returns: EXPORTS + IMPORTS latest values + 12-month history
```

**Batch MCP — NAFTA/USMCA Trade Partners Comparison (New in Batch 14):**
```typescript
const usmcaComparison = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'inegi_mexico', params: { indicator: 'GDP_QUARTERLY' } },
      { tool: 'inegi_mexico', params: { indicator: 'CPI' } },
      { tool: 'inegi_mexico', params: { indicator: 'UNEMPLOYMENT' } },
      { tool: 'inegi_mexico', params: { indicator: 'EXPORTS' } },
      { tool: 'statcan_canada', params: { indicator: 'GDP_REAL' } },
      { tool: 'statcan_canada', params: { indicator: 'CPI_ALL_ITEMS' } },
      { tool: 'statcan_canada', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'statcan_canada', params: { indicator: 'MERCHANDISE_EXPORTS' } }
    ]
  })
});
```

**Batch MCP — Latin American Macro Dashboard (New in Batch 14):**
```typescript
const latamDashboard = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'inegi_mexico', params: { indicator: 'GDP_QUARTERLY' } },
      { tool: 'inegi_mexico', params: { indicator: 'CPI' } },
      { tool: 'inegi_mexico', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'ibge_brazil', params: { indicator: 'GDP_YOY' } },
      { tool: 'ibge_brazil', params: { indicator: 'IPCA_12M' } },
      { tool: 'ibge_brazil', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'inegi_mexico', params: { indicator: 'AUTO_PRODUCTION' } },
      { tool: 'ibge_brazil', params: { indicator: 'RETAIL_SALES' } }
    ]
  })
});
```

**Batch MCP — Global Auto Industry Tracker (New in Batch 14):**
```typescript
const autoIndustry = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'inegi_mexico', params: { indicator: 'AUTO_PRODUCTION' } },
      { tool: 'statistics_austria', params: { indicator: 'NEW_CAR_REGISTRATIONS' } },
      { tool: 'destatis_germany', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'estat_japan', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'istat_italy', params: { indicator: 'INDUSTRIAL_PRODUCTION' } },
      { tool: 'inegi_mexico', params: { indicator: 'EXPORTS' } },
      { tool: 'inegi_mexico', params: { indicator: 'INDUSTRIAL_PRODUCTION' } }
    ]
  })
});
```

**Coverage totals after Batch 14:**
- 49 government/central bank/regulatory/institutional/alt-data modules
- 35 countries + EU-wide + global + 190 IMF member nations + 38 OECD members: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇭🇺 🇧🇬 🇭🇷 🇨🇾 🇱🇻 🇱🇹 🇱🇺 🇲🇹 🇸🇰 🇸🇮 🇬🇷 🇧🇷 🇲🇽 🇪🇺 🌍 🌐
- 940+ indicators from official government, central bank, international institution, geopolitical event, patent innovation, and national statistics sources
- New in Batch 14: Mexican national accounts (GDP quarterly), consumer prices (CPI headline + core), labour market (ENOE unemployment), industrial production, foreign trade (exports/imports), consumer confidence, automotive production — the first Central/North American developing economy module, enabling USMCA trade partner comparison and Latin American macro analysis alongside Brazil
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED, HUF 12-pair, GBP 4-pair + EER, EU small-state FX), policy rates (incl. MNB base rate, BoE Bank Rate), interbank rates, monetary aggregates (incl. EA M1/M2/M3, UK M4/M4 lending growth, Brazilian M2), GDP (incl. EU-12 small state accounts, Portuguese/Brazilian/Mexican quarterly), CPI/HICP/IPCA/INPC/PPI/wholesale prices (incl. Mexican core inflation), unemployment (incl. by demographics, EU-12 youth, PNAD, ENOE), trade, housing prices, construction costs, lending rates, mortgage rates (incl. UK SVR), credit growth, MFI credit to households/NFCs, cost of borrowing indicators, banking FSIs, gold, government debt/deficit/surplus, fiscal accounts (IMF GFS, OECD REV), BoP, business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism (incl. Portuguese overnight stays), automotive registrations & production (incl. Mexican auto output), investment (GFCF), OTC/exchange-traded derivatives, FX turnover surveys, international debt securities, energy/renewables/GHG/env taxes, digital economy, cashless payments, financial inclusion, banking soundness, portfolio/FDI investment, OECD leading indicators (CLI/BCI/CCI), pension adequacy, R&D expenditure, consumer credit, gilt yield curves, geopolitical risk scores, bilateral tension indices, media sentiment, patent innovation metrics, consumer confidence indices

#### Batch 15: Global Expansion — South Korea, Thailand, Colombia, EPO Patents, USGS Earthquake, GLEIF LEI

Batch 15 adds **6 new modules** expanding into Southeast Asia (Thailand), East Asia (South Korea), South America (Colombia), and three major global data domains: European patent intelligence (EPO OPS), real-time seismic hazard monitoring (USGS), and global legal entity identification (GLEIF). This brings total coverage to **38 countries + EU-wide + global + 190 IMF member nations + 38 OECD members**, with **55 government/institutional/regulatory/alt-data modules** and **1,010+ indicators**.

**GLEIF LEI Registry** (`gleif_lei`) — Global Legal Entity Identifier Foundation:
- Total active LEI count — all entities with current, valid Legal Entity Identifiers worldwide
- Total lapsed LEI count — registrations that have expired or not been renewed
- Country entity counts: US, GB, DE, JP, FR, CN, CA, LU — number of LEI-registered entities per jurisdiction
- Entity search: fuzzy name search across the global LEI database with status, jurisdiction, registration authority
- Single LEI lookup: full entity details (legal name, legal address, HQ address, registration status, managing LOU, entity category)
- Corporate hierarchy: parent and child relationships for any LEI — ultimate vs immediate parent structure
- **10 predefined indicators** (registry aggregate counts) + 3 special commands (search, lookup, hierarchy)
- API: `https://api.gleif.org/api/v1` (JSON:API, open access, no auth required)
- Cache TTL: 24h (registry data refreshed daily)

**Bank of Thailand** (`bank_of_thailand`) — BOT Monetary & Macro Statistics:
- Policy rate: BOT 1-day bilateral repurchase rate — Thailand's key policy instrument (monthly)
- Interbank rates: weighted-average overnight interbank rate, 1-day private repo rate (monthly)
- BIBOR (Bangkok Interbank Offered Rate): 1-week, 3-month, 6-month, and 1-year tenors (monthly)
- Government bond yields: Thai sovereign benchmarks at 1Y, 5Y, 10Y, and 20Y maturities (monthly)
- Balance of payments: current account balance (USD), international reserves (USD) (monthly)
- FX: THB/USD end-of-period monthly rate
- Monetary aggregates: narrow money (M1), broad money supply (monthly)
- National accounts: real GDP, real GDP year-on-year growth, nominal GDP (annual)
- Consumer prices: headline CPI, headline CPI year-on-year, core CPI, core CPI year-on-year (annual)
- Commercial banking: total assets, loans excl. interbank, deposits excl. interbank, loan-to-deposit ratio (monthly)
- Daily FX rates: comprehensive THB/foreign-currency rates via BOT FX API (daily, 1h cache)
- **27 indicators** across policy rates, interbank/BIBOR, bonds, macro, BoP, FX, monetary, CPI, and banking
- API: `https://gateway.api.bot.or.th` (REST JSON, requires free `BOT_API_KEY` via `X-IBM-Client-Id` header)
- Cache TTL: 1h for FX, 24h for macro series

**DANE Colombia** (`dane_colombia`) — Departamento Administrativo Nacional de Estadística:
- GDP: production approach at current prices in COP billions (quarterly, from PIB_PRODUCCION dataflow)
- Consumer prices: CPI index (monthly, IPC dataflow)
- Labour market: unemployment rate from the Gran Encuesta Integrada de Hogares — GEIH (monthly)
- Industrial production: manufacturing and mining production index (monthly, EMM dataflow)
- Foreign trade: trade balance in USD millions (monthly, BALANZA_COMERCIAL dataflow)
- Producer prices: PPI index (monthly, IPP dataflow)
- Annual manufacturing survey: total manufacturing output in COP millions (annual, EAM dataflow)
- **7 indicators** via SDMX 2.1 REST interface with SDMX-JSON 1.0 parsing
- API: `https://sdmx.dane.gov.co/gateway/rest` (SDMX 2.1 REST, open access, no auth required)
- Cache TTL: 24h (data updated monthly/quarterly by DANE)

**EPO Open Patent Services** (`epo_ops`) — European Patent Office:
- Patent full-text search: query across titles, abstracts, and claims using CQL syntax — returns patent numbers, titles, applicants, IPC classes
- Applicant/company filings: all patent applications from a specific organization or company name — enables corporate IP portfolio analysis
- Patent family: cross-office family members for any patent number (EP/WO/US/JP/CN/KR and more) — essential for understanding global IP protection scope
- EP Register status: procedural status of European patent applications (filed, examination, grant, opposition, appeal)
- IPC technology trends: filing volume analysis by International Patent Classification code with annual publication counts — tracks innovation waves in specific technology domains
- Recent EP grants: newly published European patents (rolling ~30-day window)
- **6 indicators** covering search, corporate IP, families, register status, tech trends, and recent publications
- OAuth2 client credentials authentication (consumer key + secret)
- API: `https://ops.epo.org/3.2/rest-services` (REST XML, OAuth2 token via `https://ops.epo.org/3.2/auth/accesstoken`)
- Auth: `EPO_CONSUMER_KEY` + `EPO_CONSUMER_SECRET` environment variables (free at https://developers.epo.org)
- Rate limit: ~10 requests/second; Cache TTL: 24h

**USGS Earthquake Hazards** (`usgs_earthquake`) — FDSN Event Web Service:
- Significant global events: worldwide earthquakes M5.0+ in the last 24 hours — near real-time monitoring (5-minute cache)
- Recent M4+ worldwide: global seismicity M4.0+ over the past 7 days with full event metadata (magnitude, depth, coordinates, felt reports, tsunami flag)
- PAGER damage alerts: events with PAGER orange+ alert level and magnitude ≥4.5 over the last 30 days — indicates potential economic/casualty impact
- Regional hotspots: M3.0+ activity near five economically significant zones:
  - **Taiwan** (300 km radius from Taipei) — semiconductor manufacturing supply chain risk
  - **Japan** (500 km from Tokyo) — world's 3rd-largest economy seismic exposure
  - **Chile** (800 km from Santiago) — copper/lithium mining region monitoring
  - **Turkey** (400 km from Istanbul) — Bosphorus trade route and infrastructure risk
  - **California** (300 km from Silicon Valley) — tech industry and West Coast infrastructure
- Annual M5+ count: yearly aggregate of significant earthquake events for long-term trend analysis (24h cache)
- DYFI felt reports: "Did You Feel It?" widely-reported events (minfelt ≥100) over the last 7 days — measures population impact
- **10 indicators** across global significance, regional hotspots, damage alerts, and population impact
- API: `https://earthquake.usgs.gov/fdsnws/event/1` (GeoJSON REST, fully open, no auth required)
- Cache TTL: 5 minutes for real-time feeds, 24h for historical/annual queries

**KOSIS South Korea** (`kosis_korea`) — Korean Statistical Information Service (Statistics Korea / KOSTAT):
- GDP: expenditure approach at current prices, quarterly (from National Accounts)
- Consumer prices: CPI all items (base year 2020=100, monthly)
- Labour market: unemployment rate from the Economically Active Population Survey (monthly)
- Industrial production: mining and manufacturing production index (base 2020=100, monthly)
- Merchandise exports: total goods exports by commodity and destination country (monthly)
- Housing market: nationwide apartment price index — critical for Korean household wealth tracking (monthly)
- Semiconductor production: dedicated semiconductor industry production index (monthly) — South Korea is the world's 2nd-largest chip producer (Samsung, SK Hynix)
- **7 indicators** across national accounts, prices, labour, industry, trade, housing, and high-tech manufacturing
- API: `https://kosis.kr/openapi/Param/statisticsParameterData.do` (REST JSON, requires free `KOSIS_API_KEY`)
- Auth: `KOSIS_API_KEY` environment variable (free registration at https://kosis.kr/openapi/)
- Rate limit: ~1,000 requests/day; Cache TTL: 24h

**Example response — `bank_of_thailand` `POLICY_RATE`:**
```json
{
  "success": true,
  "indicator": "POLICY_RATE",
  "name": "BOT Policy Rate (1-Day Bilateral Repo)",
  "description": "Bank of Thailand key policy interest rate",
  "unit": "%",
  "frequency": "monthly",
  "latest_value": 2.25,
  "latest_period": "2026-03",
  "period_change": 0.0,
  "period_change_pct": 0.0,
  "data_points": [{"period": "2026-03", "value": 2.25}, "..."],
  "total_observations": 60,
  "source": "https://gateway.api.bot.or.th"
}
```

**Example response — `usgs_earthquake` `SIGNIFICANT_GLOBAL`:**
```json
{
  "success": true,
  "indicator": "SIGNIFICANT_GLOBAL",
  "name": "Significant Global Earthquakes (M5.0+, 24h)",
  "description": "Worldwide earthquakes with magnitude 5.0 or greater in the last 24 hours",
  "unit": "events",
  "frequency": "real-time",
  "event_count": 3,
  "events": [
    {"mag": 6.2, "place": "148 km SE of Hualien City, Taiwan", "time": "2026-04-01T14:23:45Z", "depth_km": 22.4, "tsunami": 0, "felt": 156},
    "..."
  ],
  "source": "https://earthquake.usgs.gov/fdsnws/event/1"
}
```

**Example response — `kosis_korea` `SEMICONDUCTORS`:**
```json
{
  "success": true,
  "indicator": "SEMICONDUCTORS",
  "name": "Semiconductor Production Index (2020=100)",
  "description": "Mining & manufacturing production index for semiconductor industry",
  "unit": "index",
  "frequency": "monthly",
  "latest_value": 142.8,
  "latest_period": "2026-02",
  "period_change": 3.5,
  "period_change_pct": 2.51,
  "data_points": [{"period": "2026-02", "value": 142.8}, "..."],
  "total_observations": 60,
  "source": "KOSIS (Statistics Korea)"
}
```

**Example — GLEIF entity search:**
```bash
python3 modules/gleif_lei.py search "JPMorgan"
# Returns: {"success": true, "query": "JPMorgan", "results": [{"lei": "8I5DZWZKVSZI1NUHU748", "name": "JPMORGAN CHASE & CO.", "status": "ACTIVE", "jurisdiction": "US-DE", ...}]}
python3 modules/gleif_lei.py lookup 8I5DZWZKVSZI1NUHU748
# Returns: full entity record with legal address, HQ, registration authority, managing LOU, entity category
```

**Batch MCP — Asian Economy Comparison (New in Batch 15):**
```typescript
const asianMacro = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'kosis_korea', params: { indicator: 'GDP' } },
      { tool: 'kosis_korea', params: { indicator: 'CPI' } },
      { tool: 'kosis_korea', params: { indicator: 'UNEMPLOYMENT' } },
      { tool: 'kosis_korea', params: { indicator: 'SEMICONDUCTORS' } },
      { tool: 'bank_of_thailand', params: { indicator: 'GDP_REAL' } },
      { tool: 'bank_of_thailand', params: { indicator: 'HEADLINE_CPI_YOY' } },
      { tool: 'bank_of_thailand', params: { indicator: 'POLICY_RATE' } },
      { tool: 'estat_japan', params: { indicator: 'GDP_NOMINAL' } }
    ]
  })
});
```

**Batch MCP — Global Supply Chain Risk Monitor (New in Batch 15):**
```typescript
const supplyChainRisk = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'usgs_earthquake', params: { indicator: 'HOTSPOT_TAIWAN' } },
      { tool: 'usgs_earthquake', params: { indicator: 'HOTSPOT_JAPAN' } },
      { tool: 'usgs_earthquake', params: { indicator: 'HOTSPOT_CHILE' } },
      { tool: 'kosis_korea', params: { indicator: 'SEMICONDUCTORS' } },
      { tool: 'gdelt_global_events', params: { indicator: 'TRADE_MEDIA_VOL' } },
      { tool: 'gdelt_global_events', params: { indicator: 'country_risk', country: 'TW' } },
      { tool: 'epo_ops', params: { indicator: 'IPC_TRENDS', ipc_class: 'H01L' } },
      { tool: 'patentsview_uspto', params: { indicator: 'TECH_TRENDS', cpc_class: 'H01L' } }
    ]
  })
});
```

**Batch MCP — Emerging Markets Macro Dashboard (New in Batch 15):**
```typescript
const emDashboard = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'dane_colombia', params: { indicator: 'GDP' } },
      { tool: 'dane_colombia', params: { indicator: 'CPI' } },
      { tool: 'dane_colombia', params: { indicator: 'UNEMPLOYMENT' } },
      { tool: 'ibge_brazil', params: { indicator: 'GDP_YOY' } },
      { tool: 'ibge_brazil', params: { indicator: 'IPCA_12M' } },
      { tool: 'inegi_mexico', params: { indicator: 'GDP_QUARTERLY' } },
      { tool: 'inegi_mexico', params: { indicator: 'CPI' } },
      { tool: 'bank_of_thailand', params: { indicator: 'GDP_REAL_YOY' } }
    ]
  })
});
```

**Batch MCP — Global Patent Intelligence (New in Batch 15):**
```typescript
const patentIntel = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'epo_ops', params: { indicator: 'IPC_TRENDS', ipc_class: 'G06N' } },
      { tool: 'epo_ops', params: { indicator: 'IPC_TRENDS', ipc_class: 'H01L' } },
      { tool: 'epo_ops', params: { indicator: 'IPC_TRENDS', ipc_class: 'A61K' } },
      { tool: 'epo_ops', params: { indicator: 'RECENT_GRANTS' } },
      { tool: 'patentsview_uspto', params: { indicator: 'TECH_TRENDS', cpc_class: 'G06N' } },
      { tool: 'patentsview_uspto', params: { indicator: 'TOP_ASSIGNEES' } },
      { tool: 'oecd_enhanced', params: { indicator: 'RD_GERD_USA' } },
      { tool: 'oecd_enhanced', params: { indicator: 'RD_GERD_JPN' } }
    ]
  })
});
```

**Coverage totals after Batch 15:**
- 55 government/central bank/regulatory/institutional/alt-data modules
- 38 countries + EU-wide + global + 190 IMF member nations + 38 OECD members: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇭🇺 🇧🇬 🇭🇷 🇨🇾 🇱🇻 🇱🇹 🇱🇺 🇲🇹 🇸🇰 🇸🇮 🇬🇷 🇧🇷 🇲🇽 🇰🇷 🇹🇭 🇨🇴 🇪🇺 🌍 🌐
- 1,010+ indicators from official government, central bank, international institution, geopolitical event, patent innovation, seismic hazard, entity registry, and national statistics sources
- New in Batch 15: South Korean macro (GDP, CPI, unemployment, industrial production, exports, housing, semiconductors), Thai central bank & macro (policy rate, BIBOR, govt bonds, GDP, CPI, BoP, reserves, FX, monetary, banking), Colombian national statistics (GDP, CPI, unemployment, IPI, trade, PPI, manufacturing), European patent intelligence (EPO search, families, register, IPC trends, recent grants), real-time global earthquake monitoring (M5+ significant events, regional supply-chain hotspots, PAGER damage alerts, DYFI felt reports), global legal entity identification (GLEIF active/lapsed LEI counts, entity search, lookup, corporate hierarchy)
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED, HUF 12-pair, GBP 4-pair + EER, EU small-state FX, THB daily rates), policy rates (incl. MNB base rate, BoE Bank Rate, BOT repo rate), interbank rates (incl. BIBOR), monetary aggregates (incl. EA M1/M2/M3, UK M4, Thai M1/broad), GDP (incl. EU-12 small state, Portuguese/Brazilian/Mexican/Colombian/Thai/Korean quarterly), CPI/HICP/IPCA/INPC/PPI/wholesale prices, unemployment (incl. by demographics, GEIH Colombia, ENOE Mexico, Korean EAP survey), trade, housing prices (incl. Korean apartment index), construction costs, lending rates, mortgage rates, credit growth, MFI credit, cost of borrowing, banking FSIs (incl. Thai commercial bank balance sheet), gold, government debt/deficit/surplus, fiscal accounts, BoP (incl. Thai current account, Colombian trade balance), business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves incl. Thai 1Y–20Y), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism, automotive registrations & production, investment (GFCF), OTC/exchange-traded derivatives, FX turnover surveys, international debt securities, energy/renewables/GHG/env taxes, digital economy, cashless payments, financial inclusion, banking soundness, portfolio/FDI investment, OECD leading indicators, pension adequacy, R&D expenditure, consumer credit, gilt yield curves, geopolitical risk scores, bilateral tension indices, media sentiment, patent innovation metrics (USPTO + EPO), consumer confidence, earthquake/seismic hazard monitoring, legal entity identification (GLEIF), semiconductor production indices

#### Batch 16: Scandinavia Expansion — Norway (SSB Statistics Norway)

Batch 16 adds the **Statistics Norway (SSB)** module, expanding the platform into the Nordic oil-exporting economies and bringing Scandinavian coverage to three countries (Sweden, Denmark, Norway). Norway is Europe's largest petroleum exporter, the world's largest sovereign wealth fund manager (Government Pension Fund Global, ~$1.7 trillion), and a critical bellwether for global energy markets and Nordic monetary policy. This brings total coverage to **39 countries + EU-wide + global + 190 IMF member nations + 38 OECD members**, with **56 government/institutional/regulatory/alt-data modules** and **1,020+ indicators**.

**Statistics Norway (SSB)** (`ssb_norway`) — Statistisk sentralbyrå:
- GDP nominal: Gross domestic product at market values, current prices, in NOK million (annual, table 09189)
- GDP volume growth: Annual change in GDP volume — real growth rate (annual, table 09189)
- CPI index: Consumer Price Index, all items, base year 2015=100 (monthly, table 03013)
- CPI 12-month rate: Consumer price index year-on-year rate of change (monthly, table 03013)
- Unemployment rate: LFS unemployment rate, ages 15-74, both sexes, seasonally adjusted (monthly, table 13760)
- Goods exports: External trade in goods, total exports value in NOK (monthly, table 08799)
- Goods imports: External trade in goods, total imports value in NOK (monthly, table 08799)
- House price index: Price index for existing dwellings, all Norway (quarterly, table 07221)
- House price index (SA): Seasonally adjusted house price index for existing dwellings (quarterly, table 07221)
- Petroleum product deliveries: Total petroleum product deliveries nationwide in million litres (monthly, table 11174) — unique to Norway's oil economy, tracks domestic energy consumption patterns
- Industrial output: Total output at basic values, current prices, in NOK million (annual, table 09170)
- Gross value added: Value added at basic prices, current prices, in NOK million (annual, table 09170)
- **12 indicators** across national accounts, prices, labour, trade, housing, petroleum/energy, and industrial production
- **7 indicator groups** for batch retrieval: `gdp`, `cpi`, `unemployment`, `oil_production`, `trade`, `house_prices`, `industrial`
- Protocol: PxWeb REST API — POST JSON queries, JSON-stat2 responses (same protocol as SCB Sweden, Statistics Finland, Statistics Estonia)
- API: `https://data.ssb.no/api/v0/en/table` (fully open, no API key required, no rate limit)
- Cache TTL: 24h (data refreshed monthly/quarterly by SSB)

**Why Norway matters for financial analysis:**
- **Sovereign wealth:** Norway's Government Pension Fund Global (GPFG) holds ~$1.7T in global equities and bonds — its allocation changes ripple across world markets
- **Oil & gas:** Europe's largest hydrocarbon producer — Norwegian petroleum data is a leading indicator for Brent crude pricing, European energy security, and NOK currency movements
- **Housing market:** Norwegian house prices are among the most closely watched in Scandinavia — high household debt-to-income ratios make housing data critical for Nordic financial stability assessments
- **Nordic monetary policy:** Norges Bank's rate decisions (tracked via GDP/CPI data) influence the broader Scandinavian rate environment (SEK, DKK peg dynamics)
- **Trade exposure:** Norway's trade balance is heavily energy-weighted — tracking exports vs imports reveals terms-of-trade shifts relevant to commodity-linked currencies and European energy importers

**Example response — `ssb_norway` `GDP_GROWTH`:**
```json
{
  "success": true,
  "indicator": "GDP_GROWTH",
  "name": "GDP Volume Growth — Norway (%)",
  "description": "Annual change in GDP volume (real growth rate)",
  "unit": "%",
  "frequency": "annual",
  "table_id": "09189",
  "latest_value": 1.1,
  "latest_period": "2024",
  "period_change": -2.2,
  "period_change_pct": -66.67,
  "data_points": [{"period": "2024", "value": 1.1}, {"period": "2023", "value": 3.3}, "..."],
  "total_observations": 10,
  "source": "https://data.ssb.no/api/v0/en/table/09189"
}
```

**Example response — `ssb_norway` `PETROLEUM_DELIVERIES`:**
```json
{
  "success": true,
  "indicator": "PETROLEUM_DELIVERIES",
  "name": "Petroleum Product Deliveries — Norway (mill. litres)",
  "description": "Total deliveries of petroleum products, nationwide",
  "unit": "million litres",
  "frequency": "monthly",
  "table_id": "11174",
  "latest_value": 702.3,
  "latest_period": "2026M02",
  "period_change": -18.5,
  "period_change_pct": -2.57,
  "data_points": [{"period": "2026M02", "value": 702.3}, {"period": "2026M01", "value": 720.8}, "..."],
  "total_observations": 24,
  "source": "https://data.ssb.no/api/v0/en/table/11174"
}
```

**Batch MCP — Nordic Economy Comparison (New in Batch 16):**
```typescript
const nordicMacro = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ssb_norway', params: { indicator: 'GDP_GROWTH' } },
      { tool: 'ssb_norway', params: { indicator: 'CPI_ANNUAL_RATE' } },
      { tool: 'ssb_norway', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'scb_sweden', params: { indicator: 'GDP_QOQ' } },
      { tool: 'scb_sweden', params: { indicator: 'CPIF_ANNUAL_CHANGE' } },
      { tool: 'statistics_denmark', params: { indicator: 'UNEMPLOYMENT_RATE' } },
      { tool: 'statistics_finland', params: { indicator: 'GDP_QOQ' } },
      { tool: 'statistics_finland', params: { indicator: 'CPI_INDEX' } }
    ]
  })
});
```

**Batch MCP — European Energy & Petroleum Monitor (New in Batch 16):**
```typescript
const energyMonitor = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ssb_norway', params: { indicator: 'PETROLEUM_DELIVERIES' } },
      { tool: 'ssb_norway', params: { indicator: 'TRADE_EXPORTS' } },
      { tool: 'ssb_norway', params: { indicator: 'TRADE_IMPORTS' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'ENERGY_DEPENDENCY', geo: 'EU27_2020' } },
      { tool: 'eurostat_enhanced', params: { indicator: 'RENEWABLE_SHARE_TOTAL', geo: 'NO' } },
      { tool: 'bis_enhanced', params: { indicator: 'FX_TURNOVER_TOTAL' } },
      { tool: 'oecd_enhanced', params: { indicator: 'CLI_OECD' } }
    ]
  })
});
```

**Batch MCP — Scandinavian Housing Market (New in Batch 16):**
```typescript
const nordicHousing = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'ssb_norway', params: { indicator: 'HOUSE_PRICE_INDEX' } },
      { tool: 'ssb_norway', params: { indicator: 'HOUSE_PRICE_INDEX_SA' } },
      { tool: 'scb_sweden', params: { indicator: 'HOUSING_PRICES' } },
      { tool: 'statistics_denmark', params: { indicator: 'HOUSING_PRICES' } },
      { tool: 'statistics_finland', params: { indicator: 'HOUSING_PRICES_INDEX' } },
      { tool: 'rba_enhanced', params: { indicator: 'F5_HOUSING_VARIABLE' } },
      { tool: 'ons_uk', params: { indicator: 'PRIVATE_RENTAL_INDEX' } }
    ]
  })
});
```

**Coverage totals after Batch 16:**
- 56 government/central bank/regulatory/institutional/alt-data modules
- 39 countries + EU-wide + global + 190 IMF member nations + 38 OECD members: 🇩🇪 🇫🇷 🇮🇹 🇳🇱 🇩🇰 🇸🇪 🇪🇸 🇵🇹 🇬🇧 🇨🇦 🇯🇵 🇵🇱 🇹🇼 🇧🇪 🇮🇪 🇫🇮 🇨🇿 🇦🇺 🇦🇪 🇷🇴 🇦🇹 🇪🇪 🇭🇺 🇧🇬 🇭🇷 🇨🇾 🇱🇻 🇱🇹 🇱🇺 🇲🇹 🇸🇰 🇸🇮 🇬🇷 🇧🇷 🇲🇽 🇰🇷 🇹🇭 🇨🇴 🇳🇴 🇪🇺 🌍 🌐
- 1,020+ indicators from official government, central bank, international institution, geopolitical event, patent innovation, seismic hazard, entity registry, and national statistics sources
- New in Batch 16: Norwegian national accounts (GDP nominal + real growth), consumer prices (CPI index 2015=100 + 12-month rate of change), labour market (LFS unemployment rate SA, ages 15-74), external trade (goods exports + imports in NOK), housing market (house price index raw + seasonally adjusted), petroleum product deliveries (unique energy sector indicator for Europe's largest oil exporter), industrial production (total output + gross value added) — the first Nordic oil-economy module, completing Scandinavian trilateral coverage (Sweden, Denmark, Norway)
- Asset classes covered: FX rates (incl. 37-currency RON fixing, 26-pair CAD, 76-currency AED, HUF 12-pair, GBP 4-pair + EER, EU small-state FX, THB daily rates), policy rates (incl. MNB base rate, BoE Bank Rate, BOT repo rate), interbank rates (incl. BIBOR), monetary aggregates (incl. EA M1/M2/M3, UK M4, Thai M1/broad), GDP (incl. EU-12 small state, Portuguese/Brazilian/Mexican/Colombian/Thai/Korean/Norwegian quarterly/annual), CPI/HICP/IPCA/INPC/PPI/wholesale prices, unemployment (incl. by demographics, GEIH Colombia, ENOE Mexico, Korean EAP survey, Norwegian LFS SA), trade, housing prices (incl. Korean apartment index, Norwegian dwelling price index), construction costs, lending rates, mortgage rates, credit growth, MFI credit, cost of borrowing, banking FSIs (incl. Thai commercial bank balance sheet), gold, government debt/deficit/surplus, fiscal accounts, BoP (incl. Thai current account, Colombian trade balance), business surveys, IIP, financial accounts, securities filings, regulatory registers, construction, building approvals, retail trade, bond yields (sovereign yield curves incl. Thai 1Y–20Y), term premiums, income inequality, commodity indices, payment systems, insurance/pension balance sheets, tourism, automotive registrations & production, investment (GFCF), OTC/exchange-traded derivatives, FX turnover surveys, international debt securities, energy/renewables/GHG/env taxes, digital economy, cashless payments, financial inclusion, banking soundness, portfolio/FDI investment, OECD leading indicators, pension adequacy, R&D expenditure, consumer credit, gilt yield curves, geopolitical risk scores, bilateral tension indices, media sentiment, patent innovation metrics (USPTO + EPO), consumer confidence, earthquake/seismic hazard monitoring, legal entity identification (GLEIF), semiconductor production indices, petroleum product deliveries

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
Each of the 1,080 data modules gets an auto-generated REST endpoint:
```
/api/v1/prices?ticker=AAPL
/api/v1/technicals?ticker=AAPL&indicators=rsi,macd
/api/v1/screener?min-cap=10B&sector=Technology
/api/v1/options-chain?ticker=AAPL&expiration=2026-04-17
/api/v1/fred-enhanced?series=GDP&start=2020-01-01
```

---

## Natural Language Queries (DCC)

The Data Command Center (DCC) allows natural language queries against all 1,080 modules:

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
| **ModuleBrowserPanel** | Browse and search all 1,080 modules by category |
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
| Statistics Austria (OGD) | No | Open (CC BY 4.0) | Austrian GDP (nominal/real/annual), CPI (2015=100), PPI (2021=100), wholesale prices, employment, foreign trade, tourism overnight stays, car registrations, industrial/construction production, household consumption, GFCF |
| CZSO Czech Republic (Open Data) | No | Open (CC BY 4.0) | Czech GDP (nominal/real/growth), GVA, GFCF, CPI (YoY/MoM/index/food/housing/transport), unemployment/employment, IPI (total + automotive), construction output, foreign trade |
| Statistics Estonia (PxWeb) | No | Open | Estonian GDP (nominal/real growth), CPI/HICP annual & monthly, employment/unemployment rates, labour force, trade (exports/imports), industrial production index & YoY |
| ECB Enhanced (SDMX) | No | Open | Euro Area M1/M2/M3 monetary aggregates, MFI loans to HH/NFC/housing, composite cost of borrowing, NFC/HH lending rates, HH deposit rate, HICP headline/core/food |
| Eurostat Enhanced (JSON-stat) | No | Open (~100/hr) | EU27 government deficit/debt, fiscal revenue/spending, energy production/consumption/dependency, renewables share, GHG emissions by sector, environmental taxes, digital economy |
| BIS Enhanced (SDMX v2) | No | Open | Global OTC derivatives outstanding, exchange-traded derivatives OI & turnover, FX/IR turnover surveys, international debt securities (5 countries), CPMI cashless payments & macro |
| IMF Enhanced (DBnomics) | No | Open (rate-limited) | FAS financial access (ATMs, branches, mobile money for 190+ countries), FSI banking soundness (NPL, capital, ROA/ROE), CPIS portfolio investment, CDIS FDI positions, GFS government fiscal accounts (revenue, expenditure, tax, social benefits, interest, debt) |
| OECD Enhanced (SDMX 3.0) | No | Open (~60/hr) | CLI leading indicators (6 countries), BCI/CCI confidence, KEI unemployment/CPI/GDP/interest rates, tax revenue structure (3 countries), pension replacement rates, R&D expenditure (GERD/BERD/HERD) |
| BoE IADB Enhanced | No | Open | Gilt zero-coupon yields (5Y/10Y/20Y), Bank Rate, M4 outstanding & lending growth, mortgage SVR, consumer credit, GBP FX (4 crosses), Sterling EER |
| MNB Hungary (SOAP) | No | Open | MNB base rate, HUF FX (12 currencies), CEE & G4 composite baskets |
| EU Small Central Banks (ECB+national) | No | Open | HICP + MFI rates for 9 EU countries, FX from 5 national CBs, Slovenia extras |
| EU Small Statistics (Eurostat) | No | Open (~100/hr) | GDP/CPI/unemployment/employment/govt debt/deficit for 12 smaller EU countries |
| INE Portugal (JSON API) | No | Open | Portuguese GDP real/nominal/per capita, CPI/HICP, unemployment, tourism, exports/imports, trade coverage, construction costs |
| IBGE Brazil (SIDRA API) | No | Open | Brazilian GDP YoY/QoQ, IPCA inflation (monthly/12M/YTD/index), PNAD unemployment, PIM-PF industrial production, PMC retail sales |
| GDELT Project (DOC 2.0) | No | Open (fair use) | Global geopolitical risk: protest/military/terror/conflict/economic media volume & sentiment, country risk scoring, bilateral tension, topic tracking, article search |
| USPTO ODP (PatentsView) | Yes (free) | 45/min | US patent search, grants by assignee (35+ ticker mappings), technology trends by CPC class, top assignees, patent detail |
| INEGI Mexico (BIE API) | Yes (free token) | Open | Mexican GDP quarterly, CPI headline & core inflation, ENOE unemployment, industrial production, exports/imports, consumer confidence, automotive production |
| GLEIF LEI (JSON:API) | No | Open | Global LEI registry: active/lapsed entity counts, entity search/lookup, corporate hierarchy, country-level entity distributions |
| Bank of Thailand (BOT Gateway) | Yes (free key) | Open | BOT policy rate, BIBOR term structure (1W–1Y), Thai govt bonds (1Y–20Y), GDP, CPI, current account, reserves, THB FX, monetary aggregates, commercial bank stats |
| DANE Colombia (SDMX) | No | Open | Colombian GDP (production approach), CPI, GEIH unemployment, industrial production (EMM), trade balance, PPI, annual manufacturing survey |
| EPO Open Patent Services | Yes (free OAuth2) | ~10/s | European/global patent search, applicant filings, patent family members, EP register status, IPC technology trends, recent EP grants |
| USGS Earthquake Hazards (FDSN) | No | Open (real-time) | Global M5+ events, M4+ seismicity, PAGER damage alerts, regional hotspots (Taiwan/Japan/Chile/Turkey/California), annual counts, DYFI felt reports |
| KOSIS South Korea (KOSTAT) | Yes (free key) | ~1,000/day | Korean GDP, CPI, unemployment, industrial production, exports, housing prices, semiconductor production index |
| SSB Norway (PxWeb) | No | Open (no limit) | Norwegian GDP (nominal/growth), CPI (index 2015=100/12mo rate), unemployment (SA), goods exports/imports, house price index (raw/SA), petroleum deliveries, industrial output, gross value added |

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

49 phases completed across 9 categories:

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
├── modules/                          # 1,080 Python data modules
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
│   ├── statistics_austria.py        # Statistics Austria (GDP, CPI, PPI, trade, tourism, industry)
│   ├── czso_czech.py               # CZSO Czech Republic (GDP, CPI, labour, IPI, trade)
│   ├── statistics_estonia.py       # Statistics Estonia (GDP, CPI, labour, trade, IPI)
│   ├── ecb_enhanced.py             # ECB Enhanced (M1/M2/M3, MFI credit, HICP, rates)
│   ├── eurostat_enhanced.py        # Eurostat Enhanced (govt finance, energy, emissions, digital)
│   ├── bis_enhanced.py             # BIS Enhanced (derivatives, FX turnover, debt, payments)
│   ├── imf_enhanced.py             # IMF Enhanced (FAS, FSI, CPIS, CDIS, GFS — 190+ countries)
│   ├── oecd_enhanced.py            # OECD Enhanced (CLI, KEI, tax, pensions, R&D — 38 OECD members)
│   ├── boe_iadb_enhanced.py        # Bank of England IADB (gilt yields, M4, FX, rates)
│   ├── mnb_hungary.py              # MNB Hungary (base rate, HUF FX, CEE/G4 baskets)
│   ├── eu_small_central_banks.py   # EU Small CBs (9 countries: BG/HR/CY/LV/LT/LU/MT/SK/SI)
│   ├── eu_small_statistics.py      # EU Small Statistics (12 countries via Eurostat)
│   ├── ine_portugal.py             # INE Portugal (GDP, CPI, labour, tourism, trade, construction)
│   ├── ibge_brazil.py              # IBGE Brazil (GDP, IPCA, unemployment, industry, retail)
│   ├── gdelt_global_events.py      # GDELT Global Events (geopolitical risk, media sentiment)
│   ├── patentsview_uspto.py        # USPTO PatentsView (patent search, tech trends, assignees)
│   ├── inegi_mexico.py             # INEGI Mexico (GDP, CPI, unemployment, trade, auto)
│   ├── gleif_lei.py                # GLEIF LEI Registry (entity search, hierarchy, counts)
│   ├── bank_of_thailand.py         # Bank of Thailand (rates, bonds, GDP, CPI, FX, banking)
│   ├── dane_colombia.py            # DANE Colombia SDMX (GDP, CPI, unemployment, trade)
│   ├── epo_ops.py                  # EPO Open Patent Services (search, families, trends)
│   ├── usgs_earthquake.py          # USGS Earthquake Hazards (real-time seismic events)
│   ├── kosis_korea.py              # KOSIS South Korea (GDP, CPI, industry, semiconductors)
│   ├── ssb_norway.py               # SSB Norway (GDP, CPI, unemployment, trade, house prices, petroleum, industry)
│   ├── ... (1,080 modules total)
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
USPTO_ODP_API_KEY=                   # USPTO Open Data Portal (free at https://data.uspto.gov/apis/getting-started)
INEGI_API_TOKEN=                     # INEGI Mexico BIE (free at https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify)
BOT_API_KEY=                         # Bank of Thailand Gateway (free at https://apiportal.bot.or.th)
EPO_CONSUMER_KEY=                    # EPO Open Patent Services (free at https://developers.epo.org)
EPO_CONSUMER_SECRET=                 # EPO OPS OAuth2 client secret
KOSIS_API_KEY=                       # KOSIS South Korea (free at https://kosis.kr/openapi/)

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

*1,080 modules • 49 phases • 38 countries + EU-wide + global + 190 IMF member nations + 38 OECD members (22 EU + UK + Canada + Japan + Poland + Taiwan + Ireland + Czech Republic + Australia + UAE + Romania + Austria + Estonia + Hungary + Bulgaria + Croatia + Cyprus + Latvia + Lithuania + Luxembourg + Malta + Slovakia + Slovenia + Greece + Brazil + Mexico + South Korea + Thailand + Colombia + Euro Area + EU27 + BIS global + IMF global + OECD + GDELT global + EPO global + USGS global + GLEIF global) • 55 government/central bank/institutional/alt-data modules • 1,010+ macro, geopolitical, patent, seismic & entity indicators • The data layer powering the MoneyClawX ecosystem*
