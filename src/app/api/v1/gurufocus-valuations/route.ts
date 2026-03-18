import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 500);
  const undervalued = searchParams.get('undervalued') === 'true';

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, gf_value, dcf_value, graham_number,
                peter_lynch_value, median_ps_value, current_price,
                price_to_gf_value, fetched_at, payload
         FROM gf_valuations WHERE symbol = $1 ORDER BY fetched_at DESC LIMIT $2`,
        [symbol.toUpperCase(), limit]
      );
      return NextResponse.json({ symbol, count: rows.length, data: rows });
    }

    let sql = `SELECT DISTINCT ON (symbol) symbol, gf_symbol, gf_value, dcf_value,
                graham_number, peter_lynch_value, current_price, price_to_gf_value, fetched_at
               FROM gf_valuations`;

    if (undervalued) {
      sql += ` WHERE price_to_gf_value IS NOT NULL AND price_to_gf_value < 1.0`;
    }

    sql += ` ORDER BY symbol, fetched_at DESC`;

    const wrapper = undervalued
      ? `SELECT * FROM (${sql}) sub ORDER BY price_to_gf_value ASC LIMIT $1`
      : `SELECT * FROM (${sql}) sub ORDER BY fetched_at DESC LIMIT $1`;

    const rows = await query(wrapper, [limit]);
    return NextResponse.json({ count: rows.length, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
