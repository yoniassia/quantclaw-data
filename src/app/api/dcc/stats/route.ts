import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const [moduleStats] = await query<{
      total: string;
      active: string;
      bronze: string;
      silver: string;
      gold: string;
      platinum: string;
      none: string;
    }>(`
      SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_active) as active,
        COUNT(*) FILTER (WHERE current_tier = 'bronze') as bronze,
        COUNT(*) FILTER (WHERE current_tier = 'silver') as silver,
        COUNT(*) FILTER (WHERE current_tier = 'gold') as gold,
        COUNT(*) FILTER (WHERE current_tier = 'platinum') as platinum,
        COUNT(*) FILTER (WHERE current_tier = 'none' OR current_tier IS NULL) as none
      FROM modules
    `);

    const cadenceStats = await query<{ cadence: string; count: string }>(`
      SELECT cadence, COUNT(*) as count FROM modules GROUP BY cadence ORDER BY count DESC
    `);

    const [alertStats] = await query<{
      total_unresolved: string;
      critical: string;
      warning: string;
      info: string;
    }>(`
      SELECT
        COUNT(*) as total_unresolved,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning,
        COUNT(*) FILTER (WHERE severity = 'info') as info
      FROM alerts WHERE resolved = false
    `);

    const [pipelineStats] = await query<{
      total_runs: string;
      success: string;
      failed: string;
      running: string;
      today_runs: string;
      today_success: string;
      avg_duration_ms: string;
    }>(`
      SELECT
        COUNT(*) as total_runs,
        COUNT(*) FILTER (WHERE status = 'success') as success,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COUNT(*) FILTER (WHERE status = 'running') as running,
        COUNT(*) FILTER (WHERE started_at >= CURRENT_DATE) as today_runs,
        COUNT(*) FILTER (WHERE started_at >= CURRENT_DATE AND status = 'success') as today_success,
        COALESCE(AVG(duration_ms) FILTER (WHERE status = 'success'), 0)::int as avg_duration_ms
      FROM pipeline_runs
    `);

    const [freshness] = await query<{ on_schedule: string; overdue: string }>(`
      SELECT
        COUNT(*) FILTER (WHERE next_run_at IS NULL OR next_run_at > NOW()) as on_schedule,
        COUNT(*) FILTER (WHERE next_run_at IS NOT NULL AND next_run_at <= NOW()) as overdue
      FROM modules WHERE is_active = true
    `);

    const [platinumStats] = await query<{
      total_records: string;
      unique_symbols: string;
      avg_score: string;
      latest_refresh: string;
    }>(`
      SELECT
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as unique_symbols,
        COALESCE(ROUND(AVG(composite_score)::numeric, 1), 0) as avg_score,
        MAX(generated_at) as latest_refresh
      FROM platinum_records
    `);

    return NextResponse.json({
      modules: {
        total: +moduleStats.total,
        active: +moduleStats.active,
        tiers: {
          bronze: +moduleStats.bronze,
          silver: +moduleStats.silver,
          gold: +moduleStats.gold,
          platinum: +moduleStats.platinum,
          none: +moduleStats.none,
        },
      },
      cadence: cadenceStats.map(r => ({ cadence: r.cadence, count: +r.count })),
      alerts: {
        unresolved: +(alertStats?.total_unresolved ?? 0),
        critical: +(alertStats?.critical ?? 0),
        warning: +(alertStats?.warning ?? 0),
        info: +(alertStats?.info ?? 0),
      },
      pipeline: {
        totalRuns: +pipelineStats.total_runs,
        success: +pipelineStats.success,
        failed: +pipelineStats.failed,
        running: +pipelineStats.running,
        todayRuns: +pipelineStats.today_runs,
        todaySuccess: +pipelineStats.today_success,
        avgDurationMs: +pipelineStats.avg_duration_ms,
      },
      freshness: {
        onSchedule: +(freshness?.on_schedule ?? 0),
        overdue: +(freshness?.overdue ?? 0),
      },
      platinum: {
        totalRecords: +(platinumStats?.total_records ?? 0),
        uniqueSymbols: +(platinumStats?.unique_symbols ?? 0),
        avgCompositeScore: +(platinumStats?.avg_score ?? 0),
        latestRefresh: platinumStats?.latest_refresh,
      },
    });
  } catch (err) {
    console.error('DCC stats error:', err);
    return NextResponse.json({ error: 'Failed to fetch stats' }, { status: 500 });
  }
}
