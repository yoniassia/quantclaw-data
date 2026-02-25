import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Climate Risk Scoring API (Phase 72)
 * Endpoints:
 * - GET /api/v1/climate-risk?action=climate-risk&ticker=AAPL
 * - GET /api/v1/climate-risk?action=physical-risk&ticker=XOM
 * - GET /api/v1/climate-risk?action=transition-risk&ticker=BP
 * - GET /api/v1/climate-risk?action=carbon-scenario&ticker=TSLA
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get("action") || "climate-risk";
  const ticker = searchParams.get("ticker");

  if (!ticker) {
    return NextResponse.json(
      { error: "ticker parameter is required" },
      { status: 400 }
    );
  }

  try {
    let command = "";

    switch (action) {
      case "climate-risk":
        command = `python3 modules/climate_risk.py climate-risk ${ticker}`;
        break;

      case "physical-risk":
        command = `python3 modules/climate_risk.py physical-risk ${ticker}`;
        break;

      case "transition-risk":
        command = `python3 modules/climate_risk.py transition-risk ${ticker}`;
        break;

      case "carbon-scenario":
        command = `python3 modules/climate_risk.py carbon-scenario ${ticker}`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}. Valid actions: climate-risk, physical-risk, transition-risk, carbon-scenario` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 30000, // 30s timeout
    });

    if (stderr && !stderr.includes("Warning")) {
      console.error("Climate Risk stderr:", stderr);
    }

    const result = JSON.parse(stdout);

    return NextResponse.json({
      success: true,
      action,
      ticker: ticker.toUpperCase(),
      data: result,
    });
  } catch (error: any) {
    console.error("Climate Risk API error:", error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || "Failed to execute climate risk analysis",
        action,
        ticker: ticker?.toUpperCase(),
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
