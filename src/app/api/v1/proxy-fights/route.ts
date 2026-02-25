import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Proxy Fight Tracker API — ISS/Glass Lewis recommendations, shareholder voting, proxy contest outcomes
 * 
 * Endpoints:
 * - GET /api/v1/proxy-fights?action=filings&ticker=AAPL&years=3 — Fetch proxy-related filings (DEF 14A, DEFA14A, 8-K)
 * - GET /api/v1/proxy-fights?action=contests&ticker=TSLA — Detect proxy contests (PREC14A, DEFC14A)
 * - GET /api/v1/proxy-fights?action=voting&ticker=GOOGL — Fetch voting results from 8-K Item 5.07
 * - GET /api/v1/proxy-fights?action=advisory&ticker=META — Information on ISS/Glass Lewis data sources
 * - GET /api/v1/proxy-fights?action=summary&ticker=AAPL — Comprehensive proxy fight analysis with risk score
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "summary";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const years = request.nextUrl.searchParams.get("years") || "3";
  
  if (!ticker) {
    return NextResponse.json(
      { error: "Missing required parameter: ticker" },
      { status: 400 }
    );
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "filings":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/proxy_fights.py filings ${ticker} --years ${years}`;
        break;
      
      case "contests":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/proxy_fights.py contests ${ticker}`;
        break;
      
      case "voting":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/proxy_fights.py voting ${ticker}`;
        break;
      
      case "advisory":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/proxy_fights.py advisory ${ticker}`;
        break;
      
      case "summary":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/proxy_fights.py summary ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["filings", "contests", "voting", "advisory", "summary"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Proxy Fight Tracker stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        error: "Failed to parse module output",
        raw: stdout 
      }, { 
        status: 500 
      });
    }
    
  } catch (error: any) {
    console.error("Proxy Fight Tracker error:", error);
    return NextResponse.json({ 
      error: error.message || "Internal server error",
      details: error.stderr || error.stdout
    }, { 
      status: 500 
    });
  }
}
