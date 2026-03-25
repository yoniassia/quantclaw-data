import { NextRequest, NextResponse } from 'next/server';
import { sapiQuery } from '@/lib/sapi-db';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const search = sp.get('search') || '';
  const sector = sp.get('sector') || '';
  const limit = Math.min(+(sp.get('limit') || '200'), 2000);
  const offset = +(sp.get('offset') || '0');

  try {
    const conditions: string[] = ['i.is_tradable = true'];
    const params: unknown[] = [];
    let pi = 1;

    if (search) {
      conditions.push(`(i.symbol ILIKE $${pi} OR i.display_name ILIKE $${pi})`);
      params.push(`%${search}%`);
      pi++;
    }
    if (sector) {
      conditions.push(`i.umbrella_sector ILIKE $${pi}`);
      params.push(`%${sector}%`);
      pi++;
    }

    const where = conditions.length ? 'WHERE ' + conditions.join(' AND ') : '';

    const rows = await sapiQuery(`
      SELECT
        i.instrument_id, i.symbol, i.display_name, i.exchange, i.umbrella_sector,
        i.market_cap_class, i.logo_url,
        p.current_rate, p.closing_price, p.daily_change_pct, p.weekly_change_pct,
        p.ytd_pct, p.market_cap_usd, p.ma_50d, p.ma_200d,
        f.pe_ratio, f.roe, f.net_margin, f.rev_growth_1y,
        a.consensus, a.target_upside_pct
      FROM instruments i
      LEFT JOIN LATERAL (
        SELECT * FROM instrument_prices WHERE instrument_id = i.instrument_id ORDER BY snapshot_date DESC, snapshot_hour DESC LIMIT 1
      ) p ON true
      LEFT JOIN LATERAL (
        SELECT * FROM instrument_fundamentals WHERE instrument_id = i.instrument_id ORDER BY snapshot_date DESC LIMIT 1
      ) f ON true
      LEFT JOIN LATERAL (
        SELECT * FROM instrument_analysts WHERE instrument_id = i.instrument_id ORDER BY snapshot_date DESC LIMIT 1
      ) a ON true
      ${where}
      ORDER BY p.market_cap_usd DESC NULLS LAST
      LIMIT $${pi} OFFSET $${pi + 1}
    `, [...params, limit, offset]);

    const [countRow] = await sapiQuery(`SELECT COUNT(*) as total FROM instruments i ${where}`, params);
    const total = +(countRow as Record<string, unknown>).total || 0;

    return NextResponse.json({ instruments: rows, total });
  } catch (err) {
    console.error('SAPI instruments error:', err);
    return NextResponse.json({ error: 'Failed to fetch instruments' }, { status: 500 });
  }
}
