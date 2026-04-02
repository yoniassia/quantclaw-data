# 0061 — Bank Negara Malaysia (BNM) Open API

## What
Build `bnm_malaysia.py` module for Bank Negara Malaysia's Open API — Malaysia's central bank data portal providing free, structured access to exchange rates, interest rates, Islamic banking statistics, and key economic indicators. BNM's API is one of the best-documented central bank APIs in ASEAN, returning clean JSON with no authentication required.

## Why
Malaysia is ASEAN's 3rd-largest economy and the world's 2nd-largest palm oil producer — Malaysian macro data directly affects commodity pricing for palm oil, rubber, and tin. The ringgit (MYR) is a key EM FX pair, and BNM's Overnight Policy Rate (OPR) decisions affect regional carry trade models. Malaysia's Islamic finance sector is the world's largest, making BNM data essential for tracking Sukuk markets and Shariah-compliant instruments. QuantClaw has zero ASEAN central bank coverage — BNM fills a critical gap.

## API
- Base: `https://api.bnm.gov.my`
- Protocol: REST (GET requests)
- Auth: None (fully open, no key required)
- Formats: JSON
- Rate limits: Fair use (no hard limit published)
- Docs: https://apikijangportal.bnm.gov.my/

## Key Endpoints
- `GET /public/exchange-rate` — Daily MYR exchange rates against 20+ currencies
- `GET /public/exchange-rate/currency/{currency_code}` — Specific currency pair history
- `GET /public/opr` — Overnight Policy Rate (BNM's policy rate, equivalent to Fed Funds)
- `GET /public/base-rate` — Base rate and base lending rates for all banks
- `GET /public/interest-rate` — Interbank, deposit, and lending rates
- `GET /public/kijang-emas` — Gold prices (Kijang Emas, BNM's gold coin program)
- `GET /public/islamic-interbank-rate` — Islamic interbank money market rates
- `GET /public/consumer-alert` — Consumer financial fraud alerts

## Key Indicators
- **Overnight Policy Rate (OPR)** — BNM's key policy rate, affects all ASEAN rate models
- **MYR Exchange Rates** — Daily rates vs USD, SGD, CNY, JPY, EUR, GBP, THB, IDR
- **Interbank Rates** — KLIBOR (Kuala Lumpur Interbank Offered Rate) term structure
- **Islamic Interbank Rate** — Islamic money market rates (unique to Malaysian system)
- **Base Rate / BLR** — Bank-level lending rates across Malaysian banking system
- **Kijang Emas Gold Price** — BNM gold prices in MYR (buy/sell spreads)
- **Currency Pair History** — Historical FX rates for all supported pairs

## Module
- Filename: `bnm_malaysia.py`
- Cache: 1h for FX/rates, 24h for policy rates and structural data
- Auth: None required

## Test Commands
```bash
python modules/bnm_malaysia.py                          # Latest key indicators summary
python modules/bnm_malaysia.py exchange_rate             # All MYR exchange rates
python modules/bnm_malaysia.py exchange_rate USD         # MYR/USD rate
python modules/bnm_malaysia.py opr                       # Overnight Policy Rate
python modules/bnm_malaysia.py interbank                 # KLIBOR interbank rates
python modules/bnm_malaysia.py islamic_rate              # Islamic interbank rates
python modules/bnm_malaysia.py kijang_emas               # Gold prices in MYR
python modules/bnm_malaysia.py base_rate                 # Bank lending rates
```

## Acceptance
- [ ] Fetches MYR exchange rates for 20+ currencies
- [ ] Returns structured JSON: date, value, indicator, currency_pair, source
- [ ] OPR policy rate with historical changes
- [ ] Interbank rate term structure (overnight, 1w, 1m, 3m, 6m, 12m)
- [ ] Islamic interbank rates (unique dataset)
- [ ] Kijang Emas gold prices with buy/sell spreads
- [ ] Base rate comparison across Malaysian banks
- [ ] 1h cache for FX/rates, 24h for policy data
- [ ] CLI: `python bnm_malaysia.py [indicator] [args]`
- [ ] No API key required
- [ ] Handles BNM API error responses and empty data periods
- [ ] Date range support for historical queries
