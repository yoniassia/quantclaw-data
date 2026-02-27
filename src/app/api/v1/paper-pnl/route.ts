export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    const portfolio = req.nextUrl.searchParams.get('portfolio') || 'default';

    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 modules/paper_trading.py paper-pnl --portfolio "${portfolio}"`;
    const output = execSync(cmd, { timeout: 30000 }).toString().trim();
    const data = JSON.parse(output);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed to fetch P&L' }, { status: 500 });
  }
}
