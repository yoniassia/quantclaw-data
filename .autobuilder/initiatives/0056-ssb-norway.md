# 0056 — Statistics Norway (SSB) PxWeb API

## What
Build `ssb_norway.py` module for Statistics Norway (Statistisk sentralbyrå / SSB) — Norway's national statistics agency. SSB provides a PxWeb JSON API with open access to 5,000+ statistical tables covering GDP, CPI, oil production, labor, trade, housing, and population. Norway is the world's largest sovereign wealth fund manager (Government Pension Fund Global, $1.7T+) and a top-5 global oil/gas exporter.

## Why
Norway's economy is a bellwether for global energy markets. Petroleum production data from SSB directly impacts Brent crude pricing and European energy security models. The Government Pension Fund Global (Norges Bank Investment Management) is the largest single equity owner globally — Norwegian macro data affects allocation decisions that move markets worldwide. We have zero Nordic statistical coverage beyond Eurostat aggregates.

## API
- Base: `https://data.ssb.no/api/v0/en/table/`
- Protocol: PxWeb REST (POST JSON query to table endpoint)
- Auth: None (fully open, no key required)
- Formats: JSON-stat, JSON-stat2, CSV
- Rate limits: Fair use (no hard limit, but batch queries recommended)
- Docs: https://www.ssb.no/en/omssb/tjenester-og-verktoy/api/px-api

## Key Endpoints
- `POST /api/v0/en/table/09189` — GDP quarterly national accounts (production, expenditure, income)
- `POST /api/v0/en/table/03013` — Consumer Price Index (CPI) monthly, all items + subcategories
- `POST /api/v0/en/table/08531` — Registered unemployment by county and age (monthly)
- `POST /api/v0/en/table/11174` — Oil and gas production, monthly volumes (crude, NGL, condensate, gas)
- `POST /api/v0/en/table/08799` — External trade in goods, imports/exports by commodity (monthly)
- `POST /api/v0/en/table/07221` — House price index by region (quarterly)
- `POST /api/v0/en/table/09170` — Industrial production index (monthly)

Query body format:
```json
{
  "query": [
    {"code": "Tid", "selection": {"filter": "top", "values": ["12"]}}
  ],
  "response": {"format": "json-stat2"}
}
```

## Key Indicators
- **GDP** (table 09189) — Quarterly, real/nominal, by expenditure and production approach
- **CPI Inflation** (table 03013) — Monthly, all items + food, energy, housing subcategories
- **Unemployment** (table 08531) — Monthly registered unemployment rate by region
- **Oil & Gas Production** (table 11174) — Monthly crude oil, NGL, natural gas volumes (critical for energy models)
- **Trade Balance** (table 08799) — Monthly imports/exports, key for NOK FX models
- **House Prices** (table 07221) — Quarterly index by region (Oslo, Bergen, etc.)
- **Industrial Production** (table 09170) — Monthly manufacturing output index

## Module
- Filename: `ssb_norway.py`
- Cache: 24h (monthly/quarterly releases)
- Auth: None required

## Test Commands
```bash
python modules/ssb_norway.py                          # Latest key indicators summary
python modules/ssb_norway.py gdp                      # GDP quarterly
python modules/ssb_norway.py cpi                      # CPI inflation monthly
python modules/ssb_norway.py unemployment              # Unemployment rate
python modules/ssb_norway.py oil_production            # Oil & gas production volumes
python modules/ssb_norway.py trade                     # External trade balance
python modules/ssb_norway.py house_prices              # House price index
```

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, oil production, trade, house prices, industrial production
- [ ] Returns structured JSON: date, value, indicator, unit, source, table_id
- [ ] PxWeb POST query construction with proper filter syntax
- [ ] JSON-stat2 response parsing (dimension/value structure)
- [ ] Date range selection via Tid (time) dimension filtering
- [ ] 24h caching
- [ ] CLI: `python ssb_norway.py [indicator]`
- [ ] No API key required
- [ ] Handles PxWeb error responses (invalid table, no data for period)
- [ ] Supports both English and Norwegian table endpoints (`/en/` vs `/no/`)
