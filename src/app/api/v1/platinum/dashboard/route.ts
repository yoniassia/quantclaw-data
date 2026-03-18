import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const sortBy = searchParams.get('sort') || 'composite_score';
  const minScore = parseFloat(searchParams.get('min_score') || '0');
  const sector = searchParams.get('sector') || '';
  const limit = Math.min(parseInt(searchParams.get('limit') || '50'), 200);

  try {
    const { execSync } = await import('child_process');
    const cmd = `cd /home/quant/apps/quantclaw-data && python3 -c "
import json
from modules.platinum_enriched import get_platinum_dashboard
data = get_platinum_dashboard(
    sort_by='${sortBy.replace(/'/g, '')}',
    min_score=${isNaN(minScore) ? 0 : minScore},
    sector=${sector ? `'${sector.replace(/'/g, '')}'` : 'None'},
    limit=${limit},
)
print(json.dumps(data, default=str))
"`;
    const result = execSync(cmd, {
      timeout: 30000,
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    }).toString().trim();

    const lines = result.split('\n');
    return NextResponse.json(JSON.parse(lines[lines.length - 1]), {
      headers: { 'Cache-Control': 'public, max-age=60' },
    });
  } catch (e: any) {
    return NextResponse.json(
      { error: e.message?.slice(0, 500) },
      { status: 500 }
    );
  }
}
