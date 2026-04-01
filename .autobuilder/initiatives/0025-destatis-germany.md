# 0025 — Destatis / GENESIS-Online Germany

## What
Build `destatis_germany.py` for Germany's federal statistics office.

## API
- Base: `https://www-genesis.destatis.de/genesisWS/rest/2020/`
- Protocol: REST
- Auth: Free registration required
- Formats: JSON, CSV
- Store credentials in `.env` as `DESTATIS_USER` / `DESTATIS_PASSWORD`

## Key Datasets
- GDP (quarterly, annual)
- CPI / HICP inflation
- Labour market (employment, unemployment)
- Foreign trade
- Industrial production
- Producer price index
- Construction activity

## Acceptance
- [ ] Table search and metadata
- [ ] Fetches GDP, CPI, labour, trade
- [ ] Handles GENESIS auth
- [ ] Graceful fallback when no credentials
- [ ] 24h cache, CLI testable
