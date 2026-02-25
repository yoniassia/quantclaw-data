import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

interface WalkForwardParams {
  symbol: string;
  strategy?: string;
  inSample?: number;
  outSample?: number;
  step?: number;
  action?: 'optimize' | 'overfit-check' | 'param-stability';
}

/**
 * GET /api/v1/walk-forward?symbol=SPY&action=optimize
 * 
 * Walk-forward optimization for strategy backtesting
 * 
 * Query params:
 *   - symbol: Stock ticker (required)
 *   - action: optimize | overfit-check | param-stability (default: optimize)
 *   - strategy: sma-crossover (default)
 *   - inSample: In-sample window days (default: 252)
 *   - outSample: Out-of-sample window days (default: 63)
 *   - step: Window step days (default: 63)
 * 
 * Returns:
 *   - For optimize: Full walk-forward analysis results
 *   - For overfit-check: Boolean overfitting detection + metrics
 *   - For param-stability: Parameter stability analysis
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  
  const params: WalkForwardParams = {
    symbol: searchParams.get('symbol') || '',
    strategy: searchParams.get('strategy') || 'sma-crossover',
    inSample: parseInt(searchParams.get('inSample') || '252'),
    outSample: parseInt(searchParams.get('outSample') || '63'),
    step: parseInt(searchParams.get('step') || '63'),
    action: (searchParams.get('action') || 'optimize') as any,
  };

  if (!params.symbol) {
    return NextResponse.json(
      { error: 'Missing required parameter: symbol' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'overfit-check':
        command = `python3 ${cliPath} overfit-check ${params.symbol} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
      
      case 'param-stability':
        command = `python3 ${cliPath} param-stability ${params.symbol} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
      
      case 'optimize':
      default:
        command = `python3 ${cliPath} walk-forward ${params.symbol} --strategy ${params.strategy} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Walk-forward stderr:', stderr);
    }

    // Try to parse as JSON first (for overfit-check and param-stability)
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
      // Not JSON, return raw output
    }

    // Return formatted text output for full walk-forward analysis
    return NextResponse.json({
      success: true,
      output: stdout,
      params,
    });

  } catch (error: any) {
    console.error('Walk-forward error:', error);
    return NextResponse.json(
      { 
        error: 'Walk-forward analysis failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/v1/walk-forward
 * 
 * Same as GET but accepts JSON body for complex requests
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  
  const params: WalkForwardParams = {
    symbol: body.symbol || '',
    strategy: body.strategy || 'sma-crossover',
    inSample: body.inSample || 252,
    outSample: body.outSample || 63,
    step: body.step || 63,
    action: body.action || 'optimize',
  };

  if (!params.symbol) {
    return NextResponse.json(
      { error: 'Missing required parameter: symbol' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'overfit-check':
        command = `python3 ${cliPath} overfit-check ${params.symbol} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
      
      case 'param-stability':
        command = `python3 ${cliPath} param-stability ${params.symbol} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
      
      case 'optimize':
      default:
        command = `python3 ${cliPath} walk-forward ${params.symbol} --strategy ${params.strategy} --in-sample ${params.inSample} --out-sample ${params.outSample} --step ${params.step}`;
        break;
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024,
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Walk-forward stderr:', stderr);
    }

    // Try to parse as JSON
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
      // Not JSON
    }

    return NextResponse.json({
      success: true,
      output: stdout,
      params,
    });

  } catch (error: any) {
    console.error('Walk-forward error:', error);
    return NextResponse.json(
      { 
        error: 'Walk-forward analysis failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}
