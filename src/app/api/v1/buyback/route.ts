import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Share Buyback Analysis API (Phase 56)
 * 
 * GET /api/v1/buyback?action=full&ticker=AAPL
 * GET /api/v1/buyback?action=shares&ticker=MSFT
 * GET /api/v1/buyback?action=yield&ticker=GOOGL
 * GET /api/v1/buyback?action=dilution&ticker=META
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'full';
  const ticker = searchParams.get('ticker');

  if (!ticker) {
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
      case 'full':
        command = `python3 ${cliPath} buyback-analysis ${ticker}`;
        break;
      case 'shares':
        command = `python3 ${cliPath} share-count-trend ${ticker}`;
        break;
      case 'yield':
        command = `python3 ${cliPath} buyback-yield ${ticker}`;
        break;
      case 'dilution':
        command = `python3 ${cliPath} dilution-impact ${ticker}`;
        break;
      default:
        return NextResponse.json(
          { error: `Invalid action: ${action}. Valid actions: full, shares, yield, dilution` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });

    if (stderr && !stderr.includes('Generating')) {
      console.error('Buyback analysis stderr:', stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Buyback analysis error:', error);
    
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
        error: 'Failed to fetch buyback analysis',
        details: error.message,
        stderr: error.stderr,
      },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';
