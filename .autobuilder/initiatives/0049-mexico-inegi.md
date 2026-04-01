# 0049 — Mexico INEGI Economic Indicators API

## What
Build `inegi_mexico.py` module for Mexico's Instituto Nacional de Estadística y Geografía (INEGI) — the national statistics office. The BIE (Banco de Información Económica) API provides GDP, inflation, employment, trade, and industrial production data. Mexico is the US's largest trading partner and a key nearshoring beneficiary.

## Why
Mexico macro data is essential for NAFTA/USMCA trade modeling, nearshoring investment thesis tracking, and LatAm portfolio construction. Currently we have zero Mexico coverage — a major gap given it's the world's 12th-largest economy and #1 US trade partner.

## API
- Base: `https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR`
- Protocol: REST
- Auth: Free API token (register at inegi.org.mx/app/api/indicadores/desarrolladores/)
- Formats: JSON, XML
- Rate limits: Fair use
- Docs: https://www.inegi.org.mx/app/api/indicadores/desarrolladores/

## Key Endpoints
- `/{indicator_id}/es/0700/false/BIE/2.0/{token}?type=json` — Fetch indicator time series
- Indicator IDs are numeric codes from the BIE catalog

## Key Indicators (BIE Codes)
- **6207059827** — GDP quarterly (volume index, base 2018)
- **628194** — INPC CPI monthly (general index)
- **444612** — Core inflation (annual % change)
- **444888** — Unemployment rate (national)
- **383152** — Industrial production index (manufacturing)
- **133396** — Total exports (USD millions)
- **133397** — Total imports (USD millions)
- **628208** — Consumer confidence index
- **383159** — Automotive production (vehicles)

## Module
- Filename: `inegi_mexico.py`
- Cache: 24h
- Auth: Free token from env var `INEGI_API_TOKEN`

## Test Commands
```bash
python modules/inegi_mexico.py                    # Latest values for all key indicators
python modules/inegi_mexico.py gdp                # GDP quarterly
python modules/inegi_mexico.py cpi                # CPI inflation
python modules/inegi_mexico.py unemployment       # Unemployment rate
python modules/inegi_mexico.py trade              # Exports + imports
python modules/inegi_mexico.py auto_production    # Automotive output
```

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, industrial production, trade, auto production
- [ ] Returns structured JSON: date, value, indicator, unit, source
- [ ] Uses INEGI_API_TOKEN from .env (free registration)
- [ ] Date range queries
- [ ] 24h caching
- [ ] CLI: `python inegi_mexico.py [indicator]`
- [ ] Error handling for invalid tokens, missing indicators
