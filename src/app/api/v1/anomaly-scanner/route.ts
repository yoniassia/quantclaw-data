import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const tickers = searchParams.get('tickers') || 'AAPL,MSFT,NVDA,GOOGL,TSLA,META,AMZN,JPM,SPY,QQQ';
  
  try {
    const { execSync } = await import('child_process');
    const result = execSync(
      `cd /home/quant/apps/quantclaw-data && python3 modules/anomaly_scanner.py scan ${tickers}`,
      { timeout: 30000 }
    ).toString();
    
    return NextResponse.json(JSON.parse(result));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
