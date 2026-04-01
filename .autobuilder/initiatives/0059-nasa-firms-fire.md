# 0059 — NASA FIRMS (Fire Information for Resource Management System)

## What
Build `nasa_firms_fire.py` module for NASA FIRMS — a free satellite-based fire detection system providing near-real-time (NRT) active fire data from MODIS and VIIRS instruments. FIRMS detects thermal anomalies globally with ~375m resolution and <3h latency. This is high-value alternative data for agricultural commodity trading, insurance/reinsurance catastrophe modeling, and supply chain disruption analysis.

## Why
Wildfires directly impact financial markets across multiple vectors: agricultural commodity prices (wheat, corn, palm oil, sugar from burning regions), forestry/timber stocks, insurance and reinsurance losses (2025 CA wildfires cost $30B+), air quality affecting urban economic output, and carbon credit markets. Fire data is a leading indicator — satellite detections arrive hours before news coverage, giving quant models an edge on commodity futures and catastrophe bond pricing. The 2019-2020 Australian bushfires, Amazon deforestation burns, and annual Southeast Asian haze events all moved markets before being fully priced in.

## API
- Base: `https://firms.modaps.eosdis.nasa.gov/api`
- Protocol: REST
- Auth: MAP_KEY (free registration at https://firms.modaps.eosdis.nasa.gov/api/area/)
- Formats: JSON, CSV, GeoJSON, SHP
- Rate limits: 2,000 transactions/day (free tier)
- Docs: https://firms.modaps.eosdis.nasa.gov/api/area/

## Key Endpoints
- `GET /area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{country_code}/1` — Active fires in country, last 24h (CSV)
- `GET /area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{lat},{lon},{radius}/1` — Active fires in radius around point
- `GET /country/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{country_code}/5` — Country fires, last 5 days
- `GET /area/csv/{MAP_KEY}/MODIS_NRT/{lat},{lon},{radius}/{days}` — MODIS NRT fires near point
- Satellite sources: `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `MODIS_NRT`, `LANDSAT_NRT`
- Country codes: ISO 3166-1 alpha-3 (USA, BRA, IDN, AUS, CAN, etc.)

## Key Indicators & Financial Hotspot Regions
- **US West Coast Fires** (USA, lat=37.5, lon=-120.0, radius=500km) — California/Oregon wildfire season, insurance stocks
- **Amazon Deforestation Burns** (BRA, lat=-5.0, lon=-55.0, radius=1500km) — Soy, cattle, carbon credits
- **Southeast Asian Haze** (IDN + MYS, lat=0.5, lon=110.0, radius=1000km) — Palm oil supply disruption
- **Australian Bushfires** (AUS, lat=-33.0, lon=149.0, radius=800km) — Wheat, wool, insurance
- **Canadian Boreal Fires** (CAN, lat=55.0, lon=-105.0, radius=1000km) — Lumber, carbon, air quality
- **Mediterranean Fires** (GRC + TUR + ESP, lat=38.0, lon=23.0, radius=500km) — Tourism, olive oil
- **Siberian Fires** (RUS, lat=62.0, lon=100.0, radius=1500km) — Carbon emissions, climate
- **African Savanna Burns** (Sub-Saharan) — Agricultural cycle indicator

## Derived Metrics
- **Global Fire Activity Index** — Daily aggregated fire pixel count vs. seasonal baseline
- **Regional Fire Anomaly Score** — Z-score of current fire count vs. 5-year average for region
- **Agricultural Risk Score** — Fire intensity in key crop-growing regions weighted by commodity value
- **Insurance Exposure Score** — Fire proximity to populated areas (population-weighted)

## Module
- Filename: `nasa_firms_fire.py`
- Cache: 1h for NRT data, 24h for country-level aggregates
- Auth: Reads `NASA_FIRMS_MAP_KEY` from `.env`

## Test Commands
```bash
python modules/nasa_firms_fire.py                               # Global fire summary last 24h
python modules/nasa_firms_fire.py country USA                   # US fires last 24h
python modules/nasa_firms_fire.py country BRA 5                 # Brazil fires last 5 days
python modules/nasa_firms_fire.py hotspot amazon                # Amazon deforestation region
python modules/nasa_firms_fire.py hotspot california            # CA wildfire zone
python modules/nasa_firms_fire.py hotspot southeast_asia        # SE Asian haze region
python modules/nasa_firms_fire.py anomaly                       # Fire anomaly scores by region
```

## Acceptance
- [ ] Fetches NRT fire detections from VIIRS and MODIS satellites
- [ ] Returns structured JSON: latitude, longitude, brightness, confidence, acq_date, acq_time, satellite, country
- [ ] Country-level queries with configurable lookback (1-10 days)
- [ ] Radius-based queries around financial hotspot coordinates
- [ ] Pre-configured financial hotspot regions (Amazon, California, SE Asia, Australia, etc.)
- [ ] Fire anomaly scoring vs. seasonal baseline
- [ ] 1h cache for NRT data, 24h for aggregates
- [ ] CLI: `python nasa_firms_fire.py [command] [args]`
- [ ] API key read from `.env` (NASA_FIRMS_MAP_KEY)
- [ ] Handles multiple satellite sources (VIIRS SNPP, VIIRS NOAA-20, MODIS)
- [ ] Rate limiting awareness (2,000 transactions/day)
- [ ] CSV response parsing with proper type conversion (lat/lon as float, confidence as int)
