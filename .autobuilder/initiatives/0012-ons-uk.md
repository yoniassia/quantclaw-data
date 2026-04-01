# 0012 — ONS UK API

## What
Build `ons_uk.py` for UK Office for National Statistics.

## API
- Base: `https://api.beta.ons.gov.uk/v1`
- Protocol: REST
- Auth: Open (beta)
- Formats: JSON

## Key Datasets
- GDP (monthly, quarterly)
- CPI / RPI inflation
- Employment / unemployment
- Retail sales
- Trade balance
- House price index
- PMI equivalent data

## Acceptance
- [ ] Dataset discovery via /datasets
- [ ] Fetches GDP, CPI, labour, retail
- [ ] Handles ONS API filtering
- [ ] 24h cache, CLI testable
