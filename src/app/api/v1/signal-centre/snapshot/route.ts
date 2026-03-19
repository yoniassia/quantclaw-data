import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

interface SymbolSnapshot {
  symbol: string;
  company_name: string;
  sector: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  price_ts: string;
  beta: number;
  ema_20: number;
  ema_50: number;
  ema_200: number;
  sma_50: number;
  sma_200: number;
  eps: number;
  bvps: number;
  fcf_per_share: number;
  revenue_per_share: number;
  gf_score: number;
  growth_rank: number;
  momentum_rank: number;
  financial_strength: number;
  profitability_rank: number;
  gf_value: number;
  price_to_gf: number;
  gf_value_rank: number;
  predictability_rank: number;
  reported_eps: number;
  reported_revenue: number;
  reported_net_income: number;
  insider_tx_count_30d: number;
  insider_buys_30d: number;
  insider_sells_30d: number;
  next_earnings_date: string;
  earnings_estimate: number;
  last_updated: string;
  refreshed_at: string;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const sector = searchParams.get('sector');
  const sortBy = searchParams.get('sort') || 'gf_score';
  const order = searchParams.get('order') === 'asc' ? 'ASC' : 'DESC';
  const limit = Math.min(parseInt(searchParams.get('limit') || '100'), 500);
  const minScore = parseFloat(searchParams.get('min_score') || '0');

  const allowedSorts = [
    'gf_score', 'price', 'volume', 'beta', 'eps', 'growth_rank',
    'momentum_rank', 'financial_strength', 'profitability_rank',
    'gf_value', 'insider_tx_count_30d', 'symbol',
  ];
  const safeSort = allowedSorts.includes(sortBy) ? sortBy : 'gf_score';

  try {
    const conditions: string[] = [];
    const params: unknown[] = [];
    let paramIdx = 1;

    if (symbol) {
      const symbols = symbol.toUpperCase().split(',').map(s => s.trim());
      conditions.push(`symbol = ANY($${paramIdx})`);
      params.push(symbols);
      paramIdx++;
    }
    if (sector) {
      conditions.push(`sector ILIKE $${paramIdx}`);
      params.push(`%${sector}%`);
      paramIdx++;
    }
    if (minScore > 0) {
      conditions.push(`COALESCE(gf_score, 0) >= $${paramIdx}`);
      params.push(minScore);
      paramIdx++;
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const sql = `SELECT * FROM mv_symbol_latest ${where} ORDER BY ${safeSort} ${order} NULLS LAST LIMIT $${paramIdx}`;
    params.push(limit);

    const rows = await query<SymbolSnapshot>(sql, params);

    return NextResponse.json({
      count: rows.length,
      sort: safeSort,
      order: order.toLowerCase(),
      data: rows,
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
