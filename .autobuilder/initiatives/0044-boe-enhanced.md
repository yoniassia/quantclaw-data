# 0044 — Bank of England IADB Enhanced

## What
Enhance existing `bank_of_england*.py` with full Interactive Statistical Database (IADB) coverage.

## API
- Base: `https://www.bankofengland.co.uk/boeapps/database/` (CSV construction)
- Protocol: CSV via URL parameters
- Auth: Open

## Key Series to Add
- Full yield curve (all maturities)
- Money supply (M4, M4 lending)
- Bank Rate history (full)
- Mortgage rates (fixed, variable)
- Consumer credit
- FX rates (GBP vs major)
- Real effective exchange rate

## Acceptance
- [ ] Adds 10+ new series
- [ ] Full yield curve data
- [ ] Money supply aggregates
- [ ] No breaking changes
- [ ] CLI testable
