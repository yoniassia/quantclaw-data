import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
export const dynamic = 'force-dynamic';

const QUANTCLAW_DATA_DIR = '/home/quant/apps/quantclaw-data';
const PYTHON = 'python3';

/**
 * Signal Discovery Engine API — Automated Alpha Signal Factory
 * 
 * Systematically tests correlations between price returns and all available data modules
 * to discover new alpha signals.
 * 
 * Endpoints:
 * - GET /api/v1/signal-discovery?action=discover
 * - GET /api/v1/signal-discovery?action=discover&universe=AAPL,MSFT,NVDA&lookback=252
 * 
 * Query Parameters:
 * - action: 'discover' (default)
 * - universe: Comma-separated tickers (default: AAPL,MSFT,NVDA,GOOGL,TSLA)
 * - lookback: Historical period in days (default: 252)
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action') || 'discover';
  const universe = searchParams.get('universe') || 'AAPL,MSFT,NVDA,GOOGL,TSLA';
  const lookback = searchParams.get('lookback') || '252';
  
  try {
    let command: string;
    
    switch (action) {
      case 'discover':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.signal_discovery_engine; import json; result = modules.signal_discovery_engine.discover_signals(universe='${universe}'.split(','), lookback_days=${lookback}); print(json.dumps(result))"`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ['discover']
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 120000,  // 2 minutes (yfinance can be slow)
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Signal Discovery Engine stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: 'Response was not valid JSON'
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error('Signal Discovery API Error:', errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        suggestion: 'Make sure yfinance, numpy, scipy are installed: pip install yfinance numpy scipy'
      },
      { status: 500 }
    );
  }
}
