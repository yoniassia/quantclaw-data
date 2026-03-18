import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const periodType = searchParams.get('period') || 'annual';
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 500);

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, period_type, period_end,
                revenue, net_income, eps, total_assets, total_liabilities,
                free_cash_flow, roe, roa, debt_to_equity, fetched_at, payload
         FROM gf_fundamentals
         WHERE symbol = $1 AND period_type = $2
         ORDER BY period_end DESC NULLS LAST LIMIT $3`,
        [symbol.toUpperCase(), periodType, limit]
      );
      return NextResponse.json({ symbol, period: periodType, count: rows.length, data: rows });
    }

    const rows = await query(
      `SELECT DISTINCT ON (symbol) symbol, gf_symbol, period_type,
              revenue, net_income, eps, roe, roa, debt_to_equity, fetched_at
       FROM gf_fundamentals WHERE period_type = $1
       ORDER BY symbol, fetched_at DESC
       LIMIT $2`,
      [periodType, limit]
    );
    return NextResponse.json({ count: rows.length, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
