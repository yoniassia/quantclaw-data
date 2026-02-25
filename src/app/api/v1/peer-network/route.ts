import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Peer Network Analysis API — Interconnected Company Relationships, Revenue Dependency Mapping, Systemic Risk
 * 
 * Endpoints:
 * - GET /api/v1/peer-network?action=analyze&ticker=AAPL — Analyze company relationships and systemic risk
 * - GET /api/v1/peer-network?action=compare&tickers=AAPL,MSFT,GOOGL — Compare networks across companies
 * - GET /api/v1/peer-network?action=dependencies&ticker=AAPL&depth=2 — Map revenue dependencies recursively
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "analyze";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const tickers = request.nextUrl.searchParams.get("tickers");
  const depth = request.nextUrl.searchParams.get("depth") || "2";
  
  try {
    let command: string;
    
    switch (action) {
      case "analyze":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_network.py peer-network ${ticker}`;
        break;
      
      case "compare":
        if (!tickers) {
          return NextResponse.json(
            { error: "Missing required parameter: tickers (comma-separated)" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_network.py compare-networks ${tickers}`;
        break;
      
      case "dependencies":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/peer_network.py map-dependencies ${ticker} --depth ${depth}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["analyze", "compare", "dependencies"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Peer Network Module stderr:", stderr);
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
    console.error("Peer Network API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker: ticker || tickers
      },
      { status: 500 }
    );
  }
}
