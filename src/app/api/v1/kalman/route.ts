import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Kalman Filter Trends API — Adaptive Moving Averages & Regime Detection
 * 
 * Endpoints:
 * - GET /api/v1/kalman?action=kalman&ticker=AAPL&period=6mo — Extract smooth price trend
 * - GET /api/v1/kalman?action=adaptive-ma&ticker=AAPL&period=6mo — Adaptive MA signals
 * - GET /api/v1/kalman?action=regime-detect&ticker=AAPL&period=6mo&window=20 — Regime changes
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "kalman";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const period = request.nextUrl.searchParams.get("period") || "6mo";
  const window = request.nextUrl.searchParams.get("window") || "20";
  
  try {
    let command: string;
    
    // Validate ticker for all actions
    if (!ticker) {
      return NextResponse.json(
        { error: "ticker parameter required" },
        { status: 400 }
      );
    }
    
    switch (action) {
      case "kalman":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/kalman_filter.py kalman ${ticker} --period ${period}`;
        break;
      
      case "adaptive-ma":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/kalman_filter.py adaptive-ma ${ticker} --period ${period}`;
        break;
      
      case "regime-detect":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/kalman_filter.py regime-detect ${ticker} --period ${period} --window ${window}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["kalman", "adaptive-ma", "regime-detect"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Kalman Filter Module stderr:", stderr);
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
    console.error("Kalman Filter API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        period,
        window
      },
      { status: 500 }
    );
  }
}
