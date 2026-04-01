# 0020 — Danmarks Nationalbank StatBank API

## What
Build `danmarks_nationalbank.py` for Denmark's central bank.

## API
- Base: Uses Statistics Denmark StatBank: `https://api.statbank.dk/v1`
- Also: Own data at nationalbanken.dk/en/statistics
- Protocol: REST (JSON, XML, CSV)
- Auth: Open
- Formats: JSON, CSV, SDMX

## Key Datasets
- Interest rates (policy rate, lending facility)
- FX rates (DKK vs major currencies, EUR/DKK peg)
- Government securities yields
- Balance of payments
- MFI balance sheets
- Financial stability indicators

## Acceptance
- [ ] Fetches policy rates and FX
- [ ] Government bond yields
- [ ] BoP data
- [ ] 24h cache, CLI testable
