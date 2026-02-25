import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

interface AlertDashboardParams {
  ticker?: string;
  alertType?: 'rsi' | 'volume' | 'breakout' | 'earnings';
  years?: number;
  action?: 'backtest' | 'performance' | 'optimize' | 'report';
  holdDays?: number;
}

/**
 * GET /api/v1/alert-dashboard?action=backtest&ticker=AAPL&alertType=rsi&years=3
 * 
 * Alert backtesting dashboard with profit factor, Sharpe ratio, and win rate
 * 
 * Query params:
 *   - action: backtest | performance | optimize | report (required)
 *   - ticker: Stock ticker (required for backtest/optimize)
 *   - alertType: rsi | volume | breakout | earnings (required for backtest, default: rsi for optimize)
 *   - years: Years of historical data (default: 3)
 *   - holdDays: Days to hold position (default: 5, used in backtest)
 * 
 * Returns:
 *   - For backtest: Individual alert type performance with profit factor, Sharpe, win rate, max drawdown
 *   - For performance: Comparison of all alert types across multiple tickers
 *   - For optimize: Best parameters for alert type on specific ticker
 *   - For report: Comprehensive report across all tickers and alert types
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  
  const params: AlertDashboardParams = {
    action: (searchParams.get('action') || 'backtest') as any,
    ticker: searchParams.get('ticker') || '',
    alertType: (searchParams.get('alertType') || 'rsi') as any,
    years: parseInt(searchParams.get('years') || '3'),
    holdDays: parseInt(searchParams.get('holdDays') || '5'),
  };

  // Validate required params based on action
  if (params.action === 'backtest' || params.action === 'optimize') {
    if (!params.ticker) {
      return NextResponse.json(
        { error: `Missing required parameter: ticker (for ${params.action} action)` },
        { status: 400 }
      );
    }
  }

  if (params.action === 'backtest' && !params.alertType) {
    return NextResponse.json(
      { error: 'Missing required parameter: alertType (for backtest action)' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'backtest':
        command = `python3 ${cliPath} dashboard-backtest ${params.alertType} --ticker ${params.ticker} --years ${params.years} --hold-days ${params.holdDays}`;
        break;
      
      case 'performance':
        command = `python3 ${cliPath} dashboard-performance --years ${params.years}`;
        break;
      
      case 'optimize':
        command = `python3 ${cliPath} dashboard-optimize ${params.ticker} --alert-type ${params.alertType} --years ${params.years}`;
        break;
      
      case 'report':
        // Use temp file for report output
        const reportFile = `/tmp/alert-report-${Date.now()}.json`;
        command = `python3 ${cliPath} dashboard-report --output ${reportFile}`;
        break;
      
      default:
        return NextResponse.json(
          { error: `Invalid action: ${params.action}. Must be one of: backtest, performance, optimize, report` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 20 * 1024 * 1024, // 20MB buffer
      timeout: 120000, // 120 second timeout
    });

    if (stderr && !stderr.includes('FutureWarning') && !stderr.includes('Storing cookies') && !stderr.includes('[*********************100%')) {
      console.error('Alert dashboard stderr:', stderr);
    }

    // For report action, try to read the JSON file
    if (params.action === 'report') {
      const reportFile = command.match(/--output\s+(\S+)/)?.[1];
      if (reportFile) {
        try {
          const fs = require('fs');
          const reportData = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
          fs.unlinkSync(reportFile); // Clean up temp file
          return NextResponse.json({
            success: true,
            data: reportData,
            params,
          });
        } catch (e) {
          console.error('Failed to read report file:', e);
        }
      }
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
    console.error('Alert dashboard error:', error);
    return NextResponse.json(
      { 
        error: 'Alert dashboard command failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/v1/alert-dashboard
 * 
 * Same as GET but accepts JSON body
 * 
 * Body:
 * {
 *   "action": "backtest",
 *   "ticker": "AAPL",
 *   "alertType": "rsi",
 *   "years": 3,
 *   "holdDays": 5
 * }
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  
  const params: AlertDashboardParams = {
    action: body.action || 'backtest',
    ticker: body.ticker || '',
    alertType: body.alertType || 'rsi',
    years: body.years || 3,
    holdDays: body.holdDays || 5,
  };

  // Validate required params based on action
  if (params.action === 'backtest' || params.action === 'optimize') {
    if (!params.ticker) {
      return NextResponse.json(
        { error: `Missing required parameter: ticker (for ${params.action} action)` },
        { status: 400 }
      );
    }
  }

  if (params.action === 'backtest' && !params.alertType) {
    return NextResponse.json(
      { error: 'Missing required parameter: alertType (for backtest action)' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');
    
    let command: string;
    
    switch (params.action) {
      case 'backtest':
        command = `python3 ${cliPath} dashboard-backtest ${params.alertType} --ticker ${params.ticker} --years ${params.years} --hold-days ${params.holdDays}`;
        break;
      
      case 'performance':
        command = `python3 ${cliPath} dashboard-performance --years ${params.years}`;
        break;
      
      case 'optimize':
        command = `python3 ${cliPath} dashboard-optimize ${params.ticker} --alert-type ${params.alertType} --years ${params.years}`;
        break;
      
      case 'report':
        const reportFile = `/tmp/alert-report-${Date.now()}.json`;
        command = `python3 ${cliPath} dashboard-report --output ${reportFile}`;
        break;
      
      default:
        return NextResponse.json(
          { error: `Invalid action: ${params.action}. Must be one of: backtest, performance, optimize, report` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execPromise(command, {
      cwd: projectRoot,
      maxBuffer: 20 * 1024 * 1024,
      timeout: 120000,
    });

    if (stderr && !stderr.includes('FutureWarning') && !stderr.includes('Storing cookies') && !stderr.includes('[*********************100%')) {
      console.error('Alert dashboard stderr:', stderr);
    }

    // For report action, try to read the JSON file
    if (params.action === 'report') {
      const reportFile = command.match(/--output\s+(\S+)/)?.[1];
      if (reportFile) {
        try {
          const fs = require('fs');
          const reportData = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
          fs.unlinkSync(reportFile);
          return NextResponse.json({
            success: true,
            data: reportData,
            params,
          });
        } catch (e) {
          console.error('Failed to read report file:', e);
        }
      }
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
    console.error('Alert dashboard error:', error);
    return NextResponse.json(
      { 
        error: 'Alert dashboard command failed',
        details: error.message,
        stderr: error.stderr 
      },
      { status: 500 }
    );
  }
}
