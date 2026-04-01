# 0052 — Colombia DANE SDMX API

## What
Build `dane_colombia.py` module for Colombia's Departamento Administrativo Nacional de Estadística (DANE) — the national statistics office. DANE publishes all major Colombian economic indicators via an SDMX REST API. Colombia is Latin America's 4th-largest economy, a major oil/coal exporter, and an increasingly important EM debt market.

## Why
Colombian GDP, CPI, unemployment, and industrial production are key inputs for EM fixed income models, commodity price forecasting (oil, coal, coffee), and Andean region allocation. We have Brazil (IBGE) and Mexico (INEGI) but zero Andean coverage. Colombia is the missing piece for LatAm macro completeness.

## API
- Base: `https://sdmx.dane.gov.co/gateway/rest`
- Protocol: SDMX REST 2.1
- Auth: None (fully open, no key required)
- Formats: SDMX-JSON, SDMX-ML (XML)
- Rate limits: Fair use
- Docs: https://sdmx.dane.gov.co/

## Key Endpoints
- `GET /data/{flow_id}/{key}` — Fetch data by dataflow and key
- `GET /dataflow/DANE` — List all available dataflows
- `GET /datastructure/DANE/{dsd_id}` — Data structure definitions
- `GET /codelist/DANE/{codelist_id}` — Code list lookups
- Headers: `Accept: application/vnd.sdmx.data+json;version=1.0.0`

## Key Dataflows & Indicators
- **PIB_PRODUCCION** — GDP by production approach (quarterly)
- **IPC** — Consumer Price Index / inflation (monthly)
- **GEIH** — Gran Encuesta Integrada de Hogares — unemployment rate (monthly)
- **EMM** — Encuesta Mensual Manufacturera — industrial production (monthly)
- **EAM** — Encuesta Anual Manufacturera — annual manufacturing survey
- **BALANZA_COMERCIAL** — Trade balance (exports/imports monthly)
- **IPP** — Producer Price Index (monthly)

## Module
- Filename: `dane_colombia.py`
- Cache: 24h (monthly/quarterly releases)

## Test Commands
```bash
python modules/dane_colombia.py                       # Latest values for all key indicators
python modules/dane_colombia.py gdp                   # GDP quarterly
python modules/dane_colombia.py cpi                   # CPI inflation monthly
python modules/dane_colombia.py unemployment          # Unemployment rate
python modules/dane_colombia.py industrial_production # Manufacturing output
python modules/dane_colombia.py trade_balance         # Exports/imports
```

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, industrial production, trade balance, PPI
- [ ] Returns structured JSON: date, value, indicator, unit, source
- [ ] SDMX query with date range filtering
- [ ] 24h caching
- [ ] CLI: `python dane_colombia.py [indicator]`
- [ ] Parses SDMX-JSON response format correctly
- [ ] Handles DANE's period format (quarterly and monthly)
- [ ] Error handling for unavailable dataflows/periods
