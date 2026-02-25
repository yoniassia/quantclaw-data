import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Multi-Timeframe Analysis API — Combine signals from daily/weekly/monthly charts
 * 
 * Endpoints:
 * - GET /api/v1/multi-timeframe?action=mtf&ticker=AAPL — Full multi-timeframe analysis
 * - GET /api/v1/multi-timeframe?action=trend-alignment&ticker=AAPL — Check trend alignment
 * - GET /api/v1/multi-timeframe?action=signal-confluence&ticker=AAPL — Signal confluence scoring
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "mtf";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  
  try {
    // Validate ticker
    if (!ticker) {
      return NextResponse.json(
        { error: "ticker parameter required" },
        { status: 400 }
      );
    }
    
    let command: string;
    
    switch (action) {
      case "mtf":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/multi_timeframe.py mtf ${ticker}`;
        break;
      
      case "trend-alignment":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/multi_timeframe.py trend-alignment ${ticker}`;
        break;
      
      case "signal-confluence":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/multi_timeframe.py signal-confluence ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["mtf", "trend-alignment", "signal-confluence"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000,  // 45s timeout for fetching multiple timeframes
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Multi-Timeframe Module stderr:", stderr);
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
    console.error("Multi-Timeframe API Error:", errorMessage);
    
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
