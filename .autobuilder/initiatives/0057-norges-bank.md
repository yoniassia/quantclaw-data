# 0057 — Norges Bank SDMX REST API

## What
Build `norges_bank.py` module for Norges Bank — Norway's central bank. Norges Bank provides an SDMX REST API with exchange rates (40+ currency pairs against NOK), the key policy rate history, interbank rates (NIBOR), and monetary statistics. This complements `ssb_norway.py` (macro stats) with monetary policy and FX data.

## Why
Norges Bank manages the world's largest sovereign wealth fund ($1.7T+ Government Pension Fund Global) and sets monetary policy for a major oil-exporting economy. NOK is one of the most traded commodity-linked currencies in FX markets. NIBOR rates are the benchmark for Nordic fixed income. The key policy rate decisions move Scandinavian bond and FX markets. We currently have zero Norwegian monetary data coverage.

## API
- Base: `https://data.norges-bank.no/api/data/`
- Protocol: SDMX REST 2.1
- Auth: None (fully open, no key required)
- Formats: SDMX-JSON, CSV, XML
- Rate limits: Fair use (no hard limit)
- Docs: https://app.norges-bank.no/query/index.html

## Key Endpoints
- `GET /EXR/B.USD.NOK.SP?format=sdmx-json&startPeriod=2024-01&endPeriod=2026-04` — USD/NOK daily exchange rate
- `GET /EXR/B.EUR.NOK.SP?format=sdmx-json&lastNObservations=30` — EUR/NOK last 30 observations
- `GET /EXR/B..NOK.SP?format=sdmx-json&lastNObservations=1` — All currency pairs, latest rate
- `GET /KPRA/B.KPRA?format=sdmx-json` — Key policy rate (folio rate) full history
- `GET /NIBOR/B.NIBOR1W+NIBOR1M+NIBOR3M+NIBOR6M?format=sdmx-json&lastNObservations=30` — NIBOR interbank rates by tenor

SDMX key structure: `{frequency}.{currency}.{base_currency}.{series_type}`

## Key Indicators
- **USD/NOK Exchange Rate** (EXR/B.USD.NOK.SP) — Daily spot rate
- **EUR/NOK Exchange Rate** (EXR/B.EUR.NOK.SP) — Daily spot rate (most traded NOK pair)
- **GBP/NOK, SEK/NOK, DKK/NOK** — Cross rates for Nordic/European pairs
- **Key Policy Rate** (KPRA/B.KPRA) — Norges Bank folio rate, changed ~6x/year
- **NIBOR 1W/1M/3M/6M** (NIBOR/B.NIBOR*) — Norwegian Interbank Offered Rate by tenor
- **I44 Trade-Weighted Index** (EXR/B.I44.NOK.SP) — Import-weighted NOK effective exchange rate

## Module
- Filename: `norges_bank.py`
- Cache: 1h for FX rates, 24h for policy rate history
- Auth: None required

## Test Commands
```bash
python modules/norges_bank.py                          # Latest key rates summary
python modules/norges_bank.py fx USD                   # USD/NOK exchange rate
python modules/norges_bank.py fx EUR                   # EUR/NOK exchange rate
python modules/norges_bank.py fx_all                   # All currency pairs latest
python modules/norges_bank.py policy_rate              # Key policy rate history
python modules/norges_bank.py nibor                    # NIBOR term structure
python modules/norges_bank.py i44                      # Trade-weighted NOK index
```

## Acceptance
- [ ] Fetches daily FX rates for 40+ currency pairs against NOK
- [ ] Returns structured JSON: date, value, currency_pair, indicator, source
- [ ] Key policy rate history with decision dates
- [ ] NIBOR term structure (1W, 1M, 3M, 6M tenors)
- [ ] I44 trade-weighted exchange rate index
- [ ] SDMX-JSON response parsing (dimension/observation structure)
- [ ] Date range queries via startPeriod/endPeriod
- [ ] lastNObservations support for latest-N queries
- [ ] 1h cache for FX, 24h for policy rate
- [ ] CLI: `python norges_bank.py [command] [args]`
- [ ] No API key required
- [ ] Handles SDMX error responses and empty series
