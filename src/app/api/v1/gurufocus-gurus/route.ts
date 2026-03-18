import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const guruId = searchParams.get('guru_id');
  const symbol = searchParams.get('symbol');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 500);

  try {
    if (guruId) {
      const guru = await query(
        `SELECT * FROM gf_gurus WHERE guru_id = $1`,
        [guruId]
      );
      const holdings = await query(
        `SELECT symbol, gf_symbol, portfolio_date, shares, portfolio_weight,
                change_type, change_pct, current_price, market_value, fetched_at
         FROM gf_guru_holdings WHERE guru_id = $1
         ORDER BY portfolio_weight DESC NULLS LAST LIMIT $2`,
        [guruId, limit]
      );
      return NextResponse.json({
        guru: guru[0] || null,
        holdings_count: holdings.length,
        holdings,
      });
    }

    if (symbol) {
      const holders = await query(
        `SELECT h.guru_id, g.name as guru_name, g.firm,
                h.shares, h.portfolio_weight, h.change_type, h.change_pct,
                h.portfolio_date, h.fetched_at
         FROM gf_guru_holdings h
         JOIN gf_gurus g ON g.guru_id = h.guru_id
         WHERE h.symbol = $1
         ORDER BY h.portfolio_weight DESC NULLS LAST LIMIT $2`,
        [symbol.toUpperCase(), limit]
      );
      return NextResponse.json({ symbol, holders_count: holders.length, holders });
    }

    const gurus = await query(
      `SELECT guru_id, name, firm, portfolio_date, num_holdings,
              portfolio_value, fetched_at
       FROM gf_gurus ORDER BY portfolio_value DESC NULLS LAST LIMIT $1`,
      [limit]
    );
    return NextResponse.json({ count: gurus.length, gurus });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
