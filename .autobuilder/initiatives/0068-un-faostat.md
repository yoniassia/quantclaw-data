# 0068 — UN FAO FAOSTAT Data API

## What
Build `faostat_api.py` module for the United Nations Food and Agriculture Organization FAOSTAT API — the world's most comprehensive database of food and agriculture statistics covering 245 countries and territories from 1961 to present. Provides production, trade, food balances, prices, land use, emissions, food security, and fertilizer data. Goes far beyond the existing `fao_food_price_index_api.py` module (which only covers the monthly FAO Food Price Index) to expose the full breadth of FAOSTAT's 20,000+ indicators.

## Why
Agricultural commodity markets are a $5T+ sector where supply fundamentals drive prices. FAOSTAT production data (cereals, oilseeds, livestock) provides the ground-truth supply side for commodity futures models. Country-level crop production forecasts affect wheat, corn, soybean, rice, sugar, and palm oil futures. Trade flow data reveals export bans, tariff impacts, and supply chain rerouting — Russia/Ukraine grain disruption in 2022 caused 40%+ spikes in wheat futures. Fertilizer price and consumption data leads crop yields by one growing season. Land use changes signal long-term agricultural capacity shifts. Food security indicators (undernourishment, food inflation) correlate with political instability in import-dependent nations. The existing FAO Food Price Index module covers only 1 of 20,000+ available series.

## API
- Base: `https://fenixservices.fao.org/faostat/api/v1`
- Protocol: REST (GET requests)
- Auth: None (fully open, no key required)
- Formats: JSON, CSV
- Rate limits: Fair use (~60 requests/minute recommended)
- Docs: https://fenixservices.fao.org/faostat/api/v1/en/definitions/domain

## Key Endpoints
- `GET /en/definitions/domain` — List all available domains (QCL, TP, PP, etc.)
- `GET /en/data/{domain_code}?area={country_code}&element={element_code}&item={item_code}&year={year}` — Fetch data by domain, country, item, and element
- `GET /en/definitions/domain/{domain_code}/area` — Available countries for a domain
- `GET /en/definitions/domain/{domain_code}/element` — Available elements (Production, Yield, Area, etc.)
- `GET /en/definitions/domain/{domain_code}/item` — Available items (Wheat, Rice, Maize, etc.)
- `GET /en/definitions/domain/{domain_code}/year` — Available years

Key domain codes:
- `QCL` — Crops and livestock production (area harvested, yield, production quantity)
- `TP` — Trade: Crops and livestock products (import/export quantity and value)
- `PP` — Producer prices (farm-gate prices by commodity)
- `CP` — Consumer prices (food CPI by country)
- `FBS` — Food balance sheets (supply utilization accounts)
- `RL` — Land use (arable land, forest, agricultural area)
- `RFN` — Fertilizers by nutrient (N, P, K consumption)
- `GT` — Emissions from agriculture (CO2, CH4, N2O)
- `FS` — Food security indicators (undernourishment, food inadequacy)
- `IC` — Investment: Credit to agriculture
- `OA` — Population estimates (used as denominators)

## Key Indicators
- **Global Crop Production** — Wheat, rice, maize, soybeans, sugar annual production by country
- **Crop Yields** — Tonnes/hectare trends (agricultural productivity signal)
- **Agricultural Trade Flows** — Import/export volumes and values by commodity-country pair
- **Producer Prices** — Farm-gate prices for major commodities (local currency and USD)
- **Fertilizer Consumption** — Nitrogen, phosphorus, potassium use by country (yield predictor)
- **Land Use Change** — Arable land expansion/contraction, deforestation rates
- **Food Balance Sheets** — Per capita food supply (kcal, protein, fat)
- **Agricultural Emissions** — Methane and N2O from farming (ESG/carbon data)
- **Food Security** — Prevalence of undernourishment, food price inflation
- **Livestock Inventory** — Cattle, poultry, swine head counts by country

## Module
- Filename: `faostat_api.py`
- Cache: 24h (annual data, updated quarterly)
- Auth: None required

## Test Commands
```bash
python modules/faostat_api.py                                          # Summary of available domains
python modules/faostat_api.py production wheat                         # Global wheat production latest
python modules/faostat_api.py production maize US                      # US maize production
python modules/faostat_api.py trade soybeans                           # Global soybean trade flows
python modules/faostat_api.py prices wheat US                          # US wheat producer prices
python modules/faostat_api.py fertilizer nitrogen                      # Global nitrogen fertilizer use
python modules/faostat_api.py land_use BR                              # Brazil land use data
python modules/faostat_api.py food_security                            # Global food security indicators
python modules/faostat_api.py emissions                                # Agricultural emissions by country
python modules/faostat_api.py domains                                  # List all available domains
```

## Acceptance
- [ ] Fetches production, trade, prices, fertilizer, land use, emissions, food security data
- [ ] Returns structured JSON: country, year, item, element, value, unit, source, domain
- [ ] Domain discovery: list all available domains, items, elements, areas
- [ ] Country filtering by ISO3 code or FAO area code
- [ ] Item filtering by commodity name or FAOSTAT item code
- [ ] Multi-year time series queries
- [ ] 24h caching (data updates quarterly)
- [ ] CLI: `python faostat_api.py [domain] [item] [country]`
- [ ] No API key required
- [ ] Handles large result sets with pagination
- [ ] Maps FAO country codes to ISO3 for cross-source joining
- [ ] Commodity name normalization (wheat/Wheat/WHEAT all resolve)
- [ ] Top-N producer/exporter ranking queries
- [ ] CSV fallback for bulk data when JSON response is too large
