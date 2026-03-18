import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const minGurus = parseInt(searchParams.get('min_gurus') || '2');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    if (symbol) {
      const holders = await query(
        `SELECT h.guru_id, g.name as guru_name, g.firm,
                h.shares, h.portfolio_weight, h.change_type, h.change_pct,
                h.current_price, h.market_value, h.portfolio_date
         FROM gf_guru_holdings h
         JOIN gf_gurus g ON g.guru_id = h.guru_id
         WHERE h.symbol = $1
         ORDER BY h.portfolio_weight DESC NULLS LAST`,
        [symbol.toUpperCase()]
      );
      return NextResponse.json({
        symbol,
        guru_count: holders.length,
        holders,
      });
    }

    const consensus = await query(
      `SELECT
          h.symbol,
          COUNT(DISTINCT h.guru_id) as guru_count,
          ROUND(AVG(h.portfolio_weight)::numeric, 4) as avg_weight,
          ROUND(MAX(h.portfolio_weight)::numeric, 4) as max_weight,
          ROUND(SUM(h.market_value)::numeric, 2) as total_guru_value,
          ARRAY_AGG(DISTINCT g.name ORDER BY g.name) as guru_names
       FROM gf_guru_holdings h
       JOIN gf_gurus g ON g.guru_id = h.guru_id
       WHERE h.symbol IS NOT NULL AND h.symbol != ''
       GROUP BY h.symbol
       HAVING COUNT(DISTINCT h.guru_id) >= $1
       ORDER BY COUNT(DISTINCT h.guru_id) DESC, AVG(h.portfolio_weight) DESC
       LIMIT $2`,
      [minGurus, limit]
    );

    return NextResponse.json({ min_gurus: minGurus, count: consensus.length, data: consensus });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
