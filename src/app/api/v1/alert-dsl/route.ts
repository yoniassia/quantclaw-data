import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Alert DSL API — Domain-Specific Language for Complex Multi-Condition Alert Rules
 * 
 * Endpoints:
 * - GET /api/v1/alert-dsl?action=help — DSL syntax help and examples
 * - GET /api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price>200 — Evaluate expression for single ticker
 * - GET /api/v1/alert-dsl?action=scan&expression=rsi<25&universe=SP500&limit=10 — Scan universe with expression
 * 
 * Examples:
 * - /api/v1/alert-dsl?action=eval&ticker=AAPL&expression=price > 200 AND rsi < 30
 * - /api/v1/alert-dsl?action=eval&ticker=TSLA&expression=sma(20) crosses_above sma(50)
 * - /api/v1/alert-dsl?action=scan&expression=rsi < 25&universe=SP500&limit=10
 * - /api/v1/alert-dsl?action=scan&expression=volume > 10M AND change_pct(1d) > 5&universe=AAPL,MSFT,GOOGL
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "help";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const expression = request.nextUrl.searchParams.get("expression") || "";
  const universe = request.nextUrl.searchParams.get("universe") || "SP500";
  const limit = request.nextUrl.searchParams.get("limit") || "";
  
  try {
    let command: string;
    
    switch (action) {
      case "help":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/alert_dsl.py dsl-help`;
        break;
      
      case "eval":
        if (!ticker) {
          return NextResponse.json(
            { error: "ticker parameter required for eval action" },
            { status: 400 }
          );
        }
        if (!expression) {
          return NextResponse.json(
            { error: "expression parameter required for eval action" },
            { status: 400 }
          );
        }
        // Escape quotes in expression
        const escapedExpression = expression.replace(/"/g, '\\"');
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/alert_dsl.py dsl-eval ${ticker} "${escapedExpression}"`;
        break;
      
      case "scan":
        if (!expression) {
          return NextResponse.json(
            { error: "expression parameter required for scan action" },
            { status: 400 }
          );
        }
        const escapedScanExpression = expression.replace(/"/g, '\\"');
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/alert_dsl.py dsl-scan "${escapedScanExpression}" --universe ${universe}`;
        if (limit) {
          command += ` --limit ${limit}`;
        }
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["help", "eval", "scan"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000, // 60s timeout for scan operations
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer for large scan results
    });
    
    if (stderr) {
      console.error("Alert DSL Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      // For help command, return plain text
      if (action === "help") {
        return NextResponse.json({ 
          help: stdout.trim()
        });
      }
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Alert DSL API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        expression,
        universe,
        limit
      },
      { status: 500 }
    );
  }
}
