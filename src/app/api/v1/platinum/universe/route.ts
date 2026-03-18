import { NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json
from modules.platinum_enriched import get_universe
print(json.dumps({'universe': get_universe(), 'count': len(get_universe())}))
"`;
    const result = execSync(cmd, { timeout: 10000 }).toString().trim();
    const lines = result.split('\n');
    return NextResponse.json(JSON.parse(lines[lines.length - 1]));
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
