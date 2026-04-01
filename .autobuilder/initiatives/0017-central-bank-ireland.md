# 0017 — Central Bank of Ireland Open Data

## What
Build `central_bank_ireland.py` for Ireland's central bank.

## API
- Base: `https://opendata.centralbank.ie`
- Protocol: REST
- Auth: Open
- Formats: CSV, XLSX, JSON-stat

## Key Datasets
- Money and banking statistics
- Interest rates (lending, deposit)
- FX rates
- Payment statistics
- Securities issues
- Insurance statistics

## Acceptance
- [ ] Dataset discovery
- [ ] Fetches interest rates, banking, payments
- [ ] Parses JSON-stat format
- [ ] 24h cache, CLI testable
