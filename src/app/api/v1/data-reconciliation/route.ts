import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Multi-Source Data Reconciliation API — Compare data across sources, confidence-based voting
 * 
 * Endpoints:
 * - GET /api/v1/data-reconciliation?action=reconcile-price&symbol=AAPL — Compare price across Yahoo/CoinGecko/FRED
 * - GET /api/v1/data-reconciliation?action=reconcile-price&symbol=BTC&type=crypto — Reconcile crypto prices
 * - GET /api/v1/data-reconciliation?action=data-quality-report — Overall data quality metrics
 * - GET /api/v1/data-reconciliation?action=source-reliability — Source reliability rankings
 * - GET /api/v1/data-reconciliation?action=discrepancy-log&hours=24 — Recent discrepancies
 * - GET /api/v1/data-reconciliation?action=discrepancy-log&symbol=AAPL&hours=48 — Filter by symbol
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "reconcile-price";
  const symbol = request.nextUrl.searchParams.get("symbol");
  const assetType = request.nextUrl.searchParams.get("type") || "auto";
  const hours = request.nextUrl.searchParams.get("hours") || "24";
  
  try {
    let command: string;
    
    switch (action) {
      case "reconcile-price":
        if (!symbol) {
          return NextResponse.json(
            { error: "Missing required parameter: symbol" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/data_reconciliation.py reconcile-price ${symbol} --type ${assetType}`;
        break;
      
      case "data-quality-report":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/data_reconciliation.py data-quality-report`;
        break;
      
      case "source-reliability":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/data_reconciliation.py source-reliability`;
        break;
      
      case "discrepancy-log":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/data_reconciliation.py discrepancy-log --hours ${hours}`;
        if (symbol) {
          command += ` --symbol ${symbol}`;
        }
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["reconcile-price", "data-quality-report", "source-reliability", "discrepancy-log"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Data Reconciliation Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      // Return raw output if not JSON
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Data Reconciliation API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        symbol: symbol || undefined
      },
      { status: 500 }
    );
  }
}
