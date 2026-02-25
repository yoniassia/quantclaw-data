import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Pairs Trading API
 * Phase 32: Cointegration detection, mean reversion opportunities, spread monitoring
 */

const MODULES_DIR = path.join(process.cwd(), 'modules');
const PAIRS_MODULE = path.join(MODULES_DIR, 'pairs_trading.py');

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const action = searchParams.get('action') || 'help';
    
    let command: string;
    
    switch (action) {
      case 'cointegration': {
        const symbol1 = searchParams.get('symbol1');
        const symbol2 = searchParams.get('symbol2');
        const lookback = searchParams.get('lookback') || '252';
        
        if (!symbol1 || !symbol2) {
          return NextResponse.json({
            error: 'Missing required parameters: symbol1, symbol2'
          }, { status: 400 });
        }
        
        command = `python3 ${PAIRS_MODULE} cointegration ${symbol1} ${symbol2} --lookback ${lookback}`;
        break;
      }
      
      case 'pairs-scan': {
        const sector = searchParams.get('sector');
        const limit = searchParams.get('limit') || '10';
        
        if (!sector) {
          return NextResponse.json({
            error: 'Missing required parameter: sector'
          }, { status: 400 });
        }
        
        command = `python3 ${PAIRS_MODULE} pairs-scan ${sector} --limit ${limit}`;
        break;
      }
      
      case 'spread-monitor': {
        const symbol1 = searchParams.get('symbol1');
        const symbol2 = searchParams.get('symbol2');
        const period = searchParams.get('period') || '30d';
        
        if (!symbol1 || !symbol2) {
          return NextResponse.json({
            error: 'Missing required parameters: symbol1, symbol2'
          }, { status: 400 });
        }
        
        command = `python3 ${PAIRS_MODULE} spread-monitor ${symbol1} ${symbol2} --period ${period}`;
        break;
      }
      
      case 'help':
      default: {
        return NextResponse.json({
          service: 'Pairs Trading Signals',
          phase: 32,
          description: 'Cointegration detection, mean reversion opportunities, spread monitoring',
          endpoints: {
            cointegration: {
              description: 'Test cointegration between two symbols using Engle-Granger test',
              params: {
                symbol1: 'First ticker symbol (required)',
                symbol2: 'Second ticker symbol (required)',
                lookback: 'Lookback period in days (default: 252)'
              },
              example: '/api/v1/pairs?action=cointegration&symbol1=KO&symbol2=PEP'
            },
            'pairs-scan': {
              description: 'Scan sector for cointegrated pairs',
              params: {
                sector: 'Sector name: tech, finance, energy, healthcare, consumer, beverage, retail (required)',
                limit: 'Max pairs to return (default: 10)'
              },
              example: '/api/v1/pairs?action=pairs-scan&sector=beverage&limit=5'
            },
            'spread-monitor': {
              description: 'Monitor spread dynamics and z-score history',
              params: {
                symbol1: 'First ticker symbol (required)',
                symbol2: 'Second ticker symbol (required)',
                period: 'Monitoring period (default: 30d)'
              },
              example: '/api/v1/pairs?action=spread-monitor&symbol1=AAPL&symbol2=MSFT&period=60d'
            }
          },
          techniques: {
            'Engle-Granger Test': 'Two-step cointegration test for stationary spreads',
            'Hedge Ratio': 'OLS regression coefficient for spread construction',
            'Half-Life': 'Mean reversion speed (Ornstein-Uhlenbeck process)',
            'Z-Score': 'Standardized spread for entry/exit signals'
          }
        });
      }
    }
    
    // Execute Python module
    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 60000, // 60 second timeout
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Python stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({
        error: 'Failed to parse Python output',
        raw: stdout,
        stderr: stderr
      }, { status: 500 });
    }
    
  } catch (error: any) {
    console.error('Pairs API error:', error);
    return NextResponse.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, { status: 500 });
  }
}
