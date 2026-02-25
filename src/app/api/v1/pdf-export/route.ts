import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';

const execAsync = promisify(exec);

/**
 * PDF Report Exporter API (Phase 79)
 * 
 * GET /api/v1/pdf-export?action=export&ticker=AAPL&modules=all
 * GET /api/v1/pdf-export?action=batch&tickers=AAPL,MSFT,GOOGL&modules=all
 * GET /api/v1/pdf-export?action=templates
 * GET /api/v1/pdf-export?action=download&file=AAPL_report_20260225_015000.pdf
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'export';
  const ticker = searchParams.get('ticker');
  const tickers = searchParams.get('tickers');
  const modules = searchParams.get('modules') || 'all';
  const template = searchParams.get('template') || 'default';
  const file = searchParams.get('file');

  try {
    const projectRoot = path.resolve(process.cwd());
    const cliPath = path.join(projectRoot, 'cli.py');

    let command: string;
    
    switch (action) {
      case 'export':
      case 'export-pdf':
        if (!ticker) {
          return NextResponse.json(
            { error: 'Missing required parameter: ticker' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} export-pdf ${ticker.toUpperCase()} --modules ${modules} --template ${template}`;
        break;
        
      case 'batch':
      case 'batch-report':
        if (!tickers) {
          return NextResponse.json(
            { error: 'Missing required parameter: tickers' },
            { status: 400 }
          );
        }
        command = `python3 ${cliPath} batch-report ${tickers.toUpperCase()} --modules ${modules} --template ${template}`;
        break;
        
      case 'templates':
      case 'report-template':
        command = `python3 ${cliPath} report-template list`;
        break;
        
      case 'download':
        if (!file) {
          return NextResponse.json(
            { error: 'Missing required parameter: file' },
            { status: 400 }
          );
        }
        
        // Security: Only allow files from reports directory
        const reportsDir = path.join(projectRoot, 'data', 'reports');
        const filePath = path.join(reportsDir, path.basename(file)); // Prevent directory traversal
        
        try {
          const fileBuffer = await fs.readFile(filePath);
          return new NextResponse(fileBuffer, {
            headers: {
              'Content-Type': 'application/pdf',
              'Content-Disposition': `attachment; filename="${path.basename(file)}"`,
            },
          });
        } catch (error: any) {
          return NextResponse.json(
            { error: 'File not found', details: error.message },
            { status: 404 }
          );
        }
        
      default:
        return NextResponse.json(
          { 
            error: `Invalid action: ${action}`,
            valid_actions: ['export', 'batch', 'templates', 'download']
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: projectRoot,
      maxBuffer: 10 * 1024 * 1024, // 10MB
      timeout: 120000, // 120 second timeout (PDF generation may take time)
    });

    if (stderr) {
      console.error('PDF exporter stderr:', stderr);
    }

    // Parse JSON output
    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error('PDF exporter error:', error);
    
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
        error: 'Failed to generate PDF report',
        details: error.message,
        action: action
      },
      { status: 500 }
    );
  }
}
