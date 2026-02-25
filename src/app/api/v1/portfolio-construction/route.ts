import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Portfolio Construction API (Phase 81)
 * MPT optimizer, Black-Litterman, ESG constraints, tax-aware rebalancing
 * 
 * Endpoints:
 * - GET /api/v1/portfolio-construction?action=mpt-optimize&tickers=AAPL,MSFT,GOOGL&target_return=0.15&esg_min=60
 * - GET /api/v1/portfolio-construction?action=efficient-frontier&tickers=AAPL,TSLA,NVDA&esg_min=60
 * - GET /api/v1/portfolio-construction?action=rebalance-plan
 * - GET /api/v1/portfolio-construction?action=portfolio-risk&tickers=AAPL,MSFT,GOOGL&weights=0.33,0.33,0.34
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get("action") || "mpt-optimize";
  const tickers = searchParams.get("tickers") || "";
  const targetReturn = searchParams.get("target_return");
  const esgMin = searchParams.get("esg_min");
  const weights = searchParams.get("weights");

  try {
    let command = "";

    switch (action) {
      case "mpt-optimize":
        if (!tickers) {
          return NextResponse.json(
            { error: "Missing required parameter: tickers (comma-separated list)" },
            { status: 400 }
          );
        }
        command = `python3 modules/portfolio_construction.py mpt-optimize ${tickers}`;
        if (targetReturn) command += ` --target-return ${targetReturn}`;
        if (esgMin) command += ` --esg-min ${esgMin}`;
        break;

      case "efficient-frontier":
        if (!tickers) {
          return NextResponse.json(
            { error: "Missing required parameter: tickers (comma-separated list)" },
            { status: 400 }
          );
        }
        command = `python3 modules/portfolio_construction.py efficient-frontier ${tickers}`;
        if (esgMin) command += ` --esg-min ${esgMin}`;
        break;

      case "rebalance-plan":
        command = `python3 modules/portfolio_construction.py rebalance-plan`;
        break;

      case "portfolio-risk":
        if (!tickers) {
          return NextResponse.json(
            { error: "Missing required parameter: tickers (comma-separated list)" },
            { status: 400 }
          );
        }
        command = `python3 modules/portfolio_construction.py portfolio-risk ${tickers}`;
        if (weights) command += ` --weights ${weights}`;
        break;

      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}. Valid actions: mpt-optimize, efficient-frontier, rebalance-plan, portfolio-risk` 
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 60000, // 60s timeout for optimization
    });

    if (stderr && !stderr.includes("Warning") && !stderr.includes("FutureWarning")) {
      console.error("Portfolio Construction stderr:", stderr);
    }

    // Return formatted output
    const result = {
      raw_output: stdout,
      timestamp: new Date().toISOString()
    };

    return NextResponse.json({
      success: true,
      action,
      data: result,
      params: {
        tickers: tickers || undefined,
        target_return: targetReturn || undefined,
        esg_min: esgMin || undefined,
        weights: weights || undefined
      }
    });
  } catch (error: any) {
    console.error("Portfolio Construction API error:", error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || "Failed to execute portfolio construction",
        action,
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  return NextResponse.json(
    { error: "POST not supported. Use GET with query parameters." },
    { status: 405 }
  );
}
