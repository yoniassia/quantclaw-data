# 0050 — GLEIF LEI Registry API

## What
Build `gleif_lei.py` module for the Global Legal Entity Identifier Foundation (GLEIF) — the authoritative registry of Legal Entity Identifiers (LEIs). LEIs are the global standard for uniquely identifying legal entities participating in financial transactions. The API provides entity lookup, relationship mapping, and corporate hierarchy data for 2.5M+ entities worldwide.

## Why
LEI data is critical infrastructure for entity resolution in financial analysis — mapping company names to standardized identifiers, discovering parent-subsidiary relationships, and identifying ultimate beneficial owners. Useful for compliance screening, M&A analysis, and cross-referencing filings across jurisdictions (SEC EDGAR + ESMA + local regulators).

## API
- Base: `https://api.gleif.org/api/v1`
- Protocol: REST (JSON:API specification)
- Auth: None (fully open, no key required)
- Formats: JSON (JSON:API), CSV bulk download
- Rate limits: Fair use
- Docs: https://documenter.getpostman.com/view/7679680/SVYrrxMq

## Key Endpoints
- `GET /lei-records?filter[lei]={lei}` — Lookup by LEI code
- `GET /lei-records?filter[entity.legalName]={name}` — Search by entity name
- `GET /lei-records?filter[entity.registeredAs]={id}` — Search by registration number
- `GET /lei-records/{lei}/direct-parent` — Direct parent entity
- `GET /lei-records/{lei}/ultimate-parent` — Ultimate parent entity
- `GET /lei-records?filter[entity.jurisdiction]=US-DE` — Filter by jurisdiction
- `GET /autocompletions?field=fulltext&q={query}` — Autocomplete entity search

## Indicators to Implement
- Entity lookup by name, LEI, or registration number
- Corporate hierarchy (parent → child chain)
- Ultimate beneficial owner resolution
- Entity status (active, lapsed, retired, merged)
- Jurisdiction distribution (entities per country)
- Registration statistics (new LEIs over time as market activity proxy)

## Module
- Filename: `gleif_lei.py`
- Cache: 24h (LEI data changes infrequently)

## Test Commands
```bash
python modules/gleif_lei.py                              # Summary stats (total active LEIs)
python modules/gleif_lei.py search "Apple Inc"           # Search by company name
python modules/gleif_lei.py lookup 5493001KJTIIGC8Y1R12  # Lookup by LEI (Apple)
python modules/gleif_lei.py hierarchy 5493001KJTIIGC8Y1R12  # Parent/child tree
python modules/gleif_lei.py jurisdiction US               # US-registered entities
```

## Acceptance
- [ ] Entity search by name (fuzzy), LEI, registration number
- [ ] Returns structured JSON: lei, legal_name, jurisdiction, status, registration_date
- [ ] Parent/subsidiary relationship traversal
- [ ] Ultimate parent resolution
- [ ] Autocomplete search support
- [ ] 24h caching
- [ ] CLI: `python gleif_lei.py [command] [args]`
- [ ] Pagination for large result sets (JSON:API page parameters)
