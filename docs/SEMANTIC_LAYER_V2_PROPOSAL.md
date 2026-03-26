# QuantClaw Data — Semantic Layer V2: Taxonomy & Architecture Proposal

> Deep research output — March 26, 2026
> For: Shay Heffets, Yoni Assia

---

## Executive Summary

The current DCC semantic layer (schema-catalog → NL query engine → safety layer → chat UI) works well for ad-hoc equity queries but has structural limitations that will break as we add more apps (TerminalX, AgentX, PICentral, external consumers). This proposal addresses three problems:

1. **No canonical instrument identity** — `symbol` is a free VARCHAR; no ISIN, FIGI, or standard identifiers
2. **No formal taxonomy** — sector/industry are scattered strings across 4+ tables with no hierarchy or controlled vocabulary
3. **Equity-only semantic model** — matviews and routing only cover stocks; crypto, FX, ETFs, bonds, macro exist in legacy modules but aren't wired into the semantic layer

---

## Part 1: Current State (What We Have)

### Classification Fields Today

| Location | Fields | Problem |
|----------|--------|---------|
| `symbol_universe` | `asset_class`, `sector`, `industry` | Free text, no codes, no hierarchy |
| `gf_profiles` | `sector`, `industry`, `country` | GuruFocus strings, may differ from `symbol_universe` |
| `platinum_records` | `sector`, `industry` | Denormalized copy, can drift |
| `mv_symbol_latest` | `sector` only | Missing industry, country, asset_class |
| `data_points.payload` | Per-module JSON | Unstructured, inconsistent keys |
| `tag_definitions` | Module tags only | Classifies pipelines, not instruments |

### Identifiers Today

| ID Type | Where Used | Coverage |
|---------|-----------|----------|
| `symbol` (string) | Everywhere | Universal but no standard format |
| `etoro_instrument_id` (int) | `symbol_universe`, `gf_symbol_map` | eToro instruments only |
| `gf_symbol` (`EXCHANGE:TICKER`) | GF tables | GuruFocus API only |
| ISIN | Not in schema | Missing entirely |
| FIGI | Not in schema | Missing entirely |

### NL Routing Gaps

- `symbol_universe` never auto-selected by keyword routing
- `mv_cross_cadence_daily` never selected despite being a rich semantic asset
- `data_points` excluded from most queries
- Views (like `platinum_latest`) invisible to catalog
- No synonym handling ("revenue" vs "sales" vs "top line")

---

## Part 2: Instrument Taxonomy Design

### 2.1 Instrument Master (`dim_instrument`)

The golden record for every tradeable thing in the system. One row per instrument.

```
dim_instrument
├── instrument_id          (UUID, PK — internal)
├── symbol                 (VARCHAR, unique — backward compat)
├── display_name           (VARCHAR)
├── isin                   (CHAR(12), nullable — ISO 6166)
├── figi                   (CHAR(12), nullable — OpenFIGI)
├── cfi_code               (CHAR(6), nullable — ISO 10962)
├── lei                    (CHAR(20), nullable — issuer LEI)
├── etoro_instrument_id    (INT, nullable)
├── gf_symbol              (VARCHAR, nullable)
├── yahoo_ticker           (VARCHAR, nullable)
├── instrument_type_id     (FK → dim_instrument_type)
├── gics_sub_industry_id   (FK → dim_gics, nullable — equities only)
├── domicile_country_code  (CHAR(2), ISO 3166-1)
├── primary_exchange_mic   (CHAR(4), ISO 10383)
├── currency               (CHAR(3), ISO 4217)
├── is_active              (BOOLEAN)
├── metadata               (JSONB — extensibility)
├── created_at             (TIMESTAMPTZ)
├── updated_at             (TIMESTAMPTZ)
```

**Key design decisions:**
- Multiple identifier columns for cross-referencing (eToro ID, GF symbol, Yahoo ticker, ISIN, FIGI)
- ISO standards for country, exchange, currency
- `instrument_type_id` for asset class hierarchy (not a free string)
- `gics_sub_industry_id` for industry hierarchy (not a free string)
- Backward compatible via `symbol` column

### 2.2 GICS Hierarchy (`dim_gics`)

4-level industry classification aligned with MSCI/S&P standard.

```
dim_gics
├── id                     (SERIAL PK)
├── gics_code              (VARCHAR(8), unique — "10", "1010", "101010", "10101010")
├── level                  (SMALLINT — 1=sector, 2=group, 3=industry, 4=sub_industry)
├── name                   (VARCHAR)
├── parent_id              (FK → self, nullable)
├── effective_date         (DATE — for rebalances)
├── is_current             (BOOLEAN)
```

Structure: 11 sectors → 25 industry groups → 74 industries → 163 sub-industries

**Why GICS over ICB?** GICS is the dominant standard for equity investing, used by MSCI, S&P, and most institutional investors. eToro's sector labels already roughly map to GICS sectors.

### 2.3 Instrument Type Hierarchy (`dim_instrument_type`)

Multi-asset classification — goes beyond equities.

```
dim_instrument_type
├── id                     (SERIAL PK)
├── code                   (VARCHAR, unique — "EQ.CS", "EQ.ADR", "ETF", "FX.SPOT", etc.)
├── name                   (VARCHAR)
├── asset_class            (VARCHAR — "Equity", "Fixed Income", "FX", "Commodity", "Crypto", "Derivative")
├── sub_class              (VARCHAR — "Common Stock", "ADR", "ETF", "Government Bond", etc.)
├── parent_id              (FK → self, nullable)
├── cfi_category           (CHAR(1), nullable — maps to ISO 10962 char 1)
├── is_tradeable           (BOOLEAN)
```

**Proposed hierarchy:**

```
Equity (EQ)
├── Common Stock (EQ.CS)
├── ADR/GDR (EQ.ADR)
├── Preferred (EQ.PREF)
├── REIT (EQ.REIT)
└── SPAC (EQ.SPAC)

Fund (FUND)
├── ETF (FUND.ETF)
├── Mutual Fund (FUND.MF)
└── Closed-End Fund (FUND.CEF)

Fixed Income (FI)
├── Government Bond (FI.GOV)
├── Corporate Bond (FI.CORP)
├── Municipal Bond (FI.MUNI)
└── Treasury Bill/Note (FI.TBILL)

FX (FX)
├── Spot (FX.SPOT)
└── Forward (FX.FWD)

Commodity (CMD)
├── Energy (CMD.ENERGY)
├── Metal (CMD.METAL)
└── Agricultural (CMD.AGRI)

Crypto (CRYPTO)
├── Layer 1 (CRYPTO.L1)
├── Token (CRYPTO.TOKEN)
├── Stablecoin (CRYPTO.STABLE)
└── DeFi Token (CRYPTO.DEFI)

Derivative (DERIV)
├── Listed Option (DERIV.OPT)
├── Future (DERIV.FUT)
└── CFD (DERIV.CFD)

Index (IDX)
├── Equity Index (IDX.EQ)
├── Bond Index (IDX.FI)
└── Volatility Index (IDX.VOL)

Macro Indicator (MACRO)
├── Interest Rate (MACRO.RATE)
├── Economic (MACRO.ECON)
└── Sentiment (MACRO.SENT)
```

### 2.4 Geography Dimension (`dim_geography`)

```
dim_geography
├── id                     (SERIAL PK)
├── country_code           (CHAR(2), ISO 3166-1)
├── country_name           (VARCHAR)
├── region                 (VARCHAR — "North America", "Europe", "Asia Pacific", etc.)
├── sub_region             (VARCHAR — "Western Europe", "Southeast Asia", etc.)
├── developed_emerging     (VARCHAR — "Developed", "Emerging", "Frontier")
```

---

## Part 3: Semantic Layer V2 Architecture

### 3.1 Three-Layer Model

```
┌─────────────────────────────────────────────────────┐
│                    CONSUMERS                         │
│  TerminalX │ AgentX │ PICentral │ DCC │ External    │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              SEMANTIC LAYER (V2)                      │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Metrics     │  │ Dimensions   │  │ NL Router   │ │
│  │ Catalog     │  │ (Taxonomy)   │  │ (Intent +   │ │
│  │             │  │              │  │  Schema)    │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                │                  │        │
│  ┌──────▼──────────────▼──────────────────▼──────┐ │
│  │           Semantic View Registry               │ │
│  │  (Metric definitions, join paths, synonyms)    │ │
│  └────────────────────┬───────────────────────────┘ │
└───────────────────────┼─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              DATA LAYER                              │
│                                                       │
│  dim_instrument │ dim_gics │ dim_instrument_type      │
│  dim_geography  │ fact_price │ fact_fundamentals       │
│  fact_rankings  │ fact_insider │ fact_sentiment         │
│  mv_symbol_latest │ mv_cross_cadence │ data_points    │
└─────────────────────────────────────────────────────┘
```

### 3.2 Metrics Catalog (Define Once, Use Everywhere)

Instead of each app computing its own metrics, we define canonical metrics in one place.

```yaml
# metrics/equity_valuation.yaml
metrics:
  pe_ratio:
    display_name: "P/E Ratio"
    description: "Price to trailing twelve months earnings"
    formula: "current_price / NULLIF(eps_ttm, 0)"
    grain: symbol
    dimensions: [sector, industry, country, exchange, instrument_type]
    source_table: mv_symbol_latest
    non_additive: true
    
  market_cap:
    display_name: "Market Capitalization"
    formula: "current_price * shares_outstanding"
    grain: symbol
    dimensions: [sector, industry, country, asset_class]
    unit: USD
    
  gf_score:
    display_name: "GuruFocus Score"
    description: "Composite quality + value + growth + momentum score (0-100)"
    formula: "gf_score"
    grain: symbol
    source_table: gf_rankings
    range: [0, 100]

  alpha_score:
    display_name: "Alpha Composite Score"
    description: "QuantClaw proprietary composite rating"
    formula: "composite_score"
    grain: symbol
    source_table: platinum_records
    range: [0, 100]
```

**Benefits:**
- TerminalX, AgentX, DCC all use the same metric definitions
- Metric changes propagate to all consumers automatically
- Self-documenting — new developers know what each metric means
- NL engine uses metric catalog for better query understanding

### 3.3 Enhanced NL Router (Intent Classification)

Replace keyword matching with structured intent classification.

**Current:** keyword → table list (brittle, misses tables)

**Proposed:** question → intent → (metrics, dimensions, filters, time window)

```
Intent Schema:
├── entity_type     ("equity", "etf", "crypto", "macro", "guru", "module")
├── metric_refs     (["pe_ratio", "market_cap"])  — from metrics catalog
├── dimensions      (["sector", "industry", "country"])
├── filters         (["sector = Technology", "market_cap > 10B"])
├── time_scope      ("latest", "trailing_12m", "2024-01-01..2025-01-01")
├── aggregation     ("rank", "top_n", "compare", "trend")
├── output_hint     ("table", "chart", "single_value", "list")
```

**Example mappings:**

| Question | Intent |
|----------|--------|
| "Top 10 tech stocks by GF score" | entity=equity, metric=gf_score, dim=sector, filter=sector=Technology, agg=top_n(10) |
| "Insider buying in healthcare last month" | entity=equity, metric=insider_buy_count, dim=sector, filter=sector=Healthcare, time=30d |
| "Compare AAPL and MSFT fundamentals" | entity=equity, metric=[revenue,eps,roe], filter=symbol IN (AAPL,MSFT), agg=compare |
| "Bitcoin price trend this year" | entity=crypto, metric=price, time=ytd, output=line_chart |
| "Which ETFs hold NVDA?" | entity=etf, metric=weight, filter=holding=NVDA, agg=list |

### 3.4 Synonym Dictionary

Map natural language terms to canonical schema names.

```json
{
  "revenue": ["sales", "top line", "total revenue", "net sales"],
  "pe_ratio": ["P/E", "price to earnings", "earnings multiple", "PE"],
  "market_cap": ["market capitalization", "mkt cap", "size"],
  "gf_score": ["guru focus score", "GF", "quality score"],
  "sector": ["industry sector", "GICS sector"],
  "insider_buying": ["insider purchases", "insider buys", "management buying"],
  "eps": ["earnings per share", "EPS", "earnings"],
  "rsi": ["RSI", "relative strength", "RSI 14"],
  "sma": ["moving average", "SMA", "simple moving average"],
  "fair_value": ["intrinsic value", "DCF value", "GF value", "fair price"]
}
```

### 3.5 Verified Query Library

Pre-validated SQL templates for common questions. The NL engine checks here first before generating fresh SQL.

```yaml
verified_queries:
  top_stocks_by_score:
    patterns:
      - "top {n} stocks by {metric}"
      - "best {metric} stocks"
      - "highest {metric}"
    sql_template: |
      SELECT symbol, company_name, sector, {metric_col}
      FROM mv_symbol_latest
      WHERE {metric_col} IS NOT NULL
      ORDER BY {metric_col} DESC
      LIMIT {n}
    parameters:
      n: { type: int, default: 10 }
      metric: { type: metric_ref, maps_to: metric_col }
      
  sector_comparison:
    patterns:
      - "compare sectors by {metric}"
      - "sector breakdown"
      - "which sector has the highest {metric}"
    sql_template: |
      SELECT g.name AS sector, 
             AVG({metric_col}) AS avg_{metric},
             COUNT(*) AS stock_count
      FROM mv_symbol_latest m
      JOIN dim_instrument i ON i.symbol = m.symbol
      JOIN dim_gics g ON g.id = i.gics_sub_industry_id
      WHERE g.level = 1
      GROUP BY g.name
      ORDER BY avg_{metric} DESC
```

---

## Part 4: Migration Path (How We Get There)

### Phase 1: Foundation (Week 1-2)
**Goal:** Instrument master + GICS hierarchy. Zero breaking changes.

1. Create `dim_gics` table, seed with full GICS hierarchy (163 sub-industries)
2. Create `dim_instrument_type` table, seed with type hierarchy
3. Create `dim_geography` table, seed country/region data
4. Create `dim_instrument` table — populate from `symbol_universe` + `gf_profiles`
5. Build GICS mapper: GuruFocus sector/industry strings → GICS codes (fuzzy match + manual overrides)
6. Add ISIN/FIGI columns, backfill from OpenFIGI API (free, 200 req/sec)
7. Keep `symbol_universe` as-is (backward compat) — `dim_instrument` becomes the new canonical source

### Phase 2: Semantic Layer (Week 2-3)
**Goal:** Metrics catalog + enhanced NL router.

1. Define metrics YAML for all existing computed values
2. Build synonym dictionary from common user queries (mine NL chat history)
3. Enhance `selectRelevantSchema()` → intent-based routing
4. Add `dim_instrument`, `dim_gics`, `dim_instrument_type` to schema catalog
5. Build verified query library (start with top 20 most common questions)
6. Update `mv_symbol_latest` to include `industry`, `country`, `gics_sector`, `gics_industry`, `instrument_type`

### Phase 3: Multi-Asset Expansion (Week 3-4)
**Goal:** Bring non-equity data into the semantic model.

1. Create `mv_crypto_latest`, `mv_macro_latest`, `mv_etf_latest` materialized views
2. Wire legacy crypto/FX/bond modules into `data_points` with proper `dim_instrument` entries
3. Extend NL router to handle multi-asset queries
4. Add cross-asset queries: "compare gold vs S&P 500 YTD"

### Phase 4: Multi-App Contract (Week 4+)
**Goal:** Standardized API for all consumers.

1. Semantic API layer: `/api/v2/metrics/{metric}?dimensions=sector&filters=...`
2. MCP v2 tools that use metrics catalog (not raw SQL)
3. TerminalX adapter, AgentX adapter — same data, same definitions
4. Row-level security for multi-tenant access (per-app API keys with allowed metrics/dimensions)

---

## Part 5: Multi-App Access Architecture

### Current: Each App Queries Differently

```
TerminalX  →  raw SQL / custom endpoints
AgentX     →  MCP tools (per-module)
PICentral  →  MCP tools
DCC        →  NL → SQL → PG
External   →  REST API (ad hoc)
```

Problem: 5 apps, 5 different interpretations of "P/E ratio" or "market cap"

### Proposed: Unified Semantic Contract

```
All Apps  →  Semantic API  →  Metric Resolution  →  SQL Generation  →  PG
                 │
                 ├── GET /api/v2/query
                 │     { metric: "pe_ratio", dimensions: ["sector"], filters: [...] }
                 │
                 ├── GET /api/v2/instruments/{symbol}
                 │     Returns full taxonomy: GICS, type, identifiers, geography
                 │
                 ├── GET /api/v2/metrics
                 │     Lists all available metrics with definitions
                 │
                 ├── GET /api/v2/dimensions
                 │     Lists all dimension hierarchies (GICS, type, geography)
                 │
                 └── POST /api/v2/nl-query
                       Same NL chat but backed by metrics catalog
```

**Benefits for each app:**

| App | Current Pain | V2 Benefit |
|-----|-------------|------------|
| **TerminalX** | Must know raw table schemas | Query by metric name, get consistent definitions |
| **AgentX** | MCP tools are module-specific | Ask for "alpha_score" across any dimension |
| **PICentral** | Limited to what MCP exposes | Full taxonomy drill-down (sector → industry → sub-industry) |
| **DCC** | NL routing misses tables | Intent-based routing + verified queries = fewer errors |
| **External** | No standard contract | Self-documenting API with metric catalog |

---

## Part 6: Data Quality & Governance

### Source of Truth Priority

```
Instrument identity:  dim_instrument (golden record)
GICS classification:  dim_gics (seeded from MSCI standard)
Sector/Industry:      dim_instrument.gics_sub_industry_id → dim_gics (NOT free text)
Prices:               financial_datasets → eToro SAPI (fallback)
Fundamentals:         GuruFocus → Financial Datasets (fallback)
```

### Lineage Rules

- Every metric definition documents its source table(s) and formula
- Every `dim_instrument` row tracks when identifiers were last verified
- GICS mappings include confidence score (automatic vs manually verified)
- Changes to metric definitions are versioned (Git) with effective dates

---

## Appendix A: GICS Sector → Code Mapping

| Code | Sector |
|------|--------|
| 10 | Energy |
| 15 | Materials |
| 20 | Industrials |
| 25 | Consumer Discretionary |
| 30 | Consumer Staples |
| 35 | Health Care |
| 40 | Financials |
| 45 | Information Technology |
| 50 | Communication Services |
| 55 | Utilities |
| 60 | Real Estate |

Full hierarchy: 11 sectors → 25 industry groups → 74 industries → 163 sub-industries

## Appendix B: OpenFIGI Backfill Plan

OpenFIGI API is free (200 req/sec, no key needed for basic access).

```
POST https://api.openfigi.com/v3/mapping
[{"idType": "TICKER", "idValue": "AAPL", "exchCode": "US"}]

Response includes: FIGI, name, ticker, exchCode, securityType, marketSector
```

We can backfill FIGI + security type for all ~273 instruments in one API call (batch of 100).

## Appendix C: eToro Sector → GICS Mapping (Sample)

| eToro Sector String | GICS Code | GICS Sector |
|---------------------|-----------|-------------|
| "Technology" | 45 | Information Technology |
| "Healthcare" | 35 | Health Care |
| "Financial Services" | 40 | Financials |
| "Consumer Cyclical" | 25 | Consumer Discretionary |
| "Consumer Defensive" | 30 | Consumer Staples |
| "Communication Services" | 50 | Communication Services |
| "Energy" | 10 | Energy |
| "Industrials" | 20 | Industrials |
| "Basic Materials" | 15 | Materials |
| "Utilities" | 55 | Utilities |
| "Real Estate" | 60 | Real Estate |

---

*End of proposal. Ready for review and prioritization.*
