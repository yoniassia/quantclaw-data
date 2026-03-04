import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get('action') || 'get_stock_quote';
  const symbol = searchParams.get('symbol') || '';
  const start = searchParams.get('start') || '';
  const end = searchParams.get('end') || '';
  const period = searchParams.get('period') || 'annual';
  const interval = searchParams.get('interval') || '1d';
  const limit = searchParams.get('limit') || '50';

  try {
    const { execSync } = await import('child_process');
    
    let cmd = '';
    
    // Route to appropriate function
    switch(action) {
      case 'get_stock_quote':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_stock_quote('${symbol}'), default=str))"`;
        break;
      case 'get_historical_prices':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_historical_prices('${symbol}', ${start ? `'${start}'` : 'None'}, ${end ? `'${end}'` : 'None'}, '${interval}'), default=str))"`;
        break;
      case 'get_financial_statements':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_financial_statements('${symbol}', '${period}'), default=str))"`;
        break;
      case 'get_analyst_estimates':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_analyst_estimates('${symbol}'), default=str))"`;
        break;
      case 'get_economic_calendar':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_economic_calendar(${start ? `'${start}'` : 'None'}, ${end ? `'${end}'` : 'None'}), default=str))"`;
        break;
      case 'get_etf_holdings':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_etf_holdings('${symbol}'), default=str))"`;
        break;
      case 'get_options_chains':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_options_chains('${symbol}'), default=str))"`;
        break;
      case 'get_insider_trading':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_insider_trading('${symbol}', ${limit}), default=str))"`;
        break;
      case 'get_institutional_holders':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_institutional_holders('${symbol}'), default=str))"`;
        break;
      case 'get_news':
        cmd = `cd /home/quant/apps/quantclaw-data && /usr/bin/python3 -c "import modules.openbb_platform as m; import json; print(json.dumps(m.get_news('${symbol}', ${limit}), default=str))"`;
        break;
      default:
        return NextResponse.json({ error: 'Invalid action', available_actions: [
          'get_stock_quote', 'get_historical_prices', 'get_financial_statements',
          'get_analyst_estimates', 'get_economic_calendar', 'get_etf_holdings',
          'get_options_chains', 'get_insider_trading', 'get_institutional_holders',
          'get_news'
        ]}, { status: 400 });
    }
    
    const result = execSync(cmd, { timeout: 60000 }).toString().trim();
    const lines = result.split('\n');
    const jsonLine = lines[lines.length - 1];
    return NextResponse.json(JSON.parse(jsonLine));
  } catch (e: any) {
    return NextResponse.json({ error: e.message?.slice(0, 500) }, { status: 500 });
  }
}
