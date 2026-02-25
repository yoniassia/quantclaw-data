import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Transaction Cost Analysis (TCA) API — Market impact, execution optimization, cost analysis
 * 
 * Endpoints:
 * - GET /api/v1/tca?action=spread&ticker=AAPL — Bid-ask spread analysis
 * - GET /api/v1/tca?action=impact&ticker=AAPL&trade_size=5000000 — Market impact estimation
 * - GET /api/v1/tca?action=shortfall&ticker=AAPL&decision_price=270.00&exec_prices=270.10,270.15,270.25&exec_sizes=1000,1500,2000&side=buy — Implementation shortfall
 * - GET /api/v1/tca?action=optimize&ticker=AAPL&total_shares=50000&window=240&strategy=vwap — Execution schedule
 * - GET /api/v1/tca?action=compare&ticker=AAPL&trade_size=10000000 — Strategy comparison
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "spread";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const tradeSize = request.nextUrl.searchParams.get("trade_size") || "";
  const decisionPrice = request.nextUrl.searchParams.get("decision_price") || "";
  const execPrices = request.nextUrl.searchParams.get("exec_prices") || "";
  const execSizes = request.nextUrl.searchParams.get("exec_sizes") || "";
  const side = request.nextUrl.searchParams.get("side") || "buy";
  const totalShares = request.nextUrl.searchParams.get("total_shares") || "";
  const window = request.nextUrl.searchParams.get("window") || "240";
  const strategy = request.nextUrl.searchParams.get("strategy") || "vwap";
  
  try {
    if (!ticker) {
      return NextResponse.json(
        { error: "ticker parameter required" },
        { status: 400 }
      );
    }
    
    let command: string;
    
    switch (action) {
      case "spread":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py tca-spread ${ticker}`;
        break;
      
      case "impact":
        if (!tradeSize) {
          return NextResponse.json(
            { error: "trade_size parameter required for impact analysis" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py tca-impact ${ticker} --trade-size ${tradeSize}`;
        break;
      
      case "shortfall":
        if (!decisionPrice || !execPrices || !execSizes) {
          return NextResponse.json(
            { error: "decision_price, exec_prices, and exec_sizes parameters required for shortfall analysis" },
            { status: 400 }
          );
        }
        const execPricesFormatted = execPrices.split(',').map(p => parseFloat(p)).join(' ');
        const execSizesFormatted = execSizes.split(',').map(s => parseInt(s)).join(' ');
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py tca-shortfall ${ticker} --decision-price ${decisionPrice} --exec-prices ${execPricesFormatted} --exec-sizes ${execSizesFormatted} --side ${side}`;
        break;
      
      case "optimize":
        if (!totalShares) {
          return NextResponse.json(
            { error: "total_shares parameter required for optimization" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py tca-optimize ${ticker} --total-shares ${totalShares} --window ${window} --strategy ${strategy}`;
        break;
      
      case "compare":
        if (!tradeSize) {
          return NextResponse.json(
            { error: "trade_size parameter required for strategy comparison" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py tca-compare ${ticker} --trade-size ${tradeSize}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["spread", "impact", "shortfall", "optimize", "compare"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000, // 30 seconds
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("TCA Module stderr:", stderr);
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
    console.error("TCA API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        parameters: {
          trade_size: tradeSize,
          decision_price: decisionPrice,
          exec_prices: execPrices,
          exec_sizes: execSizes,
          side,
          total_shares: totalShares,
          window,
          strategy
        }
      },
      { status: 500 }
    );
  }
}
