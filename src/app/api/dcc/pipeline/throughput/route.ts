import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const hourly = await query<{ hour: string; total: string; success: string; failed: string }>(`
      SELECT
        date_trunc('hour', started_at) as hour,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'success') as success,
        COUNT(*) FILTER (WHERE status = 'failed') as failed
      FROM pipeline_runs
      WHERE started_at >= NOW() - INTERVAL '7 days'
      GROUP BY 1
      ORDER BY 1 DESC
      LIMIT 168
    `);

    const daily = await query<{ day: string; total: string; success: string; failed: string; avg_ms: string }>(`
      SELECT
        date_trunc('day', started_at) as day,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'success') as success,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COALESCE(AVG(duration_ms) FILTER (WHERE status = 'success'), 0)::int as avg_ms
      FROM pipeline_runs
      WHERE started_at >= NOW() - INTERVAL '30 days'
      GROUP BY 1
      ORDER BY 1 DESC
    `);

    return NextResponse.json({
      hourly: hourly.map(r => ({
        hour: r.hour,
        total: +r.total,
        success: +r.success,
        failed: +r.failed,
      })),
      daily: daily.map(r => ({
        day: r.day,
        total: +r.total,
        success: +r.success,
        failed: +r.failed,
        avgMs: +r.avg_ms,
      })),
    });
  } catch (err) {
    console.error('DCC throughput error:', err);
    return NextResponse.json({ error: 'Failed to fetch throughput' }, { status: 500 });
  }
}
