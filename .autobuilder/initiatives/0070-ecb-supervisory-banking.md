# 0070 — ECB Supervisory Banking Statistics (SSM Data)

## What
Build `ecb_supervisory_banking.py` module for the ECB's Supervisory Banking Statistics published through the Statistical Data Warehouse (SDW) SDMX API. This covers aggregated prudential data for all significant banks under ECB direct supervision (~110 banking groups representing 82% of Euro area banking assets). Provides capital adequacy ratios (CET1, Tier 1), non-performing loan ratios, return on equity, liquidity coverage, leverage ratios, and asset quality metrics. This is fundamentally different from existing ECB modules (which cover monetary policy, FX rates, and HICP) — this module focuses on bank health and financial stability data.

## Why
Banking sector health is the transmission mechanism for monetary policy and the primary systemic risk channel. CET1 capital ratios determine banks' capacity to lend and absorb losses — declining ratios preceded every major banking crisis (2008 GFC, 2012 Euro crisis, 2023 SVB). NPL ratios are the earliest signal of credit cycle deterioration, rising 6-12 months before recession declarations. ROE drives bank equity valuations (Euro STOXX Banks index) and dividend sustainability. Liquidity Coverage Ratios (LCR) reveal stress points before they become public — Silicon Valley Bank's LCR deteriorated quarters before its collapse. ECB supervisory data covers the entire Euro area banking system with quarterly granularity. Existing ECB modules cover monetary aggregates and FX; no QuantClaw module provides bank-level supervisory metrics.

## API
- Base: `https://data-api.ecb.europa.eu/service`
- Protocol: SDMX 2.1 REST (GET requests)
- Auth: None (fully open, no key required)
- Formats: SDMX-JSON, SDMX-ML (XML), CSV
- Rate limits: Fair use (no hard limit, ~60 req/min recommended)
- Docs: https://data.ecb.europa.eu/help/api/overview

## Key Endpoints
- `GET /data/CBD2/{frequency}.{ref_area}.{rep_agent}.{cb_item}.{maturity}.{data_type}?startPeriod={date}&format=csvdata` — Consolidated Banking Data (aggregated bank balance sheets)
- `GET /data/SUP/{frequency}.{ref_area}.{sup_item}?format=csvdata` — Supervisory statistics (capital ratios, NPLs, profitability)
- `GET /data/BSI/{frequency}.{ref_area}.{bs_item}?format=csvdata` — Balance Sheet Items (MFI balance sheet, for cross-referencing)
- `GET /dataflow/ECB?format=jsondata` — List all available ECB dataflows
- `GET /codelist/ECB/CL_AREA?format=jsondata` — Country code list

Key series for supervisory data (CBD2 dataflow):
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E03.T` — CET1 Capital Ratio (Euro area aggregate)
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E04.T` — Tier 1 Capital Ratio
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E08.T` — Non-performing Loans Ratio
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E15.T` — Return on Equity
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E16.T` — Return on Assets
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E20.T` — Leverage Ratio
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E25.T` — Liquidity Coverage Ratio
- `Q.U2.X0.Z5.Z0.Z.A.Z.Z.Z.Z.Z.E30.T` — Cost-to-Income Ratio

Country breakdown: Replace `U2` (Euro area) with `DE` (Germany), `FR` (France), `IT` (Italy), `ES` (Spain), etc.

## Key Indicators
- **CET1 Capital Ratio** — Common Equity Tier 1 / Risk-Weighted Assets (solvency core metric)
- **Tier 1 Capital Ratio** — Broader Tier 1 capital adequacy
- **Total Capital Ratio** — Overall regulatory capital buffer
- **NPL Ratio** — Non-performing loans / total gross loans (credit quality)
- **NPL Coverage Ratio** — Provisions / NPLs (loss absorption capacity)
- **Return on Equity** — Net income / shareholders' equity (bank profitability)
- **Return on Assets** — Net income / total assets (efficiency metric)
- **Cost-to-Income Ratio** — Operating expenses / operating income (operational efficiency)
- **Leverage Ratio** — Tier 1 capital / total exposure (non-risk-weighted solvency)
- **Liquidity Coverage Ratio** — HQLA / 30-day net outflows (short-term liquidity stress)
- **Loan-to-Deposit Ratio** — Total loans / total deposits (funding structure)
- **Risk-Weighted Asset Density** — RWA / total assets (risk profile indicator)

## Module
- Filename: `ecb_supervisory_banking.py`
- Cache: 24h (quarterly data releases with ~3 month lag)
- Auth: None required

## Test Commands
```bash
python modules/ecb_supervisory_banking.py                              # Euro area banking overview
python modules/ecb_supervisory_banking.py cet1                         # CET1 ratio trend
python modules/ecb_supervisory_banking.py npl                          # NPL ratio across countries
python modules/ecb_supervisory_banking.py roe                          # Return on equity
python modules/ecb_supervisory_banking.py lcr                          # Liquidity coverage ratio
python modules/ecb_supervisory_banking.py leverage                     # Leverage ratio
python modules/ecb_supervisory_banking.py country DE                   # Germany banking metrics
python modules/ecb_supervisory_banking.py country IT                   # Italy banking metrics
python modules/ecb_supervisory_banking.py compare cet1 DE FR IT ES     # Cross-country CET1 comparison
python modules/ecb_supervisory_banking.py dataflows                    # List available banking dataflows
```

## Acceptance
- [ ] Fetches CET1, NPL, ROE, ROA, LCR, leverage, cost-to-income ratios
- [ ] Returns structured JSON: country, period, indicator, value, unit, source, dataflow
- [ ] SDMX 2.1 REST protocol compliance (consistent with existing ECB modules)
- [ ] Euro area aggregate and individual country breakdowns
- [ ] Quarterly time series with startPeriod/endPeriod filtering
- [ ] Cross-country comparison for any indicator
- [ ] Dataflow and codelist discovery endpoints
- [ ] 24h caching (quarterly release cadence)
- [ ] CLI: `python ecb_supervisory_banking.py [indicator] [country]`
- [ ] No API key required
- [ ] SDMX key construction for CBD2/SUP dataflows
- [ ] Handles varying data availability across countries and periods
- [ ] Maps ECB series keys to human-readable indicator names
- [ ] Trend detection: flag significant quarter-over-quarter changes
- [ ] Compatible with existing ECB module patterns for potential future merge
