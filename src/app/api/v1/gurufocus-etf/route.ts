import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const etf = searchParams.get('etf') || searchParams.get('symbol');
  const holding = searchParams.get('holding');
  const limit = Math.min(parseInt(searchParams.get('limit') || '100'), 500);

  try {
    if (etf) {
      const rows = await query(
        `SELECT etf_symbol, holding_symbol, holding_name, weight, shares, market_value, fetched_at
         FROM gf_etf_holdings WHERE etf_symbol = $1
         ORDER BY weight DESC NULLS LAST LIMIT $2`,
        [etf.toUpperCase(), limit]
      );
      return NextResponse.json({ etf, holdings_count: rows.length, holdings: rows });
    }

    if (holding) {
      const rows = await query(
        `SELECT etf_symbol, holding_symbol, holding_name, weight, shares, market_value, fetched_at
         FROM gf_etf_holdings WHERE holding_symbol = $1
         ORDER BY weight DESC NULLS LAST LIMIT $2`,
        [holding.toUpperCase(), limit]
      );
      return NextResponse.json({ holding, etfs_holding_count: rows.length, data: rows });
    }

    const summary = await query(
      `SELECT etf_symbol, COUNT(*) as holdings_count,
              MAX(fetched_at) as last_fetched
       FROM gf_etf_holdings GROUP BY etf_symbol ORDER BY etf_symbol`
    );
    return NextResponse.json({ etf_count: summary.length, etfs: summary });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
