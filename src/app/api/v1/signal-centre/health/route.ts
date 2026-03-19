import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

interface ModuleHealth {
  module_id: number;
  name: string;
  display_name: string;
  cadence: string;
  current_tier: string;
  quality_score: number;
  is_active: boolean;
  run_count: number;
  error_count: number;
  consecutive_failures: number;
  last_run_at: string;
  last_success_at: string;
  avg_duration_ms: number;
  row_count: number;
  symbol_count: number;
  health_status: string;
  runs_24h_success: number;
  runs_24h_failed: number;
  refreshed_at: string;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const tier = searchParams.get('tier');
  const status = searchParams.get('status');
  const sortBy = searchParams.get('sort') || 'quality_score';
  const order = searchParams.get('order') === 'asc' ? 'ASC' : 'DESC';

  const allowedSorts = [
    'quality_score', 'name', 'row_count', 'symbol_count',
    'consecutive_failures', 'last_run_at', 'avg_duration_ms', 'health_status',
  ];
  const safeSort = allowedSorts.includes(sortBy) ? sortBy : 'quality_score';

  try {
    const conditions: string[] = [];
    const params: unknown[] = [];
    let paramIdx = 1;

    if (tier) {
      conditions.push(`current_tier = $${paramIdx}`);
      params.push(tier.toLowerCase());
      paramIdx++;
    }
    if (status) {
      conditions.push(`health_status = $${paramIdx}`);
      params.push(status.toLowerCase());
      paramIdx++;
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const sql = `SELECT * FROM mv_module_health ${where} ORDER BY ${safeSort} ${order} NULLS LAST`;

    const rows = await query<ModuleHealth>(sql, params);

    const summary = {
      total: rows.length,
      by_status: {} as Record<string, number>,
      by_tier: {} as Record<string, number>,
    };
    for (const row of rows) {
      summary.by_status[row.health_status] = (summary.by_status[row.health_status] || 0) + 1;
      summary.by_tier[row.current_tier] = (summary.by_tier[row.current_tier] || 0) + 1;
    }

    return NextResponse.json({ summary, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
