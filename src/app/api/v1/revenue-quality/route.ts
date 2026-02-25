import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Revenue Quality Analysis API — Cash Flow vs Earnings Divergence, DSO Trends, Channel Stuffing Detection
 * 
 * Endpoints:
 * - GET /api/v1/revenue-quality?action=analyze&ticker=AAPL — Comprehensive revenue quality analysis
 * - GET /api/v1/revenue-quality?action=dso-trends&ticker=AAPL — DSO trend analysis with visualization data
 * - GET /api/v1/revenue-quality?action=channel-stuffing&ticker=AAPL — Detect channel stuffing red flags
 * - GET /api/v1/revenue-quality?action=cash-flow-divergence&ticker=AAPL — CFO vs net income divergence
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "analyze";
  const ticker = request.nextUrl.searchParams.get("ticker");
  
  if (!ticker) {
    return NextResponse.json(
      { error: "Missing required parameter: ticker" },
      { status: 400 }
    );
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "analyze":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/revenue_quality.py analyze ${ticker}`;
        break;
      
      case "dso-trends":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/revenue_quality.py dso-trends ${ticker}`;
        break;
      
      case "channel-stuffing":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/revenue_quality.py channel-stuffing ${ticker}`;
        break;
      
      case "cash-flow-divergence":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/revenue_quality.py cash-flow-divergence ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["analyze", "dso-trends", "channel-stuffing", "cash-flow-divergence"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Revenue Quality Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Revenue Quality API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker
      },
      { status: 500 }
    );
  }
}
