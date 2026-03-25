# QuantClaw Data — Phases 94-113: Global Public Data Sources
# FREE government/institutional economic & financial data → unified CLI/MCP

## Overview
20 modules scraping/API-ing free public data sources worldwide.
All data that hedge funds pay $50K+/yr for but is actually free at the source.

---

## Phase Plan

### 94. World Bank Open Data
**Source:** https://api.worldbank.org/v2/ (REST API, no key needed)
**Data:** GDP, GNI, inflation, trade balance, FDI, poverty rates for 217 countries
**CLI:** `python cli.py worldbank GDP USA`, `worldbank-compare GDP USA CHN DEU`
**Scrape freq:** Weekly (data updates quarterly/annually)
**Why:** Foundation for any macro model. Compare any country on 1,400+ indicators.

### 95. IMF World Economic Outlook
**Source:** https://www.imf.org/external/datamapper/api/ (JSON API, free)
**Data:** GDP forecasts, inflation projections, current account, govt debt for 190 countries
**CLI:** `python cli.py imf-outlook USA`, `imf-forecast GDP 2026 2027`
**Scrape freq:** Twice yearly (April WEO + October WEO updates)
**Why:** The single most-cited macro forecast in finance. Every hedge fund tracks revisions.

### 96. CIA World Factbook
**Source:** https://www.cia.gov/the-world-factbook/ (bulk JSON download available)
**Data:** Country profiles, military expenditure, demographics, energy production, trade partners, natural resources
**CLI:** `python cli.py factbook Israel`, `factbook-compare military USA CHN RUS`
**Scrape freq:** Monthly (updates irregularly, ~quarterly)
**Why:** Geopolitical risk scoring. Defense sector analysis. Commodity supply mapping.

### 97. US BLS (Bureau of Labor Statistics)
**Source:** https://api.bls.gov/publicAPI/v2/ (free API, 500 req/day with key)
**Data:** CPI components, PPI, employment by sector, wages, productivity, import/export prices
**CLI:** `python cli.py bls-cpi`, `bls-employment`, `bls-wages sector=tech`
**Scrape freq:** Monthly (aligned with release calendar — CPI 2nd week, jobs 1st Friday)
**Why:** CPI components predict Fed moves. Wage data = inflation leading indicator. Every quant needs this.

### 98. US Census Bureau Economic Indicators
**Source:** https://api.census.gov/ (free API key)
**Data:** Retail sales, housing starts, building permits, trade deficit, manufacturing orders, business inventories
**CLI:** `python cli.py census-retail`, `census-housing`, `census-trade`
**Scrape freq:** Monthly (each has specific release date)
**Why:** Retail sales = consumer health. Housing = leading indicator. Trade deficit = currency impact.

### 99. Eurostat (EU Statistics)
**Source:** https://ec.europa.eu/eurostat/api/ (JSON/SDMX API, free)
**Data:** EU GDP, HICP inflation, unemployment, industrial production, trade for 27 EU countries
**CLI:** `python cli.py eurostat GDP DEU`, `eurostat-hicp`, `eurostat-unemployment FRA`
**Scrape freq:** Weekly (various monthly/quarterly releases)
**Why:** Europe = 2nd largest economy. EU data directly moves EUR/USD, European equities.

### 100. Bank of Japan / BOJ Statistics
**Source:** https://www.stat-search.boj.or.jp/ssi/html/nme_base.html (API available)
**Data:** Japanese GDP, monetary base, interest rates, FX reserves, Tankan survey
**CLI:** `python cli.py boj-tankan`, `boj-monetary`, `boj-fx-reserves`
**Scrape freq:** Monthly (Tankan quarterly)
**Why:** JPY carry trade = global risk indicator. BOJ policy affects all markets.

### 101. People's Bank of China / NBS China
**Source:** https://data.stats.gov.cn/english/ (scrape) + https://www.pbc.gov.cn (scrape)
**Data:** China GDP, PMI, trade surplus, FX reserves, loan growth, property prices
**CLI:** `python cli.py china-pmi`, `china-trade`, `china-property`, `china-credit`
**Scrape freq:** Monthly (NBS releases mid-month)
**Why:** China = world's factory. PMI moves copper, iron ore, AUD. Property crisis = global contagion.

### 102. OECD Data Explorer
**Source:** https://data-explorer.oecd.org/ (SDMX REST API, free)
**Data:** Leading indicators (CLI), composite indicators, productivity, housing prices, tax revenue for 38 OECD countries
**CLI:** `python cli.py oecd-cli`, `oecd-housing`, `oecd-productivity USA`
**Scrape freq:** Monthly (CLI updated monthly)
**Why:** OECD CLI (Composite Leading Indicator) = most reliable recession predictor globally.

### 103. UN Comtrade (International Trade)
**Source:** https://comtradeapi.un.org/ (free API, 500 req/hr)
**Data:** Bilateral trade flows, commodity imports/exports, trade dependencies between any 2 countries
**CLI:** `python cli.py comtrade USA CHN`, `comtrade-commodity oil`, `comtrade-dependency ISR`
**Scrape freq:** Monthly (data lags 2-3 months)
**Why:** Trade war impact modeling. Supply chain risk. Sanctions analysis.

### 104. FRED Enhanced (300+ Series)
**Source:** https://api.stlouisfed.org/fred/ (free API key: already have)
**Data:** Yield curve (2s10s, 3m10y), M2 money supply, consumer credit, bank lending, leading index, financial conditions
**CLI:** `python cli.py fred-yield-curve`, `fred-financial-conditions`, `fred-money-supply`, `fred-leading-index`
**Scrape freq:** Daily for rates, weekly for most, monthly for some
**Why:** We already use FRED for basics. This expands to 300+ key series that institutional quants track.

### 105. ECB Statistical Data Warehouse
**Source:** https://data.ecb.europa.eu/data/ (SDMX REST API, free)
**Data:** Euro area interest rates, monetary aggregates (M1/M2/M3), bank lending, TARGET balances, securities holdings
**CLI:** `python cli.py ecb-rates`, `ecb-lending`, `ecb-money-supply`, `ecb-target-balances`
**Scrape freq:** Weekly (rates daily, lending monthly)
**Why:** ECB policy = EUR/USD driver. TARGET balances = EU fragmentation risk indicator.

### 106. Global PMI Aggregator
**Source:** S&P Global PMI (scrape press releases), ISM (scrape), Caixin China (scrape)
**Data:** Manufacturing & Services PMI for 30+ countries, composite index, new orders, employment sub-indices
**CLI:** `python cli.py pmi global`, `pmi USA manufacturing`, `pmi-heatmap`
**Scrape freq:** Monthly (1st & 3rd business day of month)
**Why:** THE leading indicator. PMI > 50 = expansion. Every macro trader watches this.

### 107. Government Bond Yields (Global)
**Source:** Investing.com (scrape), ECB, BOJ, Treasury.gov
**Data:** 10Y yields for 40+ countries, real yields, breakeven inflation, term premiums
**CLI:** `python cli.py global-yields`, `yield-spread USA DEU`, `real-yields USA`
**Scrape freq:** Daily
**Why:** Bond yields drive EVERYTHING — equity valuations, currency, credit, housing. Global yield map = risk sentiment.

### 108. Sovereign Wealth Fund Tracker
**Source:** SWFI (scrape swfinstitute.org), NBIM (Norway), GIC, ADIA annual reports
**Data:** SWF AUM, allocation changes, major equity/real estate investments, top holdings
**CLI:** `python cli.py swf-list`, `swf-holdings norway`, `swf-trends`
**Scrape freq:** Quarterly (filings lag 45-90 days)
**Why:** SWFs manage $12T+. Their allocation shifts = massive market impact. Norway alone = $1.7T.

### 109. Central Bank Balance Sheets
**Source:** Fed H.4.1, ECB, BOJ, PBOC (various free APIs/PDFs)
**Data:** Total assets, QE holdings, reverse repo, bank reserves, lending facilities
**CLI:** `python cli.py cb-balance-sheet FED`, `cb-compare FED ECB BOJ`, `cb-qe-tracker`
**Scrape freq:** Weekly (Fed H.4.1 = Thursday, ECB = weekly)
**Why:** Central bank liquidity = #1 driver of risk assets since 2008. QT/QE cycles predict S&P direction.

### 110. Global Shipping & Trade Indicators
**Source:** Baltic Exchange (scrape), Freightos (API), UNCTAD
**Data:** Baltic Dry Index, container freight rates, port congestion, ship tracking volumes
**CLI:** `python cli.py shipping-bdi`, `shipping-containers`, `shipping-congestion`
**Scrape freq:** Daily (BDI), weekly (container rates)
**Why:** Shipping = real-time global trade health. BDI predicts manufacturing. Container rates = inflation input.

### 111. Global Real Estate Indices
**Source:** FRED (Case-Shiller), Eurostat (house prices), BIS residential property
**Data:** Home prices by country/city, rent indices, housing affordability, mortgage rates
**CLI:** `python cli.py housing USA`, `housing-compare NYC LON TLV`, `housing-affordability`
**Scrape freq:** Monthly (most indices monthly/quarterly)
**Why:** Real estate = largest asset class. Housing weakness = recession signal. Affects banks, REITs, consumer.

### 112. Energy & Commodity Inventories
**Source:** EIA (api.eia.gov, free key), IEA (scrape monthly reports)
**Data:** Crude oil inventories, natural gas storage, strategic petroleum reserve, refinery utilization, renewable capacity
**CLI:** `python cli.py eia-crude`, `eia-natgas`, `eia-spr`, `eia-renewable`
**Scrape freq:** Weekly (EIA Wednesday 10:30 ET for crude, Thursday for natgas)
**Why:** EIA inventory = single biggest weekly mover for oil prices. Energy = inflation input.

### 113. Global Debt Monitor
**Source:** BIS (bis.org/statistics), IMF Fiscal Monitor, World Bank
**Data:** Govt debt/GDP ratios, corporate debt, household debt, credit gaps for 60+ countries
**CLI:** `python cli.py debt-monitor USA`, `debt-compare G7`, `credit-gap CHN`
**Scrape freq:** Quarterly (BIS quarterly review)
**Why:** Debt sustainability = sovereign crisis predictor. Credit gaps predicted 2008. Japan debt/GDP = 260%.

---

## Data Source Summary

| # | Source | API Type | Key Needed? | Update Freq | Countries |
|---|--------|----------|-------------|-------------|-----------|
| 94 | World Bank | REST API | No | Weekly | 217 |
| 95 | IMF WEO | JSON API | No | 2x/year | 190 |
| 96 | CIA Factbook | Bulk JSON | No | Monthly | 266 |
| 97 | US BLS | REST API | Free key | Monthly | US |
| 98 | US Census | REST API | Free key | Monthly | US |
| 99 | Eurostat | SDMX API | No | Weekly | 27 EU |
| 100 | BOJ | API/scrape | No | Monthly | Japan |
| 101 | NBS China | Scrape | No | Monthly | China |
| 102 | OECD | SDMX API | No | Monthly | 38 |
| 103 | UN Comtrade | REST API | Free key | Monthly | 200+ |
| 104 | FRED Enhanced | REST API | Free key ✅ | Daily-Monthly | US/Global |
| 105 | ECB | SDMX API | No | Weekly | 20 Euro |
| 106 | PMI Aggregator | Scrape | No | Monthly | 30+ |
| 107 | Global Yields | Scrape/API | No | Daily | 40+ |
| 108 | SWF Tracker | Scrape | No | Quarterly | 20+ |
| 109 | CB Balance Sheets | API/scrape | No | Weekly | 4 major |
| 110 | Shipping | Scrape/API | No | Daily-Weekly | Global |
| 111 | Real Estate | API/scrape | No | Monthly | 60+ |
| 112 | EIA Energy | REST API | Free key | Weekly | US/Global |
| 113 | Global Debt | Scrape/API | No | Quarterly | 60+ |

## Scrape Schedule Summary

| Frequency | Modules | Cron Pattern |
|-----------|---------|-------------|
| **Daily** | Yields (107), Shipping (110) | `0 18 * * *` (after US close) |
| **Weekly** | World Bank (94), FRED (104), ECB (105), CB Balance (109), EIA (112) | `0 6 * * SAT` |
| **Monthly** | BLS (97), Census (98), Eurostat (99), BOJ (100), China (101), OECD (102), Comtrade (103), PMI (106), Housing (111) | `0 6 15 * *` (mid-month) |
| **Quarterly** | IMF (95), SWF (108), Debt (113) | `0 6 1 1,4,7,10 *` |
| **As Updated** | CIA Factbook (96) | `0 6 1 * *` (monthly check) |

## Beyond 113 — More Free Sources to Map

After these 20, there's MORE gold:
- **SEC XBRL** — Machine-readable financials for every US public company
- **OpenStreetMap** — Store count changes, geographic expansion signals
- **Global Fishing Watch** — Maritime activity anomalies
- **NASA Earth Data** — Drought, wildfire, natural disaster economic impact
- **USDA** — Crop reports, livestock, farm prices (huge for commodity trading)
- **WTO** — Trade dispute tracker, tariff databases
- **ILO** — Global labor statistics
- **WHO** — Pandemic/health emergency economic impact data
- **Patent offices** — EPO (Europe), CNIPA (China), JPO (Japan) — expand beyond USPTO
- **Electricity grids** — ENTSO-E (Europe), CAISO (California) — industrial activity proxy
- **Airport traffic** — Eurocontrol, FAA — real-time economic activity proxy
- **Container port data** — Shanghai, Rotterdam, LA/Long Beach throughput
- **Satellite AIS** — Ship tracking for oil tanker flows, grain shipments
- **GitHub/StackOverflow** — Tech hiring proxy, developer activity trends
