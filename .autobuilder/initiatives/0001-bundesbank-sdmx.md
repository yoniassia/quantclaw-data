# 0001 — Deutsche Bundesbank SDMX API

## What
Build `bundesbank_sdmx.py` module for Germany's central bank statistical data.

## API
- Base: `https://api.statistiken.bundesbank.de/rest`
- Protocol: SDMX 2.1 REST
- Auth: None (open)
- Formats: SDMX-JSON, SDMX-CSV, BBK-CSV, XML
- Rate limits: Fair use

## Key Datasets
- Interest rates (money market, bank lending, deposit)
- Securities issues and holdings
- Balance of payments
- External position
- Banking statistics (aggregated)
- Financial accounts

## Indicators to Implement
- Policy-relevant rates (deposit facility, main refinancing)
- German government bond yields (1Y, 2Y, 5Y, 10Y, 30Y)
- Bank lending rates to households and corporates
- Money supply contributions
- Current account balance

## Acceptance
- [ ] Fetches at least 10 series via SDMX-JSON
- [ ] Caching (24h)
- [ ] CLI: `python bundesbank_sdmx.py [series_key]`
- [ ] Error handling for unavailable series
