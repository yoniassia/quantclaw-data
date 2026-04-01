# 0029 — DNB Netherlands Statistics API

## What
Build `dnb_netherlands.py` for Netherlands' central bank.

## API
- Base: `https://api.portal.dnb.nl/` (subscription key required)
- Protocol: REST JSON
- Auth: Free My DNB registration + subscription key
- Formats: JSON
- Store key in `.env` as `DNB_SUBSCRIPTION_KEY`

## Key Datasets
- Balance sheet statistics
- Insurance/pension fund data
- Payment statistics
- Financial stability indicators

## Acceptance
- [ ] Connects with subscription key
- [ ] Fetches banking, insurance, payments data
- [ ] Graceful fallback when no key
- [ ] 24h cache, CLI testable
