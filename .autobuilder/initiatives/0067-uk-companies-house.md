# 0067 — UK Companies House API

## What
Build `uk_companies_house.py` module for the UK Companies House API — a free, government-operated REST API providing structured data on 5M+ UK-registered companies, their officers (directors), filing history, charges (secured debt), insolvency proceedings, and persons with significant control (PSC). This is high-value alternative data for corporate governance screening, credit risk assessment, and M&A signal detection.

## Why
The UK is the world's 6th-largest economy and London is the global financial capital. Companies House data is the authoritative source for UK corporate structure — all UK limited companies must file annual accounts, confirmation statements, and notify officer changes by law. New incorporations surge before IPO waves and M&A cycles. Mass director resignations are early distress signals (Carillion, Thomas Cook both showed unusual officer churn pre-collapse). Charges data reveals secured lending patterns and covenant structures. PSC (Persons with Significant Control) data exposes ultimate beneficial ownership — critical for sanctions compliance and connected-party analysis. Insolvency filings provide real-time corporate distress signals. No existing QuantClaw module covers UK company registry data.

## API
- Base: `https://api.company-information.service.gov.uk`
- Protocol: REST (GET requests)
- Auth: API key (free registration at https://developer.company-information.service.gov.uk/)
- Formats: JSON
- Rate limits: 600 requests/5 minutes (120 req/min)
- Docs: https://developer-specs.company-information.service.gov.uk/

## Key Endpoints
- `GET /search/companies?q={query}&items_per_page=20` — Search companies by name or number
- `GET /company/{company_number}` — Company profile (status, SIC codes, addresses, filing dates)
- `GET /company/{company_number}/officers` — Current and resigned officers (directors, secretaries)
- `GET /company/{company_number}/filing-history` — All filed documents with dates and categories
- `GET /company/{company_number}/charges` — Secured charges (mortgages, debentures, liens)
- `GET /company/{company_number}/insolvency` — Insolvency cases and practitioner details
- `GET /company/{company_number}/persons-with-significant-control` — Beneficial owners (>25% control)
- `GET /search/officers?q={name}` — Search officers (directors) across all companies
- `GET /search/disqualified-officers?q={name}` — Disqualified directors lookup
- `GET /advanced-search/companies?sic_codes={code}&incorporated_from={date}` — Advanced filtered search

SIC code categories useful for financial analysis: 64xx (Financial services), 65xx (Insurance), 66xx (Fund management), 70xx (Head offices/consultancy).

## Key Indicators
- **New Incorporations** — Daily/weekly count of new company registrations (business formation signal)
- **Dissolution Rate** — Companies struck off or dissolved (economic distress proxy)
- **Insolvency Filings** — Active insolvency proceedings by type (CVA, administration, liquidation)
- **Officer Churn** — Director appointments vs resignations by company/sector
- **Filing Compliance** — Late filing patterns (correlates with financial distress)
- **Charges Activity** — New charges registered (secured lending proxy)
- **PSC Changes** — Beneficial ownership changes (M&A and restructuring signals)
- **SIC Code Distribution** — Sector composition of new registrations
- **Disqualified Directors** — New disqualifications (regulatory action signal)
- **Company Age Distribution** — Survival rates by sector and incorporation year

## Module
- Filename: `uk_companies_house.py`
- Cache: 1h for search results, 6h for company profiles, 24h for filing history
- Auth: Reads `UK_COMPANIES_HOUSE_API_KEY` from `.env`

## Test Commands
```bash
python modules/uk_companies_house.py                                    # Summary statistics
python modules/uk_companies_house.py search "Barclays"                  # Search companies by name
python modules/uk_companies_house.py company 09740322                   # Company profile by number
python modules/uk_companies_house.py officers 09740322                  # Officers for a company
python modules/uk_companies_house.py filings 09740322                   # Filing history
python modules/uk_companies_house.py charges 09740322                   # Charges (secured debt)
python modules/uk_companies_house.py insolvency 09740322                # Insolvency proceedings
python modules/uk_companies_house.py psc 09740322                       # Persons with significant control
python modules/uk_companies_house.py search_officers "John Smith"       # Search directors
python modules/uk_companies_house.py sector 6411                        # Companies by SIC code
```

## Acceptance
- [ ] Company search by name, number, and SIC code
- [ ] Returns structured JSON: company_number, name, status, sic_codes, officers, filings, source
- [ ] Officer listing with appointment/resignation dates
- [ ] Filing history with document categories and dates
- [ ] Charges (secured debt) data with creation/satisfaction dates
- [ ] Insolvency case tracking with practitioner details
- [ ] PSC (beneficial ownership) extraction
- [ ] Officer search across all companies (director network mapping)
- [ ] Disqualified directors lookup
- [ ] 1h cache for searches, 6h for profiles, 24h for historical data
- [ ] CLI: `python uk_companies_house.py [command] [args]`
- [ ] API key read from `.env` (UK_COMPANIES_HOUSE_API_KEY)
- [ ] Handles rate limiting (600 req/5min) with backoff
- [ ] Pagination handling for large result sets (officers, filings)
- [ ] Company status classification (active, dissolved, liquidation, administration)
