import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ symbol: string }> }
) {
  const { symbol } = await params;
  const { searchParams } = new URL(request.url);
  const mode = searchParams.get('mode') || 'full';
  const nocache = searchParams.get('nocache') === '1';

  const ticker = symbol.toUpperCase().replace(/[^A-Z0-9.\-]/g, '');
  if (!ticker || ticker.length > 10) {
    return NextResponse.json({ error: 'Invalid symbol' }, { status: 400 });
  }

  const action = mode === 'summary' ? 'summary' : 'full';
  const cacheFlag = nocache ? 'False' : 'True';

  try {
    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json, sys
from modules.platinum_enriched import get_platinum, get_platinum_summary
data = get_platinum_summary('${ticker}') if '${action}' == 'summary' else get_platinum('${ticker}', use_cache=${cacheFlag})
print(json.dumps(data, default=str))
"`;
    const result = execSync(cmd, {
      timeout: 120000,
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    }).toString().trim();

    const lines = result.split('\n');
    const jsonLine = lines[lines.length - 1];
    const data = JSON.parse(jsonLine);

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, max-age=300, s-maxage=600',
        'X-Platinum-Tier': 'true',
      },
    });
  } catch (e: any) {
    return NextResponse.json(
      { error: e.message?.slice(0, 500), ticker },
      { status: 500 }
    );
  }
}
