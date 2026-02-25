import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * ML Factor Discovery API — Automated discovery of new predictive factors with feature engineering
 * 
 * Endpoints:
 * - POST /api/v1/ml-factor-discovery?action=discover — Auto-discover predictive factors (price, volume, fundamentals)
 *   Body: { tickers: string[], lookback?: number }
 * - GET /api/v1/ml-factor-discovery?action=ic — Information Coefficient rankings for all factors
 *   Query: ?action=ic&horizon=5d&topN=20
 * - GET /api/v1/ml-factor-discovery?action=backtest — Walk-forward backtest of specific factor
 *   Query: ?action=backtest&factor=momentum_3m&horizon=5d
 * - GET /api/v1/ml-factor-discovery?action=importance — ML ensemble feature importance (RF, GBM, Lasso)
 *   Query: ?action=importance&horizon=5d&topN=20
 */

export async function POST(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "discover";
  
  if (action !== "discover") {
    return NextResponse.json(
      { error: "POST only supports action=discover" },
      { status: 400 }
    );
  }
  
  try {
    const body = await request.json();
    const tickers = body.tickers;
    const lookback = body.lookback || 504;
    
    if (!tickers || !Array.isArray(tickers) || tickers.length === 0) {
      return NextResponse.json(
        { error: "tickers array is required" },
        { status: 400 }
      );
    }
    
    const tickerList = tickers.join(",");
    const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py discover-factors ${tickerList} --lookback ${lookback}`;
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 120000, // 2 minutes
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr && !stderr.includes("Warning:")) {
      console.error("ML Factor Discovery stderr:", stderr);
    }
    
    return NextResponse.json({ 
      result: "Factor discovery complete",
      output: stdout.trim(),
      tickers: tickers,
      lookback: lookback
    });
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("ML Factor Discovery API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "ic";
  const horizon = request.nextUrl.searchParams.get("horizon") || "5d";
  const topN = request.nextUrl.searchParams.get("topN") || "20";
  const factor = request.nextUrl.searchParams.get("factor");
  
  try {
    let command: string;
    
    switch (action) {
      case "ic":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py factor-ic --top-n ${topN}`;
        break;
      
      case "backtest":
        if (!factor) {
          return NextResponse.json(
            { error: "factor parameter is required for backtest action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py factor-backtest ${factor} --horizon ${horizon}`;
        break;
      
      case "importance":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py feature-importance --horizon ${horizon} --top-n ${topN}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["ic", "backtest", "importance"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000,
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr && !stderr.includes("Warning:")) {
      console.error("ML Factor Discovery stderr:", stderr);
    }
    
    // Try to parse output as JSON, otherwise return as text
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        result: stdout.trim(),
        action,
        horizon,
        factor
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("ML Factor Discovery API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
