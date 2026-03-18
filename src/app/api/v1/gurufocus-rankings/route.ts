import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 500);
  const minScore = searchParams.get('min_score');
  const sortBy = searchParams.get('sort') || 'gf_score';

  try {
    if (symbol) {
      const rows = await query(
        `SELECT symbol, gf_symbol, gf_score, financial_strength, profitability_rank,
                growth_rank, gf_value_rank, momentum_rank, predictability_rank,
                fetched_at, payload
         FROM gf_rankings WHERE symbol = $1 ORDER BY fetched_at DESC LIMIT $2`,
        [symbol.toUpperCase(), limit]
      );
      return NextResponse.json({ symbol, count: rows.length, data: rows });
    }

    const validSorts: Record<string, string> = {
      gf_score: 'gf_score DESC NULLS LAST',
      financial_strength: 'financial_strength DESC NULLS LAST',
      profitability: 'profitability_rank DESC NULLS LAST',
      growth: 'growth_rank DESC NULLS LAST',
      value: 'gf_value_rank DESC NULLS LAST',
      momentum: 'momentum_rank DESC NULLS LAST',
    };
    const orderBy = validSorts[sortBy] || validSorts.gf_score;

    let sql = `SELECT DISTINCT ON (symbol) symbol, gf_symbol, gf_score, financial_strength,
                profitability_rank, growth_rank, gf_value_rank, momentum_rank,
                predictability_rank, fetched_at
               FROM gf_rankings`;
    const params: unknown[] = [];

    if (minScore) {
      params.push(parseFloat(minScore));
      sql += ` WHERE gf_score >= $${params.length}`;
    }

    sql += ` ORDER BY symbol, fetched_at DESC`;

    const subquery = `SELECT * FROM (${sql}) sub ORDER BY ${orderBy} LIMIT $${params.length + 1}`;
    params.push(limit);

    const rows = await query(subquery, params);
    return NextResponse.json({ count: rows.length, data: rows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
