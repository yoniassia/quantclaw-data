# 0065 — Philippine Statistics Authority (PSA) OpenSTAT

## What
Build `psa_philippines.py` module for the Philippine Statistics Authority OpenSTAT API — the Philippines' official open data portal providing access to GDP, CPI, labor force statistics, trade, agricultural production, and population data. PSA uses the PxWeb API framework, returning structured JSON with no authentication required. The Philippines is the 34th-largest economy and the fastest-growing major ASEAN economy.

## Why
The Philippines is a $450B+ economy with 115M people — one of Asia's fastest-growing consumer markets and a massive BPO/remittance hub. Overseas Filipino Worker (OFW) remittances (~$37B/year, 9% of GDP) are a unique macro signal that correlates with USD/PHP FX moves, consumer spending, and real estate demand. Philippine GDP growth consistently outpaces ASEAN peers, making it a key EM investment destination. Agricultural production data (rice, coconut, sugar) feeds into Southeast Asian food commodity models. Combined with the BNM Malaysia module, this establishes meaningful ASEAN coverage for QuantClaw.

## API
- Base: `https://openstat.psa.gov.ph/PXWeb/api/v1/en/`
- Protocol: PxWeb REST (POST JSON query to table endpoint)
- Auth: None (fully open, no key required)
- Formats: JSON-stat, JSON-stat2, CSV
- Rate limits: Fair use (no hard limit, batch queries recommended)
- Docs: https://openstat.psa.gov.ph/

## Key Endpoints
- `POST /PN/TS/NA/NA_AE/0012008.px` — GDP at constant prices by expenditure (quarterly)
- `POST /PN/TS/PR/PR_CPI/0012001.px` — Consumer Price Index (monthly, all items + subcategories)
- `POST /PN/TS/LF/LFS/0012001.px` — Labor force survey: employment, unemployment rate (quarterly)
- `POST /PN/TS/FT/FT_MER/0012001.px` — Merchandise trade: imports and exports (monthly)
- `POST /PN/TS/AG/AG_CR/0012001.px` — Agricultural crop production (quarterly)
- `POST /PN/TS/PR/PR_PPI/0012001.px` — Producer Price Index (quarterly)
- `POST /PN/TS/OF/OFW_REMIT/0012001.px` — Overseas Filipino Worker remittance statistics

PxWeb query body format:
```json
{
  "query": [
    {"code": "Year and Quarter", "selection": {"filter": "top", "values": ["8"]}}
  ],
  "response": {"format": "json-stat2"}
}
```

## Key Indicators
- **GDP Growth** — Quarterly real GDP by expenditure, production approach
- **CPI Inflation** — Monthly, all items + food, housing, transport, education subcategories
- **Unemployment Rate** — Quarterly labor force survey (employment, underemployment)
- **OFW Remittances** — Overseas worker cash remittances (monthly, unique signal)
- **Trade Balance** — Monthly merchandise imports/exports by commodity
- **Agricultural Production** — Rice, coconut, sugarcane, corn output (quarterly)
- **Producer Price Index** — Quarterly PPI for manufacturing and agriculture
- **Population** — Annual/quarterly demographic updates

## Module
- Filename: `psa_philippines.py`
- Cache: 24h (monthly/quarterly releases)
- Auth: None required

## Test Commands
```bash
python modules/psa_philippines.py                          # Latest key indicators summary
python modules/psa_philippines.py gdp                      # GDP quarterly growth
python modules/psa_philippines.py cpi                      # CPI inflation monthly
python modules/psa_philippines.py unemployment              # Unemployment rate quarterly
python modules/psa_philippines.py remittances               # OFW remittance data
python modules/psa_philippines.py trade                     # Trade balance monthly
python modules/psa_philippines.py agriculture               # Crop production data
python modules/psa_philippines.py ppi                       # Producer Price Index
```

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, remittances, trade, agriculture, PPI
- [ ] Returns structured JSON: date, value, indicator, unit, source, table_id
- [ ] PxWeb POST query construction with proper filter syntax
- [ ] JSON-stat2 response parsing (dimension/value structure)
- [ ] OFW remittance data extraction (unique Philippine macro signal)
- [ ] Date range selection via time dimension filtering
- [ ] 24h caching
- [ ] CLI: `python psa_philippines.py [indicator]`
- [ ] No API key required
- [ ] Handles PxWeb error responses (invalid table, no data for period)
- [ ] Table discovery endpoint for browsing available datasets
- [ ] Properly handles Philippine-specific time period formatting
