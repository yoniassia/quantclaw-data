# QuantClaw Data Platform — Architecture

**Owner:** Shay Heffets | **Builder:** Quant | **Date:** 2026-03-18
**Primary Consumer:** signalcentre.quantclaw.org

---

## 1. Overview

Transform 970+ data collection modules from file-based scripts into a production-grade, PostgreSQL-backed data platform with quality tiers, automated pipelines, and real-time consumption via Kafka.

## 2. Quality Tiers

| Tier | Description | Criteria |
|------|-------------|----------|
| **Bronze** | Raw ingestion — data as-is from source | Module runs, returns data, stored with metadata |
| **Silver** | Cleaned — nulls handled, types validated, deduped | Schema validation passes, no critical nulls, timestamps normalized |
| **Gold** | Validated & signal-ready | Completeness >95%, timeliness within cadence, cross-source consistency checks pass |
| **Platinum** | Enriched / derived | Cross-module joins, forward-filled, composite indicators, ML features |

## 3. Infrastructure Stack

- **PostgreSQL 14 + TimescaleDB** — primary store, hypertables for time-series, locf() for forward-fill
- **Apache Kafka** — message bus, topic-per-domain, enables multi-consumer architecture
- **Redis** — hot cache (latest values), pub/sub (dashboard updates), rate limiting (API throttling)
- **Python** — pipeline framework, module runtime
- **PM2** — process management for pipeline workers and orchestrator

## 4. Database Schema

### Database: `quantclaw_data`

### 4.1 modules — Registry of all 970+ modules

```sql
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    source_file VARCHAR(500),
    source_url TEXT,
    cadence VARCHAR(20) NOT NULL DEFAULT 'daily',
    -- realtime, 1min, 5min, 15min, 1h, 4h, daily, weekly, monthly, quarterly
    granularity VARCHAR(20) NOT NULL DEFAULT 'symbol',
    -- symbol, market, macro, global
    current_tier VARCHAR(10) NOT NULL DEFAULT 'bronze',
    quality_score SMALLINT DEFAULT 0,
    output_schema JSONB,
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_modules_cadence ON modules(cadence);
CREATE INDEX idx_modules_tags ON modules USING GIN(tags);
CREATE INDEX idx_modules_tier ON modules(current_tier);
CREATE INDEX idx_modules_active ON modules(is_active) WHERE is_active = true;
```

### 4.2 tags — Hierarchical taxonomy

```sql
CREATE TABLE tag_definitions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    -- asset_class, data_type, region, sector, frequency
    label VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES tag_definitions(id),
    description TEXT,
    UNIQUE(category, label)
);

CREATE TABLE module_tags (
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tag_definitions(id) ON DELETE CASCADE,
    PRIMARY KEY (module_id, tag_id)
);
```

### 4.3 data_points — The actual data (TimescaleDB hypertable)

```sql
CREATE TABLE data_points (
    ts TIMESTAMPTZ NOT NULL,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    symbol VARCHAR(50),
    cadence VARCHAR(20) NOT NULL,
    tier VARCHAR(10) NOT NULL DEFAULT 'bronze',
    quality_score SMALLINT DEFAULT 0,
    payload JSONB NOT NULL,
    source_hash VARCHAR(64),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('data_points', 'ts',
    chunk_time_interval => INTERVAL '1 month');

CREATE INDEX idx_dp_symbol_ts ON data_points (symbol, ts DESC);
CREATE INDEX idx_dp_module_ts ON data_points (module_id, ts DESC);
CREATE INDEX idx_dp_module_symbol ON data_points (module_id, symbol, ts DESC);
CREATE INDEX idx_dp_tier ON data_points (tier);
CREATE INDEX idx_dp_payload ON data_points USING GIN (payload jsonb_path_ops);
```

### 4.4 pipeline_runs — Execution audit trail

```sql
CREATE TABLE pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    tier_target VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    -- running, success, failed, retrying
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    rows_in INTEGER DEFAULT 0,
    rows_out INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    retry_attempt SMALLINT DEFAULT 0,
    error_message TEXT,
    error_stacktrace TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_runs_module ON pipeline_runs(module_id, started_at DESC);
CREATE INDEX idx_runs_status ON pipeline_runs(status);
```

### 4.5 quality_checks — Per-run validation

```sql
CREATE TABLE quality_checks (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id),
    check_type VARCHAR(30) NOT NULL,
    -- completeness, timeliness, accuracy, consistency, schema_valid
    passed BOOLEAN NOT NULL,
    score SMALLINT DEFAULT 0,
    details JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_qc_run ON quality_checks(run_id);
```

### 4.6 alerts — Error queue + notifications

```sql
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id),
    run_id BIGINT REFERENCES pipeline_runs(id),
    severity VARCHAR(10) NOT NULL DEFAULT 'warning',
    -- info, warning, critical
    category VARCHAR(30),
    -- source_down, quality_drop, timeout, schema_change, missing_data
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    resolved BOOLEAN DEFAULT false,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    notified_channels TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_unresolved ON alerts(resolved, severity) WHERE resolved = false;
CREATE INDEX idx_alerts_module ON alerts(module_id, created_at DESC);
```

### 4.7 symbol_universe — Instrument registry

```sql
CREATE TABLE symbol_universe (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    asset_class VARCHAR(30) NOT NULL,
    -- us_equities, eu_equities, crypto, fx, indices, commodities, etf
    exchange VARCHAR(50),
    etoro_instrument_id INTEGER,
    sector VARCHAR(100),
    industry VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_universe_asset ON symbol_universe(asset_class);
CREATE INDEX idx_universe_active ON symbol_universe(is_active) WHERE is_active = true;
```

## 5. Kafka Topics

```
quantclaw.pipeline.bronze.{domain}    -- raw data ingested
quantclaw.pipeline.silver.{domain}    -- cleaned data
quantclaw.pipeline.gold.{domain}      -- validated data
quantclaw.pipeline.errors             -- all failures
quantclaw.pipeline.alerts             -- material alerts → WhatsApp
quantclaw.pipeline.status             -- module status changes
```

Domains: us_equities, sentiment, earnings, fundamentals, corporate_actions, macro, crypto, fx, commodities

## 6. Redis Usage

- `qcd:latest:{module}:{symbol}` — latest data point per module/symbol (hot cache)
- `qcd:health:{module}` — module health status
- `qcd:queue:retry` — retry queue for failed modules
- Pub/sub channel `qcd:updates` — real-time dashboard updates
- Rate limiter keys `qcd:ratelimit:{source}` — API source throttling

## 7. Pipeline Flow

```
Cron Trigger (per-module cadence)
  → Pipeline Orchestrator
    → Bronze: Module.fetch() → raw data → PostgreSQL (tier=bronze) → Kafka bronze topic
    → Silver: validate schema, clean nulls, normalize timestamps → PostgreSQL (tier=silver) → Kafka silver topic
    → Gold: completeness check, timeliness check, cross-source consistency → PostgreSQL (tier=gold) → Kafka gold topic
    → Quality checks recorded in quality_checks table
    → Module stats updated (last_run, quality_score, tier)
    → Errors: retry 3x → alert → human queue
```

## 8. Module Refactor Pattern

Each module becomes a class inheriting from BaseModule:

```python
class AaiiSentiment(BaseModule):
    name = "aaii_sentiment"
    cadence = "weekly"
    granularity = "market"
    tags = ["sentiment", "us_equities"]

    def fetch(self) -> List[DataPoint]:
        """Bronze: fetch raw data from source"""

    def clean(self, raw: List[DataPoint]) -> List[DataPoint]:
        """Silver: validate, clean, normalize"""

    def validate(self, clean: List[DataPoint]) -> QualityReport:
        """Gold: run quality checks"""
```

## 9. Forward-Fill Strategy (Cross-Cadence Joins)

TimescaleDB `locf()` enables native forward-fill at query time:

```sql
SELECT
    p.ts,
    p.symbol,
    p.payload->>'close' AS price,
    locf(e.payload->>'eps' OVER (PARTITION BY p.symbol ORDER BY p.ts)) AS eps_ffilled,
    locf(s.payload->>'bull_bear_spread' OVER (ORDER BY p.ts)) AS sentiment_ffilled
FROM data_points p
LEFT JOIN LATERAL (
    SELECT payload FROM data_points
    WHERE module_id = (SELECT id FROM modules WHERE name = 'earnings_quarterly')
    AND symbol = p.symbol AND ts <= p.ts
    ORDER BY ts DESC LIMIT 1
) e ON true
LEFT JOIN LATERAL (
    SELECT payload FROM data_points
    WHERE module_id = (SELECT id FROM modules WHERE name = 'aaii_sentiment')
    AND ts <= p.ts
    ORDER BY ts DESC LIMIT 1
) s ON true
WHERE p.module_id = (SELECT id FROM modules WHERE name = 'daily_prices')
AND p.symbol = 'AAPL'
ORDER BY p.ts DESC;
```

Materialized views for common joins (refreshed after each pipeline run).

## 10. Monitoring & Alerting

**Dashboard (signalcentre.quantclaw.org):**
- Module health grid: green/yellow/red per module
- Drill-down: module → runs → data points → individual payloads
- Quality scorecard: completeness, timeliness, accuracy per module
- Pipeline status: running/queued/failed counts
- Tag-based filtering: view by domain (US Equities, Sentiment, etc.)

**Alerts:**
- Critical: module fails 3x → WhatsApp group notification
- Warning: quality score drops below threshold
- Info: new data available, pipeline complete

## 11. Initial Symbol Universe (200)

Start with 155 active instruments from vipsignals + expand to 200:
- All current Signal Centre instruments
- Add top market-cap US equities not yet covered
- Initial focus: S&P 500 top 200 by market cap

## 12. Cron Schedule

| Cadence | Schedule | Example Modules |
|---------|----------|----------------|
| realtime | Every 1 min | price_stream (when ready) |
| hourly | Every hour at :05 | social_sentiment, news_feed |
| daily | 01:00 UTC | daily_prices, RSI, MACD, volume |
| weekly | Sunday 02:00 UTC | aaii_sentiment, COT_report |
| monthly | 1st at 03:00 UTC | macro_gdp, employment |
| quarterly | 15th of Jan/Apr/Jul/Oct | earnings_reports, 10-Q filings |
