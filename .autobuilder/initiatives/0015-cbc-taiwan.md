# 0015 — CBC Taiwan API

## What
Build `cbc_taiwan.py` for Taiwan's central bank.

## API
- Base: `https://cpx.cbc.gov.tw/API/DataAPI/Get`
- Protocol: REST
- Auth: Open (verify ToS)
- Formats: JSON

## Key Datasets
- FX rates (TWD vs major currencies)
- Monetary aggregates (M1B, M2)
- Interest rates (discount rate, deposit rates)
- Financial institution statistics
- Reserve assets

## Acceptance
- [ ] Fetches FX rates
- [ ] Monetary aggregates
- [ ] Interest rate history
- [ ] 24h cache, CLI testable
