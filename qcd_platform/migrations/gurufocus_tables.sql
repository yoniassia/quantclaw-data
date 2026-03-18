-- GuruFocus Integration — DB Tables
-- Run once: psql -d quantclaw_data -f qcd_platform/migrations/gurufocus_tables.sql

-- ============================================
-- 1. GF Stock Rankings (GF Score, quality, value, growth)
-- ============================================
CREATE TABLE IF NOT EXISTS gf_rankings (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    gf_score NUMERIC(5,2),
    financial_strength NUMERIC(5,2),
    profitability_rank NUMERIC(5,2),
    growth_rank NUMERIC(5,2),
    gf_value_rank NUMERIC(5,2),
    momentum_rank NUMERIC(5,2),
    predictability_rank VARCHAR(20),

    payload JSONB NOT NULL DEFAULT '{}',
    UNIQUE(symbol, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_gf_rankings_symbol ON gf_rankings(symbol, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_gf_rankings_gf_score ON gf_rankings(gf_score DESC NULLS LAST);

-- ============================================
-- 2. GF Valuations (DCF, Graham, GF Value, fair value)
-- ============================================
CREATE TABLE IF NOT EXISTS gf_valuations (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    gf_value NUMERIC(14,2),
    dcf_value NUMERIC(14,2),
    graham_number NUMERIC(14,2),
    peter_lynch_value NUMERIC(14,2),
    median_ps_value NUMERIC(14,2),
    current_price NUMERIC(14,2),
    price_to_gf_value NUMERIC(8,4),

    payload JSONB NOT NULL DEFAULT '{}',
    UNIQUE(symbol, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_gf_valuations_symbol ON gf_valuations(symbol, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_gf_valuations_gap ON gf_valuations(price_to_gf_value) WHERE price_to_gf_value IS NOT NULL;

-- ============================================
-- 3. GF Fundamentals (income, balance sheet, cashflow)
-- ============================================
CREATE TABLE IF NOT EXISTS gf_fundamentals (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    period_type VARCHAR(10) NOT NULL DEFAULT 'annual',
    period_end DATE,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    revenue NUMERIC(18,2),
    net_income NUMERIC(18,2),
    eps NUMERIC(10,4),
    total_assets NUMERIC(18,2),
    total_liabilities NUMERIC(18,2),
    free_cash_flow NUMERIC(18,2),
    roe NUMERIC(8,4),
    roa NUMERIC(8,4),
    debt_to_equity NUMERIC(8,4),

    payload JSONB NOT NULL DEFAULT '{}',
    UNIQUE(symbol, period_type, period_end)
);
CREATE INDEX IF NOT EXISTS idx_gf_fundamentals_symbol ON gf_fundamentals(symbol, period_end DESC);

-- ============================================
-- 4. GF Guru Holdings (institutional investor portfolios)
-- ============================================
CREATE TABLE IF NOT EXISTS gf_gurus (
    id SERIAL PRIMARY KEY,
    guru_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    firm VARCHAR(300),
    portfolio_date DATE,
    num_holdings INTEGER,
    portfolio_value NUMERIC(18,2),
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_gf_gurus_name ON gf_gurus(name);

CREATE TABLE IF NOT EXISTS gf_guru_holdings (
    id BIGSERIAL PRIMARY KEY,
    guru_id VARCHAR(100) NOT NULL REFERENCES gf_gurus(guru_id),
    symbol VARCHAR(50) NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    portfolio_date DATE,
    shares NUMERIC(18,2),
    portfolio_weight NUMERIC(8,4),
    change_type VARCHAR(20),
    change_pct NUMERIC(8,4),
    current_price NUMERIC(14,2),
    market_value NUMERIC(18,2),
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(guru_id, symbol, portfolio_date)
);
CREATE INDEX IF NOT EXISTS idx_gf_guru_holdings_symbol ON gf_guru_holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_gf_guru_holdings_guru ON gf_guru_holdings(guru_id, portfolio_date DESC);

-- ============================================
-- 5. GF Insider Trading
-- ============================================
CREATE TABLE IF NOT EXISTS gf_insider_trades (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    gf_symbol VARCHAR(50),
    insider_name VARCHAR(300),
    insider_title VARCHAR(200),
    trade_type VARCHAR(20),
    shares NUMERIC(18,2),
    price NUMERIC(14,4),
    total_value NUMERIC(18,2),
    trade_date DATE NOT NULL,
    filing_date DATE,
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_gf_insider_symbol ON gf_insider_trades(symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_gf_insider_date ON gf_insider_trades(trade_date DESC);

-- ============================================
-- 6. GF Stock Profiles
-- ============================================
CREATE TABLE IF NOT EXISTS gf_profiles (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) UNIQUE NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    company_name VARCHAR(300),
    sector VARCHAR(100),
    industry VARCHAR(200),
    country VARCHAR(50),
    market_cap NUMERIC(18,2),
    employees INTEGER,
    description TEXT,
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_gf_profiles_sector ON gf_profiles(sector);

-- ============================================
-- 7. GF Segments
-- ============================================
CREATE TABLE IF NOT EXISTS gf_segments (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    segment_name VARCHAR(200),
    segment_type VARCHAR(50),
    revenue NUMERIC(18,2),
    profit NUMERIC(18,2),
    period_end DATE,
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_gf_segments_symbol ON gf_segments(symbol, period_end DESC);

-- ============================================
-- 8. GF ETF Holdings
-- ============================================
CREATE TABLE IF NOT EXISTS gf_etf_holdings (
    id BIGSERIAL PRIMARY KEY,
    etf_symbol VARCHAR(50) NOT NULL,
    holding_symbol VARCHAR(50),
    holding_name VARCHAR(300),
    weight NUMERIC(8,4),
    shares NUMERIC(18,2),
    market_value NUMERIC(18,2),
    payload JSONB NOT NULL DEFAULT '{}',
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(etf_symbol, holding_symbol, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_gf_etf_symbol ON gf_etf_holdings(etf_symbol);

-- ============================================
-- 9. GF Symbol Map Cache
-- ============================================
CREATE TABLE IF NOT EXISTS gf_symbol_map (
    id SERIAL PRIMARY KEY,
    etoro_symbol VARCHAR(50) UNIQUE NOT NULL,
    gf_symbol VARCHAR(50) NOT NULL,
    etoro_instrument_id INTEGER,
    exchange VARCHAR(50),
    verified BOOLEAN DEFAULT false,
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_gf_map_gf ON gf_symbol_map(gf_symbol);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quantclaw_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quantclaw_user;
