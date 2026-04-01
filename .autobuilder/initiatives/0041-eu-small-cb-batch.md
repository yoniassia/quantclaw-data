# 0041 — EU Small Central Banks Batch (CSV/Excel Sources)

## What
Build `eu_small_central_banks.py` — unified module for smaller EU central banks that only offer file downloads.

## Countries Covered
- Bulgaria (BNB) — bnb.bg
- Croatia (HNB) — hnb.hr
- Cyprus (CBC) — centralbank.cy
- Latvia (Latvijas Banka) — bank.lv
- Lithuania (Lietuvos bankas) — lb.lt
- Luxembourg (BCL) — bcl.lu
- Malta (CBM) — centralbankmalta.org
- Slovakia (NBS) — nbs.sk
- Slovenia (Banka Slovenije) — bsi.si

## Pattern
One module with per-country fetchers, shared caching and formatting.

## Key Datasets Per Country
- FX rates (where applicable)
- Interest rates
- Banking statistics aggregates
- Monetary indicators

## Acceptance
- [ ] At least 3 indicators per country
- [ ] Handles CSV/Excel parsing (pandas)
- [ ] 24h cache
- [ ] CLI: `python eu_small_central_banks.py [country] [indicator]`
