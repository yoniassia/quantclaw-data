import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const tradeType = searchParams.get('type');
  const days = Math.min(parseInt(searchParams.get('days') || '30'), 365);
  const limit = Math.min(parseInt(searchParams.get('limit') || '100'), 1000);

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, insider_name, insider_title, trade_type,
                shares, price, total_value, trade_date, filing_date, fetched_at
         FROM gf_insider_trades
         WHERE symbol = $1 AND trade_date >= CURRENT_DATE - $2::integer
         ORDER BY trade_date DESC LIMIT $3`,
        [symbol.toUpperCase(), days, limit]
      );

      const summary = await query(
        `SELECT trade_type, COUNT(*) as count, SUM(total_value) as total_value
         FROM gf_insider_trades
         WHERE symbol = $1 AND trade_date >= CURRENT_DATE - $2::integer
         GROUP BY trade_type`,
        [symbol.toUpperCase(), days]
      );

      return NextResponse.json({ symbol, days, trades: rows.length, summary, data: rows });
    }

    let sql = `SELECT symbol, gf_symbol, insider_name, insider_title, trade_type,
                shares, price, total_value, trade_date, fetched_at
               FROM gf_insider_trades
               WHERE trade_date >= CURRENT_DATE - $1::integer`;
    const params: unknown[] = [days];

    if (tradeType) {
      params.push(tradeType);
      sql += ` AND trade_type ILIKE $${params.length}`;
    }

    sql += ` ORDER BY trade_date DESC, total_value DESC NULLS LAST LIMIT $${params.length + 1}`;
    params.push(limit);

    const rows = await query(sql, params);
    return NextResponse.json({ days, count: rows.length, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
