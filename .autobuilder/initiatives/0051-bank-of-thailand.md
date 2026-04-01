# 0051 — Bank of Thailand (BOT) API Portal

## What
Build `bank_of_thailand.py` module for the Bank of Thailand's public data API. BOT provides programmatic access to Thai exchange rates, interest rates, financial institution statistics, and economic indicators. Thailand is ASEAN's second-largest economy and a major manufacturing/tourism hub — critical for EM macro and supply chain analysis.

## Why
Thailand is a top-10 emerging market by GDP and a bellwether for ASEAN economic health. Thai baht movements, BOT policy rates, and capital flow data are essential for EM FX models, carry trade strategies, and regional contagion analysis. Currently we have zero Thailand coverage.

## API
- Base: `https://apigw1.bot.or.th/bot/public`
- Protocol: REST
- Auth: API key (free registration at https://apiportal.bot.or.th/)
- Formats: JSON
- Rate limits: 500 requests/day (free tier)
- Docs: https://apiportal.bot.or.th/bot/public

## Key Endpoints
- `GET /Stat-ExchangeRate/v2/DAILY_AVG_EXG_RATE/` — Daily average exchange rates (THB vs 40+ currencies)
- `GET /Stat-InterestRate/v2/DAILY_INTERBANK_RATE/` — Interbank lending rates
- `GET /Stat-InterestRate/v2/POLICY_RATE/` — BOT policy rate history
- `GET /Stat-FinancialInstitutions/v1/FI_BALANCE_SHEET/` — Financial institution balance sheets
- `GET /Stat-MacroEconomic/v1/GDP/` — GDP components
- `GET /Stat-MacroEconomic/v1/CPI/` — Consumer Price Index
- Query params: `start_period=YYYY-MM-DD`, `end_period=YYYY-MM-DD`, `currency=USD`

## Indicators to Implement
- Daily THB exchange rates (USD, EUR, JPY, CNY, major EM currencies)
- BOT policy rate and interbank rate history
- Thai CPI and core inflation (monthly)
- GDP growth (quarterly, real and nominal)
- Capital flows (foreign investment in Thai bonds/equities)
- Financial institution aggregate balance sheets

## Module
- Filename: `bank_of_thailand.py`
- Cache: 1h for FX rates, 24h for macro indicators
- Auth: Reads `BOT_API_KEY` from `.env`

## Test Commands
```bash
python modules/bank_of_thailand.py                    # Latest key indicators
python modules/bank_of_thailand.py fx_rates            # Daily exchange rates
python modules/bank_of_thailand.py policy_rate         # BOT policy rate history
python modules/bank_of_thailand.py cpi                 # CPI inflation
python modules/bank_of_thailand.py gdp                 # GDP quarterly
```

## Acceptance
- [ ] Fetches exchange rates, policy rate, CPI, GDP
- [ ] Returns structured JSON: date, value, indicator, unit, source
- [ ] Date range queries via start_period/end_period
- [ ] Multi-currency FX support (40+ pairs vs THB)
- [ ] 1h cache for FX, 24h for macro
- [ ] CLI: `python bank_of_thailand.py [command]`
- [ ] API key read from `.env` (BOT_API_KEY)
- [ ] Handles rate limiting (500 req/day) with backoff
