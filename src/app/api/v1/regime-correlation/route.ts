import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
export const dynamic = 'force-dynamic';

const QUANTCLAW_DATA_DIR = '/home/quant/apps/quantclaw-data';
const PYTHON = 'python3';

/**
 * Regime Correlation API — Cross-Asset Regime Detector
 * 
 * Tracks rolling correlations between major assets to detect market regime changes.
 * Identifies: risk-on, risk-off, transition, and decorrelation regimes.
 * 
 * Endpoints:
 * - GET /api/v1/regime-correlation?action=detect
 * - GET /api/v1/regime-correlation?action=detect&lookback=60
 * - GET /api/v1/regime-correlation?action=matrix
 * - GET /api/v1/regime-correlation?action=matrix&tickers=SPY,TLT,GLD&period=6mo
 * 
 * Query Parameters:
 * - action: 'detect' or 'matrix' (default: 'detect')
 * - lookback: Number of days for regime detection (default: 60)
 * - tickers: Comma-separated tickers for correlation matrix (default: SPY,TLT,GLD,BTC-USD,DX-Y.NYB,USO)
 * - period: Time period for correlation matrix (default: 6mo)
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action') || 'detect';
  const lookback = searchParams.get('lookback') || '60';
  const tickers = searchParams.get('tickers') || 'SPY,TLT,GLD,BTC-USD,DX-Y.NYB,USO';
  const period = searchParams.get('period') || '6mo';
  
  try {
    let command: string;
    
    switch (action) {
      case 'detect':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.regime_correlation; import json; result = modules.regime_correlation.detect_regime(lookback=${lookback}); print(json.dumps(result))"`;
        break;
      
      case 'matrix':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.regime_correlation; import json; result = modules.regime_correlation.get_correlation_matrix(tickers='${tickers}'.split(','), period='${period}'); print(json.dumps(result))"`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ['detect', 'matrix']
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 90000,  // 90 seconds
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Regime Correlation Module stderr:', stderr);
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
    console.error('Regime Correlation API Error:', errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        suggestion: 'Make sure yfinance, pandas, numpy, scipy are installed'
      },
      { status: 500 }
    );
  }
}
