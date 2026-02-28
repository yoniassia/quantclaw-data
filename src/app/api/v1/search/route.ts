import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || searchParams.get('query') || '';
  const topK = parseInt(searchParams.get('top_k') || '5');

  if (!q) {
    return NextResponse.json({ error: 'Missing required param: q (e.g. ?q=OPEC+oil+production)' }, { status: 400 });
  }

  try {
    const { execSync } = await import('child_process');
    const safeQ = q.replace(/'/g, "\\'").replace(/"/g, '\\"');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
from scripts.search_modules import search
import json
results = search('${safeQ}', ${topK})
print(json.dumps(results))
"`;
    const result = execSync(cmd, { timeout: 10000 }).toString().trim();
    const lines = result.split('\n');
    const jsonLine = lines[lines.length - 1];
    return NextResponse.json(JSON.parse(jsonLine));
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
