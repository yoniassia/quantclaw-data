# 0066 — Central Bank of Turkey EVDS API

## What
Build `tcmb_evds.py` module for the Central Bank of the Republic of Turkey (TCMB) Electronic Data Delivery System (EVDS) — a comprehensive REST API serving 40,000+ economic time series for Turkey. Covers exchange rates, interest rates, CPI/PPI inflation, monetary aggregates, balance of payments, banking statistics, and financial stability indicators. Turkey is an $900B+ economy with unique macro dynamics (high inflation regime, currency volatility, unconventional monetary policy) making this extremely high-value for EM-focused strategies.

## Why
Turkey is the world's 17th-largest economy with one of the most volatile and actively traded EM currencies (USD/TRY). Turkish lira carry trades and CDS spreads are bellwether signals for EM risk appetite globally. Turkey's persistent double-digit inflation, unorthodox interest rate policy (rate cuts during inflation surges), and large current account deficit create constant macro trading opportunities. TCMB policy rate decisions move USD/TRY 2-5% in minutes and spill over into EUR, ZAR, and BRL. The EVDS API provides the authoritative source for all Turkish economic data — no existing QuantClaw module covers TCMB or Turkish central bank data directly. The `turkish_institute.py` module covers TURKSTAT (statistics office) but not the central bank.

## API
- Base: `https://evds2.tcmb.gov.tr/service/evds`
- Protocol: REST (GET requests)
- Auth: API key (free registration at https://evds2.tcmb.gov.tr/index.php?/evds/login)
- Formats: JSON, XML, CSV
- Rate limits: 100 requests/minute (free tier)
- Docs: https://evds2.tcmb.gov.tr/index.php?/evds/userDocs

## Key Endpoints
- `GET /series={series_code}&startDate=DD-MM-YYYY&endDate=DD-MM-YYYY&type=json&key={api_key}` — Fetch time series data by series code
- `GET /serieList/{datagroup_code}?type=json&key={api_key}` — List series within a data group
- `GET /datagroups?mode=0&type=json&key={api_key}` — List all available data groups (categories)
- `GET /categories?type=json&key={api_key}` — Top-level category listing

Key series codes:
- `TP.DK.USD.A.YTL` — USD/TRY exchange rate (buying)
- `TP.DK.EUR.A.YTL` — EUR/TRY exchange rate (buying)
- `TP.FG.J0` — CPI general index (monthly)
- `TP.FG.J1` — CPI food and non-alcoholic beverages
- `TP.YNTBANKAM.POLITIKAFAIZ` — TCMB policy rate (one-week repo)
- `TP.PY.P1` — Overnight interbank rate
- `TP.AB.B1` — Current account balance
- `TP.PR.ARZ01` — Total FX reserves
- `TP.MBPAR.HM1` — M1 money supply
- `TP.MBPAR.HM2` — M2 money supply
- `TP.TUFE1YI.T1` — Annual CPI inflation rate (%)

## Key Indicators
- **Policy Interest Rate** — TCMB one-week repo rate (key EM rate signal)
- **USD/TRY Exchange Rate** — Daily official FX rate
- **CPI Inflation** — Monthly headline and core CPI (Turkey's chronic inflation monitor)
- **PPI Inflation** — Monthly producer price changes (leads CPI)
- **Current Account Balance** — Monthly, Turkey's structural deficit indicator
- **FX Reserves** — Weekly gross/net reserves (market confidence proxy)
- **Money Supply (M1/M2/M3)** — Monthly monetary aggregates
- **Interbank Overnight Rate** — Daily BIST overnight rate
- **Government Bond Yields** — Benchmark yields across maturities
- **Banking Credit Growth** — Total loans, consumer vs commercial breakdown
- **Gold Reserves** — Central bank gold holdings (Turkey is a major gold buyer)
- **Tourism Revenue** — Monthly tourism receipts (significant GDP contributor)

## Module
- Filename: `tcmb_evds.py`
- Cache: 1h for FX/rates, 24h for monthly series (CPI, money supply)
- Auth: Reads `TCMB_EVDS_API_KEY` from `.env`

## Test Commands
```bash
python modules/tcmb_evds.py                                    # Latest key indicators summary
python modules/tcmb_evds.py fx USD                              # USD/TRY exchange rate
python modules/tcmb_evds.py fx EUR                              # EUR/TRY exchange rate
python modules/tcmb_evds.py policy_rate                         # Current policy interest rate
python modules/tcmb_evds.py cpi                                 # CPI inflation latest
python modules/tcmb_evds.py reserves                            # FX reserves
python modules/tcmb_evds.py money_supply                        # M1/M2 monetary aggregates
python modules/tcmb_evds.py series TP.AB.B1 01-01-2024 01-01-2025  # Custom series with date range
python modules/tcmb_evds.py categories                          # List all data categories
```

## Acceptance
- [ ] Fetches exchange rates, policy rate, CPI, money supply, reserves, current account
- [ ] Returns structured JSON: date, value, indicator, series_code, unit, source
- [ ] Series discovery via data group and category listing
- [ ] Custom series query by code with date range filtering
- [ ] 1h cache for FX/rates, 24h for monthly indicators
- [ ] CLI: `python tcmb_evds.py [command] [args]`
- [ ] API key read from `.env` (TCMB_EVDS_API_KEY)
- [ ] Handles rate limiting (100 req/min) with exponential backoff
- [ ] Proper date format conversion (EVDS uses DD-MM-YYYY)
- [ ] Multi-series batch requests where supported
- [ ] Error handling for invalid series codes and empty date ranges
- [ ] Turkish character encoding handled correctly (UTF-8)
