# 0069 — ILO ILOSTAT SDMX API (Global Labour Market)

## What
Build `ilostat_labour.py` module for the International Labour Organization ILOSTAT SDMX API — the world's most comprehensive source of labour market statistics covering 230+ countries with 100+ indicators from 1947 to present. Provides unemployment rates, employment by sector, wages, labour productivity, working poverty, informal employment, and labour force participation. Uses the standard SDMX 2.1 REST protocol, consistent with existing ECB and Eurostat modules.

## Why
Labour market data is the single most-watched macro category by central banks and bond markets. US nonfarm payrolls move Treasury yields 10-20bps in seconds, but international labour data — especially for emerging markets — is fragmented and hard to source. ILOSTAT aggregates national labour surveys into a standardized global dataset. Unemployment trends predict consumer spending, mortgage defaults, and electoral outcomes. Wage growth feeds directly into inflation expectations and central bank reaction functions. Employment-by-sector data reveals structural economic transitions (services vs manufacturing vs agriculture) that drive long-term equity allocation. Labour productivity growth is the key driver of sustainable GDP growth and currency fair value. Youth unemployment (15-24) is a political instability predictor in MENA, Southern Europe, and Sub-Saharan Africa. No existing QuantClaw module provides comprehensive global labour market data — BLS covers only the US.

## API
- Base: `https://www.ilo.org/sdmx/rest`
- Protocol: SDMX 2.1 REST (GET requests)
- Auth: None (fully open, no key required)
- Formats: SDMX-JSON, SDMX-ML (XML), CSV
- Rate limits: Fair use (~30 requests/minute recommended)
- Docs: https://ilostat.ilo.org/resources/sdmx-tools/

## Key Endpoints
- `GET /data/ILO,DF_UNE_2EAP_SEX_AGE_RT/{country}.{sex}.{age}?startPeriod={year}&endPeriod={year}&format=jsondata` — Unemployment rate by sex and age
- `GET /data/ILO,DF_EMP_TEMP_SEX_ECO_NB/{country}.{sex}.{sector}?format=jsondata` — Employment by sector (agriculture, industry, services)
- `GET /data/ILO,DF_EAR_4MTH_SEX_ECO_CUR_NB/{country}.{sex}.{sector}.{currency}?format=jsondata` — Mean monthly earnings by sector
- `GET /data/ILO,DF_GDP_211P_NOC_NB/{country}?format=jsondata` — Labour productivity (GDP per worker)
- `GET /data/ILO,DF_EAP_2WAP_SEX_AGE_RT/{country}.{sex}.{age}?format=jsondata` — Labour force participation rate
- `GET /data/ILO,DF_EIP_WDIS_SEX_AGE_NB/{country}.{sex}.{age}?format=jsondata` — Working poverty (employed below poverty line)
- `GET /dataflow/ILO?format=jsondata` — List all available dataflows (100+ indicators)
- `GET /codelist/ILO/CL_AREA?format=jsondata` — Country code list

SDMX key structure uses dot-separated dimensions: `{REF_AREA}.{SEX}.{AGE}.{CLASSIF}` etc.

## Key Indicators
- **Unemployment Rate** — Harmonized unemployment by country, sex, age group (headline macro signal)
- **Youth Unemployment** — Ages 15-24 rate (political instability predictor)
- **Labour Force Participation** — Working-age population in labour force (structural trend)
- **Employment by Sector** — Agriculture, industry, services shares (structural transformation)
- **Mean Wages** — Monthly earnings by sector and sex (inflation input)
- **Labour Productivity** — GDP per employed person (growth sustainability metric)
- **Informal Employment** — Share outside formal sector (EM development indicator)
- **Working Poverty** — Employed persons below poverty line (social stability risk)
- **Hours Worked** — Mean weekly hours (cyclical activity indicator)
- **NEET Rate** — Youth not in employment, education, or training
- **Gender Pay Gap** — Male vs female earnings ratio by country

## Module
- Filename: `ilostat_labour.py`
- Cache: 24h (monthly/quarterly/annual release cadence)
- Auth: None required

## Test Commands
```bash
python modules/ilostat_labour.py                                       # Global unemployment summary
python modules/ilostat_labour.py unemployment US                       # US unemployment rate
python modules/ilostat_labour.py unemployment TR                       # Turkey unemployment rate
python modules/ilostat_labour.py youth_unemployment ZA                 # South Africa youth unemployment
python modules/ilostat_labour.py wages DE                              # Germany mean wages
python modules/ilostat_labour.py employment_by_sector IN               # India employment by sector
python modules/ilostat_labour.py productivity JP                       # Japan labour productivity
python modules/ilostat_labour.py participation BR                      # Brazil labour force participation
python modules/ilostat_labour.py informal_employment MX                # Mexico informal employment
python modules/ilostat_labour.py dataflows                             # List all available indicators
```

## Acceptance
- [ ] Fetches unemployment, wages, employment, productivity, participation, poverty data
- [ ] Returns structured JSON: country, period, indicator, sex, age_group, value, unit, source
- [ ] SDMX 2.1 REST protocol compliance (consistent with ECB/Eurostat modules)
- [ ] Country filtering by ISO2 code
- [ ] Sex and age group dimension filtering
- [ ] Sector classification filtering (ISIC Rev.4)
- [ ] Multi-period time series queries with startPeriod/endPeriod
- [ ] Dataflow discovery: list all 100+ available indicators
- [ ] 24h caching
- [ ] CLI: `python ilostat_labour.py [indicator] [country]`
- [ ] No API key required
- [ ] SDMX-JSON response parsing (observation/dimension structure)
- [ ] Cross-country comparison queries (multiple REF_AREAs)
- [ ] Handles missing data periods gracefully (not all countries report monthly)
- [ ] Maps ILO indicator codes to human-readable names
