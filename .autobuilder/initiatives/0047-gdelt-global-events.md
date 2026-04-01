# 0047 — GDELT Global Event Database

## What
Build `gdelt_global_events.py` module for the GDELT Project — the world's largest open database of human society, monitoring broadcast, print, and web news from nearly every country in 100+ languages. Provides real-time geopolitical risk signals, country-level sentiment, and event frequency data.

## Why
GDELT is premier alternative data for geopolitical risk modeling. Event counts (protests, military actions, diplomatic events) by country pair correlate with sovereign spreads, FX volatility, and commodity disruptions. The tone/sentiment metrics provide macro sentiment at country and topic level.

## API
- Base (DOC): `https://api.gdeltproject.org/api/v2/doc/doc`
- Base (TV): `https://api.gdeltproject.org/api/v2/tv/tv`
- Base (GEO): `https://api.gdeltproject.org/api/v2/geo/geo`
- Protocol: REST (GET with query parameters)
- Auth: None (fully open, no key required)
- Formats: JSON, CSV, GeoJSON
- Rate limits: Fair use (no hard limit documented)
- Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

## Key Endpoints
- `DOC API` — Full-text article search with tone, theme, location filters
- `TV API` — Television news monitoring (closed captions from 150+ stations)
- `GEO API` — Geographic heatmaps of event activity
- `?query=...&mode=timelinevol` — Volume timeline for topic/country
- `?query=...&mode=timelinetone` — Sentiment timeline for topic/country
- `?query=...&mode=artlist&format=json` — Article list with metadata

## Indicators to Implement
- Geopolitical risk index by country (event volume for conflict/protest themes)
- Country-pair tension score (bilateral event tone: US-China, Russia-EU, etc.)
- Global protest activity index (CAMEO event codes 14x)
- Commodity disruption signals (events near key shipping lanes, oil regions)
- Media sentiment by sector/topic (central bank mentions, trade war, sanctions)
- TV news coverage volume for financial topics

## Module
- Filename: `gdelt_global_events.py`
- Cache: 1h (event data updates every 15 minutes)

## Test Commands
```bash
python modules/gdelt_global_events.py                        # Global geopolitical risk summary
python modules/gdelt_global_events.py country_risk CN         # China risk index
python modules/gdelt_global_events.py tension US CN           # US-China tension timeline
python modules/gdelt_global_events.py topic "central bank"    # Central bank media sentiment
```

## Acceptance
- [ ] DOC API: article search with tone and theme filters
- [ ] Timeline mode: volume and tone over time for topics/countries
- [ ] Country risk scoring (event frequency + tone aggregation)
- [ ] Bilateral tension metric (country-pair tone)
- [ ] 1h caching (data refreshes frequently)
- [ ] CLI: `python gdelt_global_events.py [command] [args]`
- [ ] Graceful handling of large result sets (pagination)
