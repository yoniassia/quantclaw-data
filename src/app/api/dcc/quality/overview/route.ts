import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const [overall] = await query<{ avg_quality: string; total_checks: string; passed: string; failed: string }>(`
      SELECT
        COALESCE(AVG(score), 0)::int as avg_quality,
        COUNT(*) as total_checks,
        COUNT(*) FILTER (WHERE passed = true) as passed,
        COUNT(*) FILTER (WHERE passed = false) as failed
      FROM quality_checks
    `);

    const checkTypes = await query<{ check_type: string; total: string; passed: string; avg_score: string }>(`
      SELECT
        check_type,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE passed = true) as passed,
        COALESCE(AVG(score), 0)::int as avg_score
      FROM quality_checks
      GROUP BY check_type
      ORDER BY avg_score ASC
    `);

    const tierTrend = await query<{ day: string; gold: string; silver: string; bronze: string }>(`
      SELECT
        date_trunc('day', pr.started_at) as day,
        COUNT(DISTINCT pr.module_id) FILTER (WHERE m.current_tier = 'gold') as gold,
        COUNT(DISTINCT pr.module_id) FILTER (WHERE m.current_tier = 'silver') as silver,
        COUNT(DISTINCT pr.module_id) FILTER (WHERE m.current_tier = 'bronze') as bronze
      FROM pipeline_runs pr
      JOIN modules m ON m.id = pr.module_id
      WHERE pr.started_at >= NOW() - INTERVAL '30 days'
      GROUP BY 1
      ORDER BY 1 DESC
      LIMIT 30
    `);

    const worstModules = await query(`
      SELECT m.id, m.name, m.current_tier, m.quality_score, m.error_count, m.consecutive_failures, m.cadence
      FROM modules m
      WHERE m.is_active = true
      ORDER BY m.quality_score ASC, m.error_count DESC
      LIMIT 20
    `);

    return NextResponse.json({
      overall: {
        avgQuality: +overall.avg_quality,
        totalChecks: +overall.total_checks,
        passed: +overall.passed,
        failed: +overall.failed,
      },
      checkTypes: checkTypes.map(r => ({
        checkType: r.check_type,
        total: +r.total,
        passed: +r.passed,
        avgScore: +r.avg_score,
      })),
      tierTrend: tierTrend.map(r => ({
        day: r.day,
        gold: +r.gold,
        silver: +r.silver,
        bronze: +r.bronze,
      })),
      worstModules,
    });
  } catch (err) {
    console.error('DCC quality error:', err);
    return NextResponse.json({ error: 'Failed to fetch quality data' }, { status: 500 });
  }
}
