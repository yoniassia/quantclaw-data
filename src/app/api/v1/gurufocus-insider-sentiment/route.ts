import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const days = Math.min(parseInt(searchParams.get('days') || '30'), 365);
  const sentiment = searchParams.get('sentiment');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    const rows = await query(
      `SELECT
          symbol,
          COUNT(*) FILTER (WHERE trade_type ILIKE '%buy%' OR trade_type ILIKE '%purchase%') as buys,
          COUNT(*) FILTER (WHERE trade_type ILIKE '%sell%' OR trade_type ILIKE '%sale%') as sells,
          ROUND(SUM(total_value) FILTER (WHERE trade_type ILIKE '%buy%' OR trade_type ILIKE '%purchase%')::numeric, 2) as buy_value,
          ROUND(SUM(total_value) FILTER (WHERE trade_type ILIKE '%sell%' OR trade_type ILIKE '%sale%')::numeric, 2) as sell_value,
          COUNT(DISTINCT insider_name) as unique_insiders
       FROM gf_insider_trades
       WHERE trade_date >= CURRENT_DATE - $1::integer
       AND symbol IS NOT NULL AND symbol != ''
       GROUP BY symbol
       HAVING COUNT(*) >= 2
       ORDER BY COUNT(*) DESC
       LIMIT $2`,
      [days, limit * 2]
    );

    const enriched = rows.map((r: any) => {
      const buys = parseInt(r.buys || '0');
      const sells = parseInt(r.sells || '0');
      const total = buys + sells;
      const ratio = total > 0 ? buys / total : 0.5;
      const s = ratio > 0.6 ? 'bullish' : ratio < 0.4 ? 'bearish' : 'neutral';
      return { ...r, buy_ratio: Math.round(ratio * 1000) / 1000, sentiment: s };
    });

    const filtered = sentiment
      ? enriched.filter((r: any) => r.sentiment === sentiment)
      : enriched;

    return NextResponse.json({
      period_days: days,
      count: Math.min(filtered.length, limit),
      data: filtered.slice(0, limit),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
