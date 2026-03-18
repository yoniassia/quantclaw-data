import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbols = searchParams.get('symbols') || 'AAPL,MSFT,GOOGL';
  const tickers = symbols
    .toUpperCase()
    .split(',')
    .map((s) => s.trim().replace(/[^A-Z0-9.\-]/g, ''))
    .filter(Boolean)
    .slice(0, 20);

  if (tickers.length === 0) {
    return NextResponse.json({ error: 'No valid symbols' }, { status: 400 });
  }

  try {
    const { execSync } = await import('child_process');
    const tickerList = tickers.map((t) => `'${t}'`).join(',');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json
from modules.platinum_enriched import get_platinum_batch
data = get_platinum_batch([${tickerList}])
print(json.dumps(data, default=str))
"`;
    const result = execSync(cmd, {
      timeout: 300000,
      maxBuffer: 50 * 1024 * 1024,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    }).toString().trim();

    const lines = result.split('\n');
    return NextResponse.json(JSON.parse(lines[lines.length - 1]), {
      headers: {
        'Cache-Control': 'public, max-age=300',
        'X-Platinum-Batch': String(tickers.length),
      },
    });
  } catch (e: any) {
    return NextResponse.json(
      { error: e.message?.slice(0, 500), requested: tickers },
      { status: 500 }
    );
  }
}
