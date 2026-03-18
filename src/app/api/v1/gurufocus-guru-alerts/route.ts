import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const level = searchParams.get('level');
  const symbol = searchParams.get('symbol');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    let sql = `SELECT h.guru_id, g.name as guru_name, g.firm,
                h.symbol, h.gf_symbol, h.change_type, h.change_pct,
                h.shares, h.portfolio_weight, h.current_price, h.market_value,
                h.portfolio_date, h.fetched_at
               FROM gf_guru_holdings h
               JOIN gf_gurus g ON g.guru_id = h.guru_id
               WHERE h.change_type IS NOT NULL
                 AND h.change_type NOT IN ('', 'no_change')`;

    const params: unknown[] = [];

    if (symbol) {
      params.push(symbol.toUpperCase());
      sql += ` AND h.symbol = $${params.length}`;
    }

    sql += ` ORDER BY h.fetched_at DESC LIMIT $${params.length + 1}`;
    params.push(limit * 3);

    const rows = await query(sql, params);

    const alerts = rows.map((r: any) => {
      const ct = (r.change_type || '').toLowerCase();
      const pct = Math.abs(parseFloat(r.change_pct || '0'));
      const isHigh = ct.includes('new') || ct.includes('exit') || pct > 100;
      return { ...r, alert_level: isHigh ? 'high' : 'medium' };
    }).filter((r: any) => {
      const ct = (r.change_type || '').toLowerCase();
      return ct.includes('new') || ct.includes('add') || ct.includes('sold') ||
             ct.includes('exit') || Math.abs(parseFloat(r.change_pct || '0')) > 50;
    });

    const filtered = level
      ? alerts.filter((r: any) => r.alert_level === level)
      : alerts;

    return NextResponse.json({
      count: Math.min(filtered.length, limit),
      data: filtered.slice(0, limit),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
