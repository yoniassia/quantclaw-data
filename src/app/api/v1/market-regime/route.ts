import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Market Regime Detection API — Volatility Clustering, Correlation Breakdowns, Risk-On vs Risk-Off
 * 
 * Endpoints:
 * - GET /api/v1/market-regime?action=current — Current market regime classification (risk-on/off/transition/crisis)
 * - GET /api/v1/market-regime?action=history — Regime timeline over last 60 days
 * - GET /api/v1/market-regime?action=dashboard — Comprehensive risk-on/off dashboard with volatility & correlations
 * - GET /api/v1/market-regime?action=correlation — Cross-asset correlation state and breakdown detection
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "current";
  const lookback = request.nextUrl.searchParams.get("lookback") || "252";
  
  try {
    let command: string;
    
    switch (action) {
      case "current":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/market_regime.py market-regime --lookback ${lookback}`;
        break;
      
      case "history":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/market_regime.py regime-history --lookback ${lookback}`;
        break;
      
      case "dashboard":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/market_regime.py risk-dashboard --lookback ${lookback}`;
        break;
      
      case "correlation":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/market_regime.py correlation-regime --lookback ${lookback}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["current", "history", "dashboard", "correlation"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Market Regime Module stderr:", stderr);
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
    console.error("Market Regime API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
