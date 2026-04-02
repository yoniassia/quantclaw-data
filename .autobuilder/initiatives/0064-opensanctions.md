# 0064 — OpenSanctions Global Database API

## What
Build `opensanctions_api.py` module for the OpenSanctions API — a free, open-source database aggregating sanctions lists, politically exposed persons (PEPs), and criminal watchlists from 80+ official sources worldwide. The API provides entity search, bulk dataset access, and cross-reference matching. This is essential compliance and risk data for financial screening, counterparty risk assessment, and geopolitical event detection.

## Why
Sanctions data is increasingly material for financial markets. Russian sanctions after 2022 created $300B+ in frozen assets and reshaped global commodity flows. OFAC designations move individual stocks 20-40% in minutes (e.g., Rusal in 2018). PEP screening correlates with sovereign risk events and corruption-driven capital flight. Tracking additions/removals from sanctions lists provides early signals for geopolitical de-escalation (Iran nuclear deal) or escalation events. OpenSanctions aggregates OFAC (US), EU Consolidated List, UN Security Council, UK HMT, and 70+ other watchlists into a single queryable database — no existing QuantClaw module covers sanctions or PEP data.

## API
- Base: `https://api.opensanctions.org`
- Protocol: REST (GET requests)
- Auth: API key (free tier: 50 req/day; registered non-commercial: 500 req/day)
- Formats: JSON (FollowTheMoney entity format)
- Rate limits: 50 requests/day (free), 500/day (registered)
- Docs: https://www.opensanctions.org/docs/api/

## Key Endpoints
- `GET /search/default?q={query}&schema={entity_type}` — Search entities by name across all datasets
- `GET /entities/{entity_id}` — Full entity detail with all properties and dataset sources
- `GET /match/default` — Fuzzy matching endpoint for screening (POST with entity properties)
- `GET /datasets` — List all available datasets and their metadata
- `GET /datasets/{dataset_name}` — Dataset detail (entity count, last update, coverage)
- `GET /collections/default/statistics` — Aggregate statistics across all sanctions lists

Schema types: `Person`, `Company`, `Organization`, `LegalEntity`, `Vessel`, `Aircraft`.

## Key Indicators
- **Sanctions List Size** — Total entities on each major list (OFAC SDN, EU, UN, UK HMT)
- **New Designations** — Recently added entities (signals for escalation events)
- **De-listings** — Removed entities (signals for de-escalation / diplomatic thaw)
- **Entity Search** — Screen companies, persons, vessels against all sanctions lists
- **Country Exposure** — Entity counts by jurisdiction (Russia, Iran, DPRK, Syria, etc.)
- **PEP Coverage** — Politically exposed persons by country and position type
- **Vessel Sanctions** — Sanctioned ships by flag state and vessel type
- **Cross-List Overlap** — Entities appearing on multiple sanctions regimes simultaneously

## Module
- Filename: `opensanctions_api.py`
- Cache: 6h for search results, 24h for dataset statistics
- Auth: Reads `OPENSANCTIONS_API_KEY` from `.env`

## Test Commands
```bash
python modules/opensanctions_api.py                              # Dataset statistics summary
python modules/opensanctions_api.py search "Rosneft"             # Search entity by name
python modules/opensanctions_api.py search "Gazprombank" Company  # Search companies only
python modules/opensanctions_api.py entity Q7397                  # Entity detail by ID
python modules/opensanctions_api.py datasets                      # List all sanctions datasets
python modules/opensanctions_api.py stats                         # Aggregate statistics
python modules/opensanctions_api.py country RU                    # Russia sanctions exposure
python modules/opensanctions_api.py vessels                       # Sanctioned vessels list
```

## Acceptance
- [ ] Searches entities across 80+ sanctions/watchlist datasets
- [ ] Returns structured JSON: entity_id, name, schema, datasets, properties, source
- [ ] Fuzzy name matching for compliance screening
- [ ] Dataset metadata: entity counts, last updated, source authority
- [ ] Country-level aggregation of sanctioned entities
- [ ] Vessel and aircraft sanctions queries
- [ ] PEP (politically exposed persons) searches
- [ ] 6h cache for search results, 24h for dataset statistics
- [ ] CLI: `python opensanctions_api.py [command] [args]`
- [ ] API key read from `.env` (OPENSANCTIONS_API_KEY)
- [ ] Handles rate limiting (50-500 req/day) with backoff and caching
- [ ] FollowTheMoney entity format parsing into simplified JSON
- [ ] New designation detection for alert generation
