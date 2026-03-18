import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const quarter = searchParams.get('quarter');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    let sql = `SELECT ts, payload FROM data_points
               WHERE module_id = (SELECT id FROM modules WHERE name = 'gurufocus_fund_letters')`;
    const params: unknown[] = [];

    if (quarter) {
      params.push(quarter);
      sql += ` AND payload->>'quarter' = $${params.length}`;
    }

    sql += ` ORDER BY ts DESC LIMIT $${params.length + 1}`;
    params.push(limit);

    const rows = await query(sql, params);
    const letters = rows.map((r: any) => ({ ...r.payload, fetched_at: r.ts }));
    return NextResponse.json({ count: letters.length, data: letters });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
