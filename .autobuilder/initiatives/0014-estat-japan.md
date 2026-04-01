# 0014 — e-Stat Japan API

## What
Build `estat_japan.py` for Japan's statistics portal.

## API
- Base: `https://api.e-stat.go.jp/rest/3.0/app`
- Protocol: REST
- Auth: Application ID (free registration at e-stat.go.jp)
- Formats: JSON, XML, CSV
- Store key in `.env` as `ESTAT_JAPAN_APP_ID`

## Key Datasets
- GDP (SNA)
- CPI
- Labour force survey
- Industrial production
- Trade statistics
- Housing starts
- Machinery orders

## Acceptance
- [ ] Table search via /getStatsList
- [ ] Fetches GDP, CPI, labour, industrial production
- [ ] Handles e-Stat app ID auth
- [ ] Graceful fallback when no key
- [ ] 24h cache, CLI testable
