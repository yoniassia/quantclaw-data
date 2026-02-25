import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Earnings Quality Metrics API — Accruals Ratio, Beneish M-Score, Altman Z-Score
 * 
 * Fraud and distress detection via three proven models:
 * - Accruals Ratio: (Net Income - OCF) / Total Assets (>0.1 = manipulation risk)
 * - Beneish M-Score: 8-variable fraud detection (>-2.22 = likely manipulator)
 * - Altman Z-Score: Bankruptcy prediction (<1.81 = distress, >2.99 = safe)
 * 
 * Endpoints:
 * - GET /api/v1/earnings-quality?action=analyze&ticker=AAPL — Full analysis (all 3 metrics)
 * - GET /api/v1/earnings-quality?action=accruals-trend&ticker=AAPL — Accruals ratio trend over 4 periods
 * - GET /api/v1/earnings-quality?action=fraud-indicators&ticker=AAPL — Quick red flags summary
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
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/earnings_quality.py analyze ${ticker}`;
        break;
      
      case "accruals-trend":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/earnings_quality.py accruals-trend ${ticker}`;
        break;
      
      case "fraud-indicators":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/earnings_quality.py fraud-indicators ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["analyze", "accruals-trend", "fraud-indicators"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Earnings Quality Module stderr:", stderr);
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
    console.error("Earnings Quality API Error:", errorMessage);
    
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
