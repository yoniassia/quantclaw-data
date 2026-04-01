# 0027 — RBA Australia Enhanced (CSV feeds)

## What
Enhance existing `rba_economic_data_feed.py` with all available statistical tables.

## API
- Base: `https://www.rba.gov.au/statistics/tables/csv/`
- Protocol: Direct CSV download (stable URLs)
- Auth: Open
- Formats: CSV

## Key Tables to Add
- F1 — Interest Rates (cash rate target)
- F2 — Capital Market Yields
- F5 — Indicator Lending Rates
- F11 — Exchange Rates
- F13 — Monetary Aggregates
- D1 — Growth in Financial Aggregates
- H1 — Payments System

## Acceptance
- [ ] All major statistical table CSVs
- [ ] Proper date/value parsing
- [ ] 1h cache for rates, 24h for aggregates
- [ ] CLI testable
