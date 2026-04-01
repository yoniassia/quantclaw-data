# 0045 — INE Portugal Statistics

## What
Build `ine_portugal.py` for Portugal's national statistics institute.

## API
- Base: `https://www.ine.pt/xportal/` (web API / PxWeb variants)
- Protocol: REST / PxWeb
- Auth: Open
- Formats: JSON, CSV

## Key Datasets
- GDP growth
- CPI inflation
- Employment
- Tourism statistics
- Foreign trade
- Housing/construction

## Acceptance
- [ ] Data discovery
- [ ] Fetches GDP, CPI, labour
- [ ] 24h cache, CLI testable
