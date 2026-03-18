import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const limit = Math.min(+(req.nextUrl.searchParams.get('limit') ?? 50), 200);
    const status = req.nextUrl.searchParams.get('status');

    const conditions = ['1=1'];
    const params: unknown[] = [];
    let idx = 1;

    if (status) {
      conditions.push(`pr.status = $${idx++}`);
      params.push(status);
    }

    const runs = await query(
      `SELECT pr.id, pr.module_id, m.name as module_name, pr.tier_target,
              pr.status, pr.started_at, pr.completed_at, pr.duration_ms,
              pr.rows_in, pr.rows_out, pr.rows_failed, pr.retry_attempt,
              pr.error_message
       FROM pipeline_runs pr
       JOIN modules m ON m.id = pr.module_id
       WHERE ${conditions.join(' AND ')}
       ORDER BY pr.started_at DESC
       LIMIT $${idx++}`,
      [...params, limit]
    );

    const [throughput] = await query<{ runs_today: string; success_rate: string }>(`
      SELECT
        COUNT(*) as runs_today,
        CASE WHEN COUNT(*) > 0
          THEN ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / COUNT(*), 1)
          ELSE 0
        END as success_rate
      FROM pipeline_runs
      WHERE started_at >= CURRENT_DATE
    `);

    return NextResponse.json({
      runs,
      throughput: {
        runsToday: +(throughput?.runs_today ?? 0),
        successRate: +(throughput?.success_rate ?? 0),
      },
    });
  } catch (err) {
    console.error('DCC pipeline error:', err);
    return NextResponse.json({ error: 'Failed to fetch pipeline data' }, { status: 500 });
  }
}
