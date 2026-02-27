import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get('action') || 'find_coordinated_trades';

  try {
    const { execSync } = await import('child_process');
    const query = searchParams.get('query') || '';
    const args = query ? `'${query.replace(/'/g, "\\'")}'` : '';
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "import modules.insider_network as m; import json; print(json.dumps(m.${action}(${args})))"`;
    const result = execSync(cmd, { timeout: 60000 }).toString().trim();
    const lines = result.split('\n');
    const jsonLine = lines[lines.length - 1];
    return NextResponse.json(JSON.parse(jsonLine));
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
