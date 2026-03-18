import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const tier = searchParams.get('tier');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    const rows = await query(
      `SELECT DISTINCT ON (r.symbol)
          r.symbol, r.gf_symbol, r.gf_score, r.financial_strength,
          r.profitability_rank, r.growth_rank,
          f.roe, f.roa, f.debt_to_equity, f.free_cash_flow
       FROM gf_rankings r
       LEFT JOIN LATERAL (
          SELECT roe, roa, debt_to_equity, free_cash_flow
          FROM gf_fundamentals WHERE symbol = r.symbol ORDER BY fetched_at DESC LIMIT 1
       ) f ON true
       WHERE r.gf_score IS NOT NULL
       ORDER BY r.symbol, r.fetched_at DESC`
    );

    const scored = rows.map((r: any) => {
      const fs = parseFloat(r.financial_strength || '0');
      const prof = parseFloat(r.profitability_rank || '0');
      const growth = parseFloat(r.growth_rank || '0');
      const roe = parseFloat(r.roe || '0');
      const de = parseFloat(r.debt_to_equity || '0');
      let q = (fs * 0.3 + prof * 0.3 + growth * 0.2) / 10;
      if (roe > 0.15) q += 10;
      if (de > 0 && de < 0.5) q += 5;
      q = Math.min(100, Math.max(0, q));
      const t = q >= 70 ? 'premium' : q >= 40 ? 'standard' : 'junk';
      return { ...r, quality_score: Math.round(q * 10) / 10, quality_tier: t };
    });

    const filtered = tier
      ? scored.filter((r: any) => r.quality_tier === tier)
      : scored;

    filtered.sort((a: any, b: any) => b.quality_score - a.quality_score);

    return NextResponse.json({
      count: Math.min(filtered.length, limit),
      data: filtered.slice(0, limit),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
