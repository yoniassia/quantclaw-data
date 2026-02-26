import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const ticker = searchParams.get('ticker') || 'AAPL';
  
  try {
    const { execSync } = await import('child_process');
    const result = execSync(
      `cd /home/quant/apps/quantclaw-data && python3 modules/signal_fusion.py get ${ticker}`,
      { timeout: 30000 }
    ).toString();
    
    return NextResponse.json(JSON.parse(result));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
