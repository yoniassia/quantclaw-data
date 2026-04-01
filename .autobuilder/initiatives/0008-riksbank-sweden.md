# 0008 — Sveriges Riksbank API

## What
Build `riksbank_sweden.py` for Sweden's central bank.

## API
- Base: `https://api.riksbank.se` (new REST, replaces retired SOAP)
- Protocol: REST
- Auth: Open (portal registration for higher limits)
- Formats: JSON

## Key Datasets
- Policy rate (repo rate)
- FX rates (SEK vs major currencies)
- Securities statistics
- Payment statistics
- Financial stability indicators

## Acceptance
- [ ] Fetches policy rate history
- [ ] FX rates (SEK/EUR, SEK/USD, SEK/GBP)
- [ ] Securities data
- [ ] 24h cache, CLI testable
