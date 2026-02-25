import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * CDS Spreads API — Sovereign and Corporate Credit Risk Signals
 * 
 * Endpoints:
 * - GET /api/v1/cds?action=credit-spreads — Overall credit market dashboard
 * - GET /api/v1/cds?action=entity&ticker=AAPL — Corporate CDS spreads
 * - GET /api/v1/cds?action=sovereign&country=Italy — Sovereign risk analysis
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "credit-spreads";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const country = request.nextUrl.searchParams.get("country") || "";
  
  try {
    let command: string;
    
    switch (action) {
      case "credit-spreads":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/cds_spreads.py credit-spreads`;
        break;
      
      case "entity":
        if (!ticker) {
          return NextResponse.json(
            { error: "ticker parameter required for entity action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/cds_spreads.py cds ${ticker}`;
        break;
      
      case "sovereign":
        if (!country) {
          return NextResponse.json(
            { error: "country parameter required for sovereign action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/cds_spreads.py sovereign-risk ${country}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["credit-spreads", "entity", "sovereign"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("CDS Module stderr:", stderr);
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
    console.error("CDS API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        country
      },
      { status: 500 }
    );
  }
}
