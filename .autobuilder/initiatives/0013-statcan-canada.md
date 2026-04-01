# 0013 — Statistics Canada WDS API

## What
Build `statcan_canada.py` for Canada's statistics office.

## API
- Base: `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action` (WDS)
- Protocol: REST
- Auth: Open
- Formats: JSON, CSV

## Endpoints
- `/getAllCubesList` — list all tables
- `/getDataFromCubePidCoordAndLatestNPeriods` — fetch data
- `/getCubeMetadata` — table metadata

## Key Datasets
- GDP
- CPI inflation
- Labour force survey
- Foreign trade
- Housing starts
- Retail sales

## Acceptance
- [ ] Table discovery
- [ ] Fetches GDP, CPI, labour, trade
- [ ] Handles WDS query format
- [ ] 24h cache, CLI testable
