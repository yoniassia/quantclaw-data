import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const sources = await query<{
      source_url: string;
      module_count: string;
      last_success: string | null;
      last_run: string | null;
      total_runs: string;
      success_runs: string;
      failed_runs: string;
      avg_duration: string;
    }>(`
      SELECT
        COALESCE(m.source_url, 'local') as source_url,
        COUNT(DISTINCT m.id) as module_count,
        MAX(m.last_success_at) as last_success,
        MAX(m.last_run_at) as last_run,
        COALESCE(SUM(m.run_count), 0)::int as total_runs,
        COALESCE(SUM(m.run_count) - SUM(m.error_count), 0)::int as success_runs,
        COALESCE(SUM(m.error_count), 0)::int as failed_runs,
        COALESCE(AVG(m.avg_duration_ms), 0)::int as avg_duration
      FROM modules m
      WHERE m.is_active = true
      GROUP BY COALESCE(m.source_url, 'local')
      ORDER BY module_count DESC
    `);

    const cadenceConfig = await query<{ cadence: string; count: string; next_runs: string }>(`
      SELECT
        cadence,
        COUNT(*) as count,
        COUNT(*) FILTER (WHERE next_run_at IS NOT NULL AND next_run_at > NOW()) as next_runs
      FROM modules
      WHERE is_active = true
      GROUP BY cadence
      ORDER BY count DESC
    `);

    const [symbolStats] = await query<{ total: string; active: string; asset_classes: string }>(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE is_active) as active,
        COUNT(DISTINCT asset_class) as asset_classes
      FROM symbol_universe
    `);

    const assetClasses = await query<{ asset_class: string; count: string }>(`
      SELECT asset_class, COUNT(*) as count
      FROM symbol_universe
      WHERE is_active = true
      GROUP BY asset_class
      ORDER BY count DESC
    `);

    return NextResponse.json({
      sources: sources.map(s => ({
        sourceUrl: s.source_url,
        moduleCount: +s.module_count,
        lastSuccess: s.last_success,
        lastRun: s.last_run,
        totalRuns: +s.total_runs,
        successRuns: +s.success_runs,
        failedRuns: +s.failed_runs,
        avgDuration: +s.avg_duration,
        uptime: +s.total_runs > 0 ? +(((+s.success_runs) / (+s.total_runs)) * 100).toFixed(1) : 0,
      })),
      cadenceConfig: cadenceConfig.map(c => ({
        cadence: c.cadence,
        count: +c.count,
        nextRuns: +c.next_runs,
      })),
      symbolUniverse: {
        total: +(symbolStats?.total ?? 0),
        active: +(symbolStats?.active ?? 0),
        assetClasses: +(symbolStats?.asset_classes ?? 0),
      },
      assetClasses: assetClasses.map(a => ({ assetClass: a.asset_class, count: +a.count })),
    });
  } catch (err) {
    console.error('DCC sources error:', err);
    return NextResponse.json({ error: 'Failed to fetch sources' }, { status: 500 });
  }
}
