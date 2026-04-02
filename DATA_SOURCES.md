# QuantClaw Data Sources — Complete Reference for AI Agents

> **1,079 Python modules** across 9+ categories. Access via MCP tool calls, REST API, or direct CLI.
> This file is THE reference for AI agents (claws) to know what data is available and how to get it.

**Base URL:** `http://localhost:3055` (local) / `https://data.quantclaw.org` (production)
**MCP Proxy:** `http://localhost:3056/api/data`

---

## Quick Lookup — Common Queries → Modules

| Query | Modules |
|-------|---------|
| GDP data | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `rba_enhanced` (H1 real/nominal GDP), `uae_data`, `destatis_germany`, `ine_spain`, `statistics_austria`, `czso_czech`, `statistics_estonia`, `eurostat_macro`, `inegi_mexico`, `ibge_brazil`, `ine_portugal` |
| Inflation / CPI | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `nbb_belgium`, `abs_australia_sdmx`, `uae_data`, `destatis_germany`, `ine_spain`, `statbel_belgium`, `statistics_austria`, `czso_czech`, `statistics_estonia`, `ecb_enhanced` (EA HICP headline/core/food), `bls` |
| Unemployment | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `destatis_germany`, `ine_spain`, `statbel_belgium`, `statistics_austria`, `czso_czech`, `statistics_estonia`, `bls`, `inegi_mexico` (ENOE), `ibge_brazil` (PNAD), `ine_portugal` |
| Stock price / quote | `prices`, `market_quote`, `alpha_picker`, `tiingo`, `polygon_io` |
| Technical analysis | `technicals`, `breadth_indicators`, `momentum_factor_backtest` |
| Options data | `options_chain`, `options_flow`, `cboe_put_call`, `volatility_surface` |
| Crypto prices | `coingecko_crypto`, `crypto_onchain`, `bitcoin_onchain` |
| CZK exchange rates | `cnb_czech` (CZK/EUR, CZK/USD, CZK/GBP + 9 more FX pairs, daily fixing) |
| PRIBOR rates | `cnb_czech` (O/N, 1W, 2W, 1M, 3M, 6M, 1Y interbank rates) |
| Czech central bank | `cnb_czech` (2W repo, discount, Lombard policy rates) |
| PLN exchange rates | `nbp_poland` (Table A mid, Table B exotic, Table C bid/ask, gold) |
| TWD exchange rates | `cbc_taiwan` (TWD/USD close, buy, sell) |
| EUR exchange rates | `banque_de_france`, `riksbank_sweden`, `banco_de_portugal`, `ecb_fx_rates`, `alphavantage_fx` |
| Bond yields | `bundesbank_sdmx`, `riksbank_sweden`, `danmarks_nationalbank`, `rba_enhanced` (AU 2Y–10Y + indexed), `bank_of_canada_valet` (GoC 2Y–30Y + RRB + T-bills), `treasury_curve`, `yield_curve` |
| Central bank rates | `bundesbank_sdmx` (ECB), `riksbank_sweden`, `bank_of_england`, `fed_policy`, `cbc_taiwan` (CBC), `central_bank_ireland` (ECB), `danmarks_nationalbank` (DN), `cnb_czech` (CNB 2W repo), `rba_enhanced` (RBA cash rate + intl comparison: Fed/BOJ/ECB/BOE/BOC), `bank_of_canada_valet` (BoC overnight, bank rate, CORRA) |
| Euribor rates | `banco_de_espana`, `central_bank_ireland` |
| DKK exchange rates | `danmarks_nationalbank` (EUR/USD/GBP/JPY/CHF/NOK/SEK per DKK) |
| Belgian macro / BoP | `nbb_belgium` (BoP, HICP, financial accounts, IIP, govt finance, business surveys) |
| Irish macro data | `cso_ireland` (GDP/GNP, CPI, unemployment, retail, housing, trade) |
| Irish banking / rates | `central_bank_ireland` (ECB rates, Euribor, retail rates, mortgages, debt, reserves) |
| Finnish macro data | `statistics_finland` (GDP, CPI, unemployment, industrial output, trade, housing) |
| Danish central bank | `danmarks_nationalbank` (DN policy rates, DKK FX, bond yields, BoP, MFI, govt securities) |
| Polish macro / FX | `nbp_poland` (FX rates 32+ currencies, bid/ask, gold PLN/g) |
| Taiwan monetary | `cbc_taiwan` (policy rates, M1A/M1B/M2, deposit/lending rates, TWD/USD) |
| UK macro data | `ons_uk` (GDP, CPIH, retail, trade, labour, construction, rental) |
| Canadian macro data | `statcan_canada` (GDP, CPI, labour, trade, retail, housing) |
| Japanese macro data | `estat_japan` (CPI, GDP, unemployment, trade, industry, housing) |
| Portuguese banking | `banco_de_portugal` (lending/deposit rates, BoP, FX, NPL, CET1, FSI) |
| Earnings data | `earnings_calendar_enhanced`, `earnings_transcripts_nlp`, `ai_earnings_analyzer` |
| Insider trades | `insider_trades`, `openinsider`, `fmp_insider_trading` |
| Congress trades | `congress_trades`, `quiver_quant_wallstreetbets` |
| Housing data | `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `ine_spain` (HPI general/YoY/QoQ), `fred_housing`, `zillow_zhvi` |
| Gold price (PLN) | `nbp_poland` |
| Australian macro data | `abs_australia_sdmx` (GDP, CPI, labour force, BoP, retail trade, building approvals, trade), `rba_enhanced` (RBA cash rate, govt bonds, lending rates, AUD FX, credit growth, M3, GDP) |
| UAE macro / FX | `uae_data` (CBUAE 76-currency FX, GDP, CPI, M2, reserves, trade) |
| German statistics (ext) | `destatis_germany` (GENESIS GDP, CPI/HICP, employment, trade, IPI, PPI, construction) |
| Japanese filings | `edinet_japan` (annual/quarterly securities reports, large shareholding, tender offers) |
| UK regulatory data | `fca_uk` (authorized firms, individuals, permissions, disciplinary, regulated markets) |
| Trade balance | `bundesbank_sdmx`, `insee_france`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `banco_de_portugal`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `nbb_belgium`, `danmarks_nationalbank`, `abs_australia_sdmx`, `destatis_germany`, `ine_spain`, `statistics_austria`, `czso_czech`, `statistics_estonia` |
| ESG / Climate | `carbon_footprint`, `climate_risk`, `eu_taxonomy_alignment`, `esg_decomposition` |
| Sentiment | `reddit_sentiment`, `news_sentiment`, `cnn_fear_greed`, `social_sentiment_spikes` |
| Company profile | `company_profile`, `screener`, `alpha_picker` |
| Short interest | `short_interest`, `short_volume`, `finra_short_interest` |
| IPO / SPAC | `ipo_pipeline`, `spac_tracker`, `spac_lifecycle` |
| AUD exchange rates | `rba_enhanced` (AUD/USD, AUD/EUR, AUD/GBP, AUD/JPY, AUD/CNY, TWI) |
| AU lending rates | `rba_enhanced` (housing variable/discounted/3Y fixed, credit card, SME lending) |
| AU credit growth | `rba_enhanced` (housing credit MoM/YoY, total credit MoM/YoY, M3 MoM/YoY, broad money) |
| International rate comparison | `rba_enhanced` (F13: Fed, BOJ, ECB, BOE, BOC, RBA side-by-side) |
| RON exchange rates | `bnr_romania` (37-currency daily BNR FX fixing + gold XAU + SDR, 10-day history) |
| CAD exchange rates | `bank_of_canada_valet` (CAD vs 26 currencies — USD/EUR/GBP/JPY/CHF/AUD + 20 more) |
| GoC bond yields | `bank_of_canada_valet` (2Y/3Y/5Y/7Y/10Y/30Y benchmarks + RRB + T-bills + avg yields) |
| Canadian rates | `bank_of_canada_valet` (overnight, bank rate, CORRA, prime, mortgage 1Y/3Y/5Y, GIC 1Y/5Y) |
| Spanish macro data | `ine_spain` (GDP, CPI, EPA unemployment, IPI, housing prices, trade) + `banco_de_espana` (Euribor, lending, BoP) |
| Dutch banking / FSI | `dnb_netherlands` (FSIs, banking structure, insurance/pension, payments, monetary, household rates) |
| Belgian statistics | `statbel_belgium` (CPI/HICP, unemployment by demographics, retail, Gini, demographics) + `nbb_belgium` (BoP, govt finance, surveys) |
| Romanian FX data | `bnr_romania` (BNR daily reference rates for RON/EUR, RON/USD + 35 more currencies + gold) |
| Austrian macro data | `statistics_austria` (GDP nominal/real, CPI, PPI, wholesale prices, employment, trade, tourism, industry, construction, investment) |
| Tourism data | `statistics_austria` (overnight stays, accommodation turnover index), `world_bank_global_indices` |
| Industrial production | `statistics_austria`, `destatis_germany`, `insee_france`, `istat_italy`, `ine_spain`, `statistics_finland`, `estat_japan`, `czso_czech` (total + automotive), `statistics_estonia` |
| Producer prices / PPI | `statistics_austria` (Erzeugerpreisindex 2021=100), `destatis_germany` (PPI monthly/annual), `fred_enhanced` |
| Income inequality | `statbel_belgium` (Gini coefficient, Belgium) |
| Commodity price index | `bank_of_canada_valet` (BCPI total, energy, metals & minerals) |
| Monetary aggregates (EA) | `ecb_enhanced` (M1/M2/M3 outstanding, MFI credit HH/NFC/housing), `nbb_belgium` (M1/M3) |
| EA cost of borrowing | `ecb_enhanced` (composite cost of borrowing NFC & HH housing, MFI new loan/deposit rates) |
| EU government debt/deficit | `eurostat_enhanced` (Maastricht debt/deficit % GDP, expenditure, revenue — all 27 Member States) |
| EU energy balance | `eurostat_enhanced` (production, consumption, import dependency, renewable share by sector) |
| Greenhouse gas emissions | `eurostat_enhanced` (total, energy, industry, transport, agriculture — Mt CO₂eq per country) |
| Environmental taxes | `eurostat_enhanced` (total, energy, transport — % GDP per country) |
| OTC derivatives market | `bis_enhanced` (total notional, swaps, gross market value, NFC counterparties — semiannual) |
| Exchange-traded derivatives | `bis_enhanced` (FX/IR/equity/commodity open interest & turnover — quarterly) |
| FX market turnover | `bis_enhanced` (total daily avg, spot, OTC IR derivatives — triennial BIS survey) |
| International debt securities | `bis_enhanced` (outstanding by country: US, UK, Japan, China, Germany — quarterly) |
| Cashless payments | `bis_enhanced` (CPMI cashless payment values — US, UK, China — annual) |
| Czech macro statistics | `czso_czech` (GDP, CPI, labour, IPI, construction, trade) + `cnb_czech` (FX, PRIBOR, policy rates) |
| Estonian macro data | `statistics_estonia` (GDP, CPI/HICP, employment, trade, industrial production) |
| Energy data | `eia_energy`, `crude_oil_fundamentals`, `natural_gas_supply_demand`, `opec` |
| Agriculture | `usda_agriculture`, `crop_yield_forecaster`, `agricultural_commodities` |
| Banking soundness / NPL | `imf_enhanced` (FSI: NPL ratio, regulatory capital, CET1, ROA, ROE — 190+ countries) |
| Financial inclusion | `imf_enhanced` (FAS: ATMs, bank branches, deposit accounts, mobile money per capita — 190+ countries) |
| Cross-border investment | `imf_enhanced` (CPIS: portfolio equity/debt assets; CDIS: inward/outward FDI equity & debt — 190+ countries) |
| Government fiscal accounts | `imf_enhanced` (GFS: revenue, expense, tax, expenditure, social benefits, interest, investment, liabilities — 190+ countries), `eurostat_enhanced` (EU27 deficit/debt) |
| IMF data | `imf_enhanced` (FAS + FSI + CPIS + CDIS + GFS via DBnomics — 29 indicators, 190+ countries) |
| OECD leading indicators | `oecd_enhanced` (CLI amplitude-adjusted for USA/GBR/DEU/JPN/FRA/OECD, BCI/CCI confidence) |
| OECD economic data | `oecd_enhanced` (KEI: unemployment, CPI YoY, GDP, short/long rates — USA) |
| Tax revenue structure | `oecd_enhanced` (REV: total tax, income tax, corporate tax, SSC, goods & services — % GDP) |
| Pension adequacy | `oecd_enhanced` (PAG: gross replacement rates, life expectancy at 65, employment 55-64) |
| R&D expenditure | `oecd_enhanced` (MSTI: GERD, BERD, HERD as % GDP — USA, DEU, JPN) |
| BoE Bank Rate | `boe_iadb_enhanced` (Bank Rate, M4, M4 lending growth, mortgage SVR, consumer credit) |
| UK gilt yields | `boe_iadb_enhanced` (gilt zero-coupon 5Y/10Y/20Y + moving averages, Svensson model) |
| GBP exchange rates | `boe_iadb_enhanced` (GBP/USD, GBP/EUR, GBP/JPY, GBP/CHF + sterling EER narrow/broad) |
| UK money supply M4 | `boe_iadb_enhanced` (M4 outstanding, M4 lending, growth rates 12M/1M/3M) |
| Hungary monetary policy | `mnb_hungary` (MNB base rate, HUF FX crosses, CEE/G4 baskets) |
| HUF exchange rates | `mnb_hungary` (EUR/USD/GBP/CHF/JPY/CZK/PLN/RON/SEK/CNY/TRY/CAD vs HUF) |
| Small EU central banks | `eu_small_central_banks` (HICP, MFI rates, FX for BG/HR/CY/LV/LT/LU/MT/SK/SI) |
| Small EU macro data | `eu_small_statistics` (GDP, CPI, unemployment, govt debt/deficit for 12 EU states) |
| Bulgarian macro | `eu_small_central_banks` (BG_HICP, BG_LENDING_RATE_HH, BG_FX_USD) + `eu_small_statistics` (GDP, CPI) |
| Croatian macro | `eu_small_central_banks` (HR_HICP, HR_LENDING_RATE_HH, HR_FX_USD) + `eu_small_statistics` (GDP, CPI) |
| Greek macro | `eu_small_statistics` (GDP, CPI, unemployment, govt debt — Eurostat data) |
| Slovenian macro | `eu_small_central_banks` (SI_HICP, SI_INFLATION_DOMESTIC, ECB rates, FX) + `eu_small_statistics` (GDP) |
| Hungarian macro | `mnb_hungary` (base rate, FX) + `eu_small_statistics` (GDP, CPI, unemployment, govt debt — HU) |
| Portuguese national stats | `ine_portugal` (GDP real/nominal/per capita, CPI/HICP, unemployment, tourism, exports/imports, trade coverage, construction costs) |
| Portuguese banking | `banco_de_portugal` (lending/deposit rates, BoP, FX, NPL, CET1, FSI) + `ine_portugal` (macro stats) |
| Brazilian macro data | `ibge_brazil` (GDP YoY/QoQ, IPCA inflation monthly/12M/YTD/index, PNAD unemployment, PIM-PF industrial production, PMC retail sales) |
| IPCA inflation (Brazil) | `ibge_brazil` (IPCA_MONTHLY, IPCA_12M, IPCA_YTD, IPCA_INDEX — Dec 1993=100) |
| Geopolitical risk | `gdelt_global_events` (protest/military/terror/conflict volume & sentiment, country risk scores 0–100, bilateral tension) |
| Media sentiment (economic) | `gdelt_global_events` (inflation/interest rate/trade/stock market/bankruptcy/sanctions media coverage volume & tone) |
| Country risk scoring | `gdelt_global_events` (country_risk command — 35+ countries, 0–100 scale with MINIMAL to ELEVATED ratings) |
| Bilateral tension | `gdelt_global_events` (tension command — any two countries, 0–100 scale, based on cross-media tone analysis) |
| Patent data / USPTO | `patentsview_uspto` (patent search, grants by assignee, top assignees, tech trends by CPC class, patent detail) |
| Corporate innovation / IP | `patentsview_uspto` (patent_grants_by_assignee — supports 35+ tickers: AAPL, MSFT, NVDA, PFE, etc.) |
| Technology trends (CPC) | `patentsview_uspto` (tech_trends — G06N=AI/ML, H01L=semiconductors, A61K=pharma, G06Q=fintech, H01M=batteries, etc.) |
| Industrial production (Brazil) | `ibge_brazil` (PIM-PF seasonally adjusted index, CNAE 2.0, Base 2022=100) |
| Tourism (Portugal) | `ine_portugal` (TOURISM_OVERNIGHT_STAYS — monthly total in tourist accommodation) |
| Mexican macro data | `inegi_mexico` (GDP quarterly, CPI, core inflation, unemployment, industrial production, exports/imports, consumer confidence, auto production) |
| Mexican inflation / CPI | `inegi_mexico` (CPI headline INPC + CORE_INFLATION ex food & energy, monthly) |
| Mexico trade / exports | `inegi_mexico` (EXPORTS + IMPORTS — merchandise trade in USD mn, monthly customs data) |
| Automotive production | `inegi_mexico` (AUTO_PRODUCTION — total motor vehicle units, monthly, AMIA data), `statistics_austria` (NEW_CAR_REGISTRATIONS) |
| Consumer confidence | `inegi_mexico` (CONSUMER_CONFIDENCE — INEGI/Banxico index), `cbs_netherlands`, `statistics_denmark`, `istat_italy` |
| USMCA / NAFTA trade | `inegi_mexico` (Mexico), `statcan_canada` (Canada), `fred_enhanced` (US trade) |
| Latin American macro | `inegi_mexico` (Mexico), `ibge_brazil` (Brazil), `dane_colombia` (Colombia) |
| South Korean macro | `kosis_korea` (GDP, CPI, unemployment, industrial production, exports, housing, semiconductors) |
| Thai macro / rates | `bank_of_thailand` (policy rate, BIBOR, govt bonds, GDP, CPI, BoP, reserves, THB FX, banking) |
| Colombian macro | `dane_colombia` (GDP, CPI, GEIH unemployment, industrial production, trade, PPI) |
| LEI entity data | `gleif_lei` (global entity search, lookup, hierarchy, active/lapsed counts, country distributions) |
| European patents | `epo_ops` (patent search, applicant filings, family members, EP register, IPC trends) |
| US + EU patents | `patentsview_uspto` (USPTO), `epo_ops` (EPO OPS) — combined US/EU patent intelligence |
| Earthquake / seismic | `usgs_earthquake` (M5+ global, PAGER alerts, hotspots: Taiwan/Japan/Chile/Turkey/California) |
| Semiconductor data | `kosis_korea` (semiconductor production index), `patentsview_uspto` (H01L CPC tech trends), `epo_ops` (H01L IPC trends) |
| Supply chain risk | `usgs_earthquake` (seismic hotspots), `gdelt_global_events` (geopolitical risk), `kosis_korea` (semi production) |
| THB exchange rates | `bank_of_thailand` (THB/USD daily, THB end-of-period monthly FX) |
| BIBOR rates | `bank_of_thailand` (Bangkok Interbank Offered Rate: 1W/3M/6M/1Y tenors) |
| Thai bond yields | `bank_of_thailand` (1Y/5Y/10Y/20Y Thai government bonds) |
| Colombian GDP | `dane_colombia` (GDP production approach, quarterly, COP bn via SDMX) |
| Housing prices (Korea) | `kosis_korea` (nationwide apartment price index — monthly, critical for Korean household wealth) |

---

## Agent Integration

### 1. MCP Tool Call (Recommended for AI Agents)

```typescript
// Single tool call
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'bundesbank_sdmx',
    params: { indicator: 'BUND_10Y' }
  })
});

// Batch call — multiple modules at once
const results = await fetch('http://localhost:3056/api/data/batch', {
  method: 'POST',
  body: JSON.stringify({
    calls: [
      { tool: 'bundesbank_sdmx', params: { indicator: 'BUND_10Y' } },
      { tool: 'riksbank_sweden', params: { indicator: 'POLICY_RATE' } },
      { tool: 'banco_de_espana', params: { indicator: 'EURIBOR_12M' } }
    ]
  })
});
```

### 2. REST API

```
GET /api/v1/{module-name}?indicator={INDICATOR}&start_date=YYYY-MM-DD
POST /api/data?tool={module_name}&params={json}
```

### 3. Direct Python / CLI

```bash
python3 modules/<module_name>.py <INDICATOR>
python3 modules/<module_name>.py list          # List available indicators
python3 modules/<module_name>.py --help        # Show usage
```

### 4. Python Import

```python
from modules.bundesbank_sdmx import fetch_data, get_available_indicators
result = fetch_data("BUND_10Y")
indicators = get_available_indicators()
```

---

## Category 1: European Government Statistics & Central Banks

### bundesbank_sdmx.py — Deutsche Bundesbank (SDMX)

- **Source:** Deutsche Bundesbank
- **API:** `https://api.statistiken.bundesbank.de/rest`
- **Protocol:** SDMX 2.1 REST (JSON)
- **Auth:** None (open access)
- **Freshness:** Daily (yields), Monthly (rates, monetary, BOP)
- **Coverage:** Germany / Euro Area

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `BUND_1Y` | German Govt Bond Yield 1Y | Daily | % |
| `BUND_2Y` | German Govt Bond Yield 2Y | Daily | % |
| `BUND_5Y` | German Govt Bond Yield 5Y | Daily | % |
| `BUND_10Y` | German Govt Bond Yield 10Y | Daily | % |
| `BUND_30Y` | German Govt Bond Yield 30Y | Daily | % |
| `ECB_DEPOSIT_RATE` | ECB Deposit Facility Rate | Monthly | % p.a. |
| `ECB_REFI_RATE` | ECB Main Refinancing Rate | Monthly | % p.a. |
| `ECB_MARGINAL_RATE` | ECB Marginal Lending Rate | Monthly | % p.a. |
| `LENDING_RATE_NFC` | Bank Lending Rate to Corporates | Monthly | % |
| `LENDING_RATE_HOUSING` | Housing Loan Rate to Households | Monthly | % |
| `LENDING_RATE_CONSUMER` | Consumer Credit Rate | Monthly | % |
| `M2_GERMANY` | M2 Money Supply — German Contribution | Monthly | EUR bn |
| `M3_EUROAREA` | M3 Money Supply — Euro Area | Monthly | EUR bn |
| `CURRENT_ACCOUNT` | Current Account Balance | Monthly | EUR mn |
| `TRADE_BALANCE` | Trade Balance — Goods | Monthly | EUR mn |

**CLI Examples:**
```bash
python3 modules/bundesbank_sdmx.py BUND_10Y
python3 modules/bundesbank_sdmx.py yield-curve
python3 modules/bundesbank_sdmx.py policy-rates
python3 modules/bundesbank_sdmx.py list
```

---

### insee_france.py — INSEE France (National Statistics)

- **Source:** Institut national de la statistique et des études économiques
- **API:** `https://bdm.insee.fr/series/sdmx`
- **Protocol:** SDMX 2.1 REST (XML)
- **Auth:** None (open access, 30 req/min)
- **Freshness:** Monthly (CPI, IPI, confidence), Quarterly (GDP, unemployment)
- **Coverage:** France

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_GROWTH` | GDP Growth Rate (% q/q, SA-WDA) | Quarterly | % |
| `CPI_INDEX` | CPI — All Items (base 2025=100) | Monthly | index |
| `CPI_YOY` | CPI — Year-on-Year Change | Monthly | % |
| `HICP_INDEX` | HICP — All Items (base 2025=100) | Monthly | index |
| `UNEMPLOYMENT_RATE` | ILO Unemployment Rate | Quarterly | % |
| `IPI_MANUFACTURING` | Industrial Production Index (SA-WDA) | Monthly | index |
| `CONSUMER_CONFIDENCE` | Consumer Confidence Indicator | Monthly | index |
| `HOUSEHOLD_CONSUMPTION` | Household Consumption (SA-WDA) | Quarterly | EUR mn |
| `EXPORTS` | Exports — Total (SA-WDA) | Quarterly | EUR mn |
| `IMPORTS` | Imports — Total (SA-WDA) | Quarterly | EUR mn |

**CLI Examples:**
```bash
python3 modules/insee_france.py GDP_GROWTH
python3 modules/insee_france.py CPI_YOY
python3 modules/insee_france.py trade-balance
python3 modules/insee_france.py list
```

---

### banque_de_france.py — Banque de France Webstat

- **Source:** Banque de France
- **API:** `https://webstat.banque-france.fr/api/explore/v2.1/catalog/datasets`
- **Protocol:** REST (OpenDataSoft Explore v2.1)
- **Auth:** API key required (free at https://webstat.banque-france.fr/signup) — `BANQUE_DE_FRANCE_API_KEY`
- **Freshness:** Daily (FX), Monthly (credit/BoP), Quarterly (corporate)
- **Coverage:** France

**Indicators:**

| Key | Name | Frequency |
|-----|------|-----------|
| `EUR_USD` | EUR/USD Exchange Rate | Daily |
| `EUR_GBP` | EUR/GBP Exchange Rate | Daily |
| `EUR_JPY` | EUR/JPY Exchange Rate | Daily |
| `EUR_CHF` | EUR/CHF Exchange Rate | Daily |
| `EUR_CNY` | EUR/CNY Exchange Rate | Daily |
| `CREDIT_NFC` | Credit to Non-Financial Corporations (EUR mn) | Monthly |
| `CREDIT_HOUSEHOLDS` | Credit to Households (EUR mn) | Monthly |
| `MIR_NFC_NEW` | Interest Rate on New Loans to Households | Monthly |
| `BOP_CURRENT_ACCOUNT` | Balance of Payments — Current Account | Monthly |
| `BOP_TRADE_GOODS` | Balance of Payments — Trade in Goods | Monthly |
| `SME_CREDIT` | Credit to SMEs (EUR mn) | Quarterly |
| `OFC_TOTAL_ASSETS` | Other Financial Corps — Total Assets | Quarterly |
| `BUSINESS_CLIMATE` | Business Climate Indicator — France | Monthly |

**CLI Examples:**
```bash
python3 modules/banque_de_france.py EUR_USD
python3 modules/banque_de_france.py CREDIT_NFC
python3 modules/banque_de_france.py --dashboard
python3 modules/banque_de_france.py --indicators
```

---

### istat_italy.py — ISTAT Italy (National Statistics)

- **Source:** Istituto Nazionale di Statistica
- **API:** `http://sdmx.istat.it/SDMXWS/rest` (fallback: `https://esploradati.istat.it/SDMXWS/rest`)
- **Protocol:** SDMX 2.1 REST (CSV)
- **Auth:** None (5 req/min — STRICT, exceeding triggers 1-2 day IP ban)
- **Freshness:** Monthly (CPI, IPI, confidence, unemployment), Quarterly (GDP)
- **Coverage:** Italy

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_QOQ` | GDP & Main Components — Quarterly (SA-WDA) | Quarterly | EUR mn / % |
| `CPI_NIC` | CPI NIC — Monthly (base 2015=100) | Monthly | index |
| `CPI_IPCA` | HICP/IPCA — Monthly (base 2015=100) | Monthly | index |
| `UNEMPLOYMENT_RATE` | Unemployment Rate — Monthly | Monthly | % |
| `INDUSTRIAL_PRODUCTION` | Industrial Production Index | Monthly | index |
| `CONSUMER_CONFIDENCE` | Consumer Confidence Index (SA) | Monthly | index |
| `BUSINESS_CONFIDENCE` | Business Confidence — IESI (SA) | Monthly | index |

**CLI Examples:**
```bash
python3 modules/istat_italy.py GDP_QOQ
python3 modules/istat_italy.py CPI_NIC
python3 modules/istat_italy.py list
python3 modules/istat_italy.py discover 163_184
```

---

### cbs_netherlands.py — CBS Netherlands StatLine

- **Source:** Centraal Bureau voor de Statistiek
- **API:** `https://opendata.cbs.nl/ODataApi/odata`
- **Protocol:** OData v3 REST (JSON)
- **Auth:** None (open access)
- **Freshness:** Monthly (most), Quarterly (GDP, housing, gov finance)
- **Coverage:** Netherlands

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_GROWTH_YOY` | GDP Volume Growth YoY | Quarterly | % |
| `GDP_GROWTH_QOQ` | GDP Volume Growth QoQ | Quarterly | % |
| `CPI_INDEX` | Consumer Price Index (2025=100) | Monthly | index |
| `CPI_ANNUAL_CHANGE` | CPI Annual Rate of Change | Monthly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate — SA | Monthly | % |
| `EMPLOYED_LABOUR_FORCE` | Employed Labour Force — SA | Monthly | x1000 |
| `HOUSE_PRICE_INDEX` | House Price Index (2020=100) | Quarterly | index |
| `HOUSE_PRICE_CHANGE_YOY` | House Price Annual Change | Quarterly | % |
| `TRADE_BALANCE` | Trade Balance — Goods | Monthly | EUR mn |
| `EXPORTS` | Total Exports — Goods | Monthly | EUR mn |
| `IMPORTS` | Total Imports — Goods | Monthly | EUR mn |
| `GOV_BALANCE_PCT_GDP` | Government Balance (% of GDP) | Quarterly | % |
| `GOV_DEBT_PCT_GDP` | Government Debt EMU (% of GDP) | Quarterly | % |
| `CONSUMER_CONFIDENCE` | Consumer Confidence Indicator | Monthly | index pts |
| `ECONOMIC_CLIMATE` | Economic Climate Indicator | Monthly | index pts |
| `PRODUCER_CONFIDENCE` | Producer Confidence — Manufacturing | Monthly | index pts |

**CLI Examples:**
```bash
python3 modules/cbs_netherlands.py GDP_GROWTH_YOY
python3 modules/cbs_netherlands.py snapshot
python3 modules/cbs_netherlands.py catalog GDP
python3 modules/cbs_netherlands.py list
```

---

### statistics_denmark.py — Statistics Denmark (DST)

- **Source:** Danmarks Statistik
- **API:** `https://api.statbank.dk/v1`
- **Protocol:** REST (POST, JSONSTAT format)
- **Auth:** None (open access)
- **Freshness:** Quarterly (GDP, housing), Monthly (CPI, unemployment, trade, confidence, IPI)
- **Coverage:** Denmark

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_NOMINAL` | GDP — Current Prices | Quarterly | DKK mn |
| `GDP_REAL` | GDP — 2020 Chained Prices | Quarterly | DKK mn |
| `GVA` | Gross Value Added — Current Prices | Quarterly | DKK mn |
| `CPI_INDEX` | Consumer Price Index (2015=100) | Monthly | index |
| `CPI_YOY` | CPI Inflation — Year-on-Year | Monthly | % |
| `HICP` | EU-Harmonized CPI (2015=100) | Monthly | index |
| `UNEMPLOYMENT_RATE` | Gross Unemployment Rate — SA | Monthly | % |
| `UNEMPLOYMENT_NET_RATE` | Net Unemployment Rate — SA | Monthly | % |
| `UNEMPLOYED_PERSONS` | Gross Unemployed Persons — SA | Monthly | persons |
| `EXPORTS_GOODS` | Goods Exports (DKK mn, SA) | Monthly | DKK mn |
| `IMPORTS_GOODS` | Goods Imports (DKK mn, SA) | Monthly | DKK mn |
| `HOUSING_PRICE_INDEX` | House Price Index (2015=100) | Quarterly | index |
| `CONSUMER_CONFIDENCE` | Consumer Confidence Indicator | Monthly | net bal |
| `CONSUMER_PRICE_EXPECT` | Consumer Price Expectations — 12M | Monthly | net bal |
| `INDUSTRIAL_PRODUCTION` | Industrial Production Index (2021=100, SA) | Monthly | index |

**CLI Examples:**
```bash
python3 modules/statistics_denmark.py GDP_NOMINAL
python3 modules/statistics_denmark.py CPI_YOY
python3 modules/statistics_denmark.py trade-balance
python3 modules/statistics_denmark.py tables GDP
```

---

### scb_sweden.py — SCB Sweden (Statistics Sweden)

- **Source:** Statistiska centralbyrån (SCB)
- **API:** `https://api.scb.se/OV0104/v1/doris/en/ssd`
- **Protocol:** PxWeb REST API (POST with JSON query)
- **Auth:** None (open access)
- **Freshness:** Monthly (most series), Quarterly (GDP, housing)
- **Coverage:** Sweden

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_QOQ` | GDP Growth QoQ (%, SA) | Quarterly | % |
| `GDP_CURRENT_PRICES` | GDP at Current Prices (SEK mn, SA) | Quarterly | SEK mn |
| `GDP_INDICATOR_MOM` | GDP Indicator MoM (%, SA) | Monthly | % |
| `GDP_INDICATOR_YOY` | GDP Indicator YoY (%) | Monthly | % |
| `CPI_INDEX` | CPI Index (2020=100) | Monthly | index |
| `CPI_ANNUAL_CHANGE` | CPI Annual Change (%) | Monthly | % |
| `CPIF_INDEX` | CPIF Index (2020=100) | Monthly | index |
| `CPIF_ANNUAL_CHANGE` | CPIF Annual Change (%) — Riksbank target | Monthly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate (%, SA) | Monthly | % |
| `EMPLOYMENT_RATE` | Employment Rate (%, SA) | Monthly | % |
| `HOUSING_PRICE_INDEX` | Housing Price Index (1981=100) | Quarterly | index |
| `PRODUCTION_INDEX_TOTAL` | Production Value Index YoY (total) | Monthly | % |
| `PRODUCTION_INDEX_MANUFACTURING` | Production Value Index YoY (manufacturing) | Monthly | % |
| `EXPORTS` | Total Exports (SEK mn) | Monthly | SEK mn |
| `IMPORTS` | Total Imports (SEK mn) | Monthly | SEK mn |
| `TRADE_BALANCE` | Trade Balance — Goods (SEK mn) | Monthly | SEK mn |
| `GOVT_DEBT` | Central Government Debt (SEK mn) | Monthly | SEK mn |

**CLI Examples:**
```bash
python3 modules/scb_sweden.py GDP_QOQ
python3 modules/scb_sweden.py CPIF_ANNUAL_CHANGE
python3 modules/scb_sweden.py navigate NR
python3 modules/scb_sweden.py list
```

---

### riksbank_sweden.py — Sveriges Riksbank

- **Source:** Sveriges Riksbank (Central Bank of Sweden)
- **API:** `https://api.riksbank.se/swea/v1`
- **Protocol:** REST (JSON)
- **Auth:** Open (IP-based rate limits)
- **Freshness:** Daily (FX, yields), as-needed (policy rates)
- **Coverage:** Sweden

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `POLICY_RATE` | Riksbank Policy Rate | Daily | % |
| `DEPOSIT_RATE` | Riksbank Deposit Rate | Daily | % |
| `LENDING_RATE` | Riksbank Lending Rate | Daily | % |
| `REFERENCE_RATE` | Riksbank Reference Rate | Daily | % |
| `SEK_EUR` | SEK/EUR Exchange Rate | Daily | SEK/EUR |
| `SEK_USD` | SEK/USD Exchange Rate | Daily | SEK/USD |
| `SEK_GBP` | SEK/GBP Exchange Rate | Daily | SEK/GBP |
| `SEK_JPY` | SEK/JPY Exchange Rate | Daily | SEK/JPY |
| `SEK_CHF` | SEK/CHF Exchange Rate | Daily | SEK/CHF |
| `SEK_NOK` | SEK/NOK Exchange Rate | Daily | SEK/NOK |
| `SEK_DKK` | SEK/DKK Exchange Rate | Daily | SEK/DKK |
| `KIX_INDEX` | KIX Trade-Weighted SEK Index | Daily | index |
| `GVB_2Y` | Swedish Govt Bond Yield 2Y | Daily | % |
| `GVB_5Y` | Swedish Govt Bond Yield 5Y | Daily | % |
| `GVB_7Y` | Swedish Govt Bond Yield 7Y | Daily | % |
| `GVB_10Y` | Swedish Govt Bond Yield 10Y | Daily | % |
| `TB_1M` | Swedish T-Bill Rate 1M | Daily | % |
| `TB_3M` | Swedish T-Bill Rate 3M | Daily | % |
| `TB_6M` | Swedish T-Bill Rate 6M | Daily | % |
| `MB_2Y` | Swedish Mortgage Bond Yield 2Y | Daily | % |
| `MB_5Y` | Swedish Mortgage Bond Yield 5Y | Daily | % |

**CLI Examples:**
```bash
python3 modules/riksbank_sweden.py POLICY_RATE
python3 modules/riksbank_sweden.py policy-rates
python3 modules/riksbank_sweden.py fx-rates
python3 modules/riksbank_sweden.py yield-curve
```

---

### banco_de_espana.py — Banco de España

- **Source:** Banco de España (Central Bank of Spain)
- **API:** `https://app.bde.es/bierest/resources/srdatosapp`
- **Protocol:** REST JSON (BdE BIEST API)
- **Auth:** None (open access)
- **Freshness:** Monthly (rates, BoP), Quarterly (housing)
- **Coverage:** Spain / Euro Area

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `EURIBOR_1W` | Euribor 1-Week | Monthly | % |
| `EURIBOR_3M` | Euribor 3-Month | Monthly | % |
| `EURIBOR_6M` | Euribor 6-Month | Monthly | % |
| `EURIBOR_12M` | Euribor 12-Month | Monthly | % |
| `MORTGAGE_RATE_NEW` | Mortgage Rate — New Business | Monthly | % |
| `CONSUMER_CREDIT_RATE` | Consumer Credit Rate — New Business | Monthly | % |
| `NFC_LENDING_RATE` | NFC Lending Rate — New Business | Monthly | % |
| `HOUSEHOLD_DEPOSIT_TERM` | Household Term Deposit Rate | Monthly | % |
| `HOUSEHOLD_DEPOSIT_SIGHT` | Household Overnight Deposit Rate | Monthly | % |
| `IRPH_MORTGAGE_REF` | IRPH — Official Mortgage Reference Rate | Monthly | % |
| `MORTGAGE_RATE_OUTSTANDING` | Mortgage Rate — Outstanding Stock | Monthly | % |
| `BOP_CURRENT_ACCOUNT` | BoP — Current Account Balance | Monthly | EUR mn |
| `BOP_GOODS_SERVICES` | BoP — Goods & Services Balance | Monthly | EUR mn |
| `BOP_INCOME` | BoP — Primary & Secondary Income | Monthly | EUR mn |
| `BOP_CAPITAL_ACCOUNT` | BoP — Capital Account Balance | Monthly | EUR mn |
| `BOP_FINANCIAL_ACCOUNT` | BoP — Financial Account Net | Monthly | EUR mn |
| `HOUSING_PRICE_M2` | Housing Price — Average Free (EUR/m²) | Quarterly | EUR/m² |
| `HOUSING_PRICE_NEW` | Housing Price — New Build (EUR/m²) | Quarterly | EUR/m² |
| `HOUSING_PRICE_USED` | Housing Price — Second Hand (EUR/m²) | Quarterly | EUR/m² |

**CLI Examples:**
```bash
python3 modules/banco_de_espana.py EURIBOR_12M
python3 modules/banco_de_espana.py rates
python3 modules/banco_de_espana.py bop
python3 modules/banco_de_espana.py list
```

---

### banco_de_portugal.py — Banco de Portugal (BPstat)

- **Source:** Banco de Portugal
- **API:** `https://bpstat.bportugal.pt/data/v1`
- **Protocol:** REST (JSON-stat 2.0)
- **Auth:** None (open access)
- **Freshness:** Daily (FX rates), Monthly (interest rates, BoP), Semi-annual (banking/FSI)
- **Coverage:** Portugal

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `IR_LOANS_NFC` | Lending Rate — Non-Financial Corporations | Monthly | % |
| `IR_LOANS_HOUSING` | Lending Rate — Housing Loans | Monthly | % |
| `IR_LOANS_CONSUMER` | Lending Rate — Consumer Credit | Monthly | % |
| `IR_DEPOSITS_AGREED` | Deposit Rate — Agreed Maturity, Non-Financial Sector | Monthly | % |
| `IR_DEPOSITS_OVERNIGHT_HH` | Deposit Rate — Overnight, Individuals | Monthly | % |
| `IR_NEWBIZ_HOUSING` | New Business Rate — Housing Loans | Monthly | % |
| `IR_NEWBIZ_CONSUMER` | New Business Rate — Consumer Credit | Monthly | % |
| `BOP_CURRENT_ACCOUNT` | Current Account Balance | Monthly | EUR mn |
| `BOP_GOODS_SERVICES` | Goods & Services Balance | Monthly | EUR mn |
| `BOP_GOODS` | Goods Balance | Monthly | EUR mn |
| `BOP_SERVICES` | Services Balance | Monthly | EUR mn |
| `BOP_PRIMARY_INCOME` | Primary Income Balance | Monthly | EUR mn |
| `BOP_CAPITAL_ACCOUNT` | Capital Account Balance | Monthly | EUR mn |
| `FX_EUR_USD` | EUR/USD Exchange Rate | Daily | USD per EUR |
| `FX_EUR_GBP` | EUR/GBP Exchange Rate | Daily | GBP per EUR |
| `FX_EUR_JPY` | EUR/JPY Exchange Rate | Daily | JPY per EUR |
| `FX_EUR_CHF` | EUR/CHF Exchange Rate | Daily | CHF per EUR |
| `FX_EUR_CNY` | EUR/CNY Exchange Rate | Daily | CNY per EUR |
| `BANK_ROA` | Banking Sector — Return on Assets | Semi-annual | % |
| `BANK_CET1` | Banking Sector — CET1 Ratio | Semi-annual | % |
| `BANK_NPL_RATIO` | Banking Sector — NPL Ratio | Semi-annual | % |
| `BANK_LOAN_TO_DEPOSIT` | Banking Sector — Loan-to-Deposit Ratio | Semi-annual | % |
| `FSI_TIER1_RATIO` | FSI — Tier 1 Capital to RWA | Semi-annual | % |
| `FSI_NPL_TO_LOANS` | FSI — NPL to Total Gross Loans | Semi-annual | % |
| `FSI_ROA` | FSI — Return on Assets | Semi-annual | % |
| `FSI_LIQUIDITY` | FSI — Liquid Assets to Short-Term Liabilities | Semi-annual | % |

**CLI Examples:**
```bash
python3 modules/banco_de_portugal.py IR_LOANS_HOUSING
python3 modules/banco_de_portugal.py BOP_CURRENT_ACCOUNT
python3 modules/banco_de_portugal.py FX_EUR_USD
python3 modules/banco_de_portugal.py list
```

---

### ons_uk.py — UK Office for National Statistics (ONS)

- **Source:** Office for National Statistics
- **API:** `https://api.beta.ons.gov.uk/v1`
- **Protocol:** REST / JSON (CMD beta API)
- **Auth:** None (open beta)
- **Freshness:** Monthly (varies by dataset)
- **Coverage:** United Kingdom / Great Britain

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_MONTHLY` | UK Monthly GDP Index (SA, 2016=100) | Monthly | index |
| `GDP_SERVICES` | UK Index of Services (SA, 2016=100) | Monthly | index |
| `GDP_PRODUCTION` | UK Production Industries Index (SA, 2016=100) | Monthly | index |
| `GDP_MANUFACTURING` | UK Manufacturing Index (SA, 2016=100) | Monthly | index |
| `CPIH_ALL` | CPIH All Items (Index, 2015=100) | Monthly | index |
| `CPIH_FOOD` | CPIH Food & Non-Alcoholic Beverages | Monthly | index |
| `CPIH_HOUSING` | CPIH Housing, Water, Electricity & Gas | Monthly | index |
| `CPIH_TRANSPORT` | CPIH Transport | Monthly | index |
| `RETAIL_SALES_VOLUME` | UK Retail Sales Volume Index (SA, 2019=100) | Monthly | index |
| `RETAIL_SALES_VALUE` | UK Retail Sales Value Index (SA, current prices) | Monthly | index |
| `TRADE_EXPORTS_TOTAL` | UK Total Goods Exports | Monthly | GBP mn |
| `TRADE_IMPORTS_TOTAL` | UK Total Goods Imports | Monthly | GBP mn |
| `TRADE_EXPORTS_EU` | UK Goods Exports to EU | Monthly | GBP mn |
| `CONSTRUCTION_OUTPUT` | UK Construction Output — All Work (SA) | Monthly | GBP mn |
| `CONSTRUCTION_NEW_WORK` | UK Construction Output — New Work (SA) | Monthly | GBP mn |
| `HOUSING_RENTAL_INDEX` | UK Private Housing Rental Price Index | Monthly | index |
| `HOUSING_RENTAL_YOY` | UK Private Housing Rental Prices YoY Change | Monthly | % |
| `UNEMPLOYMENT_RATE` | UK Unemployment Rate (16+, SA) | Quarterly-rolling | % |
| `EMPLOYMENT_RATE` | UK Employment Rate (16-64, SA) | Quarterly-rolling | % |
| `ECONOMIC_INACTIVITY_RATE` | UK Economic Inactivity Rate (16-64, SA) | Quarterly-rolling | % |

**CLI Examples:**
```bash
python3 modules/ons_uk.py GDP_MONTHLY
python3 modules/ons_uk.py CPIH_ALL
python3 modules/ons_uk.py UNEMPLOYMENT_RATE
python3 modules/ons_uk.py datasets
python3 modules/ons_uk.py list
```

---

### statcan_canada.py — Statistics Canada (WDS)

- **Source:** Statistics Canada
- **API:** `https://www150.statcan.gc.ca/t1/wds/rest`
- **Protocol:** REST (WDS — Web Data Service)
- **Auth:** None (open access)
- **Freshness:** Business days at 8:30 AM EST
- **Rate Limit:** 50 req/s global, 25 req/s per IP
- **Coverage:** Canada

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_CURRENT` | GDP at Market Prices — Current Dollars (SAAR) | Quarterly | CAD mn |
| `GDP_REAL` | GDP at Market Prices — Chained 2017$ (SAAR) | Quarterly | CAD mn |
| `GDP_MONTHLY` | Monthly GDP — All Industries | Monthly | CAD mn |
| `CPI_ALL_ITEMS` | CPI All-Items (2002=100) | Monthly | index |
| `CPI_FOOD` | CPI Food | Monthly | index |
| `CPI_SHELTER` | CPI Shelter | Monthly | index |
| `CPI_ENERGY` | CPI Energy | Monthly | index |
| `UNEMPLOYMENT_RATE` | Unemployment Rate — SA | Monthly | % |
| `EMPLOYMENT` | Employment — SA (thousands) | Monthly | thousands |
| `FULL_TIME_EMPLOYMENT` | Full-Time Employment — SA (thousands) | Monthly | thousands |
| `PARTICIPATION_RATE` | Participation Rate — SA | Monthly | % |
| `EMPLOYMENT_RATE` | Employment Rate — SA | Monthly | % |
| `MERCHANDISE_EXPORTS` | Merchandise Exports — BOP, SA | Monthly | CAD mn |
| `MERCHANDISE_IMPORTS` | Merchandise Imports — BOP, SA | Monthly | CAD mn |
| `TRADE_BALANCE` | Merchandise Trade Balance — BOP, SA | Monthly | CAD mn |
| `RETAIL_SALES` | Retail Trade Sales — Total, SA | Monthly | CAD |
| `HOUSING_STARTS` | Housing Starts — Total, SAAR (units) | Monthly | units |
| `NEW_HOUSING_PRICE_INDEX` | New Housing Price Index — Total | Monthly | index |

**CLI Examples:**
```bash
python3 modules/statcan_canada.py GDP_REAL
python3 modules/statcan_canada.py UNEMPLOYMENT_RATE
python3 modules/statcan_canada.py CPI_ALL_ITEMS
python3 modules/statcan_canada.py discover GDP
python3 modules/statcan_canada.py list
```

---

### estat_japan.py — e-Stat Japan (Government Statistics)

- **Source:** Government of Japan (Ministry of Internal Affairs, Cabinet Office, METI, MOF, MLIT)
- **API:** `https://api.e-stat.go.jp/rest/3.0/app`
- **Protocol:** REST (JSON)
- **Auth:** Application ID required (free at https://www.e-stat.go.jp/api/) — `ESTAT_JAPAN_APP_ID`
- **Freshness:** Monthly / Quarterly depending on series
- **Coverage:** Japan (national + prefectural)

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `CPI_ALL_ITEMS` | CPI All Items — National (2020=100) | Monthly | index |
| `CPI_CORE` | CPI Core — National, ex Fresh Food (2020=100) | Monthly | index |
| `GDP_NOMINAL` | Nominal GDP — Quarterly (JPY bn) | Quarterly | JPY bn |
| `GDP_REAL` | Real GDP — Quarterly (JPY bn, chained) | Quarterly | JPY bn |
| `UNEMPLOYMENT_RATE` | Unemployment Rate (%) | Monthly | % |
| `LABOUR_FORCE` | Labour Force Population (10k persons) | Monthly | 10k persons |
| `INDUSTRIAL_PRODUCTION` | Index of Industrial Production (2020=100) | Monthly | index |
| `TRADE_EXPORTS` | Exports — Total Value | Monthly | JPY mn |
| `TRADE_IMPORTS` | Imports — Total Value | Monthly | JPY mn |
| `HOUSING_STARTS` | New Housing Starts — Total Units | Monthly | units |
| `MACHINERY_ORDERS` | Machinery Orders — Private ex. Volatile | Monthly | JPY bn |

**CLI Examples:**
```bash
python3 modules/estat_japan.py CPI_ALL_ITEMS
python3 modules/estat_japan.py GDP_NOMINAL
python3 modules/estat_japan.py UNEMPLOYMENT_RATE
python3 modules/estat_japan.py search CPI 00200573
python3 modules/estat_japan.py list
```

---

### nbp_poland.py — National Bank of Poland (NBP)

- **Source:** Narodowy Bank Polski
- **API:** `https://api.nbp.pl/api`
- **Protocol:** REST (JSON)
- **Auth:** None (open access, no rate limit)
- **Freshness:** Daily (Table A/C FX, gold), Weekly on Wednesdays (Table B exotic FX)
- **Coverage:** Poland / PLN

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `FX_USD_PLN` | USD/PLN Mid Rate | Daily | PLN |
| `FX_EUR_PLN` | EUR/PLN Mid Rate | Daily | PLN |
| `FX_GBP_PLN` | GBP/PLN Mid Rate | Daily | PLN |
| `FX_CHF_PLN` | CHF/PLN Mid Rate | Daily | PLN |
| `FX_JPY_PLN` | JPY/PLN Mid Rate (per 100 JPY) | Daily | PLN |
| `FX_CAD_PLN` | CAD/PLN Mid Rate | Daily | PLN |
| `FX_AUD_PLN` | AUD/PLN Mid Rate | Daily | PLN |
| `FX_CNY_PLN` | CNY/PLN Mid Rate | Daily | PLN |
| `FX_SEK_PLN` | SEK/PLN Mid Rate | Daily | PLN |
| `FX_NOK_PLN` | NOK/PLN Mid Rate | Daily | PLN |
| `FX_CZK_PLN` | CZK/PLN Mid Rate | Daily | PLN |
| `FX_HUF_PLN` | HUF/PLN Mid Rate (per 100 HUF) | Daily | PLN |
| `FX_TWD_PLN` | TWD/PLN Mid Rate (Table B) | Weekly | PLN |
| `FX_AED_PLN` | AED/PLN Mid Rate (Table B) | Weekly | PLN |
| `FX_SAR_PLN` | SAR/PLN Mid Rate (Table B) | Weekly | PLN |
| `FX_KWD_PLN` | KWD/PLN Mid Rate (Table B) | Weekly | PLN |
| `FX_USD_PLN_BID_ASK` | USD/PLN Bid/Ask Spread (Table C) | Daily | PLN |
| `FX_EUR_PLN_BID_ASK` | EUR/PLN Bid/Ask Spread (Table C) | Daily | PLN |
| `FX_GBP_PLN_BID_ASK` | GBP/PLN Bid/Ask Spread (Table C) | Daily | PLN |
| `FX_CHF_PLN_BID_ASK` | CHF/PLN Bid/Ask Spread (Table C) | Daily | PLN |
| `GOLD_PLN` | Gold Price (PLN/gram, 1000 fineness) | Daily | PLN/g |

**CLI Examples:**
```bash
python3 modules/nbp_poland.py FX_EUR_PLN
python3 modules/nbp_poland.py GOLD_PLN
python3 modules/nbp_poland.py FX_USD_PLN_BID_ASK
python3 modules/nbp_poland.py table A            # Full Table A snapshot
python3 modules/nbp_poland.py FX_EUR_PLN 2025-01-01 2025-06-30  # Date range
python3 modules/nbp_poland.py list
```

---

### cbc_taiwan.py — Central Bank of R.O.C. (Taiwan)

- **Source:** Central Bank of the Republic of China (Taiwan)
- **API:** `https://cpx.cbc.gov.tw/API/DataAPI/Get`
- **Protocol:** REST (JSON)
- **Auth:** None (open access)
- **Freshness:** Daily (FX spot), Monthly (rates, monetary), Quarterly (weighted-average rates)
- **Coverage:** Taiwan

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `TWD_USD_CLOSE` | TWD/USD Closing Rate | Daily | NTD per USD |
| `TWD_USD_BUY` | TWD/USD Buying Rate | Daily | NTD per USD |
| `TWD_USD_SELL` | TWD/USD Selling Rate | Daily | NTD per USD |
| `CBC_DISCOUNT_RATE` | CBC Discount Rate | Monthly | % p.a. |
| `CBC_SECURED_RATE` | CBC Secured Accommodation Rate | Monthly | % p.a. |
| `CBC_UNSECURED_RATE` | CBC Unsecured Accommodation Rate | Monthly | % p.a. |
| `DEPOSIT_RATE_1Y_FIXED` | 1-Year Fixed Deposit Rate (5 major banks) | Monthly | % p.a. |
| `SAVINGS_RATE_1Y` | 1-Year Savings Deposit Rate (5 major banks) | Monthly | % p.a. |
| `BASE_LENDING_RATE` | Base Lending Rate (5 major banks) | Monthly | % p.a. |
| `RESERVE_MONEY` | Reserve Money — Daily Average | Monthly | Millions NTD |
| `M1A` | M1A Monetary Aggregate — Daily Average | Monthly | Millions NTD |
| `M1B` | M1B Monetary Aggregate — Daily Average | Monthly | Millions NTD |
| `M2` | M2 Monetary Aggregate — Daily Average | Monthly | Millions NTD |
| `RESERVE_MONEY_EOM` | Reserve Money — End of Month | Monthly | Millions NTD |
| `M1B_EOM` | M1B — End of Month Outstanding | Monthly | Millions NTD |
| `M2_EOM` | M2 — End of Month Outstanding | Monthly | Millions NTD |
| `WEIGHTED_DEPOSIT_RATE` | Weighted Avg Deposit Rate — All Banks | Quarterly | % p.a. |
| `WEIGHTED_LENDING_RATE` | Weighted Avg Lending Rate — All Banks | Quarterly | % p.a. |

**CLI Examples:**
```bash
python3 modules/cbc_taiwan.py TWD_USD_CLOSE
python3 modules/cbc_taiwan.py CBC_DISCOUNT_RATE
python3 modules/cbc_taiwan.py policy-rates        # All CBC + bank rates
python3 modules/cbc_taiwan.py monetary             # M1A/M1B/M2 aggregates
python3 modules/cbc_taiwan.py list
```

---

### nbb_belgium.py — National Bank of Belgium (NBB.Stat)

- **Source:** National Bank of Belgium
- **API:** `https://nsidisseminate-stat.nbb.be/rest`
- **Protocol:** SDMX 2.1 REST (SDMX-JSON via .Stat Suite NSI)
- **Auth:** None (open access, requires `Origin: https://dataexplorer.nbb.be` header)
- **Freshness:** Monthly (BoP, HICP, monetary, surveys), Quarterly (IIP, financial accounts, govt finance)
- **Coverage:** Belgium / Euro Area

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `BOP_CURRENT_ACCOUNT` | Current Account Balance | Monthly | EUR mn |
| `BOP_GOODS_TRADE` | Goods Trade Balance | Monthly | EUR mn |
| `BOP_SERVICES` | Services Balance | Monthly | EUR mn |
| `BOP_PRIMARY_INCOME` | Primary Income Balance | Monthly | EUR mn |
| `BOP_CAPITAL_ACCOUNT` | Capital Account Balance | Monthly | EUR mn |
| `BOP_FINANCIAL_ACCOUNT` | Financial Account Balance | Monthly | EUR mn |
| `HICP_TOTAL_YOY` | HICP Total YoY (%) | Monthly | % |
| `HICP_CORE_YOY` | HICP Core (ex food & energy) YoY (%) | Monthly | % |
| `HICP_ENERGY_YOY` | HICP Energy YoY (%) | Monthly | % |
| `HICP_SERVICES_YOY` | HICP Services YoY (%) | Monthly | % |
| `HICP_INDEX` | HICP Index (2015=100) | Monthly | Index |
| `HH_FINANCIAL_WEALTH` | Household Financial Wealth Net (EUR mn) | Quarterly | EUR mn |
| `ECONOMY_NET_FINANCIAL` | Total Economy Net Financial Position (EUR mn) | Quarterly | EUR mn |
| `IIP_NET_POSITION` | Net International Investment Position (EUR mn) | Quarterly | EUR mn |
| `IIP_PORTFOLIO_NET` | Portfolio Investment Net IIP (EUR mn) | Quarterly | EUR mn |
| `GOV_NET_LENDING` | General Govt Net Lending/Borrowing (EUR mn) | Quarterly | EUR mn |
| `GOV_TOTAL_LIABILITIES` | General Govt Total Financial Liabilities (EUR mn) | Quarterly | EUR mn |
| `GOV_DEBT_SECURITIES` | Govt Debt Securities Outstanding (EUR mn) | Quarterly | EUR mn |
| `M1_EUROAREA` | M1 Money Supply — Euro Area (EUR bn) | Monthly | EUR bn |
| `M3_EUROAREA` | M3 Money Supply — Euro Area (EUR bn) | Monthly | EUR bn |
| `BUSSURVEY_SYNTHETIC` | Business Survey Synthetic Curve | Monthly | Index |
| `BUSSURVEY_MANUFACTURING` | Business Survey — Manufacturing | Monthly | Index |
| `BUSSURVEY_TRADE` | Business Survey — Trade | Monthly | Index |
| `BUSSURVEY_SERVICES` | Business Survey — Business Services | Monthly | Index |

**CLI Examples:**
```bash
python3 modules/nbb_belgium.py HICP_TOTAL_YOY
python3 modules/nbb_belgium.py BOP_CURRENT_ACCOUNT
python3 modules/nbb_belgium.py GOV_NET_LENDING
python3 modules/nbb_belgium.py dataflows             # Discover all NBB.Stat dataflows
python3 modules/nbb_belgium.py list
```

---

### central_bank_ireland.py — Central Bank of Ireland

- **Source:** Central Bank of Ireland Open Data
- **API:** `https://opendata.centralbank.ie/api/3/action`
- **Protocol:** CKAN Datastore REST API
- **Auth:** None (open access, CC-BY-4.0 license)
- **Freshness:** Monthly (rates, reserves), Quarterly (mortgages, debt)
- **Coverage:** Ireland / Euro Area

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `ECB_DEPOSIT_RATE` | ECB Deposit Facility Rate | Monthly | % p.a. |
| `ECB_REFI_RATE` | ECB Main Refinancing Rate | Monthly | % p.a. |
| `ECB_MARGINAL_RATE` | ECB Marginal Lending Facility Rate | Monthly | % p.a. |
| `STR_RATE` | Euro Short-Term Rate — €STR | Monthly | % p.a. |
| `EURIBOR_3M` | 3-Month Euribor | Monthly | % p.a. |
| `EURIBOR_12M` | 12-Month Euribor | Monthly | % p.a. |
| `MORTGAGE_RATE_NEW` | New Mortgage Rate — Ireland | Monthly | % |
| `CONSUMER_RATE_NEW` | New Consumer Credit Rate — Ireland | Monthly | % |
| `NFC_LENDING_RATE_NEW` | New NFC Lending Rate — Ireland | Monthly | % |
| `HH_DEPOSIT_RATE_NEW` | New Household Deposit Rate — Ireland | Monthly | % |
| `NFC_DEPOSIT_RATE_NEW` | New NFC Deposit Rate — Ireland | Monthly | % |
| `HH_OVERNIGHT_DEPOSIT_RATE` | Household Overnight Deposit Rate — Stock | Monthly | % |
| `HH_TERM_DEPOSIT_RATE` | Household Term Deposit Rate ≤2Y — Stock | Monthly | % |
| `HH_OVERDRAFT_RATE` | Household Overdraft Rate — Stock | Monthly | % |
| `MORTGAGE_RATE_STOCK` | Mortgage Rate — Outstanding Stock, >5Y | Monthly | % |
| `PDH_FIXED_OVER3Y_RATE` | PDH Fixed Rate >3Y — Outstanding | Quarterly | % |
| `PDH_TRACKER_RATE` | PDH Tracker Mortgage Rate — Outstanding | Quarterly | % |
| `GROSS_NATIONAL_DEBT` | Gross National Debt — Ireland (EUR mn) | Quarterly | EUR mn |
| `RESERVE_ASSETS_TOTAL` | Official Reserve Assets — Ireland (EUR mn) | Monthly | EUR mn |
| `FX_RESERVES` | Foreign Exchange Reserves — Ireland (EUR mn) | Monthly | EUR mn |
| `GOLD_RESERVES` | Monetary Gold Reserves — Ireland (EUR mn) | Monthly | EUR mn |

**CLI Examples:**
```bash
python3 modules/central_bank_ireland.py ECB_DEPOSIT_RATE
python3 modules/central_bank_ireland.py MORTGAGE_RATE_NEW
python3 modules/central_bank_ireland.py GROSS_NATIONAL_DEBT
python3 modules/central_bank_ireland.py datasets          # Discover all CBI datasets
python3 modules/central_bank_ireland.py list
```

---

### cso_ireland.py — CSO Ireland (Central Statistics Office)

- **Source:** Central Statistics Office (CSO)
- **API:** `https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset`
- **Protocol:** PxStat / JSON-stat 2.0
- **Auth:** None (open access)
- **Freshness:** Monthly (CPI, retail, housing, trade), Quarterly (GDP, labour)
- **Coverage:** Ireland

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_QUARTERLY` | GDP at Constant Market Prices (EUR mn, SA) | Quarterly | EUR million |
| `GDP_CURRENT` | GDP at Current Market Prices (EUR mn, SA) | Quarterly | EUR million |
| `GNP_QUARTERLY` | GNP at Constant Market Prices (EUR mn, SA) | Quarterly | EUR million |
| `CPI_INDEX` | CPI All Items (Base Dec 2023=100) | Monthly | Index |
| `CPI_YOY` | CPI Annual % Change | Monthly | % |
| `CPI_MOM` | CPI Monthly % Change | Monthly | % |
| `UNEMPLOYMENT_RATE` | ILO Unemployment Rate (15-74 years, %) | Quarterly | % |
| `EMPLOYMENT_RATE` | ILO Employment Rate (15-64 years, %) | Quarterly | % |
| `PARTICIPATION_RATE` | ILO Participation Rate (15+ years, %) | Quarterly | % |
| `RETAIL_SALES_VOLUME` | Retail Sales Index — Volume (SA, 2015=100) | Monthly | Index |
| `RETAIL_SALES_VALUE` | Retail Sales Index — Value (SA, 2015=100) | Monthly | Index |
| `HOUSE_PRICE_INDEX` | Residential Property Price Index (National) | Monthly | Index |
| `HOUSE_PRICE_YOY` | House Price Annual % Change (National) | Monthly | % |
| `TRADE_EXPORTS` | Total Exports (EUR mn, SA) | Monthly | EUR million |
| `TRADE_IMPORTS` | Total Imports (EUR mn, SA) | Monthly | EUR million |
| `TRADE_BALANCE` | Trade Balance (EUR mn, SA) | Monthly | EUR million |

**CLI Examples:**
```bash
python3 modules/cso_ireland.py GDP_QUARTERLY
python3 modules/cso_ireland.py CPI_YOY
python3 modules/cso_ireland.py UNEMPLOYMENT_RATE
python3 modules/cso_ireland.py discover HPM09         # Discover table dimensions
python3 modules/cso_ireland.py list
```

---

### statistics_finland.py — Statistics Finland (Tilastokeskus)

- **Source:** Statistics Finland (Tilastokeskus)
- **API:** `https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/`
- **Protocol:** PxWeb REST API (POST with JSON query)
- **Auth:** None (open access)
- **Freshness:** Monthly (CPI, labour, industrial output), Quarterly (GDP, trade, housing)
- **Coverage:** Finland

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_QOQ` | GDP Volume Change QoQ (%, SA) | Quarterly | % |
| `GDP_YOY` | GDP Volume Change YoY (%, SA) | Quarterly | % |
| `GDP_CURRENT_PRICES` | GDP at Current Prices (EUR mn, SA) | Quarterly | EUR million |
| `CPI_INDEX` | CPI Index (2015=100) | Monthly | Index |
| `UNEMPLOYMENT_RATE` | Unemployment Rate (%, SA) | Monthly | % |
| `UNEMPLOYMENT_RATE_YOUTH` | Youth Unemployment Rate 15-24 (%, SA) | Monthly | % |
| `EMPLOYMENT_RATE` | Employment Rate 15-64 (%, SA) | Monthly | % |
| `EMPLOYED_PERSONS` | Employed Persons (1000, SA) | Monthly | 1000 persons |
| `INDUSTRIAL_OUTPUT_TOTAL` | Industrial Output Index, Total (2021=100, SA) | Monthly | Index |
| `INDUSTRIAL_OUTPUT_MFG` | Industrial Output Index, Manufacturing (2021=100, SA) | Monthly | Index |
| `INDUSTRIAL_OUTPUT_YOY` | Industrial Output YoY (%, working-day adj.) | Monthly | % |
| `EXPORTS` | Exports of Goods & Services (EUR mn) | Quarterly | EUR million |
| `IMPORTS` | Imports of Goods & Services (EUR mn) | Quarterly | EUR million |
| `HOUSING_PRICE_INDEX` | Housing Price Index, Old Dwellings (2020=100) | Quarterly | Index |
| `HOUSING_PRICE_YOY` | Housing Price Annual Change (%) | Quarterly | % |
| `HOUSING_PRICE_SQM` | Housing Price per m² (EUR) | Quarterly | EUR/m² |

**CLI Examples:**
```bash
python3 modules/statistics_finland.py GDP_QOQ
python3 modules/statistics_finland.py CPI_INDEX
python3 modules/statistics_finland.py UNEMPLOYMENT_RATE
python3 modules/statistics_finland.py navigate ntp       # Browse PxWeb table hierarchy
python3 modules/statistics_finland.py list
```

---

### danmarks_nationalbank.py — Danmarks Nationalbank

- **Source:** Danmarks Nationalbank (via Statistics Denmark StatBank)
- **API:** `https://api.statbank.dk/v1`
- **Protocol:** REST (POST with JSON-Stat responses)
- **Auth:** None (open access)
- **Freshness:** Daily (FX/rates), Monthly (BoP, MFI, securities)
- **Coverage:** Denmark

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `DN_DISCOUNT_RATE` | DN Discount Rate | Monthly | % p.a. |
| `DN_CURRENT_ACCOUNT_RATE` | DN Current-Account Deposits Rate | Monthly | % p.a. |
| `DN_LENDING_RATE` | DN Lending Rate | Monthly | % p.a. |
| `DN_CD_RATE` | DN Certificates of Deposit Rate | Monthly | % p.a. |
| `FX_EUR_DKK` | EUR/DKK Exchange Rate (ERM II peg ~746) | Monthly | DKK per 100 EUR |
| `FX_USD_DKK` | USD/DKK Exchange Rate | Monthly | DKK per 100 USD |
| `FX_GBP_DKK` | GBP/DKK Exchange Rate | Monthly | DKK per 100 GBP |
| `FX_JPY_DKK` | JPY/DKK Exchange Rate | Monthly | DKK per 100 JPY |
| `FX_CHF_DKK` | CHF/DKK Exchange Rate | Monthly | DKK per 100 CHF |
| `FX_NOK_DKK` | NOK/DKK Exchange Rate | Monthly | DKK per 100 NOK |
| `FX_SEK_DKK` | SEK/DKK Exchange Rate | Monthly | DKK per 100 SEK |
| `GOVT_BOND_YIELD` | Government Bonds Redemption Yield | Monthly | % |
| `GOVT_BOND_10Y` | 10-Year Government Bond Yield | Monthly | % |
| `MORTGAGE_BOND_YIELD` | Unit Mortgage Bonds Redemption Yield | Monthly | % |
| `BOP_CURRENT_ACCOUNT` | Current Account Balance (DKK mn, SA) | Monthly | DKK mn |
| `BOP_GOODS` | Goods Trade Balance (DKK mn, SA) | Monthly | DKK mn |
| `BOP_SERVICES` | Services Trade Balance (DKK mn, SA) | Monthly | DKK mn |
| `BOP_PRIMARY_INCOME` | Primary Income Balance (DKK mn, SA) | Monthly | DKK mn |
| `MFI_LOANS_TOTAL` | MFI Total Domestic Loans (DKK mn) | Monthly | DKK mn |
| `MFI_LOANS_NFC` | MFI Loans to Non-Financial Corporates (DKK mn) | Monthly | DKK mn |
| `MFI_LOANS_HOUSEHOLDS` | MFI Loans to Households (DKK mn) | Monthly | DKK mn |
| `MFI_LENDING_RATE` | MFI Average Lending Rate (%) | Monthly | % |
| `GOVT_SECURITIES_TOTAL` | Government Debt Securities Outstanding (DKK mn) | Monthly | DKK mn |
| `GOVT_BONDS_STOCK` | Government Bonds Outstanding (DKK mn) | Monthly | DKK mn |

**CLI Examples:**
```bash
python3 modules/danmarks_nationalbank.py DN_DISCOUNT_RATE
python3 modules/danmarks_nationalbank.py FX_EUR_DKK
python3 modules/danmarks_nationalbank.py policy-rates     # All DN policy rates
python3 modules/danmarks_nationalbank.py fx-rates          # DKK exchange rates
python3 modules/danmarks_nationalbank.py bond-yields       # Govt & mortgage bond yields
python3 modules/danmarks_nationalbank.py list
```

---

### cnb_czech.py — Czech National Bank (CNB)

- **Source:** Czech National Bank (Česká národní banka)
- **APIs:**
  - FX fixing: `https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt`
  - PRIBOR: `https://www.cnb.cz/en/financial-markets/money-market/pribor/fixing-of-interest-rates-on-interbank-deposits-pribor/daily.txt`
  - Policy rates: `https://www.cnb.cz/en/faq/.galleries/development_of_the_cnb_2w_repo_rate.txt`
  - ARAD (deep data): `https://www.cnb.cz/aradb/api/v1` (requires free API key)
- **Protocol:** REST TXT/CSV (open feeds), REST JSON (ARAD)
- **Auth:** None for FX/PRIBOR/policy feeds; ARAD requires `ARAD_API_KEY` env var (free)
- **Freshness:** Daily (FX fixing ~14:15 CET, PRIBOR 48h delay), Event-driven (policy rates)
- **Coverage:** Czech Republic

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `FX_USD` | CZK/USD Daily Fixing | Daily | CZK |
| `FX_EUR` | CZK/EUR Daily Fixing | Daily | CZK |
| `FX_GBP` | CZK/GBP Daily Fixing | Daily | CZK |
| `FX_CHF` | CZK/CHF Daily Fixing | Daily | CZK |
| `FX_JPY` | CZK/JPY Daily Fixing (per 100 JPY) | Daily | CZK/100 |
| `FX_CAD` | CZK/CAD Daily Fixing | Daily | CZK |
| `FX_AUD` | CZK/AUD Daily Fixing | Daily | CZK |
| `FX_PLN` | CZK/PLN Daily Fixing | Daily | CZK |
| `FX_HUF` | CZK/HUF Daily Fixing (per 100 HUF) | Daily | CZK/100 |
| `FX_SEK` | CZK/SEK Daily Fixing | Daily | CZK |
| `FX_NOK` | CZK/NOK Daily Fixing | Daily | CZK |
| `FX_CNY` | CZK/CNY Daily Fixing | Daily | CZK |
| `PRIBOR_1D` | PRIBOR Overnight (% p.a.) | Daily | % p.a. |
| `PRIBOR_1W` | PRIBOR 1 Week (% p.a.) | Daily | % p.a. |
| `PRIBOR_2W` | PRIBOR 2 Weeks (% p.a.) | Daily | % p.a. |
| `PRIBOR_1M` | PRIBOR 1 Month (% p.a.) | Daily | % p.a. |
| `PRIBOR_3M` | PRIBOR 3 Months (% p.a.) | Daily | % p.a. |
| `PRIBOR_6M` | PRIBOR 6 Months (% p.a.) | Daily | % p.a. |
| `PRIBOR_1Y` | PRIBOR 1 Year (% p.a.) | Daily | % p.a. |
| `CNB_2W_REPO` | CNB 2-Week Repo Rate (%) | Event | % |
| `CNB_DISCOUNT` | CNB Discount Rate (%) | Event | % |
| `CNB_LOMBARD` | CNB Lombard Rate (%) | Event | % |

**CLI Examples:**
```bash
python3 modules/cnb_czech.py FX_EUR              # CZK/EUR daily fixing
python3 modules/cnb_czech.py PRIBOR_3M            # 3-month PRIBOR rate
python3 modules/cnb_czech.py CNB_2W_REPO          # Main CNB policy rate
python3 modules/cnb_czech.py pribor-curve          # Full PRIBOR term structure
python3 modules/cnb_czech.py policy-rates          # All CNB official policy rates
python3 modules/cnb_czech.py list                  # List all available indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'cnb_czech',
    params: { indicator: 'FX_EUR' }
  })
});
```

---

### abs_australia_sdmx.py — ABS Australia Enhanced (SDMX 2.1)

- **Source:** Australian Bureau of Statistics
- **API:** `https://data.api.abs.gov.au/rest`
- **Protocol:** SDMX 2.1 REST (SDMX-JSON 2.0)
- **Auth:** None (open access)
- **Freshness:** Quarterly (GDP, CPI, BoP), Monthly (labour force, retail trade, building approvals, trade)
- **Coverage:** Australia

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP` | GDP — Chain Volume Measures (AUD mn) | Quarterly | AUD mn |
| `GDP_GROWTH` | GDP Growth — Quarterly (% change) | Quarterly | % |
| `GDP_PER_CAPITA` | GDP Per Capita — Chain Volume (AUD) | Quarterly | AUD |
| `TERMS_OF_TRADE` | Terms of Trade — Index | Quarterly | Index |
| `HOUSEHOLD_SAVING_RATIO` | Household Saving Ratio (%) | Quarterly | % |
| `CPI_INDEX` | CPI — All Groups Index | Quarterly | Index |
| `CPI_ANNUAL_CHANGE` | CPI — Annual % Change (Monthly Indicator) | Monthly | % |
| `CPI_QUARTERLY_CHANGE` | CPI — Quarterly % Change | Quarterly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate (%) | Monthly | % |
| `EMPLOYMENT` | Employed Persons ('000) | Monthly | '000 |
| `PARTICIPATION_RATE` | Labour Force Participation Rate (%) | Monthly | % |
| `LABOUR_FORCE` | Labour Force ('000) | Monthly | '000 |
| `CURRENT_ACCOUNT` | Current Account Balance (AUD mn) | Quarterly | AUD mn |
| `BOP_GOODS_BALANCE` | Goods Balance (AUD mn) | Quarterly | AUD mn |
| `RETAIL_TRADE` | Retail Turnover — Total (AUD mn) | Monthly | AUD mn |
| `BUILDING_APPROVALS` | Building Approvals — Total Residential Dwellings | Monthly | Number |
| `TRADE_BALANCE` | Goods Trade Balance (AUD mn) | Monthly | AUD mn |
| `EXPORTS` | Total Goods Exports (AUD mn) | Monthly | AUD mn |

**CLI Examples:**
```bash
python3 modules/abs_australia_sdmx.py GDP_GROWTH
python3 modules/abs_australia_sdmx.py UNEMPLOYMENT_RATE
python3 modules/abs_australia_sdmx.py dashboard            # Headline macro dashboard
python3 modules/abs_australia_sdmx.py discover labour      # Discover ABS dataflows
python3 modules/abs_australia_sdmx.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'abs_australia_sdmx',
    params: { indicator: 'GDP_GROWTH' }
  })
});
```

---

### uae_data.py — UAE Open Data & CBUAE

- **Source:** Central Bank of the UAE (CBUAE) + World Bank
- **APIs:** CBUAE FX: `https://www.centralbank.ae/umbraco/Surface/Exchange/GetExchangeRateAllCurrency` / World Bank: `https://api.worldbank.org/v2/country/ARE/indicator`
- **Protocol:** CBUAE Surface API (HTML scraping, Arabic-to-ISO mapping) + World Bank REST JSON
- **Auth:** None (open access)
- **Freshness:** Daily (FX rates), Annual (macro indicators from World Bank)
- **Coverage:** United Arab Emirates

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `FX_USD` | AED per USD (CBUAE Official, pegged ~3.6725) | Daily | AED |
| `FX_EUR` | AED per EUR (CBUAE Official) | Daily | AED |
| `FX_GBP` | AED per GBP (CBUAE Official) | Daily | AED |
| `FX_JPY` | AED per JPY (CBUAE Official) | Daily | AED |
| `FX_CHF` | AED per CHF (CBUAE Official) | Daily | AED |
| `FX_SAR` | AED per SAR (CBUAE Official) | Daily | AED |
| `FX_CNY` | AED per CNY (CBUAE Official) | Daily | AED |
| `FX_INR` | AED per INR (CBUAE Official) | Daily | AED |
| `FX_KWD` | AED per KWD (CBUAE Official) | Daily | AED |
| `FX_EGP` | AED per EGP (CBUAE Official) | Daily | AED |
| `GDP_CURRENT_USD` | UAE GDP — Current USD | Annual | USD |
| `GDP_GROWTH` | UAE GDP Growth Rate (%) | Annual | % |
| `CPI_INFLATION` | UAE CPI Inflation (%) | Annual | % |
| `CPI_INDEX` | UAE Consumer Price Index (2010=100) | Annual | index |
| `BROAD_MONEY` | UAE Broad Money — M2 (AED) | Annual | AED |
| `FX_RESERVES` | UAE Total Reserves incl. Gold (USD) | Annual | USD |
| `EXPORTS` | UAE Exports of Goods & Services (USD) | Annual | USD |
| `IMPORTS` | UAE Imports of Goods & Services (USD) | Annual | USD |
| `CURRENT_ACCOUNT` | UAE Current Account Balance (USD) | Annual | USD |
| `GDP_PER_CAPITA` | UAE GDP per Capita (USD) | Annual | USD |

**CLI Examples:**
```bash
python3 modules/uae_data.py FX_USD                 # AED/USD peg rate
python3 modules/uae_data.py GDP_GROWTH              # UAE GDP growth
python3 modules/uae_data.py fx                      # All CBUAE FX rates (76 currencies)
python3 modules/uae_data.py macro                   # UAE macroeconomic summary
python3 modules/uae_data.py list
```

---

### destatis_germany.py — Destatis GENESIS-Online (Statistisches Bundesamt)

- **Source:** Statistisches Bundesamt (Federal Statistical Office of Germany)
- **API:** `https://www-genesis.destatis.de/genesisWS/rest/2020`
- **Protocol:** REST POST with header auth (flat-file CSV or JSON response)
- **Auth:** Free registration required — `DESTATIS_USER` and `DESTATIS_PASSWORD` in .env
- **Freshness:** Monthly (CPI, IPI, PPI, trade, construction), Quarterly (GDP), Annual (some series)
- **Coverage:** Germany

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_ANNUAL` | GDP — Gross Domestic Product (Annual) | Annual | EUR bn |
| `GDP_QUARTERLY` | GDP — Gross Domestic Product (Quarterly) | Quarterly | EUR bn |
| `CPI_MONTHLY` | Consumer Price Index (Monthly, 2020=100) | Monthly | Index |
| `CPI_ANNUAL` | Consumer Price Index (Annual, 2020=100) | Annual | Index |
| `HICP_MONTHLY` | Harmonised Index of Consumer Prices (Monthly, 2015=100) | Monthly | Index |
| `HICP_ANNUAL` | Harmonised Index of Consumer Prices (Annual, 2015=100) | Annual | Index |
| `EMPLOYMENT` | Employment & Unemployment (Annual) | Annual | 1000 persons |
| `TRADE_MONTHLY` | Foreign Trade — Exports & Imports (Monthly) | Monthly | EUR mn |
| `TRADE_ANNUAL` | Foreign Trade — Exports & Imports (Annual) | Annual | EUR mn |
| `INDUSTRIAL_PRODUCTION` | Industrial Production Index (Monthly, 2021=100) | Monthly | Index |
| `PPI_MONTHLY` | Producer Price Index (Monthly, 2021=100) | Monthly | Index |
| `PPI_ANNUAL` | Producer Price Index (Annual, 2021=100) | Annual | Index |
| `CONSTRUCTION` | Construction Activity (Monthly) | Monthly | various |

**CLI Examples:**
```bash
python3 modules/destatis_germany.py GDP_QUARTERLY
python3 modules/destatis_germany.py CPI_MONTHLY
python3 modules/destatis_germany.py INDUSTRIAL_PRODUCTION
python3 modules/destatis_germany.py search "Bruttoinlandsprodukt"  # Search GENESIS tables
python3 modules/destatis_germany.py check-auth                     # Verify credentials
python3 modules/destatis_germany.py list
```

---

### edinet_japan.py — EDINET Japan Securities Filings (FSA)

- **Source:** EDINET — Financial Services Agency (FSA) of Japan
- **API:** `https://api.edinet-fsa.go.jp/api/v2`
- **Protocol:** REST (JSON metadata, ZIP document bundles)
- **Auth:** Subscription-Key required (free at https://disclosure.edinet-fsa.go.jp) — `EDINET_API_KEY`
- **Freshness:** Daily (filings published continuously)
- **Coverage:** All Japanese listed companies

**Indicators:**

| Key | Name | Frequency |
|-----|------|-----------|
| `ANNUAL_REPORTS` | Annual Securities Reports (有価証券報告書) | Annual |
| `QUARTERLY_REPORTS` | Quarterly Securities Reports (四半期報告書) | Quarterly |
| `SEMIANNUAL_REPORTS` | Semi-Annual Reports (半期報告書) | Semi-annual |
| `LARGE_SHAREHOLDING` | Large Shareholding Reports (5%+ ownership) | Event-driven |
| `TENDER_OFFERS` | Tender Offer Notifications (公開買付届出書) | Event-driven |
| `SECURITIES_REGISTRATION` | Securities Registration Statements (IPOs) | Event-driven |
| `ALL_FILINGS` | All Filings (全書類) — all types for date | Daily |

**CLI Examples:**
```bash
python3 modules/edinet_japan.py ANNUAL_REPORTS              # Today's annual reports
python3 modules/edinet_japan.py ANNUAL_REPORTS 2026-03-31   # Specific date
python3 modules/edinet_japan.py LARGE_SHAREHOLDING 2026-03-01 2026-03-31  # Date range
python3 modules/edinet_japan.py search "Toyota"             # Search by company name
python3 modules/edinet_japan.py download S100XXXX 5         # Download CSV extract
python3 modules/edinet_japan.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'edinet_japan',
    params: { indicator: 'ANNUAL_REPORTS', start_date: '2026-04-01' }
  })
});
```

---

### fca_uk.py — FCA UK Financial Services Register

- **Source:** UK Financial Conduct Authority
- **API:** `https://register.fca.org.uk/services/V0.1`
- **Protocol:** REST JSON (FCA Register API V0.1)
- **Auth:** API key + email required (free at https://register.fca.org.uk/Developer/s/) — `FCA_API_KEY`, `FCA_API_EMAIL`
- **Freshness:** Real-time (regulatory register is continuously updated)
- **Coverage:** United Kingdom (all FCA-regulated entities)

**Indicators:**

| Key | Name | Query |
|-----|------|-------|
| `FIRM_SEARCH` | Search FCA-authorized firms | firm name or FRN |
| `INDIVIDUAL_SEARCH` | Search approved/prohibited individuals | individual name |
| `FUND_SEARCH` | Search collective investment schemes | fund name or PRN |
| `FIRM_DETAILS` | Full regulatory details for a firm | FRN (e.g. 122702) |
| `FIRM_PERMISSIONS` | Regulated activities and permissions | FRN |
| `FIRM_INDIVIDUALS` | Approved individuals at a firm | FRN |
| `FIRM_PASSPORTS` | Cross-border passporting permissions | FRN |
| `FIRM_DISCIPLINARY` | Enforcement actions, fines, sanctions | FRN |
| `FIRM_REQUIREMENTS` | Regulatory requirements and conditions | FRN |
| `FIRM_ADDRESSES` | Registered addresses, phone, websites | FRN |
| `FIRM_EXCLUSIONS` | PSD2 and payment service exclusions | FRN |
| `INDIVIDUAL_DETAILS` | Controlled functions for an individual | IRN (e.g. MXC29012) |
| `REGULATED_MARKETS` | FCA-recognized regulated exchanges | none |

**CLI Examples:**
```bash
python3 modules/fca_uk.py FIRM_SEARCH "barclays bank"       # Search firms
python3 modules/fca_uk.py FIRM_DETAILS 122702               # Firm details by FRN
python3 modules/fca_uk.py FIRM_DISCIPLINARY 122702           # Disciplinary history
python3 modules/fca_uk.py INDIVIDUAL_SEARCH "mark carney"    # Search individuals
python3 modules/fca_uk.py REGULATED_MARKETS                  # UK regulated exchanges
python3 modules/fca_uk.py status 122702                      # Quick firm status check
python3 modules/fca_uk.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'fca_uk',
    params: { indicator: 'FIRM_SEARCH', query: 'barclays' }
  })
});
```

---

### rba_enhanced.py — Reserve Bank of Australia (RBA Enhanced)

- **Source:** Reserve Bank of Australia
- **API:** `https://www.rba.gov.au/statistics/tables/csv`
- **Protocol:** Direct CSV download (stable URLs per table)
- **Auth:** None (open access, no rate limits)
- **Freshness:** Daily (F1 money market, F2 bond yields), Monthly (F5 lending rates, F11 FX, F13 international rates, D1 financial aggregates), Quarterly (H1 GDP/income)
- **Coverage:** Australia / International comparison (F13)

**Tables Covered:**

| Table | Name | Frequency |
|-------|------|-----------|
| F1 | Interest Rates & Yields — Money Market | Daily |
| F2 | Capital Market Yields — Government Bonds | Daily |
| F5 | Indicator Lending Rates | Monthly |
| F11 | Exchange Rates | Monthly |
| F13 | International Official Interest Rates | Monthly |
| D1 | Growth in Financial Aggregates | Monthly |
| H1 | GDP and Income | Quarterly |

**Indicators:**

| Key | Name | Table | Frequency | Unit |
|-----|------|-------|-----------|------|
| `F1_CASH_RATE_TARGET` | RBA Cash Rate Target | F1 | Daily | % |
| `F1_OVERNIGHT_RATE` | Interbank Overnight Cash Rate | F1 | Daily | % |
| `F1_3M_BABS` | 3-Month BABs/NCDs Rate | F1 | Daily | % |
| `F1_3M_OIS` | 3-Month OIS Rate | F1 | Daily | % |
| `F1_3M_TREASURY_NOTE` | 3-Month Treasury Note Rate | F1 | Daily | % |
| `F2_GOVT_2Y` | AU Govt Bond Yield 2Y | F2 | Daily | % p.a. |
| `F2_GOVT_3Y` | AU Govt Bond Yield 3Y | F2 | Daily | % p.a. |
| `F2_GOVT_5Y` | AU Govt Bond Yield 5Y | F2 | Daily | % p.a. |
| `F2_GOVT_10Y` | AU Govt Bond Yield 10Y | F2 | Daily | % p.a. |
| `F2_GOVT_INDEXED` | AU Govt Indexed Bond Yield 10Y | F2 | Daily | % p.a. |
| `F5_HOUSING_VARIABLE` | Housing Loan Rate — Variable Standard Owner-Occ | F5 | Monthly | % p.a. |
| `F5_HOUSING_DISCOUNTED` | Housing Loan Rate — Variable Discounted Owner-Occ | F5 | Monthly | % p.a. |
| `F5_HOUSING_3YR_FIXED` | Housing Loan Rate — 3-Year Fixed Owner-Occ | F5 | Monthly | % p.a. |
| `F5_CREDIT_CARD_STD` | Credit Card Rate — Standard | F5 | Monthly | % p.a. |
| `F5_SME_VARIABLE` | Small Business Lending Rate — Variable Term | F5 | Monthly | % p.a. |
| `F11_AUD_USD` | AUD/USD Exchange Rate | F11 | Monthly | USD |
| `F11_TWI` | AUD Trade-Weighted Index | F11 | Monthly | Index |
| `F11_AUD_CNY` | AUD/CNY Exchange Rate | F11 | Monthly | CNY |
| `F11_AUD_JPY` | AUD/JPY Exchange Rate | F11 | Monthly | JPY |
| `F11_AUD_EUR` | AUD/EUR Exchange Rate | F11 | Monthly | EUR |
| `F11_AUD_GBP` | AUD/GBP Exchange Rate | F11 | Monthly | GBP |
| `F13_US_FED_FUNDS` | US Federal Funds Max Target Rate | F13 | Monthly | % p.a. |
| `F13_JAPAN_RATE` | Japan Policy Rate (BOJ) | F13 | Monthly | % p.a. |
| `F13_ECB_REFI` | ECB Refinancing Rate | F13 | Monthly | % p.a. |
| `F13_UK_BANK_RATE` | UK Bank Rate (BOE) | F13 | Monthly | % p.a. |
| `F13_CANADA_RATE` | Canada Target Rate (BOC) | F13 | Monthly | % p.a. |
| `F13_AUSTRALIA_RATE` | Australia Target Cash Rate (RBA, F13 intl) | F13 | Monthly | % p.a. |
| `D1_CREDIT_HOUSING_MOM` | Housing Credit — Monthly Growth | D1 | Monthly | % |
| `D1_CREDIT_HOUSING_YOY` | Housing Credit — 12-Month Growth | D1 | Monthly | % |
| `D1_CREDIT_TOTAL_MOM` | Total Credit — Monthly Growth | D1 | Monthly | % |
| `D1_CREDIT_TOTAL_YOY` | Total Credit — 12-Month Growth | D1 | Monthly | % |
| `D1_M3_MOM` | M3 — Monthly Growth | D1 | Monthly | % |
| `D1_M3_YOY` | M3 — 12-Month Growth | D1 | Monthly | % |
| `D1_BROAD_MONEY_YOY` | Broad Money — 12-Month Growth | D1 | Monthly | % |
| `H1_REAL_GDP` | Real GDP (AUD mn, chain volume) | H1 | Quarterly | AUD mn |
| `H1_REAL_GDP_GROWTH` | Real GDP Growth — Year-Ended | H1 | Quarterly | % |
| `H1_NOMINAL_GDP` | Nominal GDP (AUD mn, current price) | H1 | Quarterly | AUD mn |
| `H1_NOMINAL_GDP_GROWTH` | Nominal GDP Growth — Year-Ended | H1 | Quarterly | % |
| `H1_TERMS_OF_TRADE` | Terms of Trade (Index) | H1 | Quarterly | Index |

**CLI Examples:**
```bash
python3 modules/rba_enhanced.py F1_CASH_RATE_TARGET      # RBA cash rate target
python3 modules/rba_enhanced.py F2_GOVT_10Y              # 10Y AU govt bond yield
python3 modules/rba_enhanced.py F5_HOUSING_VARIABLE      # Variable housing loan rate
python3 modules/rba_enhanced.py F11_AUD_USD              # AUD/USD exchange rate
python3 modules/rba_enhanced.py F13_US_FED_FUNDS         # US Fed Funds from RBA table
python3 modules/rba_enhanced.py D1_CREDIT_HOUSING_YOY    # Housing credit 12M growth
python3 modules/rba_enhanced.py H1_REAL_GDP_GROWTH       # Real GDP year-ended growth
python3 modules/rba_enhanced.py yield-curve              # AU govt bond yield curve
python3 modules/rba_enhanced.py rates                    # All interest/policy rates
python3 modules/rba_enhanced.py fx                       # All AUD exchange rates
python3 modules/rba_enhanced.py list                     # List all 39 indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'rba_enhanced',
    params: { indicator: 'F1_CASH_RATE_TARGET' }
  })
});
```

---

### bank_of_canada_valet.py — Bank of Canada (Valet API Enhanced)

- **Source:** Bank of Canada
- **API:** `https://www.bankofcanada.ca/valet`
- **Protocol:** REST (JSON)
- **Auth:** None (open access)
- **Freshness:** Daily (FX, yields), Weekly (T-bills, bank rates), Monthly/Quarterly (BCPI, BOS)
- **Coverage:** Canada

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `OVERNIGHT_RATE` | BoC Overnight Rate | Daily | % |
| `BANK_RATE` | BoC Bank Rate | Monthly | % |
| `CORRA` | CORRA — Overnight Repo Rate Average | Daily | % |
| `GOC_2Y` | GoC Benchmark Bond Yield 2Y | Daily | % |
| `GOC_3Y` | GoC Benchmark Bond Yield 3Y | Daily | % |
| `GOC_5Y` | GoC Benchmark Bond Yield 5Y | Daily | % |
| `GOC_7Y` | GoC Benchmark Bond Yield 7Y | Daily | % |
| `GOC_10Y` | GoC Benchmark Bond Yield 10Y | Daily | % |
| `GOC_LONG` | GoC Benchmark Bond Yield Long-Term (30Y) | Daily | % |
| `GOC_RRB` | GoC Real Return Bond Yield | Daily | % |
| `GOC_AVG_1TO3Y` | GoC Marketable Bond Avg Yield 1-3Y | Daily | % |
| `GOC_AVG_3TO5Y` | GoC Marketable Bond Avg Yield 3-5Y | Daily | % |
| `GOC_AVG_5TO10Y` | GoC Marketable Bond Avg Yield 5-10Y | Daily | % |
| `GOC_AVG_OVER10Y` | GoC Marketable Bond Avg Yield >10Y | Daily | % |
| `TBILL_1M` | T-Bill Yield 1 Month | Weekly | % |
| `TBILL_3M` | T-Bill Yield 3 Month | Weekly | % |
| `TBILL_6M` | T-Bill Yield 6 Month | Weekly | % |
| `TBILL_1Y` | T-Bill Yield 1 Year | Weekly | % |
| `TBILL_MID_90D` | 90-Day T-Bill Mid Rate | Daily | % |
| `FX_USD_CAD` | USD/CAD Exchange Rate | Daily | CAD |
| `FX_EUR_CAD` | EUR/CAD Exchange Rate | Daily | CAD |
| `FX_GBP_CAD` | GBP/CAD Exchange Rate | Daily | CAD |
| `FX_JPY_CAD` | JPY/CAD Exchange Rate | Daily | CAD |
| `FX_CHF_CAD` | CHF/CAD Exchange Rate | Daily | CAD |
| `FX_AUD_CAD` | AUD/CAD Exchange Rate | Daily | CAD |
| `FX_CNY_CAD` | CNY/CAD Exchange Rate | Daily | CAD |
| `FX_KRW_CAD` | KRW/CAD Exchange Rate | Daily | CAD |
| `FX_SEK_CAD` | SEK/CAD Exchange Rate | Daily | CAD |
| `FX_NOK_CAD` | NOK/CAD Exchange Rate | Daily | CAD |
| `FX_MXN_CAD` | MXN/CAD Exchange Rate | Daily | CAD |
| `FX_BRL_CAD` | BRL/CAD Exchange Rate | Daily | CAD |
| `FX_INR_CAD` | INR/CAD Exchange Rate | Daily | CAD |
| `FX_SGD_CAD` | SGD/CAD Exchange Rate | Daily | CAD |
| `FX_TWD_CAD` | TWD/CAD Exchange Rate | Daily | CAD |
| `FX_ZAR_CAD` | ZAR/CAD Exchange Rate | Daily | CAD |
| `PRIME_RATE` | Chartered Bank Prime Rate | Weekly | % |
| `MORTGAGE_1Y` | Posted Mortgage Rate 1Y | Weekly | % |
| `MORTGAGE_3Y` | Posted Mortgage Rate 3Y | Weekly | % |
| `MORTGAGE_5Y` | Posted Mortgage Rate 5Y | Weekly | % |
| `GIC_1Y` | Posted GIC Rate 1Y | Weekly | % |
| `GIC_5Y` | Posted GIC Rate 5Y Personal Fixed | Weekly | % |
| `YIELD_VOLATILITY_GOC` | GoC Bond Yield Volatility | Daily | index |
| `TERM_PREMIUM_2Y` | GoC 2Y Term Premium (ACM) | Daily | % |
| `TERM_PREMIUM_5Y` | GoC 5Y Term Premium (ACM) | Daily | % |
| `TERM_PREMIUM_10Y` | GoC 10Y Term Premium (ACM) | Daily | % |
| `BOS_INDICATOR` | Business Outlook Survey Indicator | Quarterly | index |
| `BCPI_TOTAL` | BCPI Total — Monthly | Monthly | index |
| `BCPI_ENERGY` | BCPI Energy — Monthly | Monthly | index |
| `BCPI_METALS` | BCPI Metals & Minerals — Monthly | Monthly | index |

**CLI Examples:**
```bash
python3 modules/bank_of_canada_valet.py GOC_10Y
python3 modules/bank_of_canada_valet.py OVERNIGHT_RATE
python3 modules/bank_of_canada_valet.py FX_USD_CAD
python3 modules/bank_of_canada_valet.py yield-curve        # Full GoC + T-bill yield curve
python3 modules/bank_of_canada_valet.py fx-rates            # All 26 CAD FX pairs
python3 modules/bank_of_canada_valet.py policy-rates        # BoC policy & overnight rates
python3 modules/bank_of_canada_valet.py group bond_yields   # All bond yield indicators
python3 modules/bank_of_canada_valet.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'bank_of_canada_valet',
    params: { indicator: 'GOC_10Y' }
  })
});
```

---

### ine_spain.py — INE Spain (Instituto Nacional de Estadística)

- **Source:** Instituto Nacional de Estadística
- **API:** `https://servicios.ine.es/wstempus/js/EN/`
- **Protocol:** REST JSON (Tempus3 API)
- **Auth:** None (open access)
- **Freshness:** Monthly (CPI, IPI), Quarterly (GDP, EPA labour force, housing, trade)
- **Coverage:** Spain

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_CURRENT` | GDP at Market Prices — Current Prices (EUR mn) | Quarterly | EUR mn |
| `GDP_QOQ` | GDP QoQ Growth Rate — SA Volume (%) | Quarterly | % |
| `GDP_YOY` | GDP YoY Growth Rate — SA Volume (%) | Quarterly | % |
| `CPI_INDEX` | CPI Overall Index (Base 2024=100) | Monthly | Index |
| `CPI_MOM` | CPI Monthly Variation Rate (%) | Monthly | % |
| `CPI_YOY` | CPI Annual Inflation Rate (%) | Monthly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate — All Ages (%) | Quarterly | % |
| `YOUTH_UNEMPLOYMENT` | Youth Unemployment Rate — Under 25 (%) | Quarterly | % |
| `ACTIVE_POPULATION` | Active Population — 16+ (thousands) | Quarterly | thousands |
| `EMPLOYED_PERSONS` | Employed Persons — 16+ (thousands) | Quarterly | thousands |
| `IPI_TOTAL` | Industrial Production Index — SA Total (2021=100) | Monthly | Index |
| `IPI_MOM` | IPI Monthly Variation Rate — SA (%) | Monthly | % |
| `HPI_INDEX` | Housing Price Index — General (2015=100) | Quarterly | Index |
| `HPI_YOY` | Housing Price Index — YoY Change (%) | Quarterly | % |
| `HPI_QOQ` | Housing Price Index — QoQ Change (%) | Quarterly | % |
| `EXPORTS_VOLUME` | Exports of Goods & Services — SA Volume Index | Quarterly | Index |
| `EXPORTS_YOY` | Exports YoY Growth — SA Volume (%) | Quarterly | % |
| `IMPORTS_VOLUME` | Imports of Goods & Services — SA Volume Index | Quarterly | Index |
| `IMPORTS_YOY` | Imports YoY Growth — SA Volume (%) | Quarterly | % |

**CLI Examples:**
```bash
python3 modules/ine_spain.py GDP_QOQ
python3 modules/ine_spain.py CPI_YOY
python3 modules/ine_spain.py UNEMPLOYMENT_RATE
python3 modules/ine_spain.py HPI_INDEX
python3 modules/ine_spain.py operations        # Discover all INE statistical operations
python3 modules/ine_spain.py tables 237        # List tables for GDP operation
python3 modules/ine_spain.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'ine_spain',
    params: { indicator: 'GDP_QOQ' }
  })
});
```

---

### dnb_netherlands.py — De Nederlandsche Bank (DNB)

- **Source:** De Nederlandsche Bank
- **API:** `https://api.dnb.nl/statpub-intapi-prd/v1`
- **Protocol:** REST JSON (Azure APIM)
- **Auth:** Subscription key via `DNB_SUBSCRIPTION_KEY` env var (optional — public fallback key available)
- **Freshness:** Monthly (monetary aggregates, household rates), Quarterly (FSI, banking, insurance, pension), Half-yearly (payments)
- **Coverage:** Netherlands

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `FINANCIAL_STABILITY_Q` | Financial Stability Indicators (Quarterly) | Quarterly | % / ratio |
| `FINANCIAL_STABILITY_Y` | Financial Stability Indicators (Yearly) | Yearly | % / ratio |
| `BANK_STRUCTURE` | Structural Indicators — Dutch Banking System | Quarterly | EUR mn / count |
| `INSURANCE_BALANCE_SHEET` | Insurance Corporations Balance Sheet | Quarterly | EUR mn |
| `PENSION_BALANCE_SHEET` | Pension Funds Balance Sheet | Quarterly | EUR mn |
| `INSURERS_CASHFLOW` | Insurers Cash Flow Statement | Quarterly | EUR mn |
| `PAYMENT_TRANSACTIONS` | Payment Transactions (Number & Value) | Half-yearly | EUR mn / millions |
| `PAYMENT_INFRA` | Domestic Payment Infrastructure (Units) | Half-yearly | units / millions |
| `MONETARY_AGGREGATES` | Dutch Contribution to Monetary Aggregates | Monthly | EUR mn |
| `HOUSEHOLD_RATES` | Household Deposits & Loans Interest Rates | Monthly | % |

**CLI Examples:**
```bash
python3 modules/dnb_netherlands.py FINANCIAL_STABILITY_Q
python3 modules/dnb_netherlands.py HOUSEHOLD_RATES
python3 modules/dnb_netherlands.py MONETARY_AGGREGATES
python3 modules/dnb_netherlands.py FINANCIAL_STABILITY_Q indicator=capital   # Dimension filter
python3 modules/dnb_netherlands.py search "monetary"                         # Search DNB datasets
python3 modules/dnb_netherlands.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'dnb_netherlands',
    params: { indicator: 'FINANCIAL_STABILITY_Q' }
  })
});
```

---

### bnr_romania.py — National Bank of Romania (BNR)

- **Source:** National Bank of Romania (Banca Națională a României)
- **API:** `https://www.bnr.ro/nbrfxrates.xml` (daily) + `https://www.bnr.ro/nbrfxrates10days.xml` (10-day)
- **Protocol:** XML feeds (open access, stable)
- **Auth:** None
- **Freshness:** Daily (published ~13:00 EET on business days)
- **Coverage:** Romania — RON base currency

**Indicators (37 FX pairs):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `RON_EUR` | RON/EUR (Euro) | Daily | RON |
| `RON_USD` | RON/USD (US Dollar) | Daily | RON |
| `RON_GBP` | RON/GBP (British Pound) | Daily | RON |
| `RON_CHF` | RON/CHF (Swiss Franc) | Daily | RON |
| `RON_JPY` | RON/JPY (Japanese Yen, per 100) | Daily | RON |
| `RON_AUD` | RON/AUD (Australian Dollar) | Daily | RON |
| `RON_CAD` | RON/CAD (Canadian Dollar) | Daily | RON |
| `RON_CNY` | RON/CNY (Chinese Yuan) | Daily | RON |
| `RON_CZK` | RON/CZK (Czech Koruna) | Daily | RON |
| `RON_DKK` | RON/DKK (Danish Krone) | Daily | RON |
| `RON_HUF` | RON/HUF (Hungarian Forint, per 100) | Daily | RON |
| `RON_PLN` | RON/PLN (Polish Zloty) | Daily | RON |
| `RON_SEK` | RON/SEK (Swedish Krona) | Daily | RON |
| `RON_NOK` | RON/NOK (Norwegian Krone) | Daily | RON |
| `RON_TRY` | RON/TRY (Turkish Lira) | Daily | RON |
| `RON_ZAR` | RON/ZAR (South African Rand) | Daily | RON |
| `RON_KRW` | RON/KRW (South Korean Won, per 100) | Daily | RON |
| `RON_INR` | RON/INR (Indian Rupee) | Daily | RON |
| `RON_BRL` | RON/BRL (Brazilian Real) | Daily | RON |
| `RON_MXN` | RON/MXN (Mexican Peso) | Daily | RON |
| `RON_SGD` | RON/SGD (Singapore Dollar) | Daily | RON |
| `RON_HKD` | RON/HKD (Hong Kong Dollar) | Daily | RON |
| `RON_NZD` | RON/NZD (New Zealand Dollar) | Daily | RON |
| `RON_THB` | RON/THB (Thai Baht) | Daily | RON |
| `RON_PHP` | RON/PHP (Philippine Peso) | Daily | RON |
| `RON_MYR` | RON/MYR (Malaysian Ringgit) | Daily | RON |
| `RON_IDR` | RON/IDR (Indonesian Rupiah, per 100) | Daily | RON |
| `RON_ILS` | RON/ILS (Israeli Shekel) | Daily | RON |
| `RON_EGP` | RON/EGP (Egyptian Pound) | Daily | RON |
| `RON_MDL` | RON/MDL (Moldovan Leu) | Daily | RON |
| `RON_RSD` | RON/RSD (Serbian Dinar) | Daily | RON |
| `RON_RUB` | RON/RUB (Russian Ruble) | Daily | RON |
| `RON_UAH` | RON/UAH (Ukrainian Hryvnia) | Daily | RON |
| `RON_ISK` | RON/ISK (Icelandic Króna, per 100) | Daily | RON |
| `RON_AED` | RON/AED (UAE Dirham) | Daily | RON |
| `RON_XAU` | RON/XAU (Gold, troy oz) | Daily | RON |
| `RON_XDR` | RON/XDR (IMF SDR) | Daily | RON |

**CLI Examples:**
```bash
python3 modules/bnr_romania.py RON_EUR             # Today's RON/EUR reference rate
python3 modules/bnr_romania.py RON_USD             # Today's RON/USD reference rate
python3 modules/bnr_romania.py rates               # All rates for today
python3 modules/bnr_romania.py rates 2026-03-28    # All rates for specific date
python3 modules/bnr_romania.py history             # 10-day history all currencies
python3 modules/bnr_romania.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'bnr_romania',
    params: { indicator: 'RON_EUR' }
  })
});
```

---

### statbel_belgium.py — Statbel (Statistics Belgium)

- **Source:** Statbel — Belgian Statistical Office
- **APIs:**
  - CPI data: `https://statbel.fgov.be/sites/default/files/.../CPI%20All%20base%20years.zip` (pipe-delimited TXT in ZIP)
  - HVD API: `https://opendata-api.statbel.fgov.be` (PostgREST JSON)
- **Protocol:** Direct file download (CPI) + PostgREST REST API (all others)
- **Auth:** None (open access, CC BY 4.0)
- **Freshness:** Monthly (CPI, HICP, retail), Annual (unemployment, demographics, inequality)
- **Coverage:** Belgium

**Indicators:**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `CPI_INDEX` | Consumer Price Index (base 2013=100) | Monthly | index |
| `CPI_INFLATION` | CPI Inflation Rate (YoY %) | Monthly | % |
| `CPI_HEALTH_INDEX` | Health Index (base 2013=100) | Monthly | index |
| `CPI_EXCL_ENERGY` | CPI Excluding Energy (base 2013=100) | Monthly | index |
| `HICP_FOOD` | HICP — Food & Non-Alcoholic Beverages (2015=100) | Monthly | index |
| `HICP_HOUSING` | HICP — Housing, Water, Electricity & Gas (2015=100) | Monthly | index |
| `HICP_TRANSPORT` | HICP — Transport (2015=100) | Monthly | index |
| `HICP_RESTAURANTS` | HICP — Restaurants & Hotels (2015=100) | Monthly | index |
| `UNEMPLOYMENT_MALE_YOUTH` | Male Youth Unemployment Rate (15–24) | Annual | ratio |
| `UNEMPLOYMENT_FEMALE_YOUTH` | Female Youth Unemployment Rate (15–24) | Annual | ratio |
| `UNEMPLOYMENT_MALE_PRIME` | Male Prime-Age Unemployment Rate (25–54) | Annual | ratio |
| `UNEMPLOYMENT_FEMALE_PRIME` | Female Prime-Age Unemployment Rate (25–54) | Annual | ratio |
| `RETAIL_TURNOVER` | Retail Trade Turnover Index (2021=100) | Monthly | index |
| `GINI_COEFFICIENT` | Gini Coefficient — Equivalised Disposable Income | Annual | coefficient |
| `BIRTH_RATE` | Crude Birth Rate (per 1,000 population) | Annual | rate |
| `DEATH_RATE` | Crude Death Rate (per 1,000 population) | Annual | rate |

**CLI Examples:**
```bash
python3 modules/statbel_belgium.py CPI_INDEX
python3 modules/statbel_belgium.py CPI_INFLATION
python3 modules/statbel_belgium.py HICP_FOOD
python3 modules/statbel_belgium.py GINI_COEFFICIENT
python3 modules/statbel_belgium.py UNEMPLOYMENT_MALE_YOUTH
python3 modules/statbel_belgium.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'statbel_belgium',
    params: { indicator: 'CPI_INFLATION' }
  })
});
```

---

### statistics_austria.py — Statistics Austria (Konjunkturmonitor)

- **Source:** Statistik Austria — Austrian Federal Statistical Office
- **API:** `https://data.statistik.gv.at` (OGD CSV download, open access, CC BY 4.0)
- **Dataset:** OGD_konjunkturmonitor_KonMon_1 (Konjunkturmonitor / Economic Trend Monitor)
- **Auth:** None (open access)
- **Coverage:** Austria
- **Data freshness:** Monthly/quarterly (updated as releases occur)
- **Cache TTL:** 24 hours

**Available indicators (15):**

| Indicator Key | Name | Frequency | Unit |
|---------------|------|-----------|------|
| `GDP_NOMINAL_Q` | GDP Nominal, Quarterly | Quarterly | EUR mn |
| `GDP_REAL_Q` | GDP Real, Chain-linked Quarterly | Quarterly | EUR mn |
| `GDP_NOMINAL_Y` | GDP Nominal, Annual | Annual | EUR mn |
| `CPI` | Consumer Price Index (Verbraucherpreisindex) | Monthly | index (2015=100) |
| `PRODUCER_PRICE_INDEX` | Industrial Output Price Index (Erzeugerpreisindex) | Monthly | index (2021=100) |
| `WHOLESALE_PRICE_INDEX` | Wholesale Trade Price Index (Großhandelspreisindex) | Monthly | index (2025=100) |
| `EMPLOYED` | Employed Persons | Quarterly | thousands |
| `UNEMPLOYED` | Unemployed Persons | Quarterly | thousands |
| `IMPORTS_TOTAL` | Total Goods Imports | Monthly | EUR |
| `EXPORTS_TOTAL` | Total Goods Exports | Monthly | EUR |
| `OVERNIGHT_STAYS` | Tourism Overnight Stays (Nächtigungen) | Monthly | count |
| `TOURISM_TURNOVER_INDEX` | Accommodation & Food Service Turnover | Quarterly | index (2021=100) |
| `NEW_CAR_REGISTRATIONS` | New Passenger Car Registrations (Pkw-Neuzulassungen) | Monthly | count |
| `INDUSTRIAL_PRODUCTION_INDEX` | Industrial Production Index (Produktionsindex) | Monthly | index (2021=100) |
| `CONSTRUCTION_PRODUCTION_INDEX` | Construction Production Index | Monthly | index (2021=100) |
| `HOUSEHOLD_CONSUMPTION` | Private Household Consumption Expenditure | Quarterly | EUR mn |
| `GROSS_FIXED_CAPITAL_FORMATION` | Gross Fixed Capital Formation (Bruttoanlageinvestitionen) | Quarterly | EUR mn |

**CLI Examples:**
```bash
python3 modules/statistics_austria.py GDP_NOMINAL_Q
python3 modules/statistics_austria.py CPI
python3 modules/statistics_austria.py PRODUCER_PRICE_INDEX
python3 modules/statistics_austria.py EMPLOYED
python3 modules/statistics_austria.py EXPORTS_TOTAL
python3 modules/statistics_austria.py OVERNIGHT_STAYS
python3 modules/statistics_austria.py INDUSTRIAL_PRODUCTION_INDEX
python3 modules/statistics_austria.py CONSTRUCTION_PRODUCTION_INDEX
python3 modules/statistics_austria.py HOUSEHOLD_CONSUMPTION
python3 modules/statistics_austria.py GROSS_FIXED_CAPITAL_FORMATION
python3 modules/statistics_austria.py list
python3 modules/statistics_austria.py catalog
python3 modules/statistics_austria.py              # All indicators at once
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'statistics_austria',
    params: { indicator: 'GDP_NOMINAL_Q' }
  })
});
```

---

### czso_czech.py — CZSO Czech Republic Statistics

- **Source:** Český statistický úřad (Czech Statistical Office)
- **API:** `https://vdb.czso.cz/pll/eweb/lkod_ld.datova_sada`
- **Protocol:** REST / Open Data CSV
- **Auth:** None (open access, CC BY 4.0)
- **Freshness:** Monthly (CPI, IPI, construction, trade), Quarterly (labour), Annual (GDP)
- **Coverage:** Czech Republic

**Indicators (20):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_NOMINAL` | GDP at Current Prices | Annual | CZK mn |
| `GDP_REAL` | GDP at Constant 2020 Prices | Annual | CZK mn |
| `GDP_GROWTH` | GDP Growth YoY | Annual | % |
| `GVA_NOMINAL` | Gross Value Added, Current Prices | Annual | CZK mn |
| `GFCF_NOMINAL` | Gross Fixed Capital Formation | Annual | CZK mn |
| `CPI_YOY` | CPI Year-on-Year (all items) | Monthly | % |
| `CPI_MOM` | CPI Month-on-Month | Monthly | % |
| `CPI_INDEX` | CPI Index (2015=100) | Monthly | index |
| `CPI_FOOD_YOY` | CPI Food & Non-Alcoholic Beverages YoY | Monthly | % |
| `CPI_HOUSING_YOY` | CPI Housing, Water, Energy YoY | Monthly | % |
| `CPI_TRANSPORT_YOY` | CPI Transport YoY | Monthly | % |
| `UNEMPLOYMENT_RATE` | General Unemployment Rate | Quarterly | % |
| `EMPLOYMENT_RATE` | Employment Rate | Quarterly | % |
| `EMPLOYED` | Employed Persons | Quarterly | thousands |
| `UNEMPLOYED` | Unemployed Persons | Quarterly | thousands |
| `IPI_TOTAL` | Industrial Production Index — Total YoY | Monthly | % YoY |
| `IPI_AUTO` | Motor Vehicles Production Index YoY | Monthly | % YoY |
| `CONSTRUCTION_INDEX` | Construction Output Index YoY | Monthly | % YoY |
| `TRADE_EXPORTS` | Total Goods Exports | Monthly | CZK mn |
| `TRADE_IMPORTS` | Total Goods Imports | Monthly | CZK mn |
| `TRADE_BALANCE` | Trade Balance — Goods | Monthly | CZK mn |

**CLI Examples:**
```bash
python3 modules/czso_czech.py GDP_NOMINAL
python3 modules/czso_czech.py CPI_YOY
python3 modules/czso_czech.py UNEMPLOYMENT_RATE
python3 modules/czso_czech.py IPI_TOTAL
python3 modules/czso_czech.py TRADE_BALANCE
python3 modules/czso_czech.py list
python3 modules/czso_czech.py catalog
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'czso_czech',
    params: { indicator: 'CPI_YOY' }
  })
});
```

---

### statistics_estonia.py — Statistics Estonia (PxWeb)

- **Source:** Statistics Estonia (Statistikaamet)
- **API:** `https://andmed.stat.ee/api/v1/en/stat`
- **Protocol:** PxWeb REST API (POST with JSON query)
- **Auth:** None (open access)
- **Freshness:** Monthly (CPI, industrial production), Quarterly (GDP, labour, trade), Annual (CPI/HICP)
- **Coverage:** Estonia

**Indicators (13):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_NOMINAL` | GDP at Current Prices (EUR mn, quarterly) | Quarterly | EUR mn |
| `GDP_REAL_GROWTH` | Real GDP Growth YoY (%) | Quarterly | % |
| `CPI_ANNUAL` | CPI Inflation YoY (%, annual) | Annual | % |
| `CPI_MONTHLY` | CPI Inflation YoY (%, monthly) | Monthly | % |
| `HICP_ANNUAL` | HICP Inflation YoY (%, annual) | Annual | % |
| `EMPLOYMENT_RATE` | Employment Rate (%, ages 15-74) | Quarterly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate (%, ages 15-74) | Quarterly | % |
| `LABOUR_FORCE` | Labour Force (thousands, ages 15-74) | Quarterly | thousands |
| `EXPORTS` | Exports of Goods & Services (EUR mn) | Quarterly | EUR mn |
| `IMPORTS` | Imports of Goods & Services (EUR mn) | Quarterly | EUR mn |
| `INDUSTRIAL_PRODUCTION_INDEX` | Industrial Production Index (2021=100, SA) | Monthly | index |
| `INDUSTRIAL_PRODUCTION_YOY` | Industrial Production YoY Change (%) | Monthly | % |

**CLI Examples:**
```bash
python3 modules/statistics_estonia.py GDP_REAL_GROWTH
python3 modules/statistics_estonia.py CPI_MONTHLY
python3 modules/statistics_estonia.py UNEMPLOYMENT_RATE
python3 modules/statistics_estonia.py EXPORTS
python3 modules/statistics_estonia.py INDUSTRIAL_PRODUCTION_INDEX
python3 modules/statistics_estonia.py trade-balance
python3 modules/statistics_estonia.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'statistics_estonia',
    params: { indicator: 'GDP_REAL_GROWTH' }
  })
});
```

---

### ecb_enhanced.py — ECB Enhanced (Monetary, Credit, Inflation)

- **Source:** European Central Bank
- **API:** `https://data-api.ecb.europa.eu/service`
- **Protocol:** SDMX 2.1 REST (SDMX-JSON 1.0)
- **Auth:** None (public access)
- **Freshness:** Monthly (all indicators)
- **Coverage:** Euro Area (EA20)
- **Dataflows:** BSI (monetary/credit), MIR (interest rates), ICP (inflation)

**Indicators (14):**

| Key | Name | Frequency | Unit | Dataflow |
|-----|------|-----------|------|----------|
| `M1_OUTSTANDING` | M1 Monetary Aggregate — Euro Area | Monthly | EUR mn | BSI |
| `M2_OUTSTANDING` | M2 Monetary Aggregate — Euro Area | Monthly | EUR mn | BSI |
| `M3_OUTSTANDING` | M3 Monetary Aggregate — Euro Area | Monthly | EUR mn | BSI |
| `LOANS_HH` | MFI Loans to Households — Euro Area | Monthly | EUR mn | BSI |
| `LOANS_NFC` | MFI Loans to Non-Financial Corporations | Monthly | EUR mn | BSI |
| `LOANS_HH_HOUSING` | MFI Housing Loans to Households | Monthly | EUR mn | BSI |
| `CCOB_NFC` | Composite Cost of Borrowing — NFCs | Monthly | % p.a. | MIR |
| `CCOB_HH_HOUSING` | Composite Cost of Borrowing — HH Housing | Monthly | % p.a. | MIR |
| `NFC_LOAN_RATE_SHORT` | NFC New Loan Rate — Up to 1yr | Monthly | % p.a. | MIR |
| `NFC_LOAN_RATE_LONG` | NFC New Loan Rate — Over 5yr | Monthly | % p.a. | MIR |
| `HH_DEPOSIT_RATE` | Household Deposit Rate — New Business | Monthly | % p.a. | MIR |
| `HICP_HEADLINE` | HICP — All Items Annual Rate | Monthly | % | ICP |
| `HICP_CORE` | HICP Core — Excl. Energy & Food | Monthly | % | ICP |
| `HICP_FOOD` | HICP Food & Non-Alcoholic Beverages | Monthly | % | ICP |

**CLI Examples:**
```bash
python3 modules/ecb_enhanced.py M3_OUTSTANDING
python3 modules/ecb_enhanced.py LOANS_HH
python3 modules/ecb_enhanced.py HICP_HEADLINE
python3 modules/ecb_enhanced.py CCOB_NFC
python3 modules/ecb_enhanced.py monetary              # M1/M2/M3 aggregates
python3 modules/ecb_enhanced.py borrowing             # Composite cost of borrowing
python3 modules/ecb_enhanced.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'ecb_enhanced',
    params: { indicator: 'HICP_HEADLINE' }
  })
});
```

---

### eurostat_enhanced.py — Eurostat (EU Gov Finance, Energy & Environment)

- **Source:** Eurostat (European Commission)
- **API:** `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data`
- **Protocol:** REST (JSON-stat 2.0)
- **Auth:** None (open access, ~100 req/hour)
- **Freshness:** Annual (most datasets updated Q1-Q2 for prior year)
- **Coverage:** EU27 + all Member States (per-country and cross-country comparison)

**Indicators (21):**

| Key | Name | Frequency | Unit | Category |
|-----|------|-----------|------|----------|
| `GOV_DEFICIT_SURPLUS` | Government Deficit/Surplus (% GDP) | Annual | % GDP | Gov Finance |
| `GOV_DEBT` | Government Debt (% GDP) | Annual | % GDP | Gov Finance |
| `GOV_EXPENDITURE` | Government Expenditure (% GDP) | Annual | % GDP | Gov Finance |
| `GOV_REVENUE` | Government Revenue (% GDP) | Annual | % GDP | Gov Finance |
| `ENERGY_PRODUCTION` | Total Energy Production | Annual | KTOE | Energy |
| `ENERGY_CONSUMPTION` | Available Final Energy Consumption | Annual | KTOE | Energy |
| `ENERGY_DEPENDENCY` | Energy Import Dependency | Annual | % | Energy |
| `RENEWABLE_SHARE_TOTAL` | Renewable Energy Share — Overall | Annual | % | Renewables |
| `RENEWABLE_SHARE_ELECTRICITY` | Renewable Energy Share — Electricity | Annual | % | Renewables |
| `RENEWABLE_SHARE_TRANSPORT` | Renewable Energy Share — Transport | Annual | % | Renewables |
| `RENEWABLE_SHARE_HEATING` | Renewable Energy Share — Heating/Cooling | Annual | % | Renewables |
| `GHG_TOTAL` | Total GHG Emissions (Mt CO₂eq) | Annual | Mt CO₂eq | Emissions |
| `GHG_ENERGY` | GHG Emissions — Energy Sector | Annual | Mt CO₂eq | Emissions |
| `GHG_INDUSTRY` | GHG Emissions — Manufacturing/Construction | Annual | Mt CO₂eq | Emissions |
| `GHG_TRANSPORT` | GHG Emissions — Transport | Annual | Mt CO₂eq | Emissions |
| `GHG_AGRICULTURE` | GHG Emissions — Agriculture | Annual | Mt CO₂eq | Emissions |
| `ENV_TAX_TOTAL` | Total Environmental Taxes (% GDP) | Annual | % GDP | Env Taxes |
| `ENV_TAX_ENERGY` | Energy Taxes (% GDP) | Annual | % GDP | Env Taxes |
| `ENV_TAX_TRANSPORT` | Transport Taxes (% GDP) | Annual | % GDP | Env Taxes |
| `DIGITAL_INTERNET_ACCESS` | Household Internet Access | Annual | % HH | Digital |
| `DIGITAL_INTERNET_USE` | Internet Use by Individuals | Annual | % ind. | Digital |
| `DIGITAL_ECOMMERCE` | E-Commerce by Individuals | Annual | % ind. | Digital |

**CLI Examples:**
```bash
python3 modules/eurostat_enhanced.py GOV_DEBT DE        # Germany govt debt % GDP
python3 modules/eurostat_enhanced.py GOV_DEBT FR        # France govt debt
python3 modules/eurostat_enhanced.py RENEWABLE_SHARE_TOTAL SE   # Sweden renewables
python3 modules/eurostat_enhanced.py GHG_TOTAL DE       # Germany total GHG
python3 modules/eurostat_enhanced.py compare GOV_DEBT   # Compare across all EU27
python3 modules/eurostat_enhanced.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'eurostat_enhanced',
    params: { indicator: 'GOV_DEBT', geo: 'DE' }
  })
});
```

---

### bis_enhanced.py — BIS (Derivatives, FX Turnover, Debt, Payments)

- **Source:** Bank for International Settlements
- **API:** `https://stats.bis.org/api/v2`
- **Protocol:** BIS SDMX REST API v2 (CSV output)
- **Auth:** None (open access)
- **Freshness:** Semiannual (OTC derivatives), Quarterly (exchange-traded, debt), Triennial (FX turnover), Annual (CPMI)
- **Coverage:** Global / 60+ countries
- **Dataflows:** WS_OTC_DERIV2, WS_XTD_DERIV, WS_DER_OTC_TOV, WS_NA_SEC_DSS, WS_CPMI_CASHLESS, WS_CPMI_MACRO

**Indicators (22):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `OTC_NOTIONAL_TOTAL` | OTC Derivatives — Total Notional Outstanding | Semiannual | USD bn |
| `OTC_NOTIONAL_SWAPS` | OTC Derivatives — Swaps Notional | Semiannual | USD bn |
| `OTC_GMV_TOTAL` | OTC Derivatives — Gross Market Value | Semiannual | USD bn |
| `OTC_NOTIONAL_NFC` | OTC Derivatives — Non-Financial Counterparties | Semiannual | USD bn |
| `XTD_OI_FX` | Exchange-Traded — FX Open Interest | Quarterly | USD mn |
| `XTD_OI_IR` | Exchange-Traded — Interest Rate Open Interest | Quarterly | USD mn |
| `XTD_OI_EQUITY` | Exchange-Traded — Equity Open Interest | Quarterly | USD mn |
| `XTD_OI_COMMODITY` | Exchange-Traded — Commodity Open Interest | Quarterly | USD mn |
| `XTD_TURNOVER_FX` | Exchange-Traded — FX Turnover | Quarterly | USD mn |
| `FX_TURNOVER_TOTAL` | FX Turnover — Daily Average Total | Triennial | USD mn |
| `IR_DERIV_TURNOVER` | OTC IR Derivatives — Daily Average Turnover | Triennial | USD mn |
| `FX_TURNOVER_SPOT` | FX Spot Turnover — Daily Average | Triennial | USD mn |
| `DEBT_SEC_US` | Debt Securities Outstanding — United States | Quarterly | USD bn |
| `DEBT_SEC_GB` | Debt Securities Outstanding — United Kingdom | Quarterly | USD bn |
| `DEBT_SEC_JP` | Debt Securities Outstanding — Japan | Quarterly | USD bn |
| `DEBT_SEC_CN` | Debt Securities Outstanding — China | Quarterly | USD bn |
| `DEBT_SEC_DE` | Debt Securities Outstanding — Germany | Quarterly | USD bn |
| `CPMI_CASHLESS_US_VALUE` | CPMI Cashless Payments — US Total Value | Annual | USD mn |
| `CPMI_CASHLESS_GB_VALUE` | CPMI Cashless Payments — UK Total Value | Annual | GBP mn |
| `CPMI_CASHLESS_CN_VALUE` | CPMI Cashless Payments — China Total Value | Annual | CNY mn |
| `CPMI_MACRO_US_POP` | CPMI Macro — US Population | Annual | thousands |
| `CPMI_MACRO_US_BANKNOTES` | CPMI Macro — US Banknotes & Coins | Annual | USD |

**CLI Examples:**
```bash
python3 modules/bis_enhanced.py OTC_NOTIONAL_TOTAL     # Total OTC notional outstanding
python3 modules/bis_enhanced.py XTD_OI_IR              # Interest rate open interest
python3 modules/bis_enhanced.py DEBT_SEC_US             # US debt securities
python3 modules/bis_enhanced.py FX_TURNOVER_TOTAL       # BIS triennial FX turnover
python3 modules/bis_enhanced.py derivatives             # Derivatives market dashboard
python3 modules/bis_enhanced.py debt-securities         # Debt securities comparison
python3 modules/bis_enhanced.py datasets                # Show covered BIS datasets
python3 modules/bis_enhanced.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'bis_enhanced',
    params: { indicator: 'OTC_NOTIONAL_TOTAL' }
  })
});
```

---

### imf_enhanced.py — IMF Enhanced (FAS + FSI + CPIS + CDIS + GFS)

- **Source:** International Monetary Fund (5 databases via DBnomics mirror)
- **API:** `https://api.db.nomics.world/v22`
- **Protocol:** DBnomics REST JSON (mirrors IMF FAS, FSI, CPIS, CDIS, GFSMAB)
- **Auth:** None (open access, rate-limited)
- **Freshness:** Annual (FAS, CPIS, CDIS, GFS), Quarterly (FSI)
- **Coverage:** Global / 190+ countries (ISO2 country codes)
- **Default Country:** US

**Indicators (29):**

| Key | Name | Database | Frequency | Unit |
|-----|------|----------|-----------|------|
| `FAS_ATMS_PER_100K` | ATMs per 100,000 Adults | FAS | Annual | per 100k adults |
| `FAS_BRANCHES_PER_100K` | Commercial Bank Branches per 100,000 Adults | FAS | Annual | per 100k adults |
| `FAS_ATMS_PER_1000KM2` | ATMs per 1,000 km² | FAS | Annual | per 1000 km² |
| `FAS_BRANCHES_PER_1000KM2` | Bank Branches per 1,000 km² | FAS | Annual | per 1000 km² |
| `FAS_DEPOSIT_ACCTS_PER_1000` | Deposit Accounts per 1,000 Adults | FAS | Annual | per 1000 adults |
| `FAS_MOBILE_MONEY_ACTIVE` | Active Mobile Money Accounts per 1,000 Adults | FAS | Annual | per 1000 adults |
| `FAS_MOBILE_MONEY_REGISTERED` | Registered Mobile Money Accounts per 1,000 Adults | FAS | Annual | per 1000 adults |
| `FSI_NPL_RATIO` | Non-performing Loans to Total Gross Loans | FSI | Annual | % |
| `FSI_REGULATORY_CAPITAL` | Regulatory Capital to Risk-Weighted Assets | FSI | Annual | % |
| `FSI_CET1_RATIO` | Common Equity Tier 1 to Risk-Weighted Assets | FSI | Annual | % |
| `FSI_ROA` | Return on Assets (Deposit Takers) | FSI | Annual | % |
| `FSI_ROE` | Return on Equity (Deposit Takers) | FSI | Annual | % |
| `CPIS_TOTAL_ASSETS` | Total Portfolio Investment Assets (World) | CPIS | Annual | USD |
| `CPIS_EQUITY_ASSETS` | Portfolio Equity Assets (World) | CPIS | Annual | USD |
| `CPIS_DEBT_LT_ASSETS` | Portfolio Long-term Debt Assets (World) | CPIS | Annual | USD |
| `CDIS_INWARD_EQUITY` | Inward FDI Equity Positions (World) | CDIS | Annual | USD mn |
| `CDIS_INWARD_DEBT_ASSETS` | Inward FDI Debt Assets (World) | CDIS | Annual | USD mn |
| `CDIS_INWARD_DEBT_LIAB` | Inward FDI Debt Liabilities (World) | CDIS | Annual | USD mn |
| `CDIS_OUTWARD_EQUITY` | Outward FDI Equity Positions (World) | CDIS | Annual | USD mn |
| `CDIS_OUTWARD_DEBT_ASSETS` | Outward FDI Debt Assets (World) | CDIS | Annual | USD mn |
| `CDIS_OUTWARD_DEBT_LIAB` | Outward FDI Debt Liabilities (World) | CDIS | Annual | USD mn |
| `GFS_REVENUE` | General Government Revenue | GFSMAB | Annual | domestic currency bn |
| `GFS_EXPENSE` | General Government Expense | GFSMAB | Annual | domestic currency bn |
| `GFS_TAX_REVENUE` | Tax Revenue | GFSMAB | Annual | domestic currency bn |
| `GFS_EXPENDITURE` | Total Government Expenditure | GFSMAB | Annual | domestic currency bn |
| `GFS_SOCIAL_BENEFITS` | Social Benefits Expense | GFSMAB | Annual | domestic currency bn |
| `GFS_INTEREST_EXPENSE` | Interest Expense | GFSMAB | Annual | domestic currency bn |
| `GFS_NET_INVESTMENT` | Net Investment in Nonfinancial Assets | GFSMAB | Annual | domestic currency bn |
| `GFS_NET_LIABILITIES` | Net Incurrence of Liabilities | GFSMAB | Annual | domestic currency bn |

**CLI Examples:**
```bash
python3 modules/imf_enhanced.py FSI_NPL_RATIO US        # US bank NPL ratio
python3 modules/imf_enhanced.py FSI_CET1_RATIO DE       # German bank CET1
python3 modules/imf_enhanced.py FAS_ATMS_PER_100K IN    # India ATM density
python3 modules/imf_enhanced.py FAS_MOBILE_MONEY_ACTIVE KE  # Kenya mobile money
python3 modules/imf_enhanced.py CPIS_TOTAL_ASSETS US    # US portfolio investment
python3 modules/imf_enhanced.py CDIS_INWARD_EQUITY CN   # China inward FDI
python3 modules/imf_enhanced.py GFS_REVENUE JP          # Japan govt revenue
python3 modules/imf_enhanced.py GFS_SOCIAL_BENEFITS FR  # France social spending
python3 modules/imf_enhanced.py fsi US                  # Full FSI dashboard
python3 modules/imf_enhanced.py fas BR                  # Brazil financial access
python3 modules/imf_enhanced.py gfs DE                  # Germany govt finance
python3 modules/imf_enhanced.py banking-health CN       # China banking health
python3 modules/imf_enhanced.py access NG               # Nigeria financial inclusion
python3 modules/imf_enhanced.py list                    # All available indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'imf_enhanced',
    params: { indicator: 'FSI_NPL_RATIO', country: 'US' }
  })
});
```

---

### oecd_enhanced.py — OECD Enhanced (CLI, KEI, REV, PAG, MSTI)

- **Source:** Organisation for Economic Co-operation and Development
- **API:** `https://sdmx.oecd.org/public/rest/data`
- **Protocol:** SDMX 3.0 REST (CSV/JSON)
- **Auth:** None (open access, ~60 req/hr)
- **Freshness:** Monthly (CLI, KEI), Annual (REV, PAG, MSTI)
- **Coverage:** 38 OECD members + key partner economies

**Indicators (30):**

| Key | Name | Dataflow | Frequency | Unit |
|-----|------|----------|-----------|------|
| `CLI_USA` | Composite Leading Indicator — USA | CLI | Monthly | index (100=trend) |
| `CLI_GBR` | Composite Leading Indicator — UK | CLI | Monthly | index |
| `CLI_DEU` | Composite Leading Indicator — Germany | CLI | Monthly | index |
| `CLI_JPN` | Composite Leading Indicator — Japan | CLI | Monthly | index |
| `CLI_FRA` | Composite Leading Indicator — France | CLI | Monthly | index |
| `CLI_OECD` | Composite Leading Indicator — OECD Total | CLI | Monthly | index |
| `BCI_USA` | Business Confidence Index — USA | KEI | Monthly | index (100=neutral) |
| `CCI_USA` | Consumer Confidence Index — USA | KEI | Monthly | index (100=neutral) |
| `KEI_UNEMP_USA` | Harmonised Unemployment Rate — USA | KEI | Monthly | % |
| `KEI_CPI_YOY_USA` | CPI Year-on-Year — USA | KEI | Monthly | % |
| `KEI_GDP_USA` | GDP Volume at Market Prices — USA | KEI | Quarterly | index |
| `KEI_STIR_USA` | Short-term Interest Rate — USA | KEI | Monthly | % p.a. |
| `KEI_LTIR_USA` | Long-term Interest Rate — USA | KEI | Monthly | % p.a. |
| `TAX_TOTAL_USA` | Total Tax Revenue — USA | REV | Annual | % GDP |
| `TAX_INCOME_USA` | Income Tax Revenue — USA | REV | Annual | % GDP |
| `TAX_CORP_USA` | Corporate Tax Revenue — USA | REV | Annual | % GDP |
| `TAX_SSC_USA` | Social Security Contributions — USA | REV | Annual | % GDP |
| `TAX_GOODS_USA` | Taxes on Goods & Services — USA | REV | Annual | % GDP |
| `TAX_TOTAL_GBR` | Total Tax Revenue — UK | REV | Annual | % GDP |
| `TAX_TOTAL_DEU` | Total Tax Revenue — Germany | REV | Annual | % GDP |
| `PENSION_GRR_USA` | Gross Replacement Rate — USA | PAG | Annual | % |
| `PENSION_GRR_GBR` | Gross Replacement Rate — UK | PAG | Annual | % |
| `PENSION_GRR_DEU` | Gross Replacement Rate — Germany | PAG | Annual | % |
| `PENSION_LE_USA` | Life Expectancy at 65 — USA | PAG | Annual | years |
| `PENSION_EMPRATE_USA` | Employment Rate 55-64 — USA | PAG | Annual | % |
| `RD_GERD_USA` | GERD as % GDP — USA | MSTI | Annual | % GDP |
| `RD_BERD_USA` | BERD as % GDP — USA | MSTI | Annual | % GDP |
| `RD_HERD_USA` | HERD as % GDP — USA | MSTI | Annual | % GDP |
| `RD_GERD_DEU` | GERD as % GDP — Germany | MSTI | Annual | % GDP |
| `RD_GERD_JPN` | GERD as % GDP — Japan | MSTI | Annual | % GDP |

**CLI Examples:**
```bash
python3 modules/oecd_enhanced.py CLI_USA              # US leading indicator
python3 modules/oecd_enhanced.py CLI_OECD             # OECD total CLI
python3 modules/oecd_enhanced.py BCI_USA              # US business confidence
python3 modules/oecd_enhanced.py TAX_TOTAL_USA        # US tax revenue % GDP
python3 modules/oecd_enhanced.py PENSION_GRR_GBR      # UK pension replacement rate
python3 modules/oecd_enhanced.py RD_GERD_JPN          # Japan R&D spending
python3 modules/oecd_enhanced.py list                 # All available indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'oecd_enhanced',
    params: { indicator: 'CLI_USA' }
  })
});
```

---

### boe_iadb_enhanced.py — Bank of England (IADB)

- **Source:** Bank of England — Interactive Analytical Database
- **API:** `https://www.bankofengland.co.uk/boeapps/iadb/FromShowColumns.asp`
- **Protocol:** XML (custom BoE namespace)
- **Auth:** None (open access)
- **Freshness:** Daily (yields, FX, EER), Monthly (Bank Rate, M4, mortgage, credit)
- **Coverage:** United Kingdom

**Indicators (22):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `GILT_NZC_5Y` | Gilt Zero-Coupon Yield 5Y | yield_curve | Daily | % |
| `GILT_NZC_10Y` | Gilt Zero-Coupon Yield 10Y | yield_curve | Daily | % |
| `GILT_NZC_20Y` | Gilt Zero-Coupon Yield 20Y | yield_curve | Daily | % |
| `GILT_NZC_5Y_MAVG` | Gilt ZC 5Y (3M Moving Avg) | yield_curve | Daily | % |
| `GILT_NZC_10Y_MAVG` | Gilt ZC 10Y (3M Moving Avg) | yield_curve | Daily | % |
| `GILT_NZC_20Y_MAVG` | Gilt ZC 20Y (3M Moving Avg) | yield_curve | Daily | % |
| `BANK_RATE` | Bank of England Official Bank Rate | policy_rate | Monthly | % |
| `M4_OUTSTANDING` | M4 Outstanding (SA) | money_supply | Monthly | GBP mn |
| `M4_LENDING_OUTSTANDING` | M4 Lending Outstanding | money_supply | Monthly | GBP mn |
| `M4_LENDING_12M_GROWTH` | M4 Lending 12-Month Growth | money_supply | Monthly | % |
| `M4_LENDING_1M_GROWTH` | M4 Lending 1-Month Growth | money_supply | Monthly | % |
| `M4_LENDING_3M_GROWTH` | M4 Lending 3-Month Growth (Ann.) | money_supply | Monthly | % |
| `MORTGAGE_SVR` | Mortgage Standard Variable Rate | mortgage | Monthly | % |
| `CONSUMER_CREDIT_EXCL_CARD` | Consumer Credit Excl. Cards (Net Flow) | consumer_credit | Monthly | GBP mn |
| `CONSUMER_CREDIT_TOTAL_EXCL_CARD` | Consumer Credit Excl. Cards (Outstanding) | consumer_credit | Monthly | GBP mn |
| `CONSUMER_CREDIT_EXCL_CARD_1M_GROWTH` | Consumer Credit 1M Growth | consumer_credit | Monthly | % |
| `GBP_USD` | GBP/USD Spot Rate | fx_rates | Daily | USD |
| `GBP_EUR` | GBP/EUR Spot Rate | fx_rates | Daily | EUR |
| `GBP_JPY` | GBP/JPY Spot Rate | fx_rates | Daily | JPY |
| `GBP_CHF` | GBP/CHF Spot Rate | fx_rates | Daily | CHF |
| `STERLING_EER` | Sterling Effective Exchange Rate (Narrow) | eer | Daily | index |
| `STERLING_BROAD_EER` | Sterling Effective Exchange Rate (Broad) | eer | Daily | index |

**CLI Examples:**
```bash
python3 modules/boe_iadb_enhanced.py BANK_RATE               # BoE Bank Rate
python3 modules/boe_iadb_enhanced.py GILT_NZC_10Y            # 10Y gilt ZC yield
python3 modules/boe_iadb_enhanced.py M4_OUTSTANDING           # M4 money supply
python3 modules/boe_iadb_enhanced.py GBP_USD                  # GBP/USD FX
python3 modules/boe_iadb_enhanced.py STERLING_EER             # Sterling EER index
python3 modules/boe_iadb_enhanced.py MORTGAGE_SVR             # Mortgage SVR rate
python3 modules/boe_iadb_enhanced.py CONSUMER_CREDIT_EXCL_CARD  # Consumer credit
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'boe_iadb_enhanced',
    params: { indicator: 'BANK_RATE' }
  })
});
```

---

### mnb_hungary.py — Magyar Nemzeti Bank (MNB)

- **Source:** Magyar Nemzeti Bank (Hungarian Central Bank)
- **API:** `http://www.mnb.hu/arfolyamok.asmx` (FX), `http://www.mnb.hu/alapkamat.asmx` (base rate)
- **Protocol:** SOAP/XML web services
- **Auth:** None (open access)
- **Freshness:** Daily (FX, base rate)
- **Coverage:** Hungary

**Indicators (16):**

| Key | Name | Source | Frequency | Unit |
|-----|------|--------|-----------|------|
| `MNB_BASE_RATE` | MNB Base Rate (Policy Rate) | base_rate | Monthly | % |
| `FX_EUR_HUF` | EUR/HUF Exchange Rate | fx | Daily | HUF |
| `FX_USD_HUF` | USD/HUF Exchange Rate | fx | Daily | HUF |
| `FX_GBP_HUF` | GBP/HUF Exchange Rate | fx | Daily | HUF |
| `FX_CHF_HUF` | CHF/HUF Exchange Rate | fx | Daily | HUF |
| `FX_JPY_HUF` | JPY/HUF Exchange Rate | fx | Daily | HUF |
| `FX_CZK_HUF` | CZK/HUF Exchange Rate | fx | Daily | HUF |
| `FX_PLN_HUF` | PLN/HUF Exchange Rate | fx | Daily | HUF |
| `FX_RON_HUF` | RON/HUF Exchange Rate | fx | Daily | HUF |
| `FX_SEK_HUF` | SEK/HUF Exchange Rate | fx | Daily | HUF |
| `FX_CNY_HUF` | CNY/HUF Exchange Rate | fx | Daily | HUF |
| `FX_TRY_HUF` | TRY/HUF Exchange Rate | fx | Daily | HUF |
| `FX_CAD_HUF` | CAD/HUF Exchange Rate | fx | Daily | HUF |
| `FX_CEE_BASKET` | CEE Equal-Weight Basket vs HUF | aggregate | Daily | index |
| `FX_G4_BASKET` | G4 Equal-Weight Basket vs HUF | aggregate | Daily | index |

**CLI Examples:**
```bash
python3 modules/mnb_hungary.py MNB_BASE_RATE        # MNB policy rate
python3 modules/mnb_hungary.py FX_EUR_HUF           # EUR/HUF rate
python3 modules/mnb_hungary.py FX_USD_HUF           # USD/HUF rate
python3 modules/mnb_hungary.py FX_CEE_BASKET        # CEE currency basket
python3 modules/mnb_hungary.py FX_G4_BASKET         # G4 basket vs HUF
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'mnb_hungary',
    params: { indicator: 'MNB_BASE_RATE' }
  })
});
```

---

### eu_small_central_banks.py — 9 Smaller EU Central Banks (Unified)

- **Source:** ECB SDMX + BNB (Bulgaria) + HNB (Croatia) + Lietuvos bankas (Lithuania) + NBS (Slovakia) + BSI (Slovenia)
- **APIs:** ECB: `https://data-api.ecb.europa.eu/service/data`; HNB: `https://api.hnb.hr/tecajn-eur/v3`; BSI: `https://api.bsi.si`; BNB: `https://www.bnb.bg`; LB: `https://www.lb.lt/webservices`; NBS: `https://nbs.sk/export`
- **Protocol:** Mixed (SDMX-JSON, XML, JSON, CSV)
- **Auth:** None (all open access)
- **Freshness:** Monthly (HICP, MFI rates via ECB), Daily (FX from national feeds)
- **Coverage:** Bulgaria, Croatia, Cyprus, Latvia, Lithuania, Luxembourg, Malta, Slovakia, Slovenia

**Indicators (47):** For each country code {CC} in [BG, HR, CY, LV, LT, LU, MT, SK, SI]:

| Pattern | Name | Source | Frequency |
|---------|------|--------|-----------|
| `{CC}_HICP` | HICP Annual Rate — {country} | ECB SDMX | Monthly |
| `{CC}_LENDING_RATE_HH` | MFI Lending Rate Households — {country} | ECB SDMX | Monthly |
| `{CC}_DEPOSIT_RATE_HH` | MFI Deposit Rate Households — {country} | ECB SDMX | Monthly |

For countries with national FX feeds [BG, HR, LT, SK, SI]:

| Pattern | Name | Source | Frequency |
|---------|------|--------|-----------|
| `{CC}_FX_USD` | {country} EUR/USD Rate | National CB | Daily |
| `{CC}_FX_GBP` | {country} EUR/GBP Rate | National CB | Daily |
| `{CC}_FX_CHF` | {country} EUR/CHF Rate | National CB | Daily |

Slovenia extras (5):

| Key | Name | Source | Frequency |
|-----|------|--------|-----------|
| `SI_INFLATION_DOMESTIC` | Slovenia Domestic Inflation | BSI | Monthly |
| `SI_INFLATION_EU` | Slovenia EU-Harmonised Inflation | BSI | Monthly |
| `SI_ECB_DEPOSIT_RATE` | ECB Deposit Facility Rate | BSI | Monthly |
| `SI_ECB_REFI_RATE` | ECB Main Refinancing Rate | BSI | Monthly |
| `SI_ECB_MARGINAL_RATE` | ECB Marginal Lending Rate | BSI | Monthly |

**CLI Examples:**
```bash
python3 modules/eu_small_central_banks.py BG_HICP              # Bulgaria HICP
python3 modules/eu_small_central_banks.py HR_FX_USD             # Croatia EUR/USD
python3 modules/eu_small_central_banks.py SI_INFLATION_DOMESTIC  # Slovenia domestic CPI
python3 modules/eu_small_central_banks.py SK_LENDING_RATE_HH    # Slovakia lending rate
python3 modules/eu_small_central_banks.py list                  # All 47 indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'eu_small_central_banks',
    params: { indicator: 'BG_HICP' }
  })
});
```

---

### eu_small_statistics.py — Eurostat Batch (12 Smaller EU NSOs)

- **Source:** Eurostat (JSON-stat 2.0) — batch queries for smaller EU members
- **API:** `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data`
- **Protocol:** Eurostat REST API (JSON-stat 2.0)
- **Auth:** None (open access, ~100 req/hr)
- **Freshness:** Quarterly (GDP, labour), Monthly (CPI), Annual (govt finance, trade)
- **Coverage:** Bulgaria (BG), Croatia (HR), Cyprus (CY), Greece (EL), Hungary (HU), Latvia (LV), Lithuania (LT), Luxembourg (LU), Malta (MT), Romania (RO), Slovakia (SK), Slovenia (SI)

**Indicators (15 per country × 12 countries = 180 combinations):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `GDP_NOMINAL` | Nominal GDP | GDP & National Accounts | Quarterly | EUR mn |
| `GDP_REAL` | Real GDP (chain-linked volumes) | GDP & National Accounts | Quarterly | EUR mn |
| `GDP_GROWTH` | Real GDP Growth Rate | GDP & National Accounts | Quarterly | % |
| `GDP_PER_CAPITA` | GDP per Capita in PPS | GDP & National Accounts | Annual | PPS |
| `CPI_YOY` | CPI Year-on-Year Change | Consumer Prices | Monthly | % |
| `CPI_FOOD_YOY` | CPI Food & Beverages YoY | Consumer Prices | Monthly | % |
| `CPI_ENERGY_YOY` | CPI Energy YoY | Consumer Prices | Monthly | % |
| `CPI_INDEX` | CPI Index Level (2015=100) | Consumer Prices | Monthly | index |
| `UNEMPLOYMENT_RATE` | ILO Unemployment Rate | Labour Market | Quarterly | % |
| `YOUTH_UNEMPLOYMENT` | Youth Unemployment Rate (<25) | Labour Market | Quarterly | % |
| `EMPLOYMENT_RATE` | Employment Rate (20-64) | Labour Market | Quarterly | % |
| `GOV_DEBT` | General Government Gross Debt (% GDP) | Government Finance | Annual | % GDP |
| `GOV_DEFICIT` | Government Deficit/Surplus (% GDP) | Government Finance | Annual | % GDP |
| `GVA_MANUFACTURING` | GVA in Manufacturing | Industry | Annual | EUR mn |
| `CURRENT_ACCOUNT` | Current Account Balance (% GDP) | External Balance | Annual | % GDP |

**CLI Examples:**
```bash
python3 modules/eu_small_statistics.py GDP_GROWTH BG          # Bulgaria GDP growth
python3 modules/eu_small_statistics.py CPI_YOY HU             # Hungary CPI
python3 modules/eu_small_statistics.py UNEMPLOYMENT_RATE EL    # Greece unemployment
python3 modules/eu_small_statistics.py GOV_DEBT HR             # Croatia govt debt
python3 modules/eu_small_statistics.py CURRENT_ACCOUNT LT      # Lithuania current account
python3 modules/eu_small_statistics.py list                    # All available indicators
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'eu_small_statistics',
    params: { indicator: 'GDP_GROWTH', geo: 'HU' }
  })
});
```

### ine_portugal.py — INE Portugal (Instituto Nacional de Estatística)

- **Source:** INE — Portugal's national statistics institute
- **API:** `https://www.ine.pt/ine/json_indicador/pindica.jsp`
- **Protocol:** REST JSON (indicator variable codes, dimension filtering)
- **Auth:** None (open access)
- **Freshness:** Monthly (CPI, tourism, construction), Quarterly (GDP, labour), Annual (trade)
- **Coverage:** Portugal

**Indicators (15):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `GDP_GROWTH_YOY` | GDP Real Growth YoY | National Accounts | Quarterly | % |
| `GDP_NOMINAL` | GDP Nominal (EUR) | National Accounts | Quarterly | EUR |
| `GDP_PERCAPITA_GROWTH` | GDP Real Per Capita Growth | National Accounts | Annual | % |
| `CPI_YOY` | CPI Year-on-Year | Prices | Monthly | % |
| `CPI_INDEX` | CPI Index (Base 2025=100) | Prices | Monthly | index |
| `HICP_YOY` | HICP Year-on-Year | Prices | Monthly | % |
| `UNEMPLOYMENT_RATE` | Unemployment Rate | Labour Market | Quarterly | % |
| `EMPLOYED_POPULATION` | Employed Population | Labour Market | Quarterly | thousands |
| `ACTIVITY_RATE` | Activity Rate (working-age) | Labour Market | Quarterly | % |
| `TOURISM_OVERNIGHT_STAYS` | Tourism Overnight Stays | Tourism | Monthly | number |
| `EXPORTS` | Exports of Goods | Foreign Trade | Annual | EUR |
| `IMPORTS` | Imports of Goods | Foreign Trade | Annual | EUR |
| `TRADE_COVERAGE` | Trade Coverage Rate | Foreign Trade | Annual | % |
| `CONSTRUCTION_COST_INDEX` | Construction Cost Index (2021) | Construction | Monthly | index |
| `CONSTRUCTION_COST_YOY` | Construction Cost Annual Change | Construction | Monthly | % |

**CLI Examples:**
```bash
python3 modules/ine_portugal.py GDP_GROWTH_YOY
python3 modules/ine_portugal.py CPI_YOY
python3 modules/ine_portugal.py UNEMPLOYMENT_RATE
python3 modules/ine_portugal.py TOURISM_OVERNIGHT_STAYS
python3 modules/ine_portugal.py EXPORTS
python3 modules/ine_portugal.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'ine_portugal',
    params: { indicator: 'GDP_GROWTH_YOY' }
  })
});
```

### ibge_brazil.py — IBGE Brazil (Instituto Brasileiro de Geografia e Estatística)

- **Source:** IBGE — Brazil's geography and statistics institute (SIDRA aggregates API)
- **API:** `https://servicodados.ibge.gov.br/api/v3/agregados`
- **Protocol:** REST JSON (table/variable selection with classification filters)
- **Auth:** None (open access)
- **Freshness:** Monthly (IPCA, unemployment, industry, retail), Quarterly (GDP)
- **Coverage:** Brazil (national)

**Indicators (9):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `GDP_YOY` | GDP Growth YoY | National Accounts | Quarterly | % |
| `GDP_QOQ` | GDP Growth QoQ (SA) | National Accounts | Quarterly | % |
| `IPCA_MONTHLY` | IPCA Monthly Inflation | Prices | Monthly | % |
| `IPCA_12M` | IPCA 12-Month Cumulative | Prices | Monthly | % |
| `IPCA_YTD` | IPCA Year-to-Date | Prices | Monthly | % |
| `IPCA_INDEX` | IPCA Price Index (Dec 1993=100) | Prices | Monthly | index |
| `UNEMPLOYMENT` | PNAD Unemployment Rate (14+) | Labour Market | Monthly | % |
| `INDUSTRIAL_PRODUCTION` | PIM-PF Industrial Index (2022=100) | Industry | Monthly | index |
| `RETAIL_SALES` | PMC Broad Retail Sales YoY | Retail | Monthly | % |

**CLI Examples:**
```bash
python3 modules/ibge_brazil.py GDP_YOY
python3 modules/ibge_brazil.py IPCA_12M
python3 modules/ibge_brazil.py UNEMPLOYMENT
python3 modules/ibge_brazil.py INDUSTRIAL_PRODUCTION
python3 modules/ibge_brazil.py gdp        # alias: GDP_YOY + GDP_QOQ
python3 modules/ibge_brazil.py ipca       # alias: IPCA_MONTHLY + IPCA_12M
python3 modules/ibge_brazil.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'ibge_brazil',
    params: { indicator: 'IPCA_12M' }
  })
});
```

### gdelt_global_events.py — GDELT Project (Global Database of Events, Language, and Tone)

- **Source:** GDELT — the world's largest open database of human society, monitoring broadcast, print, and web news from nearly every country in 100+ languages
- **API:** `https://api.gdeltproject.org/api/v2/doc/doc`
- **Protocol:** REST JSON (query + mode parameters; supports timelinevol, timelinetone, artlist modes)
- **Auth:** None (fully open, no key required, fair-use ~5s between requests)
- **Freshness:** Real-time (updates every 15 minutes)
- **Coverage:** Global (100+ languages, 35+ country-mapped FIPS codes)

**Predefined Indicators (14):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `PROTEST_ACTIVITY_GLOBAL` | Global Protest Activity Index | Geopolitical Risk | Hourly | volume % |
| `PROTEST_SENTIMENT` | Global Protest Sentiment | Geopolitical Risk | Hourly | tone score |
| `MILITARY_ACTIVITY_GLOBAL` | Global Military Activity Index | Geopolitical Risk | Hourly | volume % |
| `TERROR_THREAT_GLOBAL` | Global Terror Threat Index | Geopolitical Risk | Hourly | volume % |
| `ARMED_CONFLICT_VOL` | Armed Conflict Media Volume | Geopolitical Risk | Hourly | volume % |
| `INFLATION_MEDIA_VOL` | Inflation Media Coverage Volume | Economic Themes | Hourly | volume % |
| `INFLATION_SENTIMENT` | Inflation Media Sentiment | Economic Themes | Hourly | tone score |
| `INTEREST_RATE_MEDIA_VOL` | Interest Rate Media Volume | Economic Themes | Hourly | volume % |
| `TRADE_MEDIA_VOL` | Trade Policy Media Volume | Economic Themes | Hourly | volume % |
| `TRADE_SENTIMENT` | Trade Policy Sentiment | Economic Themes | Hourly | tone score |
| `STOCKMARKET_MEDIA_VOL` | Stock Market Media Volume | Economic Themes | Hourly | volume % |
| `STOCKMARKET_SENTIMENT` | Stock Market Media Sentiment | Economic Themes | Hourly | tone score |
| `BANKRUPTCY_MEDIA_VOL` | Bankruptcy/Default Media Volume | Economic Themes | Hourly | volume % |
| `SANCTIONS_MEDIA_VOL` | Sanctions Media Coverage Volume | Commodity/Disruption | Hourly | volume % |

**Special Commands:**
- `country_risk <CC>` — Composite geopolitical risk index (0–100) for any country (FIPS, ISO, or name)
- `tension <CC1> <CC2>` — Bilateral tension score (0–100) between two countries
- `topic "<query>"` — Media sentiment and volume for any keyword/topic
- `articles "<query>"` — Full-text article search with metadata

**CLI Examples:**
```bash
python3 modules/gdelt_global_events.py PROTEST_ACTIVITY_GLOBAL
python3 modules/gdelt_global_events.py STOCKMARKET_SENTIMENT
python3 modules/gdelt_global_events.py country_risk US
python3 modules/gdelt_global_events.py country_risk CN
python3 modules/gdelt_global_events.py tension US CN
python3 modules/gdelt_global_events.py topic "central bank rate cut"
python3 modules/gdelt_global_events.py articles "semiconductor tariff"
python3 modules/gdelt_global_events.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'gdelt_global_events',
    params: { indicator: 'PROTEST_ACTIVITY_GLOBAL' }
  })
});
```

### patentsview_uspto.py — USPTO Open Data Portal (PatentsView)

- **Source:** United States Patent and Trademark Office (USPTO) Open Data Portal
- **API:** `https://api.uspto.gov/api/v1`
- **Protocol:** REST JSON (Lucene/Solr query syntax for patent application search)
- **Auth:** API key required — set `USPTO_ODP_API_KEY` env var (free registration at https://data.uspto.gov/apis/getting-started)
- **Rate Limit:** 45 requests/minute (automatic retry on 429)
- **Freshness:** Daily (patent data updated daily on ODP)
- **Coverage:** United States (all USPTO patent applications and grants)

**Indicators (5):**

| Key | Name | Category | Frequency | Unit |
|-----|------|----------|-----------|------|
| `PATENT_SEARCH` | Patent Application Search | Search | Daily | patents |
| `PATENT_GRANTS_BY_ASSIGNEE` | Patent Grants by Assignee | Corporate IP | Daily | patents |
| `TOP_ASSIGNEES` | Top Patent Assignees | Rankings | Daily | patents |
| `TECH_TRENDS` | Technology Trend by CPC Class | Technology | Daily | patents |
| `PATENT_DETAIL` | Single Patent Detail | Detail | On-demand | patent |

**Supported Ticker-to-Assignee Mappings (35+):** AAPL→Apple, MSFT→Microsoft, GOOG→Google, AMZN→Amazon, META→Meta Platforms, NVDA→NVIDIA, TSLA→Tesla, IBM→IBM, INTC→Intel, QCOM→Qualcomm, AMD→AMD, PFE→Pfizer, JNJ→J&J, MRK→Merck, LLY→Eli Lilly, BA→Boeing, GE→GE, and more.

**Named CPC Technology Classes (22):** G06N (AI/ML), G06F (Digital Computing), G06Q (Fintech), G06V (Computer Vision), H01L (Semiconductors), H04L (Telecom), H04W (Wireless), A61K (Pharma), A61B (Med Diagnostics), C12N (Genetic Engineering), H01M (Batteries), B60L (EVs), H02S (Solar Cells), F03D (Wind Power), and more.

**CLI Examples:**
```bash
python3 modules/patentsview_uspto.py search "artificial intelligence"
python3 modules/patentsview_uspto.py patent_grants_by_assignee NVDA
python3 modules/patentsview_uspto.py patent_grants_by_assignee "Pfizer"
python3 modules/patentsview_uspto.py tech_trends G06N      # AI & Machine Learning
python3 modules/patentsview_uspto.py tech_trends H01L      # Semiconductors
python3 modules/patentsview_uspto.py top_assignees
python3 modules/patentsview_uspto.py detail 18123456
python3 modules/patentsview_uspto.py tickers               # Show ticker→assignee map
python3 modules/patentsview_uspto.py cpc_classes            # Show CPC class names
python3 modules/patentsview_uspto.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'patentsview_uspto',
    params: { indicator: 'PATENT_GRANTS_BY_ASSIGNEE', assignee: 'AAPL' }
  })
});
```

### inegi_mexico.py — INEGI Mexico (Banco de Información Económica)

- **Source:** Instituto Nacional de Estadística y Geografía — Mexico's national statistics agency
- **API:** `https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR`
- **Protocol:** REST JSON/XML (BIE indicator endpoint pattern, INDICATOR/{id}/.../{token})
- **Auth:** API token required — set `INEGI_API_TOKEN` or `INEGI_TOKEN` env var (free at https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify)
- **Freshness:** Monthly (CPI, core inflation, unemployment, industrial production, trade, consumer confidence, auto production), Quarterly (GDP)
- **Coverage:** Mexico (national)

**Indicators (9):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP_QUARTERLY` | GDP Quarterly Growth YoY (base 2018, SA) | Quarterly | % |
| `CPI` | CPI Headline Inflation Monthly (INPC, base Jul 2018=100) | Monthly | % |
| `CORE_INFLATION` | Core Inflation ex Food & Energy | Monthly | % |
| `UNEMPLOYMENT` | National Unemployment Rate (ENOE survey) | Monthly | % |
| `INDUSTRIAL_PRODUCTION` | Industrial Production Index (base 2018=100, SA) | Monthly | index |
| `EXPORTS` | Merchandise Exports | Monthly | USD mn |
| `IMPORTS` | Merchandise Imports | Monthly | USD mn |
| `CONSUMER_CONFIDENCE` | Consumer Confidence Index (INEGI/Banxico, SA) | Monthly | index |
| `AUTO_PRODUCTION` | Total Motor Vehicle Production | Monthly | units |

**CLI Examples:**
```bash
python3 modules/inegi_mexico.py GDP_QUARTERLY
python3 modules/inegi_mexico.py CPI
python3 modules/inegi_mexico.py CORE_INFLATION
python3 modules/inegi_mexico.py UNEMPLOYMENT
python3 modules/inegi_mexico.py INDUSTRIAL_PRODUCTION
python3 modules/inegi_mexico.py EXPORTS
python3 modules/inegi_mexico.py CONSUMER_CONFIDENCE
python3 modules/inegi_mexico.py AUTO_PRODUCTION
python3 modules/inegi_mexico.py gdp          # alias: GDP_QUARTERLY
python3 modules/inegi_mexico.py trade        # alias: EXPORTS + IMPORTS
python3 modules/inegi_mexico.py inflation    # alias: CPI + CORE_INFLATION
python3 modules/inegi_mexico.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'inegi_mexico',
    params: { indicator: 'GDP_QUARTERLY' }
  })
});
```

### gleif_lei.py — GLEIF LEI Registry (Global Legal Entity Identification)

- **Source:** Global Legal Entity Identifier Foundation — the global LEI regulatory and operational framework
- **API:** `https://api.gleif.org/api/v1`
- **Protocol:** JSON:API (REST, paginated, filter-based queries)
- **Auth:** None required (fully open, no rate limit documented)
- **Freshness:** Daily (registry updated continuously; module cache 24h)
- **Coverage:** Global — 100+ jurisdictions, 2M+ active LEIs

**Indicators (10):**

| Key | Name | Description |
|-----|------|-------------|
| `TOTAL_ACTIVE` | Total Active LEIs | Count of all entities with active/valid LEI status |
| `TOTAL_LAPSED` | Total Lapsed LEIs | Count of expired/non-renewed registrations |
| `US_ENTITIES` | US Entity Count | LEI-registered entities with legal address in US |
| `GB_ENTITIES` | UK Entity Count | LEI-registered entities in United Kingdom |
| `DE_ENTITIES` | Germany Entity Count | LEI-registered entities in Germany |
| `JP_ENTITIES` | Japan Entity Count | LEI-registered entities in Japan |
| `FR_ENTITIES` | France Entity Count | LEI-registered entities in France |
| `CN_ENTITIES` | China Entity Count | LEI-registered entities in China |
| `CA_ENTITIES` | Canada Entity Count | LEI-registered entities in Canada |
| `LU_ENTITIES` | Luxembourg Entity Count | LEI-registered entities in Luxembourg |

**Special Commands:** `search <name>` (fuzzy entity search), `lookup <lei>` (full entity details), `hierarchy <lei>` (parent/child relationships)

**CLI Examples:**
```bash
python3 modules/gleif_lei.py TOTAL_ACTIVE
python3 modules/gleif_lei.py US_ENTITIES
python3 modules/gleif_lei.py search "Goldman Sachs"
python3 modules/gleif_lei.py lookup 8I5DZWZKVSZI1NUHU748
python3 modules/gleif_lei.py hierarchy 8I5DZWZKVSZI1NUHU748
python3 modules/gleif_lei.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'gleif_lei',
    params: { indicator: 'TOTAL_ACTIVE' }
  })
});
```

### bank_of_thailand.py — Bank of Thailand (BOT) Monetary & Macro Statistics

- **Source:** Bank of Thailand — Thailand's central bank
- **API:** `https://gateway.api.bot.or.th` (REST JSON, IBM API Connect gateway)
- **Protocol:** REST JSON with `X-IBM-Client-Id` auth header; SDMX-style time series + dedicated FX endpoint
- **Auth:** `BOT_API_KEY` required (free at https://apiportal.bot.or.th)
- **Freshness:** Daily (FX rates, 1h cache), Monthly (rates/BoP/banking, 24h cache), Annual (GDP/CPI)
- **Coverage:** Thailand

**Indicators (27):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `POLICY_RATE` | BOT Policy Rate (1-Day Bilateral Repo) | Monthly | % |
| `INTERBANK_OVERNIGHT` | Weighted Avg Overnight Interbank Rate | Monthly | % |
| `REPO_1D` | 1-Day Private Repo Rate | Monthly | % |
| `BIBOR_1W` | BIBOR 1-Week | Monthly | % |
| `BIBOR_3M` | BIBOR 3-Month | Monthly | % |
| `BIBOR_6M` | BIBOR 6-Month | Monthly | % |
| `BIBOR_1Y` | BIBOR 1-Year | Monthly | % |
| `BOND_1Y` | Thai Govt Bond Yield 1Y | Monthly | % |
| `BOND_5Y` | Thai Govt Bond Yield 5Y | Monthly | % |
| `BOND_10Y` | Thai Govt Bond Yield 10Y | Monthly | % |
| `BOND_20Y` | Thai Govt Bond Yield 20Y | Monthly | % |
| `CURRENT_ACCOUNT_USD` | Current Account Balance | Monthly | USD mn |
| `INTL_RESERVES_USD` | International Reserves | Monthly | USD mn |
| `FX_END_PERIOD` | THB/USD End-of-Period Monthly | Monthly | THB |
| `NARROW_MONEY` | Narrow Money (M1) | Monthly | THB bn |
| `BROAD_MONEY` | Broad Money Supply | Monthly | THB bn |
| `GDP_REAL` | Real GDP | Annual | THB bn |
| `GDP_REAL_YOY` | Real GDP Year-on-Year Growth | Annual | % |
| `GDP_NOMINAL` | Nominal GDP | Annual | THB bn |
| `HEADLINE_CPI` | Headline CPI Level | Annual | index |
| `HEADLINE_CPI_YOY` | Headline CPI Year-on-Year | Annual | % |
| `CORE_CPI` | Core CPI Level | Annual | index |
| `CORE_CPI_YOY` | Core CPI Year-on-Year | Annual | % |
| `CB_TOTAL_ASSETS` | Commercial Bank Total Assets | Monthly | THB bn |
| `CB_LOANS_EX_IB` | Commercial Bank Loans excl. Interbank | Monthly | THB bn |
| `CB_DEPOSITS_EX_IB` | Commercial Bank Deposits excl. Interbank | Monthly | THB bn |
| `CB_LDR` | Commercial Bank Loan-to-Deposit Ratio | Monthly | % |

**Special Commands:** `fx_rates` (daily THB exchange rates for major currencies)

**CLI Examples:**
```bash
python3 modules/bank_of_thailand.py POLICY_RATE
python3 modules/bank_of_thailand.py BIBOR_3M
python3 modules/bank_of_thailand.py BOND_10Y
python3 modules/bank_of_thailand.py GDP_REAL
python3 modules/bank_of_thailand.py HEADLINE_CPI_YOY
python3 modules/bank_of_thailand.py CURRENT_ACCOUNT_USD
python3 modules/bank_of_thailand.py fx_rates
python3 modules/bank_of_thailand.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'bank_of_thailand',
    params: { indicator: 'POLICY_RATE' }
  })
});
```

### dane_colombia.py — DANE Colombia (SDMX National Statistics)

- **Source:** Departamento Administrativo Nacional de Estadística — Colombia's national statistics office
- **API:** `https://sdmx.dane.gov.co/gateway/rest`
- **Protocol:** SDMX 2.1 REST with SDMX-JSON 1.0 responses
- **Auth:** None required (open access)
- **Freshness:** Monthly (CPI, unemployment, IPI, trade, PPI), Quarterly (GDP), Annual (manufacturing survey)
- **Coverage:** Colombia (national)

**Indicators (7):**

| Key | Name | Dataflow | Frequency | Unit |
|-----|------|----------|-----------|------|
| `GDP` | GDP Production Approach | PIB_PRODUCCION | Quarterly | COP bn |
| `CPI` | Consumer Price Index | IPC | Monthly | index |
| `UNEMPLOYMENT` | Unemployment Rate (GEIH) | GEIH | Monthly | % |
| `INDUSTRIAL_PRODUCTION` | Industrial Production Index | EMM | Monthly | index |
| `TRADE_BALANCE` | Trade Balance | BALANZA_COMERCIAL | Monthly | USD mn |
| `PPI` | Producer Price Index | IPP | Monthly | index |
| `ANNUAL_MANUFACTURING` | Annual Manufacturing Survey | EAM | Annual | COP mn |

**CLI Examples:**
```bash
python3 modules/dane_colombia.py GDP
python3 modules/dane_colombia.py CPI
python3 modules/dane_colombia.py UNEMPLOYMENT
python3 modules/dane_colombia.py INDUSTRIAL_PRODUCTION
python3 modules/dane_colombia.py TRADE_BALANCE
python3 modules/dane_colombia.py PPI
python3 modules/dane_colombia.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'dane_colombia',
    params: { indicator: 'GDP' }
  })
});
```

### epo_ops.py — European Patent Office (Open Patent Services)

- **Source:** EPO — Europe's patent granting authority, covering worldwide patent data (DOCDB)
- **API:** `https://ops.epo.org/3.2/rest-services` (OAuth2 token: `https://ops.epo.org/3.2/auth/accesstoken`)
- **Protocol:** REST XML responses, OAuth2 client credentials flow
- **Auth:** `EPO_CONSUMER_KEY` + `EPO_CONSUMER_SECRET` (free at https://developers.epo.org)
- **Freshness:** On-demand (patents are static once published; 24h cache), Weekly (recent grants)
- **Coverage:** Global — 100+ patent authorities (EP, WO, US, JP, CN, KR, etc.)

**Indicators (6):**

| Key | Name | Description |
|-----|------|-------------|
| `PATENT_SEARCH` | Patent Full-Text Search | Keyword search across titles and abstracts |
| `APPLICANT_FILINGS` | Applicant/Company Filings | All patents from a specific applicant/organization |
| `PATENT_FAMILY` | Patent Family Members | Cross-office family for any patent number |
| `EP_REGISTER` | EP Register Status | Procedural status (grant, opposition, appeal) |
| `IPC_TRENDS` | IPC Technology Filing Trends | Annual filing volume by IPC classification code |
| `RECENT_GRANTS` | Recent EP Publications | Newly published European patents (~30-day window) |

**CLI Examples:**
```bash
python3 modules/epo_ops.py PATENT_SEARCH "battery solid state"
python3 modules/epo_ops.py APPLICANT_FILINGS "Samsung"
python3 modules/epo_ops.py PATENT_FAMILY EP3456789
python3 modules/epo_ops.py EP_REGISTER EP3456789
python3 modules/epo_ops.py IPC_TRENDS H01M
python3 modules/epo_ops.py RECENT_GRANTS
python3 modules/epo_ops.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'epo_ops',
    params: { indicator: 'IPC_TRENDS', ipc_class: 'H01M' }
  })
});
```

### usgs_earthquake.py — USGS Earthquake Hazards Program (FDSN Event Service)

- **Source:** United States Geological Survey — FDSN Event Web Service
- **API:** `https://earthquake.usgs.gov/fdsnws/event/1`
- **Protocol:** REST GeoJSON (queries: `/query`, `/count`)
- **Auth:** None required (fully open, public service)
- **Freshness:** Near real-time (5-minute cache for active feeds), Daily (24h cache for historical/annual)
- **Coverage:** Global seismicity + 5 regional economic hotspots (Taiwan, Japan, Chile, Turkey, California)

**Indicators (10):**

| Key | Name | Window | Min Mag | Cache |
|-----|------|--------|---------|-------|
| `SIGNIFICANT_GLOBAL` | M5.0+ Worldwide | 24h | 5.0 | 5 min |
| `RECENT_M4` | M4.0+ Worldwide | 7 days | 4.0 | 5 min |
| `PAGER_ALERTS` | PAGER Orange+ Alerts | 30 days | 4.5 | 5 min |
| `HOTSPOT_TAIWAN` | Taiwan Semiconductor Zone (300 km) | 30 days | 3.0 | 5 min |
| `HOTSPOT_JAPAN` | Japan/Tokyo Zone (500 km) | 30 days | 3.0 | 5 min |
| `HOTSPOT_CHILE` | Chile/Santiago Mining Zone (800 km) | 30 days | 3.0 | 5 min |
| `HOTSPOT_TURKEY` | Turkey/Istanbul Bosphorus (400 km) | 30 days | 3.0 | 5 min |
| `HOTSPOT_CALIFORNIA` | California/Silicon Valley (300 km) | 30 days | 3.0 | 5 min |
| `ANNUAL_M5_PLUS` | Annual M5+ Event Count | 1 year | 5.0 | 24h |
| `FELT_REPORTS` | DYFI Widely Felt Events | 7 days | any | 5 min |

**CLI Examples:**
```bash
python3 modules/usgs_earthquake.py SIGNIFICANT_GLOBAL
python3 modules/usgs_earthquake.py RECENT_M4
python3 modules/usgs_earthquake.py PAGER_ALERTS
python3 modules/usgs_earthquake.py HOTSPOT_TAIWAN
python3 modules/usgs_earthquake.py HOTSPOT_JAPAN
python3 modules/usgs_earthquake.py HOTSPOT_CALIFORNIA
python3 modules/usgs_earthquake.py ANNUAL_M5_PLUS
python3 modules/usgs_earthquake.py FELT_REPORTS
python3 modules/usgs_earthquake.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'usgs_earthquake',
    params: { indicator: 'HOTSPOT_TAIWAN' }
  })
});
```

### kosis_korea.py — KOSIS South Korea (Statistics Korea / KOSTAT)

- **Source:** Korean Statistical Information Service — South Korea's official statistics portal
- **API:** `https://kosis.kr/openapi/Param/statisticsParameterData.do`
- **Protocol:** REST JSON (query parameter-based)
- **Auth:** `KOSIS_API_KEY` required (free at https://kosis.kr/openapi/, ~1,000 requests/day)
- **Freshness:** Monthly (CPI, unemployment, IPI, exports, housing, semiconductors), Quarterly (GDP)
- **Coverage:** South Korea (national)

**Indicators (7):**

| Key | Name | Frequency | Unit |
|-----|------|-----------|------|
| `GDP` | GDP by Expenditure (Current Prices) | Quarterly | KRW tn |
| `CPI` | Consumer Price Index (2020=100) | Monthly | index |
| `UNEMPLOYMENT` | Unemployment Rate (EAP Survey) | Monthly | % |
| `INDUSTRIAL_PRODUCTION` | Mining & Manufacturing Production Index (2020=100) | Monthly | index |
| `EXPORTS` | Merchandise Exports by Commodity/Country | Monthly | USD mn |
| `HOUSING` | Nationwide Apartment Price Index | Monthly | index |
| `SEMICONDUCTORS` | Semiconductor Production Index | Monthly | index |

**CLI Examples:**
```bash
python3 modules/kosis_korea.py GDP
python3 modules/kosis_korea.py CPI
python3 modules/kosis_korea.py UNEMPLOYMENT
python3 modules/kosis_korea.py INDUSTRIAL_PRODUCTION
python3 modules/kosis_korea.py EXPORTS
python3 modules/kosis_korea.py HOUSING
python3 modules/kosis_korea.py SEMICONDUCTORS
python3 modules/kosis_korea.py list
```

**MCP Tool Call:**
```typescript
const result = await fetch('http://localhost:3056/api/data', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'kosis_korea',
    params: { indicator: 'SEMICONDUCTORS' }
  })
});
```

---

## Category 2: US Government & Federal Data

| Module | Source | Key Data |
|--------|--------|----------|
| `fred_enhanced` | Federal Reserve (FRED) | 800K+ macro time series — GDP, unemployment, CPI, rates |
| `bls` | Bureau of Labor Statistics | Employment, wages, CPI, PPI |
| `census` | US Census Bureau | Demographics, economic indicators, housing |
| `eia_energy` | Energy Information Administration | Oil, gas, electricity, renewables |
| `usda_agriculture` | USDA | Crop reports, supply/demand, ag prices |
| `treasury_curve` | US Treasury | Yield curves, auction results |
| `fed_policy` | Federal Reserve | FOMC minutes, policy rate expectations |
| `fed_soma` | Fed SOMA Holdings | Federal Reserve balance sheet |
| `sec_edgar_api` | SEC EDGAR | Filings, 13F, insider trading |
| `fiscaldata_treasury` | Treasury FiscalData | Government revenue, spending, debt |

---

## Category 3: Core Market Data

| Module | Source | Key Data |
|--------|--------|----------|
| `prices` | Yahoo Finance | Stock prices, history, quotes |
| `alpha_picker` | AI/Multi-source | AI-generated alpha scoring |
| `technicals` | Computed | RSI, MACD, Bollinger, SMA, EMA |
| `screener` | Multi-source | Multi-criteria stock screening |
| `options_chain` | Multiple | Options chains, Greeks, OI |
| `options_flow` | Multiple | Unusual options activity, flow |
| `cboe_put_call` | CBOE | Put/call ratio, sentiment |
| `volatility_surface` | Computed | Implied vol surface, skew |
| `polygon_io` | Polygon.io | Tick data, aggregates, reference |
| `tiingo` | Tiingo | EOD prices, IEX real-time |
| `finnhub` | Finnhub | Real-time quotes, IPOs, news |

---

## Category 4: Alternative Data

| Module | Source | Key Data |
|--------|--------|----------|
| `congress_trades` | Public filings | Congressional stock trading |
| `insider_trades` | SEC Form 4 | Insider buying/selling |
| `short_interest` | FINRA/Exchange | Short interest ratios |
| `patent_tracking` | USPTO | Patent filings, innovation signals |
| `job_posting_analyzer` | Public data | Hiring trends, workforce signals |
| `reddit_sentiment` | Reddit API | WSB sentiment, mentions |
| `news_sentiment` | Multiple | News sentiment scoring |
| `satellite_proxies` | Satellite imagery | Parking lot counts, economic activity |
| `web_traffic_estimator` | SimilarWeb/proxy | Company web traffic trends |
| `whale_wallet_tracker` | On-chain | Crypto whale wallet movements |

---

## Category 5: International & Global Macro

| Module | Source | Key Data |
|--------|--------|----------|
| `ecb_fx_rates` | European Central Bank | EUR reference FX rates |
| `eurostat_macro` | Eurostat | EU-wide macro statistics |
| `bank_of_england` | Bank of England | UK rates, yields, macro |
| `bank_of_japan_time_series_api` | Bank of Japan | JPY rates, monetary policy |
| `bank_of_korea` | Bank of Korea | KRW rates, Korean macro |
| `oecd` | OECD | CLI, economic indicators |
| `world_bank_economic_data` | World Bank | Global development indicators |
| `imf_weo` | IMF | World Economic Outlook |
| `india_macro` | RBI/NSO | Indian economic data |
| `china_nbs` | National Bureau of Statistics | Chinese macro indicators |

---

## Category 6: Fixed Income & Rates

| Module | Source | Key Data |
|--------|--------|----------|
| `yield_curve` | Multiple | US Treasury yield curve |
| `credit_spreads` | Computed | IG/HY credit spreads |
| `inflation_linked_bonds` | Multiple | TIPS, breakeven inflation |
| `fed_funds_futures` | CME | Rate expectations |
| `swap_rate_curves` | Multiple | IRS curves |
| `muni_bond` | Multiple | Municipal bond data |
| `convertible_bonds` | Multiple | Convertible bond analytics |
| `cds_spreads` | Multiple | Credit default swap spreads |
| `leveraged_loan` | Multiple | Leveraged loan market |
| `commercial_paper` | Fed | Commercial paper rates |

---

## Category 7: Crypto & Digital Assets

| Module | Source | Key Data |
|--------|--------|----------|
| `coingecko_crypto` | CoinGecko | Prices, market cap, volume |
| `bitcoin_onchain` | Multiple | Hash rate, MVRV, SOPR |
| `crypto_derivatives` | Deribit/exchanges | Futures, options, funding |
| `defi_tvl_yield` | DefiLlama | TVL, yield farming |
| `stablecoin_flows` | On-chain | USDT/USDC flows, depeg monitoring |
| `nft_market` | Multiple | NFT sales, floor prices |
| `crypto_fear_greed` | Alternative.me | Crypto sentiment index |
| `crypto_liquidation` | Exchange data | Liquidation events |

---

## Category 8: Quantitative & Analytics

| Module | Source | Key Data |
|--------|--------|----------|
| `factor_model_engine` | Computed | Fama-French, multi-factor |
| `portfolio_analytics` | Computed | Sharpe, drawdown, attribution |
| `backtesting_engine` | Computed | Strategy backtesting |
| `monte_carlo` | Computed | MC simulation, VaR |
| `correlation_regime` | Computed | Regime detection |
| `black_litterman` | Computed | BL portfolio optimization |
| `risk_parity_portfolio` | Computed | Risk parity construction |
| `kelly_criterion_sizer` | Computed | Optimal position sizing |
| `xgboost_alpha` | ML | ML-based alpha signals |
| `garch_volatility` | Computed | GARCH vol forecasting |

---

## Category 9: Corporate Events

| Module | Source | Key Data |
|--------|--------|----------|
| `ipo_pipeline` | Multiple | Upcoming IPOs, filings |
| `spac_tracker` | Multiple | SPAC lifecycle tracking |
| `earnings_calendar_enhanced` | Multiple | Earnings dates, estimates |
| `earnings_transcripts_nlp` | Multiple | Call transcripts, NLP analysis |
| `dividend_tracker` | Multiple | Dividend history, yield |
| `share_buyback` | SEC filings | Buyback announcements |
| `regulatory_calendar` | Multiple | FDA, SEC regulatory events |
| `activist_success_predictor` | SEC 13D | Activist campaign tracking |

---

## Complete Module List

All 1,062 modules in `modules/` directory, sorted alphabetically:

<details>
<summary>Click to expand full module list (1,062 modules)</summary>

```
42matters_app_intelligence    aaii_sentiment               aaii_sentiment_survey
abs                          abs_australia_sdmx            abs_australia_stats
abs_mbs_prepayment
academic_papers              activist_success_predictor    adr_gdr_arbitrage
agricultural_balance         agricultural_commodities      agricultural_supply_demand
ai_chip_demand               ai_chip_demand_forecaster     ai_earnings_analyzer
ai_research_reports          air_quality_economic          airport_traffic_aviation
aishub_data_feed             aishub_vessel_tracker         alchemy_api
alert_backtest               alert_dashboard               alert_dsl
alpaca_market_data_api       alpaca_markets_api            alpha_picker
alpha_vantage                alpha_vantage_api             alpha_vantage_commodities_api
alpha_vantage_earnings_api   alpha_vantage_forex           alpha_vantage_fund_flows
banco_de_espana              banco_de_portugal             bank_of_canada
bank_of_canada_valet         bank_of_england               banque_de_france
bcb                          bis_enhanced                  bnr_romania
bls                          bundesbank_sdmx               cbc_taiwan
cbs_netherlands              census                        central_bank_ireland
cnb_czech                    czso_czech                    destatis_germany
dnb_netherlands              ecb_enhanced
coingecko_crypto             congress_trades               cso_ireland
danmarks_nationalbank        ecb_fx_rates                  edinet_japan
crypto_onchain
eia_energy                   estat_japan                   eurostat_enhanced
eurostat_macro
fca_uk                       fred_enhanced                 ine_spain
istat_italy                  insee_france
nbb_belgium                  nbp_poland                    ons_uk
options_chain                polygon_io                    prices
rba_enhanced                 riksbank_sweden               scb_sweden
screener
sec_edgar_api                statbel_belgium               statcan_canada
statistics_austria           statistics_denmark            statistics_estonia
statistics_finland
technicals
tiingo                       treasury_curve                uae_data
yield_curve
imf_enhanced
oecd_enhanced                boe_iadb_enhanced             mnb_hungary
eu_small_central_banks       eu_small_statistics
ine_portugal                 ibge_brazil
gdelt_global_events          patentsview_uspto
inegi_mexico
gleif_lei                   bank_of_thailand              dane_colombia
epo_ops                     usgs_earthquake               kosis_korea
... (1,079 total — run `ls modules/*.py | wc -l` to verify)
```

</details>

---

## API Keys Required

| Source | Env Variable | Free Tier | Registration |
|--------|-------------|-----------|-------------|
| FRED | `FRED_API_KEY` | Unlimited | https://fred.stlouisfed.org/docs/api/api_key.html |
| Financial Datasets | `FINANCIAL_DATASETS_API_KEY` | Limited | https://financialdatasets.ai |
| Finnhub | `FINNHUB_API_KEY` | 60/min | https://finnhub.io |
| Polygon | `POLYGON_API_KEY` | 5/min | https://polygon.io |
| EIA | `EIA_API_KEY` | Unlimited | https://www.eia.gov/opendata/register.php |
| Census | `CENSUS_API_KEY` | Unlimited | https://api.census.gov/data/key_signup.html |
| Etherscan | `ETHERSCAN_API_KEY` | 5/sec | https://etherscan.io/apis |
| USDA NASS | `USDA_NASS_API_KEY` | Unlimited | https://quickstats.nass.usda.gov/api |
| Banque de France | `BANQUE_DE_FRANCE_API_KEY` | Open | https://webstat.banque-france.fr/signup |
| Bank of Korea | `BOK_API_KEY` | Open | https://ecos.bok.or.kr |
| e-Stat Japan | `ESTAT_JAPAN_APP_ID` | Open | https://www.e-stat.go.jp/api/ |
| CNB Czech (ARAD) | `ARAD_API_KEY` | Open | https://www.cnb.cz/aradb/ |
| Destatis GENESIS | `DESTATIS_USER` + `DESTATIS_PASSWORD` | Open | https://www-genesis.destatis.de |
| EDINET Japan | `EDINET_API_KEY` | Open | https://disclosure.edinet-fsa.go.jp |
| FCA UK Register | `FCA_API_KEY` + `FCA_API_EMAIL` | Open | https://register.fca.org.uk/Developer/s/ |
| DNB Netherlands | `DNB_SUBSCRIPTION_KEY` | Open (fallback) | Public fallback key available; custom key via DNB developer portal |
| USPTO ODP (PatentsView) | `USPTO_ODP_API_KEY` | 45/min | https://data.uspto.gov/apis/getting-started |
| INEGI Mexico (BIE) | `INEGI_API_TOKEN` | Open | https://www.inegi.org.mx/app/desarrolladores/generatoken/Usuarios/token_Verify |
| Bank of Thailand (BOT) | `BOT_API_KEY` | Open | https://apiportal.bot.or.th |
| EPO Open Patent Services | `EPO_CONSUMER_KEY` + `EPO_CONSUMER_SECRET` | ~10/s | https://developers.epo.org |
| KOSIS South Korea | `KOSIS_API_KEY` | ~1,000/day | https://kosis.kr/openapi/ |

Most government statistics modules (Bundesbank, INSEE, ISTAT, CBS, DST, SCB, Riksbank, BdE, BPstat, ONS, StatCan, NBP Poland, CBC Taiwan, NBB Belgium, CBI Ireland, CSO Ireland, Statistics Finland, Danmarks Nationalbank, CNB Czech, ABS Australia, CBUAE/World Bank, RBA Australia, Bank of Canada Valet, INE Spain, BNR Romania, Statbel Belgium, Statistics Austria, CZSO Czech, Statistics Estonia, ECB Enhanced, Eurostat Enhanced, BIS Enhanced, IMF Enhanced, OECD Enhanced, BoE IADB Enhanced, MNB Hungary, EU Small Central Banks, EU Small Statistics, INE Portugal, IBGE Brazil, GDELT Project, DANE Colombia, USGS Earthquake, GLEIF LEI) require **NO API key** for core data. DNB Netherlands includes a public fallback key. e-Stat Japan, Destatis GENESIS, EDINET Japan, FCA UK Register, CNB Czech ARAD, USPTO PatentsView, INEGI Mexico, Bank of Thailand, EPO OPS, and KOSIS South Korea require free registration.

---

*1,079 modules — 38 countries + EU-wide + global + 190 IMF member nations + 38 OECD members — 55 government/central bank/institutional/alt-data modules — 1,010+ macro, geopolitical, patent, seismic & entity indicators — Updated 2026-04-02 — QuantClaw Data (DCC)*
