-- QuantClaw Data Platform — Database Schema
-- Database: quantclaw_data
-- TimescaleDB required

-- ============================================
-- 1. Symbol Universe
-- ============================================
CREATE TABLE IF NOT EXISTS symbol_universe (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    asset_class VARCHAR(30) NOT NULL,
    exchange VARCHAR(50),
    etoro_instrument_id INTEGER,
    sector VARCHAR(100),
    industry VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_universe_asset ON symbol_universe(asset_class);
CREATE INDEX IF NOT EXISTS idx_universe_active ON symbol_universe(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_universe_etoro ON symbol_universe(etoro_instrument_id) WHERE etoro_instrument_id IS NOT NULL;

-- ============================================
-- 2. Module Registry
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    display_name VARCHAR(300),
    source_file VARCHAR(500),
    source_url TEXT,
    cadence VARCHAR(20) NOT NULL DEFAULT 'daily',
    granularity VARCHAR(20) NOT NULL DEFAULT 'symbol',
    current_tier VARCHAR(10) NOT NULL DEFAULT 'bronze',
    quality_score SMALLINT DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 100),
    output_schema JSONB,
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    consecutive_failures SMALLINT DEFAULT 0,
    avg_duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_modules_cadence ON modules(cadence);
CREATE INDEX IF NOT EXISTS idx_modules_tier ON modules(current_tier);
CREATE INDEX IF NOT EXISTS idx_modules_active ON modules(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_modules_next_run ON modules(next_run_at) WHERE is_active = true;

-- ============================================
-- 3. Tag System (hierarchical taxonomy)
-- ============================================
CREATE TABLE IF NOT EXISTS tag_definitions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    label VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES tag_definitions(id),
    description TEXT,
    UNIQUE(category, label)
);

CREATE TABLE IF NOT EXISTS module_tags (
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tag_definitions(id) ON DELETE CASCADE,
    PRIMARY KEY (module_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_module_tags_tag ON module_tags(tag_id);

-- ============================================
-- 4. Data Points (TimescaleDB hypertable)
-- ============================================
CREATE TABLE IF NOT EXISTS data_points (
    ts TIMESTAMPTZ NOT NULL,
    module_id INTEGER NOT NULL,
    symbol VARCHAR(50),
    cadence VARCHAR(20) NOT NULL,
    tier VARCHAR(10) NOT NULL DEFAULT 'bronze',
    quality_score SMALLINT DEFAULT 0,
    payload JSONB NOT NULL,
    source_hash VARCHAR(64),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('data_points', 'ts',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_dp_symbol_ts ON data_points (symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_dp_module_ts ON data_points (module_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_dp_module_symbol_ts ON data_points (module_id, symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_dp_tier ON data_points (tier);
CREATE INDEX IF NOT EXISTS idx_dp_payload ON data_points USING GIN (payload jsonb_path_ops);

-- ============================================
-- 5. Pipeline Runs (execution audit trail)
-- ============================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    tier_target VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('queued', 'running', 'success', 'failed', 'retrying', 'skipped')),
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

CREATE INDEX IF NOT EXISTS idx_runs_module ON pipeline_runs(module_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_status ON pipeline_runs(status) WHERE status IN ('running', 'queued', 'retrying');
CREATE INDEX IF NOT EXISTS idx_runs_recent ON pipeline_runs(started_at DESC);

-- ============================================
-- 6. Quality Checks
-- ============================================
CREATE TABLE IF NOT EXISTS quality_checks (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    check_type VARCHAR(30) NOT NULL
        CHECK (check_type IN ('completeness', 'timeliness', 'accuracy', 'consistency', 'schema_valid', 'freshness')),
    passed BOOLEAN NOT NULL,
    score SMALLINT DEFAULT 0 CHECK (score BETWEEN 0 AND 100),
    details JSONB DEFAULT '{}',
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qc_run ON quality_checks(run_id);
CREATE INDEX IF NOT EXISTS idx_qc_failed ON quality_checks(passed) WHERE passed = false;

-- ============================================
-- 7. Alerts
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id),
    run_id BIGINT REFERENCES pipeline_runs(id),
    severity VARCHAR(10) NOT NULL DEFAULT 'warning'
        CHECK (severity IN ('info', 'warning', 'critical')),
    category VARCHAR(30)
        CHECK (category IN ('source_down', 'quality_drop', 'timeout', 'schema_change',
                           'missing_data', 'rate_limit', 'auth_failure', 'system')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    resolved BOOLEAN DEFAULT false,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    notified_channels TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON alerts(resolved, severity) WHERE resolved = false;
CREATE INDEX IF NOT EXISTS idx_alerts_module ON alerts(module_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, created_at DESC) WHERE resolved = false;

-- ============================================
-- 8. Seed Tags
-- ============================================
INSERT INTO tag_definitions (category, label, description) VALUES
    ('asset_class', 'US Equities', 'US-listed stocks and ETFs'),
    ('asset_class', 'EU Equities', 'European-listed stocks'),
    ('asset_class', 'Crypto', 'Cryptocurrencies and DeFi'),
    ('asset_class', 'FX', 'Foreign exchange pairs'),
    ('asset_class', 'Indices', 'Market indices'),
    ('asset_class', 'Commodities', 'Physical commodities'),
    ('asset_class', 'ETF', 'Exchange-traded funds'),
    ('data_type', 'Fundamentals', 'Financial statements, ratios, valuations'),
    ('data_type', 'Corporate Actions', 'Dividends, splits, M&A, buybacks'),
    ('data_type', 'Sentiment', 'Social sentiment, surveys, fear/greed'),
    ('data_type', 'News', 'News feeds, NLP analysis'),
    ('data_type', 'Technical', 'Price-derived indicators, patterns'),
    ('data_type', 'Macro', 'GDP, employment, rates, inflation'),
    ('data_type', 'Alternative', 'Satellite, web traffic, app data'),
    ('data_type', 'Earnings', 'Earnings reports, estimates, surprises'),
    ('data_type', 'Insider', 'Insider trading, institutional holdings'),
    ('data_type', 'Options', 'Options flow, implied vol, Greeks'),
    ('data_type', 'ESG', 'Environmental, social, governance'),
    ('region', 'US', 'United States'),
    ('region', 'EU', 'Europe'),
    ('region', 'APAC', 'Asia-Pacific'),
    ('region', 'Global', 'Global / cross-region'),
    ('frequency', 'Realtime', 'Sub-second to minute frequency'),
    ('frequency', 'Hourly', 'Hourly updates'),
    ('frequency', 'Daily', 'End-of-day updates'),
    ('frequency', 'Weekly', 'Weekly updates'),
    ('frequency', 'Monthly', 'Monthly updates'),
    ('frequency', 'Quarterly', 'Quarterly updates')
ON CONFLICT (category, label) DO NOTHING;

-- ============================================
-- 9. Helper Functions
-- ============================================

-- Update module stats after pipeline run
CREATE OR REPLACE FUNCTION update_module_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'success' THEN
        UPDATE modules SET
            last_run_at = NEW.started_at,
            last_success_at = NEW.completed_at,
            run_count = run_count + 1,
            consecutive_failures = 0,
            avg_duration_ms = COALESCE(
                (avg_duration_ms * LEAST(run_count, 10) + NEW.duration_ms) / (LEAST(run_count, 10) + 1),
                NEW.duration_ms
            ),
            updated_at = NOW()
        WHERE id = NEW.module_id;
    ELSIF NEW.status = 'failed' THEN
        UPDATE modules SET
            last_run_at = NEW.started_at,
            error_count = error_count + 1,
            consecutive_failures = consecutive_failures + 1,
            updated_at = NOW()
        WHERE id = NEW.module_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_update_module_stats
AFTER UPDATE OF status ON pipeline_runs
FOR EACH ROW
WHEN (NEW.status IN ('success', 'failed'))
EXECUTE FUNCTION update_module_stats();

-- Compute overall quality score from checks
CREATE OR REPLACE FUNCTION compute_quality_score(p_run_id BIGINT)
RETURNS SMALLINT AS $$
DECLARE
    avg_score SMALLINT;
BEGIN
    SELECT COALESCE(AVG(score)::SMALLINT, 0) INTO avg_score
    FROM quality_checks WHERE run_id = p_run_id;
    RETURN avg_score;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quantclaw_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quantclaw_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO quantclaw_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO quantclaw_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO quantclaw_user;
