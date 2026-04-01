# 0026 — ABS Australia Enhanced (SDMX 2.1)

## What
Enhance existing `abs_australia_stats.py` with full SDMX 2.1 API coverage.

## API
- Base: `https://api.data.abs.gov.au/data/`
- Protocol: SDMX 2.1
- Auth: Open (optional key for production)
- Formats: SDMX-JSON, CSV

## Key Datasets to Add
- GDP (quarterly national accounts)
- CPI (quarterly)
- Labour force (monthly)
- Balance of payments
- Retail trade
- Building approvals
- International trade

## Acceptance
- [ ] SDMX dataflow discovery
- [ ] Fetches 7+ key macro indicators
- [ ] Proper SDMX response parsing
- [ ] 24h cache, CLI testable
