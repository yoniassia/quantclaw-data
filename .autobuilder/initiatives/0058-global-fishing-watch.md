# 0058 — Global Fishing Watch API

## What
Build `global_fishing_watch.py` module for the Global Fishing Watch (GFW) API — a free platform that uses AIS data and machine learning to track global fishing vessel activity in near-real-time. GFW provides vessel identity, fishing effort heatmaps, port visits, and encounter events covering 65,000+ fishing vessels worldwide. This is high-value alternative data for commodity trading, food security analysis, and ESG compliance screening.

## Why
Global fishing activity is a leading indicator for seafood commodity prices, food security crises, and maritime trade disruption. Fishing effort data correlates with protein commodity futures (fishmeal, fish oil), aquaculture input costs, and food inflation in protein-dependent economies. GFW data also detects illegal unreported and unregulated (IUU) fishing — a $23B/year problem that affects supply chain ESG ratings. Port visit data reveals vessel movement patterns useful for detecting sanctions evasion and trade flow shifts. No existing QuantClaw module covers fisheries or maritime fishing activity.

## API
- Base: `https://gateway.api.globalfishingwatch.org/v3`
- Protocol: REST
- Auth: Bearer token (free registration at https://globalfishingwatch.org/our-apis/)
- Formats: JSON, GeoJSON
- Rate limits: 100 requests/minute (free tier)
- Docs: https://globalfishingwatch.org/our-apis/documentation

## Key Endpoints
- `GET /vessels/search?query={name_or_mmsi}&datasets=public-global-vessel-identity:latest` — Search vessels by name, MMSI, or IMO
- `GET /vessels/{vessel_id}?dataset=public-global-vessel-identity:latest` — Vessel identity and characteristics
- `GET /4wings/report?spatial-resolution=low&temporal-resolution=monthly&group-by=flag&datasets=public-global-fishing-effort:latest&date-range=2025-01-01,2025-12-31` — Fishing effort aggregated by flag state
- `GET /events?datasets=public-global-fishing-events:latest&vessels={vessel_id}&start-date=2025-01-01&end-date=2025-12-31` — Fishing events for a vessel
- `GET /events?datasets=public-global-port-visits-c2-events:latest&start-date=2025-01-01&end-date=2025-12-31&confidences=4` — Port visit events
- `GET /events?datasets=public-global-encounters-events:latest` — Vessel encounter/transshipment events

## Key Indicators
- **Global Fishing Effort Index** — Monthly aggregated fishing hours by region/flag state
- **Top Fishing Nations Activity** — China, Indonesia, Taiwan, Japan, South Korea, Spain effort trends
- **Regional Fishing Intensity** — EEZ-level fishing hours (West Africa, South Pacific, Indian Ocean)
- **Port Visit Patterns** — Vessel arrivals/departures at major fishing ports
- **Transshipment Events** — At-sea transfers (high-risk for IUU and sanctions evasion)
- **Fleet Size Tracking** — Active vessel counts by flag state and gear type
- **Dark Vessel Detection** — Gaps in AIS transmission (potential IUU indicator)

## Module
- Filename: `global_fishing_watch.py`
- Cache: 6h for activity feeds, 24h for vessel identity lookups
- Auth: Reads `GFW_API_TOKEN` from `.env`

## Test Commands
```bash
python modules/global_fishing_watch.py                          # Global fishing effort summary
python modules/global_fishing_watch.py effort_by_flag           # Fishing hours by flag state
python modules/global_fishing_watch.py vessel_search "Hai Feng" # Search vessel by name
python modules/global_fishing_watch.py port_visits              # Recent port visit events
python modules/global_fishing_watch.py encounters               # Transshipment encounters
python modules/global_fishing_watch.py region south_pacific     # Regional fishing intensity
```

## Acceptance
- [ ] Fetches global fishing effort aggregated by flag state and region
- [ ] Returns structured JSON: date, value, flag_state, region, indicator, source
- [ ] Vessel search by name, MMSI, or IMO number
- [ ] Port visit event tracking with confidence scoring
- [ ] Transshipment encounter detection
- [ ] Regional fishing intensity queries (EEZ/high seas)
- [ ] 6h cache for activity data, 24h for vessel identity
- [ ] CLI: `python global_fishing_watch.py [command] [args]`
- [ ] API token read from `.env` (GFW_API_TOKEN)
- [ ] Handles GeoJSON response parsing
- [ ] Rate limiting awareness (100 req/min) with backoff
- [ ] Monthly time series output for trend analysis
