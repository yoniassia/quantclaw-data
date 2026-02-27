export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { name, initial_cash = 100000 } = body;
    
    if (!name) {
      return NextResponse.json({ error: 'Portfolio name required' }, { status: 400 });
    }

    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 modules/paper_trading.py paper-create "${name.replace(/"/g, '\\"')}" --cash ${initial_cash}`;
    const output = execSync(cmd, { timeout: 10000 }).toString().trim();
    const data = JSON.parse(output);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed to create portfolio' }, { status: 500 });
  }
}
