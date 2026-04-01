# 0021 — Czech National Bank ARAD API

## What
Build `cnb_czech.py` for Czech Republic's central bank time-series system.

## API
- Base: `https://www.cnb.cz/arad/` (ARAD system)
- Also: `https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/` (FX TXT)
- Protocol: REST JSON (ARAD requires free registration + API key)
- Auth: Free registration for ARAD; FX text feed is open
- Formats: JSON (ARAD), TXT/CSV (FX)

## Key Datasets
- FX rates (CZK daily fixing)
- Interest rates (2W repo rate, discount, Lombard)
- Financial market indicators
- Monetary statistics

## Acceptance
- [ ] Open FX feed (no key)
- [ ] ARAD series with API key when available
- [ ] 1h cache for FX, 24h for rates
- [ ] CLI testable
