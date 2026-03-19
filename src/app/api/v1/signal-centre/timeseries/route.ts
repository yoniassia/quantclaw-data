import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

interface CrossCadenceRow {
  trade_date: string;
  symbol: string;
  gf_score: string;
  growth_rank: string;
  momentum_rank: string;
  financial_strength: string;
  profitability_rank: string;
  eps: string;
  bvps: string;
  sector: string;
  beta: string;
  ema_20: string;
  sma_200: string;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const from = searchParams.get('from');
  const to = searchParams.get('to');
  const limit = Math.min(parseInt(searchParams.get('limit') || '30'), 365);

  if (!symbol) {
    return NextResponse.json(
      { error: 'symbol parameter required (e.g. ?symbol=AAPL)' },
      { status: 400 }
    );
  }

  try {
    const conditions: string[] = ['symbol = $1'];
    const params: unknown[] = [symbol.toUpperCase()];
    let paramIdx = 2;

    if (from) {
      conditions.push(`trade_date >= $${paramIdx}::date`);
      params.push(from);
      paramIdx++;
    }
    if (to) {
      conditions.push(`trade_date <= $${paramIdx}::date`);
      params.push(to);
      paramIdx++;
    }

    const where = `WHERE ${conditions.join(' AND ')}`;
    const sql = `SELECT * FROM mv_cross_cadence_daily ${where} ORDER BY trade_date DESC LIMIT $${paramIdx}`;
    params.push(limit);

    const rows = await query<CrossCadenceRow>(sql, params);

    return NextResponse.json({
      symbol: symbol.toUpperCase(),
      count: rows.length,
      data: rows,
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
