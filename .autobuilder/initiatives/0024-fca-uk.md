# 0024 — FCA UK Register API

## What
Build `fca_uk.py` for UK's financial services regulator public register.

## API
- Base: FCA Register Search API (developer portal)
- Protocol: REST JSON
- Auth: Free API key (developer registration)
- Store key in `.env` as `FCA_API_KEY`

## Key Datasets
- Authorized firms register
- Approved individuals
- Prohibited individuals
- Temporary permissions
- Passported firms

## Acceptance
- [ ] Firm search by name/FRN
- [ ] Individual search
- [ ] Status checks
- [ ] Graceful fallback when no key
- [ ] 24h cache, CLI testable
