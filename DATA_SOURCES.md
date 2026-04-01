# QuantClaw Data Sources — Complete Reference for AI Agents

> **1,039 Python modules** across 9+ categories. Access via MCP tool calls, REST API, or direct CLI.
> This file is THE reference for AI agents (claws) to know what data is available and how to get it.

**Base URL:** `http://localhost:3055` (local) / `https://data.quantclaw.org` (production)
**MCP Proxy:** `http://localhost:3056/api/data`

---

## Quick Lookup — Common Queries → Modules

| Query | Modules |
|-------|---------|
| GDP data | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `eurostat_macro` |
| Inflation / CPI | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `bls` |
| Unemployment | `fred_enhanced`, `insee_france`, `istat_italy`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `ons_uk`, `statcan_canada`, `estat_japan`, `bls` |
| Stock price / quote | `prices`, `market_quote`, `alpha_picker`, `tiingo`, `polygon_io` |
| Technical analysis | `technicals`, `breadth_indicators`, `momentum_factor_backtest` |
| Options data | `options_chain`, `options_flow`, `cboe_put_call`, `volatility_surface` |
| Crypto prices | `coingecko_crypto`, `crypto_onchain`, `bitcoin_onchain` |
| PLN exchange rates | `nbp_poland` (Table A mid, Table B exotic, Table C bid/ask, gold) |
| TWD exchange rates | `cbc_taiwan` (TWD/USD close, buy, sell) |
| EUR exchange rates | `banque_de_france`, `riksbank_sweden`, `banco_de_portugal`, `ecb_fx_rates`, `alphavantage_fx` |
| Bond yields | `bundesbank_sdmx`, `riksbank_sweden`, `treasury_curve`, `yield_curve` |
| Central bank rates | `bundesbank_sdmx` (ECB), `riksbank_sweden`, `bank_of_england`, `fed_policy`, `cbc_taiwan` (CBC discount rate) |
| Euribor rates | `banco_de_espana` |
| Polish macro / FX | `nbp_poland` (FX rates 32+ currencies, bid/ask, gold PLN/g) |
| Taiwan monetary | `cbc_taiwan` (policy rates, M1A/M1B/M2, deposit/lending rates, TWD/USD) |
| UK macro data | `ons_uk` (GDP, CPIH, retail, trade, labour, construction, rental) |
| Canadian macro data | `statcan_canada` (GDP, CPI, labour, trade, retail, housing) |
| Japanese macro data | `estat_japan` (CPI, GDP, unemployment, trade, industry, housing) |
| Portuguese banking | `banco_de_portugal` (lending/deposit rates, BoP, FX, NPL, CET1, FSI) |
| Earnings data | `earnings_calendar_enhanced`, `earnings_transcripts_nlp`, `ai_earnings_analyzer` |
| Insider trades | `insider_trades`, `openinsider`, `fmp_insider_trading` |
| Congress trades | `congress_trades`, `quiver_quant_wallstreetbets` |
| Housing data | `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `ons_uk`, `statcan_canada`, `estat_japan`, `fred_housing`, `zillow_zhvi` |
| Gold price (PLN) | `nbp_poland` |
| Trade balance | `bundesbank_sdmx`, `insee_france`, `cbs_netherlands`, `statistics_denmark`, `scb_sweden`, `banco_de_espana`, `banco_de_portugal`, `ons_uk`, `statcan_canada`, `estat_japan` |
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

All 1,039 modules in `modules/` directory, sorted alphabetically:

<details>
<summary>Click to expand full module list (1,039 modules)</summary>

```
42matters_app_intelligence    aaii_sentiment               aaii_sentiment_survey
abs                          abs_australia_stats           abs_mbs_prepayment
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
cbs_netherlands              census                        coingecko_crypto
congress_trades              crypto_onchain                ecb_fx_rates
eia_energy                   estat_japan                   eurostat_macro
fred_enhanced                istat_italy                   insee_france
nbp_poland                   ons_uk                        options_chain
polygon_io                   prices                        riksbank_sweden
scb_sweden                   screener                      sec_edgar_api
statcan_canada               statistics_denmark            technicals
tiingo                       treasury_curve                yield_curve
... (1,039 total — run `ls modules/*.py | wc -l` to verify)
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

Most government statistics modules (Bundesbank, INSEE, ISTAT, CBS, DST, SCB, Riksbank, BdE, BPstat, ONS, StatCan, NBP Poland, CBC Taiwan) require **NO API key**. e-Stat Japan requires a free Application ID.

---

*1,039 modules — 12 countries — Updated 2026-04-01 — QuantClaw Data (DCC)*
