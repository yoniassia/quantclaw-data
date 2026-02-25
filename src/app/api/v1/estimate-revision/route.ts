import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Estimate Revision Tracker API — Analyst Upgrades/Downgrades Velocity, Estimate Momentum Indicators
 * 
 * Endpoints:
 * - GET /api/v1/estimate-revision?action=recommendations&ticker=AAPL — Get analyst recommendation distribution and momentum
 * - GET /api/v1/estimate-revision?action=revisions&ticker=TSLA — Track EPS estimate revisions and dispersion
 * - GET /api/v1/estimate-revision?action=velocity&ticker=MSFT — Calculate revision velocity and trend
 * - GET /api/v1/estimate-revision?action=targets&ticker=NVDA — Analyze price target changes and upside
 * - GET /api/v1/estimate-revision?action=summary&ticker=GOOGL — Comprehensive momentum report with composite score
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "summary";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const lookback = request.nextUrl.searchParams.get("lookback") || "3";
  
  if (!ticker) {
    return NextResponse.json(
      { error: "Missing required parameter: ticker" },
      { status: 400 }
    );
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "recommendations":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/estimate_revision_tracker.py recommendations ${ticker}`;
        break;
      
      case "revisions":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/estimate_revision_tracker.py revisions ${ticker}`;
        break;
      
      case "velocity":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/estimate_revision_tracker.py velocity ${ticker} --lookback ${lookback}`;
        break;
      
      case "targets":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/estimate_revision_tracker.py targets ${ticker}`;
        break;
      
      case "summary":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/estimate_revision_tracker.py summary ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["recommendations", "revisions", "velocity", "targets", "summary"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Estimate Revision Tracker stderr:", stderr);
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
    console.error("Estimate Revision Tracker API Error:", errorMessage);
    
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
