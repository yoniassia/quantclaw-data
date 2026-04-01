# 0010 — Banco de España API

## What
Build `banco_de_espana.py` for Spain's central bank.

## API
- Base: `https://www.bde.es/webbe/es/estadisticas/recursos/descargas-completas.html` (bulk) + REST paths
- Protocol: REST JSON
- Auth: Open
- Formats: JSON, CSV

## Key Datasets
- Interest rates (lending, deposit, mortgage)
- Balance of payments
- Financial accounts
- Banking supervision aggregates
- Housing market indicators

## Acceptance
- [ ] Fetches interest rates and BoP data
- [ ] Handles BdE API format
- [ ] 24h cache, CLI testable
