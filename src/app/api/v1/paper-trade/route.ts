export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { ticker, quantity, side, portfolio = 'default', limit_price, order_type = 'market' } = body;
    
    if (!ticker || !quantity || !side) {
      return NextResponse.json({ error: 'ticker, quantity, and side required' }, { status: 400 });
    }
    
    if (!['buy', 'sell'].includes(side)) {
      return NextResponse.json({ error: 'side must be buy or sell' }, { status: 400 });
    }

    const { execSync } = await import('child_process');
    let cmd = `cd /home/quant/apps/quantclaw-data && python3 modules/paper_trading.py paper-${side} "${ticker}" ${quantity} --portfolio "${portfolio}"`;
    
    if (limit_price && order_type === 'limit') {
      cmd += ` --limit ${limit_price}`;
    }
    
    const output = execSync(cmd, { timeout: 15000 }).toString().trim();
    const data = JSON.parse(output);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed to execute trade' }, { status: 500 });
  }
}
