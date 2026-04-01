# 0002 — INSEE France SDMX API

## What
Build `insee_france.py` for France's national statistics office.

## API
- Base: `https://api.insee.fr/series/BDM/V1`
- Protocol: SDMX REST
- Auth: Open (optional registration for higher limits)
- Formats: JSON, CSV, SDMX-ML

## Key Datasets
- GDP growth (quarterly)
- CPI / HICP inflation
- Unemployment rate
- Industrial production index
- Consumer confidence
- Household consumption
- Foreign trade balance

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, industrial production
- [ ] Handles SDMX response parsing
- [ ] 24h cache
- [ ] CLI testable
