# 0062 — Central Bank of Peru (BCRP) Statistics API

## What
Build `bcrp_peru.py` module for the Banco Central de Reserva del Perú (BCRP) Statistics API — Peru's central bank open data service providing free REST access to 15,000+ time series covering monetary policy, exchange rates, GDP, inflation, mining production, and trade balance. The API returns structured JSON with no authentication required.

## Why
Peru is the world's 2nd-largest copper producer and a top-3 silver/zinc/gold producer — Peruvian mining output data is a leading indicator for base metal futures and global industrial commodity models. The Peruvian sol (PEN) is a key Latin American FX pair used in carry trade strategies. BCRP's policy rate decisions ripple across Andean economies. Peru's statistics API is one of the best-documented in Latin America, yet QuantClaw has no coverage. Combined with existing Brazil (IBGE) and Mexico (INEGI) modules, this completes core LatAm coverage.

## API
- Base: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api`
- Protocol: REST (GET requests)
- Auth: None (fully open, no key required)
- Formats: JSON, CSV
- Rate limits: Fair use (no hard limit published)
- Docs: https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/api

## Key Endpoints
- `GET /{series_code}/json/{start_date}/{end_date}` — Fetch time series by code and date range
- `GET /PN00015MM/json/2024-1/2026-4` — Reference rate (BCRP policy rate)
- `GET /PN01234PM/json/2024-1/2026-4` — CPI Lima Metropolitan (monthly inflation)
- `GET /PN01207PQ/json/2024-1/2026-4` — Real GDP quarterly growth rate
- `GET /PN01129XD/json/2024-1/2026-4` — PEN/USD exchange rate (daily)
- `GET /PN38684BM/json/2024-1/2026-4` — Copper production volume (monthly)
- `GET /PN38705BM/json/2024-1/2026-4` — Gold production volume (monthly)
- `GET /PN02042BM/json/2024-1/2026-4` — Trade balance (monthly)

Date format: `YYYY-M` for monthly, `YYYY-Q` for quarterly, `YYYY-M-D` for daily.

## Key Indicators
- **BCRP Reference Rate** (PN00015MM) — Monetary policy rate, key for PEN FX and LatAm rate models
- **CPI Inflation** (PN01234PM) — Lima metro CPI, monthly, all items and subcategories
- **GDP Growth** (PN01207PQ) — Quarterly real GDP growth rate
- **PEN/USD Exchange Rate** (PN01129XD) — Daily sol/dollar rate
- **Copper Production** (PN38684BM) — Monthly copper output (critical for Cu futures models)
- **Gold Production** (PN38705BM) — Monthly gold output
- **Silver Production** (PN38706BM) — Monthly silver output
- **Trade Balance** (PN02042BM) — Monthly exports minus imports
- **International Reserves** (PN00048MM) — Monthly BCRP reserves position

## Module
- Filename: `bcrp_peru.py`
- Cache: 1h for FX rates, 24h for macro/mining data
- Auth: None required

## Test Commands
```bash
python modules/bcrp_peru.py                          # Latest key indicators summary
python modules/bcrp_peru.py reference_rate            # BCRP policy rate
python modules/bcrp_peru.py cpi                       # CPI inflation
python modules/bcrp_peru.py gdp                       # GDP growth quarterly
python modules/bcrp_peru.py fx                        # PEN/USD exchange rate
python modules/bcrp_peru.py copper_production         # Copper output volumes
python modules/bcrp_peru.py gold_production           # Gold output volumes
python modules/bcrp_peru.py trade_balance             # Trade balance
python modules/bcrp_peru.py reserves                  # International reserves
```

## Acceptance
- [ ] Fetches all key series: reference rate, CPI, GDP, FX, mining output, trade balance
- [ ] Returns structured JSON: date, value, indicator, series_code, unit, source
- [ ] Date range queries with proper format handling (daily/monthly/quarterly)
- [ ] Mining production data: copper, gold, silver volumes
- [ ] 1h cache for FX, 24h for macro/mining data
- [ ] CLI: `python bcrp_peru.py [indicator]`
- [ ] No API key required
- [ ] Handles BCRP API error responses (invalid series code, no data for period)
- [ ] Series code lookup for easy indicator discovery
- [ ] Supports both JSON and CSV output formats
