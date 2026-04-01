# 0030 — INE Spain Statistics API

## What
Build `ine_spain.py` for Spain's national statistics institute.

## API
- Base: `https://servicios.ine.es/wstempus/js/EN/`
- Protocol: REST JSON
- Auth: Open
- Formats: JSON

## Key Datasets
- GDP (quarterly national accounts)
- CPI inflation
- Labour force survey (EPA)
- Industrial production
- Foreign trade
- Housing price index
- Active population survey

## Acceptance
- [ ] Operation/series discovery
- [ ] Fetches GDP, CPI, labour, housing
- [ ] Handles INE JSON format
- [ ] 24h cache, CLI testable
