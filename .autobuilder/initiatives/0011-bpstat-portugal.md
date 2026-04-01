# 0011 — Banco de Portugal BPstat API

## What
Build `banco_de_portugal.py` for Portugal's central bank statistics.

## API
- Base: `https://bpstat.bportugal.pt/data/v1`
- Protocol: REST (JSON-stat)
- Auth: Open
- Formats: JSON-stat
- ~72,000 series available

## Key Datasets
- Interest rates
- Balance of payments
- Financial accounts
- Credit conditions
- Banking system indicators
- FX rates

## Acceptance
- [ ] Series discovery
- [ ] Fetches interest rates, BoP, banking data
- [ ] Parses JSON-stat format
- [ ] 24h cache, CLI testable
