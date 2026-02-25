import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(process.cwd());

/**
 * Order Book Depth API - Phase 39
 * Level 2 data analysis, bid-ask imbalance, hidden liquidity detection
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "order-book";
  const symbol = searchParams.get("symbol");

  if (!symbol) {
    return NextResponse.json(
      { error: "Missing required parameter: symbol" },
      { status: 400 }
    );
  }

  try {
    let command = "";

    switch (action) {
      case "order-book":
        const levels = searchParams.get("levels") || "10";
        command = `python3 ${PROJECT_ROOT}/modules/order_book.py order-book ${symbol} --levels ${levels}`;
        break;

      case "bid-ask":
        command = `python3 ${PROJECT_ROOT}/modules/order_book.py bid-ask ${symbol}`;
        break;

      case "liquidity":
        command = `python3 ${PROJECT_ROOT}/modules/order_book.py liquidity ${symbol}`;
        break;

      case "imbalance":
        const period = searchParams.get("period") || "1d";
        if (!["1d", "5d", "1mo"].includes(period)) {
          return NextResponse.json(
            { error: "Invalid period. Must be one of: 1d, 5d, 1mo" },
            { status: 400 }
          );
        }
        command = `python3 ${PROJECT_ROOT}/modules/order_book.py imbalance ${symbol} --period ${period}`;
        break;

      case "support-resistance":
        const srPeriod = searchParams.get("period") || "3mo";
        command = `python3 ${PROJECT_ROOT}/modules/order_book.py support-resistance ${symbol} --period ${srPeriod}`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}. Valid actions: order-book, bid-ask, liquidity, imbalance, support-resistance` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: PROJECT_ROOT,
      timeout: 30000, // 30 second timeout
    });

    if (stderr && !stderr.includes("Storing cookies")) {
      console.error("Python stderr:", stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Order Book API error:", error);
    return NextResponse.json(
      {
        error: "Failed to execute order book command",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

/**
 * API Examples:
 *
 * GET /api/v1/order-book?action=order-book&symbol=AAPL&levels=10
 * Returns: Simulated Level 2 order book with bids/asks, imbalance metrics
 *
 * GET /api/v1/order-book?action=bid-ask&symbol=TSLA
 * Returns: Current bid-ask spread, spread percentage, mid price
 *
 * GET /api/v1/order-book?action=liquidity&symbol=SPY
 * Returns: Liquidity score (0-100), letter grade, component scores
 *
 * GET /api/v1/order-book?action=imbalance&symbol=NVDA&period=5d
 * Returns: Buy/sell volume breakdown, imbalance ratio, VWAP comparison
 *
 * GET /api/v1/order-book?action=support-resistance&symbol=AAPL&period=6mo
 * Returns: Support/resistance levels from volume clusters, strength scores
 */
