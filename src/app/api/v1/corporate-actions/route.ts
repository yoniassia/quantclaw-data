import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Corporate Action Calendar API — Dividend Ex-Dates, Stock Splits, Spin-offs, Rights Offerings
 * 
 * Endpoints:
 * - GET /api/v1/corporate-actions?action=calendar&ticker=AAPL — Get upcoming corporate actions for ticker
 * - GET /api/v1/corporate-actions?action=splits&ticker=TSLA — Get stock split history with impact analysis
 * - GET /api/v1/corporate-actions?action=dividends&tickers=AAPL,MSFT,JNJ — Get dividend calendar for watchlist
 * - GET /api/v1/corporate-actions?action=spinoffs — Track recent and upcoming spin-offs
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "calendar";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const tickers = request.nextUrl.searchParams.get("tickers");
  
  try {
    let command: string;
    
    switch (action) {
      case "calendar":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        // Call Python module and parse output
        command = `${PYTHON} -c "import sys; sys.path.insert(0, '${QUANTCLAW_DATA_DIR}/modules'); from corporate_actions import get_upcoming_dividends, get_split_history; import json; div = get_upcoming_dividends('${ticker}'); splits = get_split_history('${ticker}', 5); print(json.dumps({'dividends': div, 'splits': splits}))"`;
        break;
      
      case "splits":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} -c "import sys; sys.path.insert(0, '${QUANTCLAW_DATA_DIR}/modules'); from corporate_actions import get_split_history; import json; result = get_split_history('${ticker}', 20); print(json.dumps(result))"`;
        break;
      
      case "dividends":
        const tickerList = tickers || ticker;
        if (!tickerList) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker or tickers" },
            { status: 400 }
          );
        }
        const tickerArray = tickerList.split(',').map((t: string) => t.trim());
        const tickersJson = JSON.stringify(tickerArray);
        command = `${PYTHON} -c "import sys; sys.path.insert(0, '${QUANTCLAW_DATA_DIR}/modules'); from corporate_actions import get_dividend_calendar; import json; result = get_dividend_calendar(${tickersJson}); print(json.dumps(result))"`;
        break;
      
      case "spinoffs":
        command = `${PYTHON} -c "import sys; sys.path.insert(0, '${QUANTCLAW_DATA_DIR}/modules'); from corporate_actions import get_spinoff_tracker; import json; result = get_spinoff_tracker(); print(json.dumps(result))"`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["calendar", "splits", "dividends", "spinoffs"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Corporate Actions Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      console.error("JSON parse error:", parseError);
      console.error("stdout:", stdout);
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON",
        parseError: parseError instanceof Error ? parseError.message : String(parseError)
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Corporate Actions API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        tickers
      },
      { status: 500 }
    );
  }
}
