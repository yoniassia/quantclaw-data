# 0009 — NBP Poland API

## What
Build `nbp_poland.py` for Poland's central bank.

## API
- Base: `https://api.nbp.pl/api`
- Protocol: REST
- Auth: Open
- Formats: JSON, XML

## Key Datasets
- Exchange rates (Table A: mid rates, Table B: minor currencies, Table C: buy/sell)
- Gold prices
- Reference rate

## Endpoints
- `/exchangerates/tables/{table}/` — full rate table
- `/exchangerates/rates/{table}/{code}/` — single currency
- `/cenypokojow/api/` — gold prices

## Acceptance
- [ ] All 3 exchange rate tables
- [ ] Gold prices
- [ ] Date range queries
- [ ] 1h cache for FX, 24h for gold
- [ ] CLI testable
