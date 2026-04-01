# 0035 — Statistics Estonia (PxWeb)

## What
Build `statistics_estonia.py` for Estonia's statistics office.

## API
- Base: `https://andmed.stat.ee/api/v1/en/stat/`
- Protocol: PxWeb REST
- Auth: Open
- Formats: JSON-stat, px

## Key Datasets
- GDP
- CPI inflation
- Employment
- Foreign trade
- Industrial production

## Acceptance
- [ ] PxWeb navigation
- [ ] Fetches GDP, CPI, labour
- [ ] 24h cache, CLI testable
