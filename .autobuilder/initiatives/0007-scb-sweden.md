# 0007 — SCB Sweden (PxWeb API)

## What
Build `scb_sweden.py` for Sweden's statistics office.

## API
- Base: `https://api.scb.se/OV0104/v1/doris/en/ssd/`
- Protocol: PxWeb REST (POST with query JSON)
- Auth: Open
- Formats: JSON-stat, px

## Key Datasets
- GDP growth
- CPI / CPIF inflation
- Unemployment
- Housing price index
- Industrial production
- Foreign trade
- Government budget

## Acceptance
- [ ] PxWeb table navigation
- [ ] Fetches GDP, CPI, labour
- [ ] Handles PxWeb POST query format
- [ ] 24h cache, CLI testable
