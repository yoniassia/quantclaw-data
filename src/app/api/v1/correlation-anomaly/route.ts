import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Correlation Anomaly Detector API — Phase 87
 * Identify unusual correlation breakdowns, detect regime shifts, flag arbitrage
 * 
 * Endpoints:
 * - GET /api/v1/correlation-anomaly?action=breakdown&ticker1=AAPL&ticker2=MSFT — Correlation breakdown between two assets
 * - GET /api/v1/correlation-anomaly?action=scan&tickers=SPY,TLT,GLD — Scan correlation matrix for anomalies
 * - GET /api/v1/correlation-anomaly?action=regime&tickers=SPY,TLT,GLD,DBC — Market regime shift detection via correlation structure
 * - GET /api/v1/correlation-anomaly?action=arbitrage&tickers=XLF,XLK,XLE — Statistical arbitrage opportunities
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "scan";
  const ticker1 = request.nextUrl.searchParams.get("ticker1");
  const ticker2 = request.nextUrl.searchParams.get("ticker2");
  const tickers = request.nextUrl.searchParams.get("tickers");
  const lookback = request.nextUrl.searchParams.get("lookback") || "252";
  
  try {
    let command: string;
    
    switch (action) {
      case "breakdown":
        if (!ticker1 || !ticker2) {
          return NextResponse.json(
            { error: "Both ticker1 and ticker2 required for breakdown analysis" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/correlation_anomaly.py corr-breakdown --ticker1 ${ticker1} --ticker2 ${ticker2} --lookback ${lookback}`;
        break;
      
      case "scan":
        const scanTickers = tickers || "SPY,QQQ,IWM,TLT,GLD,USO,UUP";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/correlation_anomaly.py corr-scan --tickers ${scanTickers} --lookback ${lookback}`;
        break;
      
      case "regime":
        const regimeTickers = tickers || "SPY,TLT,GLD,DBC,UUP,EEM,HYG,LQD";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/correlation_anomaly.py corr-regime --tickers ${regimeTickers} --lookback ${lookback}`;
        break;
      
      case "arbitrage":
        const arbTickers = tickers || "XLF,XLK,XLE,XLV,XLY,XLP,XLI,XLU,XLB";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/correlation_anomaly.py corr-arbitrage --tickers ${arbTickers} --lookback ${lookback}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["breakdown", "scan", "regime", "arbitrage"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 90000,  // 90 seconds
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Correlation Anomaly Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      // If output is not JSON, return as text
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Correlation Anomaly API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
