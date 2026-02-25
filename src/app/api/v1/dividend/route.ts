import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Dividend Sustainability Analysis API (Phase 57)
 * 
 * GET /api/v1/dividend?action=health&ticker=AAPL
 * GET /api/v1/dividend?action=payout&ticker=JNJ
 * GET /api/v1/dividend?action=fcf&ticker=KO
 * GET /api/v1/dividend?action=risk&ticker=T
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'health';
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
      case 'health':
        command = `python3 ${cliPath} dividend-health ${ticker}`;
        break;
      case 'payout':
        command = `python3 ${cliPath} payout-ratio ${ticker}`;
        break;
      case 'fcf':
        command = `python3 ${cliPath} fcf-coverage ${ticker}`;
        break;
      case 'risk':
        command = `python3 ${cliPath} dividend-cut-risk ${ticker}`;
        break;
      default:
        return NextResponse.json(
          { error: `Invalid action: ${action}. Valid actions: health, payout, fcf, risk` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
    });

    if (stderr && !stderr.includes('Generating')) {
      console.error('Dividend analysis stderr:', stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Dividend analysis error:', error);
    
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
        error: 'Failed to fetch dividend sustainability analysis',
        details: error.message,
        stderr: error.stderr,
      },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';
