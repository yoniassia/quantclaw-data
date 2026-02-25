import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Executive Compensation API — Pay-for-Performance & Shareholder Alignment
 * 
 * Analyzes executive compensation from SEC DEF 14A proxy filings
 * 
 * Endpoints:
 * - GET /api/v1/executive-comp?action=comp-data&ticker=AAPL — Get CEO & NEO compensation breakdown
 * - GET /api/v1/executive-comp?action=pay-performance&ticker=AAPL&years=3 — Pay-for-performance correlation
 * - GET /api/v1/executive-comp?action=peer-compare&ticker=AAPL — Compare vs peer group compensation
 * - GET /api/v1/executive-comp?action=insider-ownership&ticker=AAPL — Insider ownership & alignment metrics
 * 
 * Data Sources:
 * - SEC EDGAR DEF 14A proxy statements
 * - Yahoo Finance for stock performance (TSR)
 * - Form 4 insider ownership data
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "comp-data";
  const ticker = request.nextUrl.searchParams.get("ticker") || "AAPL";
  const years = request.nextUrl.searchParams.get("years") || "3";
  
  try {
    let command: string;
    
    switch (action) {
      case "comp-data":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/executive_comp.py comp-data ${ticker}`;
        break;
      
      case "pay-performance":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/executive_comp.py pay-performance ${ticker} ${years}`;
        break;
      
      case "peer-compare":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/executive_comp.py peer-compare ${ticker}`;
        break;
      
      case "insider-ownership":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/executive_comp.py insider-ownership ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["comp-data", "pay-performance", "peer-compare", "insider-ownership"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Executive Comp Module stderr:", stderr);
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
    console.error("Executive Comp API Error:", errorMessage);
    
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
