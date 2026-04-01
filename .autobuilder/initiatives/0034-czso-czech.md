# 0034 — CZSO Czech Republic Statistics

## What
Build `czso_czech.py` for Czech Republic's statistics office.

## API
- Base: `https://vdb.czso.cz/pll/eweb/` (open data portal)
- Protocol: REST / Open Data
- Auth: Open
- Formats: JSON, CSV

## Key Datasets
- GDP growth
- CPI inflation
- Labour market
- Industrial production
- Foreign trade
- Housing/construction

## Acceptance
- [ ] Data catalog queries
- [ ] Fetches GDP, CPI, labour
- [ ] 24h cache, CLI testable
