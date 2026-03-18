import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const limit = Math.min(parseInt(searchParams.get('limit') || '100'), 500);

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, segment_name, segment_type, revenue, profit,
                period_end, fetched_at
         FROM gf_segments WHERE symbol = $1 ORDER BY period_end DESC NULLS LAST, revenue DESC NULLS LAST LIMIT $2`,
        [symbol.toUpperCase(), limit]
      );
      return NextResponse.json({ symbol, count: rows.length, data: rows });
    }

    const rows = await query(
      `SELECT symbol, gf_symbol, segment_name, segment_type, revenue, profit, period_end, fetched_at
       FROM gf_segments ORDER BY fetched_at DESC LIMIT $1`,
      [limit]
    );
    return NextResponse.json({ count: rows.length, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
