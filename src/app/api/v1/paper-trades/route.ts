export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    const portfolio = req.nextUrl.searchParams.get('portfolio') || 'default';
    const days = req.nextUrl.searchParams.get('days') || '30';

    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 modules/paper_trading.py paper-trades --portfolio "${portfolio}" --days ${days}`;
    const output = execSync(cmd, { timeout: 10000 }).toString().trim();
    const data = JSON.parse(output);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed to fetch trades' }, { status: 500 });
  }
}
