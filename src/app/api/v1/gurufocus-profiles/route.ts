import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const sector = searchParams.get('sector');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 500);

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, company_name, sector, industry, country,
                market_cap, employees, description, fetched_at, payload
         FROM gf_profiles WHERE symbol = $1`,
        [symbol.toUpperCase()]
      );
      return NextResponse.json(rows[0] || { error: 'Not found' });
    }

    let sql = `SELECT symbol, gf_symbol, company_name, sector, industry, country,
                market_cap, employees, fetched_at
               FROM gf_profiles`;
    const params: unknown[] = [];

    if (sector) {
      params.push(sector);
      sql += ` WHERE sector ILIKE $${params.length}`;
    }

    sql += ` ORDER BY market_cap DESC NULLS LAST LIMIT $${params.length + 1}`;
    params.push(limit);

    const rows = await query(sql, params);

    const sectorBreakdown = await query(
      `SELECT sector, COUNT(*) as count, SUM(market_cap) as total_market_cap
       FROM gf_profiles WHERE sector IS NOT NULL AND sector != ''
       GROUP BY sector ORDER BY total_market_cap DESC NULLS LAST`
    );

    return NextResponse.json({ count: rows.length, sectors: sectorBreakdown, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
