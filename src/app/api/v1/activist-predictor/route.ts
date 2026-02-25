import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Activist Success Predictor API (Phase 67)
 * 
 * GET /api/v1/activist-predictor?action=predict&ticker=AAPL
 * GET /api/v1/activist-predictor?action=history
 * GET /api/v1/activist-predictor?action=targets&sector=Technology&min_cap=1000
 * GET /api/v1/activist-predictor?action=governance-score&ticker=MSFT
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'predict';
  const ticker = searchParams.get('ticker');
  const sector = searchParams.get('sector');
  const minCap = searchParams.get('min_cap') || '1000';

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');

    let command: string;
    
    switch (action) {
      case 'predict':
      case 'activist-predict':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} activist-predict ${ticker.toUpperCase()}`;
        break;
        
      case 'history':
      case 'activist-history':
        command = `python3 ${cliPath} activist-history`;
        break;
        
      case 'targets':
      case 'activist-targets':
        const sectorArg = sector ? `--sector ${sector}` : '';
        command = `python3 ${cliPath} activist-targets ${sectorArg} --min-cap ${minCap}`;
        break;
        
      case 'governance':
      case 'governance-score':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} governance-score ${ticker.toUpperCase()}`;
        break;
        
      default:
        return NextResponse.json(
          { 
            error: `Invalid action: ${action}`,
            valid_actions: ['predict', 'history', 'targets', 'governance-score']
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
      timeout: 90000, // 90 second timeout (ML model may take longer)
    });

    if (stderr) {
      console.error('Activist predictor stderr:', stderr);
    }

    // Parse JSON output
    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('Activist predictor error:', error);
    
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
        error: 'Failed to fetch activist prediction',
        details: error.message,
        action: action
      },
      { status: 500 }
    );
  }
}
