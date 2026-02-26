export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const ticker = req.nextUrl.searchParams.get('ticker') || '';
  const strategy = req.nextUrl.searchParams.get('strategy') || '';
  const action = req.nextUrl.searchParams.get('action') || 'quick';

  const query = ticker ? `${ticker} ${strategy || action}`.trim() : '';

  try {
    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
from data.vectorbt_backtest import run
import json
result = run('${query.replace(/'/g, "\\'")}')
print(json.dumps(result, default=str))
"`;
    const output = execSync(cmd, { timeout: 60000, maxBuffer: 10 * 1024 * 1024 }).toString().trim();
    const lines = output.split('\n');
    const jsonLine = lines[lines.length - 1];
    const data = JSON.parse(jsonLine);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Backtest failed' }, { status: 500 });
  }
}
