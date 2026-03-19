-- Migration 003: Materialized views for cross-cadence joins
-- Uses TimescaleDB locf() for forward-fill across different data cadences
-- Refreshed after each overnight pipeline run

BEGIN;

-- ============================================================
-- 1. mv_symbol_latest: Point-in-time snapshot per symbol
--    Combines latest data from all active Gold/Platinum sources
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_symbol_latest AS
WITH symbols AS (
    SELECT symbol FROM symbol_universe WHERE is_active = true
),
rankings AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS rankings_ts,
        dp.payload->>'gf_score' AS gf_score,
        dp.payload->>'growth_rank' AS growth_rank,
        dp.payload->>'momentum_rank' AS momentum_rank,
        dp.payload->>'financial_strength' AS financial_strength,
        dp.payload->>'profitability_rank' AS profitability_rank,
        dp.payload->>'gf_value' AS gf_value,
        dp.payload->>'price_to_gf' AS price_to_gf,
        dp.payload->>'gf_value_rank' AS gf_value_rank,
        dp.payload->>'predictability_rank' AS predictability_rank
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_rankings_gold' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
),
valuations AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS valuations_ts,
        dp.payload->>'eps' AS eps,
        dp.payload->>'bvps' AS bvps,
        dp.payload->>'current_price' AS gf_price,
        dp.payload->>'fcf_per_share' AS fcf_per_share,
        dp.payload->>'revenue_per_share' AS revenue_per_share,
        dp.payload->>'latest_period' AS latest_valuation_period
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_valuations_gold' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
),
fundamentals AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS fundamentals_ts,
        dp.payload->>'latest_eps' AS latest_eps,
        dp.payload->>'latest_revenue' AS latest_revenue,
        dp.payload->>'latest_net_income' AS latest_net_income,
        dp.payload->>'latest_period' AS latest_fundamental_period,
        dp.payload->>'annual_count' AS annual_count,
        dp.payload->>'quarterly_count' AS quarterly_count
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_fundamentals_gold' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
),
profiles AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS profile_ts,
        dp.payload->>'sector' AS sector,
        dp.payload->>'company' AS company_name,
        dp.payload->>'beta' AS beta,
        dp.payload->>'ema_20' AS ema_20,
        dp.payload->>'ema_50' AS ema_50,
        dp.payload->>'ema_200' AS ema_200,
        dp.payload->>'sma_50' AS sma_50,
        dp.payload->>'sma_200' AS sma_200
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_profiles_gold' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
),
fin_data AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS fin_price_ts,
        dp.payload->>'close' AS fd_close,
        dp.payload->>'volume' AS fd_volume,
        dp.payload->>'open' AS fd_open,
        dp.payload->>'high' AS fd_high,
        dp.payload->>'low' AS fd_low
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'financial_datasets_prices' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
),
insider_latest AS (
    SELECT dp.symbol,
        COUNT(*) AS insider_tx_count_30d,
        SUM(CASE WHEN (dp.payload->>'transaction_type') ILIKE '%buy%' THEN 1 ELSE 0 END) AS insider_buys_30d,
        SUM(CASE WHEN (dp.payload->>'transaction_type') ILIKE '%sell%' THEN 1 ELSE 0 END) AS insider_sells_30d,
        MAX(dp.ts) AS last_insider_ts
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name IN ('financial_datasets_insider', 'insider_transaction_heatmap')
      AND dp.symbol IS NOT NULL
      AND dp.ts >= NOW() - INTERVAL '30 days'
    GROUP BY dp.symbol
),
earnings AS (
    SELECT DISTINCT ON (dp.symbol)
        dp.symbol,
        dp.ts AS earnings_ts,
        dp.payload->>'report_date' AS next_earnings_date,
        dp.payload->>'estimate' AS earnings_estimate,
        dp.payload->>'fiscal_quarter_ending' AS fiscal_quarter
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'alpha_vantage_earnings_calendar_api' AND dp.symbol IS NOT NULL
    ORDER BY dp.symbol, dp.ts DESC
)
SELECT
    s.symbol,
    p.company_name,
    p.sector,
    -- Price data
    fd.fd_close::NUMERIC AS price,
    fd.fd_open::NUMERIC AS open,
    fd.fd_high::NUMERIC AS high,
    fd.fd_low::NUMERIC AS low,
    fd.fd_volume::BIGINT AS volume,
    fd.fin_price_ts AS price_ts,
    -- Technicals
    p.beta::NUMERIC AS beta,
    p.ema_20::NUMERIC AS ema_20,
    p.ema_50::NUMERIC AS ema_50,
    p.ema_200::NUMERIC AS ema_200,
    p.sma_50::NUMERIC AS sma_50,
    p.sma_200::NUMERIC AS sma_200,
    -- Valuation
    v.eps::NUMERIC AS eps,
    v.bvps::NUMERIC AS bvps,
    v.fcf_per_share::NUMERIC AS fcf_per_share,
    v.revenue_per_share::NUMERIC AS revenue_per_share,
    v.latest_valuation_period,
    -- GF Rankings
    r.gf_score::NUMERIC AS gf_score,
    r.growth_rank::NUMERIC AS growth_rank,
    r.momentum_rank::NUMERIC AS momentum_rank,
    r.financial_strength::NUMERIC AS financial_strength,
    r.profitability_rank::NUMERIC AS profitability_rank,
    r.gf_value::NUMERIC AS gf_value,
    r.price_to_gf::NUMERIC AS price_to_gf,
    r.gf_value_rank::NUMERIC AS gf_value_rank,
    r.predictability_rank::NUMERIC AS predictability_rank,
    -- Fundamentals
    f.latest_eps::NUMERIC AS reported_eps,
    f.latest_revenue::NUMERIC AS reported_revenue,
    f.latest_net_income::NUMERIC AS reported_net_income,
    f.latest_fundamental_period,
    -- Insider Activity (30d)
    COALESCE(il.insider_tx_count_30d, 0) AS insider_tx_count_30d,
    COALESCE(il.insider_buys_30d, 0) AS insider_buys_30d,
    COALESCE(il.insider_sells_30d, 0) AS insider_sells_30d,
    il.last_insider_ts,
    -- Earnings
    e.next_earnings_date,
    e.earnings_estimate,
    e.fiscal_quarter,
    -- Freshness
    GREATEST(
        r.rankings_ts, v.valuations_ts, f.fundamentals_ts,
        p.profile_ts, fd.fin_price_ts, e.earnings_ts
    ) AS last_updated,
    NOW() AS refreshed_at
FROM symbols s
LEFT JOIN rankings r ON r.symbol = s.symbol
LEFT JOIN valuations v ON v.symbol = s.symbol
LEFT JOIN fundamentals f ON f.symbol = s.symbol
LEFT JOIN profiles p ON p.symbol = s.symbol
LEFT JOIN fin_data fd ON fd.symbol = s.symbol
LEFT JOIN insider_latest il ON il.symbol = s.symbol
LEFT JOIN earnings e ON e.symbol = s.symbol
WHERE r.symbol IS NOT NULL
   OR v.symbol IS NOT NULL
   OR f.symbol IS NOT NULL
   OR fd.symbol IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_symbol_latest_symbol ON mv_symbol_latest(symbol);

-- ============================================================
-- 2. mv_module_health: Module health dashboard
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_module_health AS
SELECT
    m.id AS module_id,
    m.name,
    m.display_name,
    m.cadence,
    m.current_tier,
    m.quality_score,
    m.is_active,
    m.run_count,
    m.error_count,
    m.consecutive_failures,
    m.last_run_at,
    m.last_success_at,
    m.next_run_at,
    m.avg_duration_ms,
    dp_stats.row_count,
    dp_stats.symbol_count,
    dp_stats.latest_data_ts,
    dp_stats.oldest_data_ts,
    CASE
        WHEN m.consecutive_failures >= 3 THEN 'critical'
        WHEN m.consecutive_failures >= 1 THEN 'warning'
        WHEN m.quality_score >= 95 THEN 'healthy'
        WHEN m.quality_score >= 80 THEN 'good'
        WHEN m.quality_score >= 50 THEN 'fair'
        ELSE 'poor'
    END AS health_status,
    runs_24h.success_count AS runs_24h_success,
    runs_24h.fail_count AS runs_24h_failed,
    NOW() AS refreshed_at
FROM modules m
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) AS row_count,
        COUNT(DISTINCT symbol) AS symbol_count,
        MAX(ts) AS latest_data_ts,
        MIN(ts) AS oldest_data_ts
    FROM data_points dp WHERE dp.module_id = m.id
) dp_stats ON true
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) FILTER (WHERE status = 'success') AS success_count,
        COUNT(*) FILTER (WHERE status = 'failed') AS fail_count
    FROM pipeline_runs pr
    WHERE pr.module_id = m.id AND pr.started_at >= NOW() - INTERVAL '24 hours'
) runs_24h ON true
WHERE m.is_active = true;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_module_health_id ON mv_module_health(module_id);

-- ============================================================
-- 3. mv_cross_cadence_daily: Forward-filled daily snapshots
--    Uses LATERAL joins for as-of lookups (ffill pattern)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cross_cadence_daily AS
WITH date_series AS (
    SELECT generate_series(
        CURRENT_DATE - INTERVAL '30 days',
        CURRENT_DATE,
        INTERVAL '1 day'
    )::DATE AS trade_date
),
price_symbols AS (
    SELECT DISTINCT symbol
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name IN ('financial_datasets_prices', 'gurufocus_rankings_gold', 'gurufocus_valuations_gold')
      AND dp.symbol IS NOT NULL
      AND dp.ts >= CURRENT_DATE - INTERVAL '60 days'
),
grid AS (
    SELECT d.trade_date, ps.symbol
    FROM date_series d
    CROSS JOIN price_symbols ps
)
SELECT
    g.trade_date,
    g.symbol,
    -- Rankings (forward-filled: daily cadence → every day)
    r_payload->>'gf_score' AS gf_score,
    r_payload->>'growth_rank' AS growth_rank,
    r_payload->>'momentum_rank' AS momentum_rank,
    r_payload->>'financial_strength' AS financial_strength,
    r_payload->>'profitability_rank' AS profitability_rank,
    -- Valuations (forward-filled)
    v_payload->>'eps' AS eps,
    v_payload->>'bvps' AS bvps,
    v_payload->>'fcf_per_share' AS fcf_per_share,
    v_payload->>'revenue_per_share' AS revenue_per_share,
    -- Fundamentals (forward-filled: weekly → daily)
    f_payload->>'latest_eps' AS reported_eps,
    f_payload->>'latest_revenue' AS reported_revenue,
    f_payload->>'latest_net_income' AS reported_net_income,
    -- Profile (forward-filled: weekly → daily)
    p_payload->>'sector' AS sector,
    p_payload->>'beta' AS beta,
    p_payload->>'ema_20' AS ema_20,
    p_payload->>'sma_200' AS sma_200,
    -- Timestamps of source data used
    r_ts AS rankings_as_of,
    v_ts AS valuations_as_of,
    f_ts AS fundamentals_as_of,
    p_ts AS profile_as_of,
    NOW() AS refreshed_at
FROM grid g
LEFT JOIN LATERAL (
    SELECT dp.payload AS r_payload, dp.ts AS r_ts
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_rankings_gold'
      AND dp.symbol = g.symbol
      AND dp.ts::date <= g.trade_date
    ORDER BY dp.ts DESC LIMIT 1
) r ON true
LEFT JOIN LATERAL (
    SELECT dp.payload AS v_payload, dp.ts AS v_ts
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_valuations_gold'
      AND dp.symbol = g.symbol
      AND dp.ts::date <= g.trade_date
    ORDER BY dp.ts DESC LIMIT 1
) v ON true
LEFT JOIN LATERAL (
    SELECT dp.payload AS f_payload, dp.ts AS f_ts
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_fundamentals_gold'
      AND dp.symbol = g.symbol
      AND dp.ts::date <= g.trade_date
    ORDER BY dp.ts DESC LIMIT 1
) f ON true
LEFT JOIN LATERAL (
    SELECT dp.payload AS p_payload, dp.ts AS p_ts
    FROM data_points dp
    JOIN modules m ON m.id = dp.module_id
    WHERE m.name = 'gurufocus_profiles_gold'
      AND dp.symbol = g.symbol
      AND dp.ts::date <= g.trade_date
    ORDER BY dp.ts DESC LIMIT 1
) p ON true
WHERE r_payload IS NOT NULL OR v_payload IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mv_xcd_symbol_date ON mv_cross_cadence_daily(symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_mv_xcd_date ON mv_cross_cadence_daily(trade_date DESC);

-- ============================================================
-- 4. Helper function: Refresh all materialized views
-- ============================================================

CREATE OR REPLACE FUNCTION refresh_all_matviews()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    RAISE NOTICE 'Refreshing mv_symbol_latest...';
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_symbol_latest;

    RAISE NOTICE 'Refreshing mv_module_health...';
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_module_health;

    RAISE NOTICE 'Refreshing mv_cross_cadence_daily...';
    REFRESH MATERIALIZED VIEW mv_cross_cadence_daily;

    RAISE NOTICE 'All materialized views refreshed at %', NOW();
END;
$$;

COMMIT;
