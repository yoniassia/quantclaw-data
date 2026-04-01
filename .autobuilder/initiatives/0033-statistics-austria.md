# 0033 — Statistics Austria Open Data

## What
Build `statistics_austria.py` for Austria's statistics office.

## API
- Base: `https://data.statistik.gv.at` (Open Data portal)
- Protocol: REST / OGD (Open Government Data)
- Auth: Open
- Formats: JSON, CSV

## Key Datasets
- GDP growth
- CPI / HICP inflation
- Labour market
- Foreign trade
- Tourism statistics
- Industrial production

## Acceptance
- [ ] Open data catalog discovery
- [ ] Fetches GDP, CPI, labour
- [ ] 24h cache, CLI testable
