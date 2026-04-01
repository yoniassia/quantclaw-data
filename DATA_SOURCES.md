# QuantClaw Data Sources — Complete Reference for AI Agents

> **1,050 Python modules** across 9+ categories. Access via MCP tool calls, REST API, or direct CLI.
> This file is THE reference for AI agents (claws) to know what data is available and how to get it.

**Base URL:** `http://localhost:3055` (local) / `https://data.quantclaw.org` (production)
**MCP Proxy:** `http://localhost:3056/api/data`

---

## Quick Lookup — Common Queries → Modules

| Query | Modules |
|-------|---------|
| GDP data | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `uae_data`, `destatis_germany`, `eurostat_macro` |
| Inflation / CPI | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `nbb_belgium`, `abs_australia_sdmx`, `uae_data`, `destatis_germany`, `bls` |
| Unemployment | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `destatis_germany`, `bls` |
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
| Bond yields | `bundesbank_sdmx`, `riksbank_sweden`, `danmarks_nationalbank`, `treasury_curve`, `yield_curve` |
| Central bank rates | `bundesbank_sdmx` (ECB), `riksbank_sweden`, `bank_of_england`, `fed_policy`, `cbc_taiwan` (CBC), `central_bank_ireland` (ECB), `danmarks_nationalbank` (DN), `cnb_czech` (CNB 2W repo) |
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
| Housing data | `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `abs_australia_sdmx`, `fred_housing`, `zillow_zhvi` |
| Gold price (PLN) | `nbp_poland` |
| Australian macro data | `abs_australia_sdmx` (GDP, CPI, labour force, BoP, retail trade, building approvals, trade) |
| UAE macro / FX | `uae_data` (CBUAE 76-currency FX, GDP, CPI, M2, reserves, trade) |
| German statistics (ext) | `destatis_germany` (GENESIS GDP, CPI/HICP, employment, trade, IPI, PPI, construction) |
| Japanese filings | `edinet_japan` (annual/quarterly securities reports, large shareholding, tender offers) |
| UK regulatory data | `fca_uk` (authorized firms, individuals, permissions, disciplinary, regulated markets) |
| Trade balance | `bundesbank_sdmx`, `insee_france`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `banco_de_portugal`, `ons_uk`, `statcan_canada`, `estat_japan`, `cso_ireland`, `statistics_finland`, `nbb_belgium`, `danmarks_nationalbank`, `abs_australia_sdmx`, `destatis_germany` |
| ESG / Climate | `carbon_footprint`, `climate_risk`, `eu_taxonomy_alignment`, `esg_decomposition` |
| Sentiment | `reddit_sentiment`, `news_sentiment`, `cnn_fear_greed`, `social_sentiment_spikes` |
| Company profile | `company_profile`, `screener`, `alpha_picker` |
| Short interest | `short_interest`, `short_volume`, `finra_short_interest` |
| IPO / SPAC | `ipo_pipeline`, `spac_tracker`, `spac_lifecycle` |
| Energy data | `eia_energy`, `crude_oil_fundamentals`, `natural_gas_supply_demand`, `opec` |
| Agriculture | `usda_agriculture`, `crop_yield_forecaster`, `agricultural_commodities` |

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

All 1,050 modules in `modules/` directory, sorted alphabetically:

<details>
<summary>Click to expand full module list (1,050 modules)</summary>

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
bank_of_england              banque_de_france              bcb
bls                          bundesbank_sdmx               cbc_taiwan
cbs_netherlands              census                        central_bank_ireland
cnb_czech                    destatis_germany
coingecko_crypto             congress_trades               cso_ireland
danmarks_nationalbank        ecb_fx_rates                  edinet_japan
crypto_onchain
eia_energy                   estat_japan                   eurostat_macro
fca_uk                       fred_enhanced                 istat_italy
insee_france
nbb_belgium                  nbp_poland                    ons_uk
options_chain                polygon_io                    prices
riksbank_sweden              scb_sweden                    screener
sec_edgar_api                statcan_canada                statistics_denmark
statistics_finland           technicals
tiingo                       treasury_curve                uae_data
yield_curve
... (1,050 total — run `ls modules/*.py | wc -l` to verify)
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

Most government statistics modules (Bundesbank, INSEE, ISTAT, CBS, DST, SCB, Riksbank, BdE, BPstat, ONS, StatCan, NBP Poland, CBC Taiwan, NBB Belgium, CBI Ireland, CSO Ireland, Statistics Finland, Danmarks Nationalbank, CNB Czech, ABS Australia, CBUAE/World Bank) require **NO API key** for core data. e-Stat Japan, Destatis GENESIS, EDINET Japan, FCA UK Register, and CNB Czech ARAD require free registration.

---

*1,050 modules — 21 countries — Updated 2026-04-01 — QuantClaw Data (DCC)*
