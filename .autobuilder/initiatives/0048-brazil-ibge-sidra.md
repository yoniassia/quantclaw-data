# 0048 — Brazil IBGE SIDRA API

## What
Build `ibge_brazil.py` module for Brazil's Instituto Brasileiro de Geografia e Estatística (IBGE) — the official national statistics agency. The SIDRA (Sistema IBGE de Recuperação Automática) API provides programmatic access to all major Brazilian economic indicators. Brazil is Latin America's largest economy and a major commodity exporter.

## Why
Brazil GDP, inflation (IPCA), employment, and industrial production are critical for EM macro models, commodity price forecasting (soybeans, iron ore, beef), and LatAm portfolio allocation. Currently we have BCB (central bank rates) and B3 (exchange data) but no IBGE macro statistics.

## API
- Base: `https://servicodados.ibge.gov.br/api/v3/agregados`
- Protocol: REST
- Auth: None (fully open, no key required)
- Formats: JSON
- Rate limits: Fair use
- Docs: https://servicodados.ibge.gov.br/api/docs/agregados

## Key Endpoints
- `/agregados` — List all available surveys/tables
- `/agregados/{table_id}/periodos` — Available time periods
- `/agregados/{table_id}/variaveis/{var_id}` — Fetch indicator data with date/location filters
- Query params: `localidades=N1[all]` (national), `periodos=-12` (last 12 periods)

## Key Tables & Indicators
- **Table 5932** — GDP quarterly (var 6561: chained volume index)
- **Table 1737** — IPCA monthly inflation (var 63: monthly % change, var 69: 12-month cumulative)
- **Table 6381** — PNAD Contínua unemployment (var 4099: unemployment rate)
- **Table 8159** — Industrial production PIM-PF (var 12607: monthly % change)
- **Table 1846** — Retail sales PMC (var 56: monthly % change)
- **Table 1621** — Foreign trade (exports/imports)

## Module
- Filename: `ibge_brazil.py`
- Cache: 24h (monthly/quarterly releases)

## Test Commands
```bash
python modules/ibge_brazil.py                       # Latest values for all key indicators
python modules/ibge_brazil.py gdp                   # GDP quarterly
python modules/ibge_brazil.py ipca                  # IPCA inflation monthly
python modules/ibge_brazil.py unemployment          # PNAD unemployment rate
python modules/ibge_brazil.py industrial_production # PIM-PF industrial output
```

## Acceptance
- [ ] Fetches GDP, IPCA, unemployment, industrial production, retail sales
- [ ] Returns structured JSON: date, value, indicator, unit, source
- [ ] Date range queries (periodos parameter)
- [ ] 24h caching
- [ ] CLI: `python ibge_brazil.py [indicator]`
- [ ] Handles IBGE's period format (YYYYMM for monthly, YYYYQQ for quarterly)
- [ ] Error handling for unavailable tables/periods
