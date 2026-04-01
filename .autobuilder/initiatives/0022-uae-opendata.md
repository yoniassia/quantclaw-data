# 0022 — UAE Open Data + CBUAE

## What
Build `uae_data.py` for UAE central bank and open data portal.

## API
- CBUAE: `https://www.centralbank.ae` (downloads)
- UAE Open Data: `https://opendata.fcsc.gov.ae` (REST JSON)
- Auth: Open
- Formats: JSON, Excel

## Key Datasets
- Monetary aggregates
- Banking system statistics
- Interest rates (EIBOR)
- FX reserves
- GDP, CPI from open data portal
- Trade statistics

## Acceptance
- [ ] CBUAE key indicators
- [ ] Open data portal JSON queries
- [ ] 24h cache, CLI testable
