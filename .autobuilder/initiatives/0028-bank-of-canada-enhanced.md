# 0028 — Bank of Canada Valet Enhanced

## What
Enhance existing `bank_of_canada*.py` modules with full Valet API coverage.

## API
- Base: `https://www.bankofcanada.ca/valet`
- Protocol: REST
- Auth: Open
- Formats: JSON, CSV, XML

## Key Series to Add
- Policy interest rate history
- Government of Canada bond yields (all maturities)
- Treasury bill yields
- Exchange rates (CAD vs 26 currencies)
- Financial conditions index
- Business outlook survey

## Acceptance
- [ ] Full bond yield curve
- [ ] All available FX pairs
- [ ] Financial conditions index
- [ ] 1h cache for FX, 24h for yields
- [ ] CLI testable
