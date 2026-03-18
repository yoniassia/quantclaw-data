import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const maxRatio = parseFloat(searchParams.get('max_ratio') || '1.0');
  const minScore = parseFloat(searchParams.get('min_gf_score') || '0');
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    const rows = await query(
      `SELECT DISTINCT ON (v.symbol)
          v.symbol, v.gf_symbol, v.gf_value, v.dcf_value, v.graham_number,
          v.current_price, v.price_to_gf_value,
          r.gf_score, r.financial_strength, r.profitability_rank, r.growth_rank
       FROM gf_valuations v
       LEFT JOIN LATERAL (
          SELECT gf_score, financial_strength, profitability_rank, growth_rank
          FROM gf_rankings WHERE symbol = v.symbol ORDER BY fetched_at DESC LIMIT 1
       ) r ON true
       WHERE v.price_to_gf_value IS NOT NULL
         AND v.price_to_gf_value <= $1
         AND (r.gf_score IS NULL OR r.gf_score >= $2)
       ORDER BY v.symbol, v.fetched_at DESC`,
      [maxRatio, minScore]
    );

    const enriched = rows.map((r: any) => ({
      ...r,
      discount_pct: r.price_to_gf_value ? Math.round((1 - r.price_to_gf_value) * 100 * 10) / 10 : null,
      opportunity_score: r.price_to_gf_value && r.gf_score
        ? Math.round(((1 - r.price_to_gf_value) * 100 * 0.4 + r.gf_score * 0.6) * 10) / 10
        : null,
    }));

    enriched.sort((a: any, b: any) => (b.opportunity_score || 0) - (a.opportunity_score || 0));

    return NextResponse.json({
      filter: { max_ratio: maxRatio, min_gf_score: minScore },
      count: Math.min(enriched.length, limit),
      data: enriched.slice(0, limit),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
