# 0016 — NBB Belgium (NBB.Stat SDMX)

## What
Build `nbb_belgium.py` for Belgium's central bank.

## API
- Base: `https://stat.nbb.be/restsdmx/sdmx.ashx`
- Protocol: SDMX 2.0/2.1
- Auth: Open
- Formats: SDMX-ML, JSON

## Key Datasets
- Balance of payments
- Financial accounts
- International investment position
- Money and banking
- Government finance statistics
- Business surveys

## Acceptance
- [ ] SDMX dataflow discovery
- [ ] Fetches BoP, financial accounts, banking
- [ ] Parses SDMX responses
- [ ] 24h cache, CLI testable
