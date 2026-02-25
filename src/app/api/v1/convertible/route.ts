import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Convertible Bond Arbitrage API (Phase 64)
 * 
 * GET /api/v1/convertible?action=scan
 * GET /api/v1/convertible?action=premium&ticker=TSLA
 * GET /api/v1/convertible?action=arb&ticker=MSTR
 * GET /api/v1/convertible?action=greeks&ticker=COIN
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'scan';
  const ticker = searchParams.get('ticker');

  // Validate ticker requirement for non-scan actions
  if (action !== 'scan' && !ticker) {
    return NextResponse.json(
      { error: 'Missing required parameter: ticker' },
      { status: 400 }
    );
  }

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');

    let command: string;
    switch (action) {
      case 'scan':
        command = `python3 ${cliPath} convertible-scan`;
        break;
      case 'premium':
        command = `python3 ${cliPath} conversion-premium ${ticker}`;
        break;
      case 'arb':
        command = `python3 ${cliPath} convertible-arb ${ticker}`;
        break;
      case 'greeks':
        command = `python3 ${cliPath} convertible-greeks ${ticker}`;
        break;
      default:
        return NextResponse.json(
          { error: `Invalid action: ${action}. Valid actions: scan, premium, arb, greeks` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });

    if (stderr && !stderr.includes('Generating')) {
      console.error('Convertible bond analysis stderr:', stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Convertible bond analysis error:', error);
    
    // Try to parse JSON from stdout even if there was an error
    if (error.stdout) {
      try {
        const result = JSON.parse(error.stdout);
        return NextResponse.json(result);
      } catch {
        // Fall through to error response
      }
    }

    return NextResponse.json(
      {
        error: 'Failed to fetch convertible bond analysis',
        details: error.message,
        stderr: error.stderr
      },
      { status: 500 }
    );
  }
}
