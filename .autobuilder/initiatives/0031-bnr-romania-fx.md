# 0031 — BNR Romania FX Rates (XML Feed)

## What
Build `bnr_romania.py` for Romania's central bank FX rates.

## API
- Base: `https://www.bnr.ro/nbrfxrates.xml` (daily), `https://www.bnr.ro/nbrfxrates10days.xml`
- Protocol: XML feeds (stable, well-structured)
- Auth: Open
- Formats: XML

## Key Datasets
- Daily FX rates (RON vs 30+ currencies)
- 10-day FX history
- Annual archives

## Acceptance
- [ ] Parses daily XML feed
- [ ] 10-day history
- [ ] All available currency pairs
- [ ] 1h cache for FX
- [ ] CLI testable
