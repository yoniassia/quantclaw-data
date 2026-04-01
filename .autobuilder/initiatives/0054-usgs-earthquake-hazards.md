# 0054 — USGS Earthquake Hazards Program API

## What
Build `usgs_earthquake.py` module for the USGS Earthquake Hazards Program real-time earthquake feed. The FDSN Event Web Service provides global earthquake data (magnitude, location, depth, felt reports) updated in real time. This is high-value alternative data for catastrophe bond pricing, reinsurance risk modeling, and commodity supply disruption analysis.

## Why
Earthquakes directly impact financial markets: insurance/reinsurance stocks (Swiss Re, Munich Re, Berkshire), catastrophe bonds (ILS market), and commodity supply chains (Chilean copper, Japanese manufacturing, Taiwan semiconductors). Real-time earthquake monitoring enables event-driven trading signals and portfolio risk alerts. The ILS market alone is $45B+ and prices directly off seismic data.

## API
- Base: `https://earthquake.usgs.gov/fdsnws/event/1`
- Protocol: REST (FDSN standard)
- Auth: None (fully open, no key required)
- Formats: GeoJSON, CSV, text
- Rate limits: Fair use (no hard limit)
- Docs: https://earthquake.usgs.gov/fdsnws/event/1/

## Key Endpoints
- `GET /query?format=geojson&starttime=YYYY-MM-DD&endtime=YYYY-MM-DD` — Query events by date range
- `GET /query?format=geojson&minmagnitude=5.0` — Filter by minimum magnitude
- `GET /query?format=geojson&latitude=35&longitude=139&maxradiuskm=500` — Radial search (e.g., near Tokyo)
- `GET /query?format=geojson&alertlevel=red` — PAGER alert level (red = significant economic impact)
- `GET /count?starttime=YYYY-MM-DD&minmagnitude=4.0` — Event count queries
- `GET /version` — API version check

## Indicators to Implement
- Real-time significant earthquake feed (M5.0+ globally)
- Regional seismic activity index (rolling 30-day count by basin)
- PAGER economic loss estimates (ShakeMap + PAGER alert level)
- Proximity alerts for financial hotspots (Tokyo, Taipei, Santiago, Istanbul)
- Historical seismicity trends (annual M6+ counts for cat bond pricing)
- Felt report intensity (DYFI — Did You Feel It community reports)

## Financial Hotspot Regions (Pre-configured)
- **Taiwan (TSMC):** lat=23.5, lon=121.0, radius=300km
- **Japan (Tokyo):** lat=35.7, lon=139.7, radius=500km
- **Chile (Copper):** lat=-33.4, lon=-70.6, radius=800km
- **Turkey (Istanbul):** lat=41.0, lon=29.0, radius=400km
- **California (Tech):** lat=37.4, lon=-122.1, radius=300km

## Module
- Filename: `usgs_earthquake.py`
- Cache: 5min for real-time feed, 24h for historical queries

## Test Commands
```bash
python modules/usgs_earthquake.py                          # Significant quakes last 24h
python modules/usgs_earthquake.py recent                   # M4.0+ last 7 days
python modules/usgs_earthquake.py hotspot taiwan           # Activity near TSMC
python modules/usgs_earthquake.py hotspot japan            # Activity near Tokyo
python modules/usgs_earthquake.py history 2025             # Annual M5+ summary
python modules/usgs_earthquake.py alerts                   # Active PAGER alerts (red/orange)
```

## Acceptance
- [ ] Fetches real-time earthquake events with magnitude, location, depth, time
- [ ] Returns structured JSON: event_id, magnitude, lat, lon, depth, place, time, alert_level
- [ ] Date range and magnitude threshold filtering
- [ ] Pre-configured financial hotspot proximity queries
- [ ] PAGER alert level filtering (green/yellow/orange/red)
- [ ] 5min cache for real-time, 24h for historical
- [ ] CLI: `python usgs_earthquake.py [command] [args]`
- [ ] GeoJSON response parsing with clean output
