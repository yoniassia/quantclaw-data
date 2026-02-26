export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const ticker = req.nextUrl.searchParams.get('ticker') || '';
  const period = req.nextUrl.searchParams.get('period') || '2y';
  const interval = req.nextUrl.searchParams.get('interval') || 'daily';
  
  const query = ticker ? `${ticker} ${period} ${interval}`.trim() : '';

  try {
    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
from data.historical_prices import run
import json
result = run('${query.replace(/'/g, "\\'")}')
print(json.dumps(result, default=str))
"`;
    const output = execSync(cmd, { timeout: 30000, maxBuffer: 50 * 1024 * 1024 }).toString().trim();
    const lines = output.split('\n');
    const jsonLine = lines[lines.length - 1];
    const data = JSON.parse(jsonLine);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed to fetch historical prices' }, { status: 500 });
  }
}
