# 0006 — Statistics Denmark (DST) API

## What
Build `statistics_denmark.py` for Denmark's statistics office.

## API
- Base: `https://api.statbank.dk/v1`
- Protocol: REST (POST for data queries)
- Auth: Open
- Formats: JSON, CSV, SDMX

## Key Datasets
- GDP (quarterly national accounts)
- CPI inflation
- Unemployment and labour force
- Foreign trade
- Housing prices
- Consumer confidence
- Industrial production

## Acceptance
- [ ] Table discovery via /tables endpoint
- [ ] Fetches GDP, CPI, labour, trade data
- [ ] Handles DST API query format
- [ ] 24h cache, CLI testable
