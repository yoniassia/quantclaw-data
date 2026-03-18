import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = req.nextUrl;
    const tier = searchParams.get('tier');
    const cadence = searchParams.get('cadence');
    const search = searchParams.get('search');
    const status = searchParams.get('status');
    const limit = Math.min(+(searchParams.get('limit') ?? 100), 1000);
    const offset = +(searchParams.get('offset') ?? 0);
    const sort = searchParams.get('sort') ?? 'name';
    const order = searchParams.get('order') === 'desc' ? 'DESC' : 'ASC';

    const conditions: string[] = [];
    const params: unknown[] = [];
    let paramIdx = 1;

    if (tier) {
      conditions.push(`current_tier = $${paramIdx++}`);
      params.push(tier);
    }
    if (cadence) {
      conditions.push(`cadence = $${paramIdx++}`);
      params.push(cadence);
    }
    if (search) {
      conditions.push(`name ILIKE $${paramIdx++}`);
      params.push(`%${search}%`);
    }
    if (status === 'active') {
      conditions.push('is_active = true');
    } else if (status === 'inactive') {
      conditions.push('is_active = false');
    } else if (status === 'errored') {
      conditions.push('consecutive_failures > 0');
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';

    const allowedSorts: Record<string, string> = {
      name: 'name',
      tier: 'current_tier',
      cadence: 'cadence',
      quality: 'quality_score',
      last_run: 'last_run_at',
      errors: 'error_count',
    };
    const sortCol = allowedSorts[sort] ?? 'name';

    const [countRow] = await query<{ count: string }>(
      `SELECT COUNT(*) as count FROM modules ${where}`, params
    );

    const modules = await query(
      `SELECT id, name, display_name, cadence, granularity, current_tier, quality_score,
              is_active, last_run_at, last_success_at, next_run_at, run_count,
              error_count, consecutive_failures, avg_duration_ms, source_url
       FROM modules ${where}
       ORDER BY ${sortCol} ${order}
       LIMIT $${paramIdx++} OFFSET $${paramIdx++}`,
      [...params, limit, offset]
    );

    return NextResponse.json({
      total: +countRow.count,
      limit,
      offset,
      modules,
    });
  } catch (err) {
    console.error('DCC modules error:', err);
    return NextResponse.json({ error: 'Failed to fetch modules' }, { status: 500 });
  }
}
