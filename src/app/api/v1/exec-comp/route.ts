import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Executive Compensation Analysis API — Pay-for-Performance, Peer Comparison, Shareholder Alignment
 * 
 * Endpoints:
 * - GET /api/v1/exec-comp?action=breakdown&ticker=AAPL — Executive compensation breakdown (CEO, CFO, top officers)
 * - GET /api/v1/exec-comp?action=pay-performance&ticker=TSLA — Pay-for-performance correlation analysis
 * - GET /api/v1/exec-comp?action=peer-compare&ticker=MSFT — Peer compensation comparison with percentile rankings
 * - GET /api/v1/exec-comp?action=shareholder-alignment&ticker=GOOGL — Shareholder alignment metrics and insider ownership
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "breakdown";
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
      case "breakdown":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/exec_compensation.py exec-comp ${ticker}`;
        break;
      
      case "pay-performance":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/exec_compensation.py pay-performance ${ticker}`;
        break;
      
      case "peer-compare":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/exec_compensation.py comp-peer-compare ${ticker}`;
        break;
      
      case "shareholder-alignment":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/exec_compensation.py shareholder-alignment ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["breakdown", "pay-performance", "peer-compare", "shareholder-alignment"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Executive Compensation Module stderr:", stderr);
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
    console.error("Executive Compensation API Error:", errorMessage);
    
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
