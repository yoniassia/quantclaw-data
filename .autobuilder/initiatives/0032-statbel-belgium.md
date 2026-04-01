# 0032 — Statbel Belgium Open Data

## What
Build `statbel_belgium.py` for Belgium's statistics office.

## API
- Base: `https://statbel.fgov.be/en/open-data`
- Protocol: REST / CSV downloads
- Auth: Open
- Formats: CSV, JSON

## Key Datasets
- CPI inflation
- GDP growth
- Employment / unemployment
- Population statistics
- Foreign trade
- Consumer confidence

## Acceptance
- [ ] Open data catalog queries
- [ ] Fetches CPI, GDP, labour
- [ ] 24h cache, CLI testable
