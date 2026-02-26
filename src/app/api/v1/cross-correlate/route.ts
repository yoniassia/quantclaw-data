import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action') || 'correlate';
  const ticker = searchParams.get('ticker') || 'SPY';
  
  try {
    const { execSync } = await import('child_process');
    let result: string;
    
    if (action === 'correlate') {
      const series1 = searchParams.get('series1') || 'price_spy';
      const series2 = searchParams.get('series2') || 'price_qqq';
      const period = searchParams.get('period') || '1y';
      
      result = execSync(
        `cd /home/quant/apps/quantclaw-data && python3 modules/cross_correlate.py correlate ${series1} ${series2} ${ticker} ${period}`,
        { timeout: 30000 }
      ).toString();
    } else if (action === 'lead') {
      const candidates = searchParams.get('candidates') || 'AAPL,MSFT,GOOGL';
      
      result = execSync(
        `cd /home/quant/apps/quantclaw-data && python3 modules/cross_correlate.py lead ${ticker} ${candidates}`,
        { timeout: 30000 }
      ).toString();
    } else {
      return NextResponse.json({ error: 'Invalid action. Use correlate or lead' }, { status: 400 });
    }
    
    return NextResponse.json(JSON.parse(result));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
