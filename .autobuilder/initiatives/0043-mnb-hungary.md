# 0043 — MNB Hungary Statistics

## What
Build `mnb_hungary.py` for Hungary's central bank.

## API
- Base: `https://statisztika.mnb.hu/` (interactive database)
- Protocol: SOAP/file exports
- Auth: Open
- Formats: Excel, CSV

## Key Datasets
- Policy rate (base rate)
- FX rates (HUF)
- Government bond yields
- Banking sector statistics
- Balance of payments

## Acceptance
- [ ] Key interest rates
- [ ] FX rates
- [ ] Banking aggregates
- [ ] 24h cache, CLI testable
