# 0063 — ENTSO-E Transparency Platform (European Energy Grid)

## What
Build `entsoe_energy.py` module for the ENTSO-E Transparency Platform API — the official data portal of the European Network of Transmission System Operators for Electricity. It provides real-time and historical data on electricity generation, consumption, cross-border flows, day-ahead/intraday prices, installed capacity, and outage information across 35 European countries. This is high-value alternative data for energy commodity trading and macro analysis.

## Why
European electricity prices are a leading indicator for industrial output, manufacturing PMI, and energy-intensive sector margins (aluminum, steel, chemicals, cement). Day-ahead power prices (EPEX SPOT) directly correlate with natural gas futures (TTF), carbon credit prices (EU ETS), and renewable energy deployment rates. Cross-border flow data reveals grid stress, demand surges, and interconnector bottleneck events before they appear in industrial production reports. ENTSO-E data covers all of EU27 plus UK, Norway, Switzerland — making it the single best source for European energy market intelligence. QuantClaw has electricity_maps modules for carbon intensity but no direct generation/pricing/flow data from the official grid operator.

## API
- Base: `https://web-api.tp.entsoe.eu/api`
- Protocol: REST (GET requests with XML response)
- Auth: Security token (free registration at https://transparency.entsoe.eu/)
- Formats: XML (application/xml)
- Rate limits: 400 requests/minute
- Docs: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html

## Key Endpoints
- `GET ?securityToken={token}&documentType=A44&in_Domain={eic}&out_Domain={eic}&periodStart={YYYYMMDDhhmm}&periodEnd={YYYYMMDDhhmm}` — Day-ahead electricity prices
- `GET ?securityToken={token}&documentType=A75&processType=A16&in_Domain={eic}&periodStart=...&periodEnd=...` — Actual generation per production type (wind, solar, nuclear, gas, coal, hydro)
- `GET ?securityToken={token}&documentType=A65&processType=A16&outBiddingZone_Domain={eic}&periodStart=...&periodEnd=...` — Actual total load (electricity consumption)
- `GET ?securityToken={token}&documentType=A11&in_Domain={eic}&out_Domain={eic}&periodStart=...&periodEnd=...` — Cross-border physical flows between countries
- `GET ?securityToken={token}&documentType=A68&processType=A33&in_Domain={eic}&periodStart=...&periodEnd=...` — Installed generation capacity per type
- `GET ?securityToken={token}&documentType=A80&in_Domain={eic}&periodStart=...&periodEnd=...` — Generation forecast (day-ahead wind/solar)

Key EIC domain codes: DE_LU (Germany/Luxembourg), FR (France), ES (Spain), IT_NORD (Italy North), NL (Netherlands), PL (Poland), NO_1 (Norway South), GB (Great Britain), SE_1-4 (Sweden zones).

## Key Indicators
- **Day-Ahead Prices** — Hourly electricity prices by bidding zone (EUR/MWh)
- **Generation by Source** — Hourly output: wind, solar, nuclear, gas, coal, hydro, biomass
- **Total Load** — Actual electricity consumption by country (hourly, GW)
- **Cross-Border Flows** — Physical electricity transfers between countries (MW)
- **Wind/Solar Forecast vs Actual** — Forecast errors as volatility signals
- **Nuclear Availability** — Planned/unplanned outages affecting baseload supply
- **Installed Capacity** — Generation fleet composition by country and fuel type
- **Net Transfer Capacity** — Maximum cross-border transmission capacity

## Module
- Filename: `entsoe_energy.py`
- Cache: 1h for real-time generation/load, 6h for day-ahead prices, 24h for capacity/structural data
- Auth: Reads `ENTSOE_API_TOKEN` from `.env`

## Test Commands
```bash
python modules/entsoe_energy.py                              # Summary of major European prices and load
python modules/entsoe_energy.py prices DE_LU                 # Day-ahead prices for Germany
python modules/entsoe_energy.py generation FR                # Generation mix for France
python modules/entsoe_energy.py load ES                      # Electricity consumption Spain
python modules/entsoe_energy.py cross_border DE_LU FR        # Physical flows Germany→France
python modules/entsoe_energy.py wind_solar DE_LU             # Wind/solar generation + forecast
python modules/entsoe_energy.py capacity PL                  # Installed capacity Poland
python modules/entsoe_energy.py nuclear FR                   # French nuclear availability
```

## Acceptance
- [ ] Fetches day-ahead electricity prices for major bidding zones
- [ ] Returns structured JSON: datetime, value, indicator, bidding_zone, unit, source
- [ ] Generation breakdown by fuel type (wind, solar, nuclear, gas, coal, hydro)
- [ ] Total load (consumption) data with hourly resolution
- [ ] Cross-border physical flow data between country pairs
- [ ] Wind/solar forecast vs actual comparison
- [ ] XML response parsing into clean JSON
- [ ] EIC domain code mapping for all 35 countries/bidding zones
- [ ] 1h cache for real-time data, 6h for prices, 24h for structural data
- [ ] CLI: `python entsoe_energy.py [command] [bidding_zone]`
- [ ] API token read from `.env` (ENTSOE_API_TOKEN)
- [ ] Handles XML namespaces and ENTSO-E error codes
- [ ] Date range support with proper YYYYMMDDhhmm formatting
