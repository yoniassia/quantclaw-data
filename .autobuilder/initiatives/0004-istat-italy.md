# 0004 — ISTAT Italy SDMX API

## What
Build `istat_italy.py` for Italy's national statistics institute.

## API
- Base: `https://esploradati.istat.it/SDMXWS/rest`
- Protocol: SDMX 2.1 REST + SOAP
- Auth: Open
- Formats: SDMX-ML, CSV

## Key Datasets
- GDP (quarterly national accounts)
- CPI inflation (NIC, FOI, IPCA)
- Labour market (employment, unemployment)
- Industrial production
- Foreign trade
- Government debt/deficit
- Business confidence

## Acceptance
- [ ] SDMX dataflow discovery
- [ ] Fetches GDP, CPI, unemployment
- [ ] Parses SDMX XML responses
- [ ] 24h cache, CLI testable
