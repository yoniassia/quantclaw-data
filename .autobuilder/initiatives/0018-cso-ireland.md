# 0018 — CSO Ireland (PxWeb API)

## What
Build `cso_ireland.py` for Ireland's statistics office.

## API
- Base: `https://data.cso.ie/api/v1` or PxStat JSON-stat
- Protocol: PxWeb / JSON-stat
- Auth: Open
- Formats: JSON, CSV

## Key Datasets
- GDP / GNI* (Modified GNI)
- CPI / HICP inflation
- Labour force survey
- Retail sales
- Housing statistics
- Foreign trade

## Acceptance
- [ ] Table discovery
- [ ] Fetches GDP, CPI, labour
- [ ] Handles PxStat format
- [ ] 24h cache, CLI testable
