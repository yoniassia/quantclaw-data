import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker') || searchParams.get('symbol') || 'SPY';
  const action = searchParams.get('action') || 'get_corporate_actions';

  try {
    const { execSync } = await import('child_process');
    const args = ticker ? `'${ticker.replace(/'/g, "\\'")}'` : '';
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "import modules.stock_split_corporate_events as m; import json; print(json.dumps(m.${action}(${args})))"`;
    const result = execSync(cmd, { timeout: 60000 }).toString().trim();
    const lines = result.split('\n');
    const jsonLine = lines[lines.length - 1];
    return NextResponse.json(JSON.parse(jsonLine));
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
