import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Peer Earnings Comparison API — Beat/Miss Patterns, Guidance Trends, Analyst Estimate Dispersion
 * 
 * Endpoints:
 * - GET /api/v1/peer-earnings?action=compare&ticker=AAPL — Compare earnings patterns across sector peers
 * - GET /api/v1/peer-earnings?action=beat-miss&ticker=TSLA — Detailed beat/miss pattern analysis
 * - GET /api/v1/peer-earnings?action=guidance&ticker=MSFT — Track management guidance and analyst trends
 * - GET /api/v1/peer-earnings?action=dispersion&ticker=NVDA — Analyze analyst estimate spread and uncertainty
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "compare";
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
      case "compare":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_earnings.py peer-earnings ${ticker}`;
        break;
      
      case "beat-miss":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_earnings.py beat-miss-history ${ticker}`;
        break;
      
      case "guidance":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_earnings.py guidance-tracker ${ticker}`;
        break;
      
      case "dispersion":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_earnings.py estimate-dispersion ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["compare", "beat-miss", "guidance", "dispersion"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Peer Earnings Module stderr:", stderr);
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
    console.error("Peer Earnings API Error:", errorMessage);
    
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
