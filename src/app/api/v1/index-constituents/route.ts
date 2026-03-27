import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const index = searchParams.get('index')?.toLowerCase();

  try {
    if (index) {
      const rows = await query(
        `SELECT symbol, display_name, sector, industry, metadata
         FROM symbol_universe
         WHERE is_active = true AND metadata->>'indices' LIKE '%' || $1 || '%'
         ORDER BY symbol`,
        [index]
      );
      return NextResponse.json({
        index,
        count: rows.length,
        symbols: rows.map((r: any) => r.symbol),
        data: rows,
      });
    }

    const stats = await query(
      `SELECT
         jsonb_array_elements_text(
           CASE WHEN metadata->>'indices' IS NOT NULL
             THEN (metadata->>'indices')::jsonb
             ELSE '[]'::jsonb END
         ) as index_name,
         COUNT(*) as count
       FROM symbol_universe
       WHERE is_active = true AND metadata->>'indices' IS NOT NULL
       GROUP BY 1 ORDER BY count DESC`
    );

    return NextResponse.json({
      available_indices: stats,
      usage: 'GET /api/v1/index-constituents?index=sp500',
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
