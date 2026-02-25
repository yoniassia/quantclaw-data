import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Dark Pool Tracker API — FINRA ADF Block Trade Detection & Institutional Accumulation
 * 
 * Endpoints:
 * - GET /api/v1/dark-pool?action=volume&ticker=AAPL — Dark pool volume estimate (OTC vs lit exchange)
 * - GET /api/v1/dark-pool?action=block-trades&ticker=TSLA — Detect large block trades
 * - GET /api/v1/dark-pool?action=accumulation&ticker=NVDA&period=30 — Institutional accumulation/distribution pattern
 * - GET /api/v1/dark-pool?action=off-exchange-ratio&ticker=SPY&period=20 — Off-exchange vs lit ratio trend
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "volume";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const period = request.nextUrl.searchParams.get("period") || "30";
  
  if (!ticker) {
    return NextResponse.json(
      { error: "Missing required parameter: ticker" },
      { status: 400 }
    );
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "volume":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/dark_pool.py dark-pool-volume ${ticker}`;
        break;
      
      case "block-trades":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/dark_pool.py block-trades ${ticker}`;
        break;
      
      case "accumulation":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/dark_pool.py institutional-accumulation ${ticker} --period ${period}`;
        break;
      
      case "off-exchange-ratio":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/dark_pool.py off-exchange-ratio ${ticker} --period ${period}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["volume", "block-trades", "accumulation", "off-exchange-ratio"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Dark Pool Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      // If output is not JSON, return as text
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Dark Pool API Error:", errorMessage);
    
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
