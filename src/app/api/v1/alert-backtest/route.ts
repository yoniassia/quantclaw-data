import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

interface AlertBacktestParams {
  symbol: string;
  condition?: string;
  period?: string;
  action?: 'backtest' | 'signal-quality' | 'alert-potential';
}

/**
 * GET /api/v1/alert-backtest?symbol=AAPL&condition=rsi<30&action=backtest
 * 
 * Alert backtesting and signal quality analysis
 * 
 * Query params:
 *   - symbol: Stock ticker (required)
 *   - action: backtest | signal-quality | alert-potential (default: backtest)
 *   - condition: Alert condition string (required for backtest, e.g. "rsi<30")
 *   - period: Historical period (default: 1y, options: 1mo, 3mo, 6mo, 1y, 2y, 5y)
 * 
 * Returns:
 *   - For backtest: Hit rates, profit factor, signal quality score, individual signals
 *   - For signal-quality: Top-ranked alert conditions by quality score
 *   - For alert-potential: Trigger frequency and volatility metrics
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  
  const params: AlertBacktestParams = {
    symbol: searchParams.get('symbol') || '',
    condition: searchParams.get('condition') || '',
    period: searchParams.get('period') || '1y',
    action: (searchParams.get('action') || 'backtest') as any,
  };

  if (!params.symbol) {
    return NextResponse.json(
      { error: 'Missing required parameter: symbol' },
      { status: 400 }
    );
  }

  if (params.action === 'backtest' && !params.condition) {
    return NextResponse.json(
      { error: 'Missing required parameter: condition (for backtest action)' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'signal-quality':
        command = `python3 ${cliPath} signal-quality ${params.symbol} --period ${params.period}`;
        break;
      
      case 'alert-potential':
        command = `python3 ${cliPath} alert-potential ${params.symbol} --period ${params.period}`;
        break;
      
      case 'backtest':
      default:
        command = `python3 ${cliPath} alert-backtest ${params.symbol} --condition "${params.condition}" --period ${params.period}`;
        break;
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer
      timeout: 60000, // 60 second timeout
    });

    if (stderr && !stderr.includes('FutureWarning') && !stderr.includes('Storing cookies')) {
      console.error('Alert backtest stderr:', stderr);
    }

    // Try to parse JSON from output
    try {
      const jsonMatch = stdout.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const data = JSON.parse(jsonMatch[0]);
        return NextResponse.json({
          success: true,
          data,
          params,
        });
      }
    } catch (e) {
      console.error('Failed to parse JSON from output:', e);
    }

    // Fallback to raw output
    return NextResponse.json({
      success: true,
      output: stdout,
      params,
    });

  } catch (error: any) {
    console.error('Alert backtest error:', error);
    return NextResponse.json(
      { 
        error: 'Alert backtest failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/v1/alert-backtest
 * 
 * Same as GET but accepts JSON body for complex requests
 * 
 * Body:
 * {
 *   "symbol": "AAPL",
 *   "condition": "rsi<30",
 *   "period": "1y",
 *   "action": "backtest"
 * }
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  
  const params: AlertBacktestParams = {
    symbol: body.symbol || '',
    condition: body.condition || '',
    period: body.period || '1y',
    action: body.action || 'backtest',
  };

  if (!params.symbol) {
    return NextResponse.json(
      { error: 'Missing required parameter: symbol' },
      { status: 400 }
    );
  }

  if (params.action === 'backtest' && !params.condition) {
    return NextResponse.json(
      { error: 'Missing required parameter: condition (for backtest action)' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'signal-quality':
        command = `python3 ${cliPath} signal-quality ${params.symbol} --period ${params.period}`;
        break;
      
      case 'alert-potential':
        command = `python3 ${cliPath} alert-potential ${params.symbol} --period ${params.period}`;
        break;
      
      case 'backtest':
      default:
        command = `python3 ${cliPath} alert-backtest ${params.symbol} --condition "${params.condition}" --period ${params.period}`;
        break;
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024,
      timeout: 60000,
    });

    if (stderr && !stderr.includes('FutureWarning') && !stderr.includes('Storing cookies')) {
      console.error('Alert backtest stderr:', stderr);
    }

    // Try to parse JSON from output
    try {
      const jsonMatch = stdout.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const data = JSON.parse(jsonMatch[0]);
        return NextResponse.json({
          success: true,
          data,
          params,
        });
      }
    } catch (e) {
      console.error('Failed to parse JSON from output:', e);
    }

    // Fallback to raw output
    return NextResponse.json({
      success: true,
      output: stdout,
      params,
    });

  } catch (error: any) {
    console.error('Alert backtest error:', error);
    return NextResponse.json(
      { 
        error: 'Alert backtest failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}
