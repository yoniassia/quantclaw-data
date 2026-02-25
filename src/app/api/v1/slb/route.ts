import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Sustainability-Linked Bonds (SLB) API — Monitor KPI Achievement & Coupon Step-Up Triggers
 * 
 * Endpoints:
 * - GET /api/v1/slb?action=market — Overall SLB market dashboard
 * - GET /api/v1/slb?action=issuer&ticker=ENEL — Issuer SLB portfolio analysis
 * - GET /api/v1/slb?action=kpi-tracker — Upcoming KPI measurement dates
 * - GET /api/v1/slb?action=coupon-forecast — Forecast potential coupon step-ups
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "market";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  
  try {
    let command: string;
    
    switch (action) {
      case "market":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/slb.py slb-market`;
        break;
      
      case "issuer":
        if (!ticker) {
          return NextResponse.json(
            { error: "ticker parameter required for issuer action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/slb.py slb-issuer ${ticker}`;
        break;
      
      case "kpi-tracker":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/slb.py slb-kpi-tracker`;
        break;
      
      case "coupon-forecast":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/slb.py slb-coupon-forecast`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["market", "issuer", "kpi-tracker", "coupon-forecast"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("SLB Module stderr:", stderr);
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
    console.error("SLB API Error:", errorMessage);
    
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
