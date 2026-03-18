import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const signal = searchParams.get('signal') || 'all';
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    const rows = await query(
      `SELECT DISTINCT ON (symbol)
          symbol, gf_symbol, gf_value, dcf_value, graham_number,
          current_price, price_to_gf_value, fetched_at
       FROM gf_valuations
       WHERE gf_value IS NOT NULL AND gf_value > 0
         AND current_price IS NOT NULL AND current_price > 0
       ORDER BY symbol, fetched_at DESC`
    );

    const enriched = rows.map((r: any) => {
      const price = parseFloat(r.current_price);
      const gfVal = parseFloat(r.gf_value);
      const dcf = parseFloat(r.dcf_value || '0');
      const graham = parseFloat(r.graham_number || '0');
      const gapPct = Math.round((gfVal - price) / gfVal * 100 * 10) / 10;
      let modelsBelow = 0;
      if (dcf > 0 && price < dcf) modelsBelow++;
      if (graham > 0 && price < graham) modelsBelow++;
      if (price < gfVal) modelsBelow++;
      const sig = gapPct > 20 ? 'undervalued' : gapPct < -20 ? 'overvalued' : 'fair';
      return { ...r, gap_pct: gapPct, models_below_price: modelsBelow, signal: sig };
    });

    const filtered = signal === 'all'
      ? enriched
      : enriched.filter((r: any) => r.signal === signal);

    filtered.sort((a: any, b: any) => b.gap_pct - a.gap_pct);

    return NextResponse.json({
      filter: signal,
      count: Math.min(filtered.length, limit),
      data: filtered.slice(0, limit),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
