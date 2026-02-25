import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Volatility Surface Modeling API — IV smile/skew analysis, volatility arbitrage, straddle/strangle scanner
 * 
 * Endpoints:
 * - GET /api/v1/volatility-surface?action=smile&ticker=AAPL&expiry=2026-03-21 — IV smile/skew analysis
 * - GET /api/v1/volatility-surface?action=arbitrage&ticker=TSLA — Volatility arbitrage opportunities
 * - GET /api/v1/volatility-surface?action=straddle&ticker=NVDA&max_days=60 — Straddle/strangle scanner
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "smile";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const expiry = request.nextUrl.searchParams.get("expiry") || "";
  const maxDays = request.nextUrl.searchParams.get("max_days") || "60";
  
  try {
    if (!ticker) {
      return NextResponse.json(
        { error: "ticker parameter required" },
        { status: 400 }
      );
    }
    
    let command: string;
    
    switch (action) {
      case "smile":
      case "skew":
        const expiryParam = expiry ? `--expiry ${expiry}` : "";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/volatility_surface.py iv-smile ${ticker} ${expiryParam} --json`;
        break;
      
      case "arbitrage":
      case "vol-arb":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/volatility_surface.py vol-arbitrage ${ticker} --json`;
        break;
      
      case "straddle":
      case "strangle":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/volatility_surface.py straddle-scan ${ticker} --max-days ${maxDays} --json`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["smile", "skew", "arbitrage", "vol-arb", "straddle", "strangle"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000, // 45 seconds for options data fetching
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Volatility Surface Module stderr:", stderr);
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
    console.error("Volatility Surface API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        expiry,
        max_days: maxDays
      },
      { status: 500 }
    );
  }
}
