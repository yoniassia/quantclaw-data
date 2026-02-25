import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Fed Policy Prediction API — FOMC Analysis & Rate Hike Probability Scoring
 * 
 * Endpoints:
 * - GET /api/v1/fed-policy?action=fed-watch — Comprehensive Fed policy analysis
 * - GET /api/v1/fed-policy?action=rate-probability — Calculate rate hike/cut probabilities
 * - GET /api/v1/fed-policy?action=fomc-calendar — Show upcoming FOMC meeting dates
 * - GET /api/v1/fed-policy?action=dot-plot — Dot plot consensus analysis
 * - GET /api/v1/fed-policy?action=yield-curve — Treasury yield curve analysis
 * - GET /api/v1/fed-policy?action=current-rate — Current fed funds rate & target range
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "fed-watch";
  
  try {
    let command: string;
    
    switch (action) {
      case "fed-watch":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py fed-watch`;
        break;
      
      case "rate-probability":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py rate-probability`;
        break;
      
      case "fomc-calendar":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py fomc-calendar`;
        break;
      
      case "dot-plot":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py dot-plot`;
        break;
      
      case "yield-curve":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py yield-curve`;
        break;
      
      case "current-rate":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/fed_policy.py current-rate`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["fed-watch", "rate-probability", "fomc-calendar", "dot-plot", "yield-curve", "current-rate"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Fed Policy Module stderr:", stderr);
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
    console.error("Fed Policy API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
