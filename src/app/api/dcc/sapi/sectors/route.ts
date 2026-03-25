import { NextResponse } from 'next/server';
import { sapiQuery } from '@/lib/sapi-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const sectors = await sapiQuery(`SELECT * FROM mv_sector_aggregates ORDER BY total_market_cap DESC NULLS LAST`);
    return NextResponse.json({ sectors });
  } catch (err) {
    console.error('SAPI sectors error:', err);
    return NextResponse.json({ sectors: [] });
  }
}
