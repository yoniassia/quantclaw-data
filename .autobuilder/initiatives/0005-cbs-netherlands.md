# 0005 — CBS Netherlands StatLine API

## What
Build `cbs_netherlands.py` for Netherlands' statistics office.

## API
- Base: `https://opendata.cbs.nl/ODataApi/odata/` (v3) or `https://odata4.cbs.nl/CBS/` (v4)
- Protocol: OData REST
- Auth: Open
- Formats: JSON

## Key Datasets
- GDP growth
- CPI inflation
- Labour market (employment, vacancies)
- Housing prices
- Foreign trade
- Government finance
- Consumer/producer confidence

## Acceptance
- [ ] OData catalog discovery
- [ ] Fetches GDP, CPI, labour, housing
- [ ] Handles OData pagination
- [ ] 24h cache, CLI testable
