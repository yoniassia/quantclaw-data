import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const search = searchParams.get('q') || searchParams.get('search');
  const exchange = searchParams.get('exchange');
  const limit = Math.min(parseInt(searchParams.get('limit') || '100'), 1000);

  try {
    if (search) {
      const rows = await query(
        `SELECT etoro_symbol, gf_symbol, exchange, verified, last_verified_at
         FROM gf_symbol_map
         WHERE etoro_symbol ILIKE $1 OR gf_symbol ILIKE $1
         ORDER BY etoro_symbol LIMIT $2`,
        [`%${search}%`, limit]
      );
      return NextResponse.json({ query: search, count: rows.length, data: rows });
    }

    let sql = `SELECT etoro_symbol, gf_symbol, exchange, verified FROM gf_symbol_map`;
    const params: unknown[] = [];

    if (exchange) {
      params.push(exchange);
      sql += ` WHERE exchange ILIKE $${params.length}`;
    }

    sql += ` ORDER BY etoro_symbol LIMIT $${params.length + 1}`;
    params.push(limit);

    const rows = await query(sql, params);

    const stats = await query(
      `SELECT exchange, COUNT(*) as count FROM gf_symbol_map
       WHERE exchange IS NOT NULL AND exchange != ''
       GROUP BY exchange ORDER BY count DESC`
    );

    return NextResponse.json({ total: rows.length, by_exchange: stats, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
