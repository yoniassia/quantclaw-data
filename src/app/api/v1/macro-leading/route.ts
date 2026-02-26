import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
export const dynamic = 'force-dynamic';

const QUANTCLAW_DATA_DIR = '/home/quant/apps/quantclaw-data';
const PYTHON = 'python3';

/**
 * Macro Leading Index API — Composite Leading Indicator
 * 
 * Pulls key economic indicators from FRED and combines them into a composite
 * leading index for recession prediction and economic cycle analysis.
 * 
 * Indicators:
 * - Yield curve (T10Y2Y): 10Y-2Y Treasury spread
 * - Initial claims (ICSA): Weekly unemployment insurance claims
 * - PMI: ISM Manufacturing PMI
 * - Consumer sentiment (UMCSENT): University of Michigan Consumer Sentiment
 * - Building permits (PERMIT): New Private Housing Units Authorized
 * 
 * Endpoints:
 * - GET /api/v1/macro-leading?action=index
 * - GET /api/v1/macro-leading?action=recession
 * - GET /api/v1/macro-leading?action=components
 * 
 * Query Parameters:
 * - action: 'index', 'recession', or 'components' (default: 'index')
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action') || 'index';
  
  try {
    let command: string;
    
    switch (action) {
      case 'index':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.macro_leading_index; import json; result = modules.macro_leading_index.get_leading_index(); print(json.dumps(result))"`;
        break;
      
      case 'recession':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.macro_leading_index; import json; result = modules.macro_leading_index.recession_probability(); print(json.dumps(result))"`;
        break;
      
      case 'components':
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} -c "import modules.macro_leading_index; import json; result = modules.macro_leading_index.get_component_data(); print(json.dumps(result))"`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ['index', 'recession', 'components']
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000,  // 60 seconds
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Macro Leading Index Module stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: 'Response was not valid JSON'
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error('Macro Leading Index API Error:', errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        suggestion: 'Make sure pandas, numpy, requests are installed'
      },
      { status: 500 }
    );
  }
}
