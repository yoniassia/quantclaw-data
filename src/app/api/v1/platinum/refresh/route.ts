import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const tickers = body.tickers as string[] | undefined;
  const workers = Math.min(parseInt(body.workers || '3'), 6);

  try {
    const { execSync } = await import('child_process');

    if (tickers && tickers.length > 0) {
      const tickerList = tickers
        .slice(0, 50)
        .map((t: string) => `'${t.toUpperCase().replace(/[^A-Z0-9.\-]/g, '')}'`)
        .join(',');
      const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json
from modules.platinum_enriched import get_platinum_batch
data = get_platinum_batch([${tickerList}], max_workers=${workers})
stats = {'total': len(data), 'success': sum(1 for v in data.values() if not v.get('error')), 'failed': [k for k,v in data.items() if v.get('error')]}
print(json.dumps(stats, default=str))
"`;
      const result = execSync(cmd, {
        timeout: 600000,
        maxBuffer: 50 * 1024 * 1024,
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
      }).toString().trim();

      const lines = result.split('\n');
      return NextResponse.json(JSON.parse(lines[lines.length - 1]));
    }

    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json
from modules.platinum_enriched import refresh_universe
data = refresh_universe(max_workers=${workers})
print(json.dumps(data, default=str))
"`;
    const result = execSync(cmd, {
      timeout: 600000,
      maxBuffer: 50 * 1024 * 1024,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    }).toString().trim();

    const lines = result.split('\n');
    return NextResponse.json(JSON.parse(lines[lines.length - 1]));
  } catch (e: any) {
    return NextResponse.json(
      { error: e.message?.slice(0, 500) },
      { status: 500 }
    );
  }
}
