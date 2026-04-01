# 0055 — South Korea KOSIS (Korean Statistical Information Service)

## What
Build `kosis_korea.py` module for KOSIS — South Korea's official statistical portal operated by Statistics Korea (KOSTAT). KOSIS provides programmatic access to 1,600+ statistical tables covering GDP, CPI, trade, employment, housing, and demographics. This complements the existing `bank_of_korea.py` (BOK monetary/financial data) with comprehensive real-economy statistics.

## Why
South Korea is the world's 13th-largest economy, home to Samsung, SK Hynix, Hyundai, and other global supply chain leaders. Korean economic data is a leading indicator for global semiconductor demand, shipbuilding, and Asian trade flows. We have BOK (central bank) data but lack the comprehensive KOSTAT macro statistics that drive GDP and sector models.

## API
- Base: `https://kosis.kr/openapi/Param/statisticsParameterData.do`
- Protocol: REST
- Auth: API key (free registration at https://kosis.kr/openapi/)
- Formats: JSON, XML
- Rate limits: 1,000 requests/day (free tier)
- Docs: https://kosis.kr/openapi/guide/guide_01List.jsp

## Key Endpoints
- `GET /statisticsParameterData.do?method=getList&apiKey={key}&itmId=T10&orgId=101&tblId=DT_1B41` — Fetch specific table data
- `GET /statisticsList.do?method=getList&apiKey={key}&vwCd=MT_ZTITLE` — List available statistics
- `GET /statisticsData.do?method=getList&apiKey={key}&orgId=101&tblId={table_id}` — Fetch table with all items
- Query params: `startPrdDe=201901`, `endPrdDe=202612`, `prdSe=M` (M=monthly, Q=quarterly, A=annual)

## Key Tables & Indicators
- **Table DT_1B41** (orgId 101) — GDP by expenditure approach (quarterly, real/nominal)
- **Table DT_1J20001** (orgId 101) — Consumer Price Index (monthly, all items + categories)
- **Table DT_1DA7012S** (orgId 101) — Economically Active Population Survey — unemployment rate (monthly)
- **Table DT_1F01013** (orgId 101) — Index of Industrial Production (monthly)
- **Table DT_1B10009** (orgId 101) — Exports/Imports by commodity and country (monthly)
- **Table DT_1YL20631** (orgId 101) — Housing Price Index (monthly)
- **Table DT_2KAA902** (orgId 101) — Semiconductor production index (monthly)

## Module
- Filename: `kosis_korea.py`
- Cache: 24h (monthly/quarterly releases)
- Auth: Reads `KOSIS_API_KEY` from `.env`

## Test Commands
```bash
python modules/kosis_korea.py                              # Latest key indicators
python modules/kosis_korea.py gdp                          # GDP quarterly
python modules/kosis_korea.py cpi                          # CPI inflation monthly
python modules/kosis_korea.py unemployment                 # Unemployment rate
python modules/kosis_korea.py industrial_production        # Industrial output index
python modules/kosis_korea.py exports                      # Export data by commodity
python modules/kosis_korea.py semiconductors               # Semiconductor production index
```

## Acceptance
- [ ] Fetches GDP, CPI, unemployment, industrial production, trade, housing, semiconductors
- [ ] Returns structured JSON: date, value, indicator, unit, source
- [ ] Date range queries via startPrdDe/endPrdDe
- [ ] Period frequency selection (monthly, quarterly, annual)
- [ ] 24h caching
- [ ] CLI: `python kosis_korea.py [indicator]`
- [ ] API key read from `.env` (KOSIS_API_KEY)
- [ ] Handles KOSIS period format (YYYYMM for monthly, YYYYQQ for quarterly)
- [ ] Error handling for unavailable tables/periods
- [ ] Rate limiting awareness (1,000 req/day)
