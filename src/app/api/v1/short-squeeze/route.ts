import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Short Squeeze Detector API (Phase 65)
 * 
 * GET /api/v1/short-squeeze?action=score&ticker=GME
 * GET /api/v1/short-squeeze?action=scan&limit=10&min_score=50
 * GET /api/v1/short-squeeze?action=short-interest&ticker=TSLA
 * GET /api/v1/short-squeeze?action=days-to-cover&ticker=AMC
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'score';
  const ticker = searchParams.get('ticker');
  const tickers = searchParams.get('tickers');
  const limit = searchParams.get('limit') || '20';
  const minScore = searchParams.get('min_score') || '35';

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');

    let command: string;
    
    switch (action) {
      case 'score':
      case 'squeeze-score':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} squeeze-score ${ticker} --json`;
        break;
        
      case 'scan':
      case 'squeeze-scan':
        const tickerList = tickers || '';
        const tickerArg = tickerList ? `--tickers ${tickerList}` : '';
        command = `python3 ${cliPath} squeeze-scan ${tickerArg} --min-score ${minScore} --limit ${limit} --json`;
        break;
        
      case 'short-interest':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} short-interest ${ticker} --json`;
        break;
        
      case 'days-to-cover':
      case 'dtc':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} days-to-cover ${ticker} --json`;
        break;
        
      default:
        return NextResponse.json(
          { 
            error: `Invalid action: ${action}`,
            valid_actions: ['score', 'scan', 'short-interest', 'days-to-cover']
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
      timeout: 60000, // 60 second timeout
    });

    if (stderr && !stderr.includes('possibly delisted')) {
      console.error('Short squeeze analysis stderr:', stderr);
    }

    // Parse JSON output
    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Short squeeze analysis error:', error);
    
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
        error: 'Failed to fetch short squeeze analysis',
        details: error.message,
        action: action
      },
      { status: 500 }
    );
  }
}
