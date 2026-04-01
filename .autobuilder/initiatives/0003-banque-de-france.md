# 0003 — Banque de France Webstat API

## What
Build `banque_de_france.py` for France's central bank data portal.

## API
- Base: `https://webstat.banque-france.fr/api/v1` (check developer.webstat.banque-france.fr)
- Protocol: REST (JSON, CSV, XLSX)
- Auth: Free registration required (API key)
- Note: Store key in `.env` as `BANQUE_DE_FRANCE_API_KEY`

## Key Datasets
- Credit to non-financial sector
- Balance of payments
- French corporate balance sheets
- Insurance sector statistics
- Regional economic indicators
- Household financial assets

## Acceptance
- [ ] Connects with API key from env
- [ ] Fetches credit, BoP, corporate data
- [ ] Graceful fallback when no key
- [ ] CLI testable
