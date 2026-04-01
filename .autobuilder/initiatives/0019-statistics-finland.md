# 0019 — Statistics Finland (PxWeb API)

## What
Build `statistics_finland.py` for Finland's statistics office.

## API
- Base: `https://pxdata.stat.fi/PXWeb/api/v1/en/StatFin/`
- Protocol: PxWeb REST
- Auth: Open
- Formats: JSON-stat, px

## Key Datasets
- GDP (quarterly national accounts)
- CPI inflation
- Employment / unemployment
- Industrial production
- Foreign trade
- Housing prices

## Acceptance
- [ ] PxWeb table navigation
- [ ] Fetches GDP, CPI, labour
- [ ] Handles PxWeb POST queries
- [ ] 24h cache, CLI testable
