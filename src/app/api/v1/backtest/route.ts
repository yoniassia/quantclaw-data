import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Backtesting Engine API
 * 
 * POST /api/v1/backtest — Run a backtest
 * Body: { strategy, ticker, start, end, params?, cash?, commission?, slippage? }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      strategy,
      ticker,
      start,
      end,
      params = null,
      cash = 100000,
      commission = 0,
      slippage = 0.0005
    } = body;

    if (!strategy || !ticker || !start || !end) {
      return NextResponse.json(
        { error: "strategy, ticker, start, and end are required" },
        { status: 400 }
      );
    }

    let command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest ${strategy} ${ticker} --start ${start} --end ${end} --cash ${cash} --commission ${commission} --slippage ${slippage}`;
    
    if (params) {
      command += ` --params '${JSON.stringify(params)}'`;
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR,
      maxBuffer: 10 * 1024 * 1024 // 10MB
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Backtest stderr:", stderr);
    }

    // Parse JSON from stdout (before the text report)
    const lines = stdout.split('\n');
    let jsonStr = '';
    let inJson = false;
    
    for (const line of lines) {
      if (line.trim() === '{') {
        inJson = true;
      }
      if (inJson) {
        jsonStr += line + '\n';
      }
      if (inJson && line.trim() === '}') {
        break;
      }
    }

    const result = JSON.parse(jsonStr);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error("Backtest error:", error);
    return NextResponse.json(
      { 
        error: "Failed to run backtest",
        details: error.message,
        stderr: error.stderr
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/v1/backtest?action=history — Get backtest history
 * GET /api/v1/backtest?action=report&run_id=1 — Get detailed report
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "history";
  
  try {
    let command: string;
    
    if (action === "history") {
      const limit = request.nextUrl.searchParams.get("limit") || "10";
      command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-history --limit ${limit}`;
    } else if (action === "report") {
      const runId = request.nextUrl.searchParams.get("run_id");
      if (!runId) {
        return NextResponse.json(
          { error: "run_id parameter required for report action" },
          { status: 400 }
        );
      }
      command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-report ${runId}`;
    } else {
      return NextResponse.json(
        { error: `Unknown action: ${action}` },
        { status: 400 }
      );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR,
      maxBuffer: 10 * 1024 * 1024
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Backtest stderr:", stderr);
    }

    if (action === "history") {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } else {
      // For report, return the text output
      return NextResponse.json({ report: stdout });
    }

  } catch (error: any) {
    console.error("Backtest error:", error);
    return NextResponse.json(
      { 
        error: "Failed to get backtest data",
        details: error.message
      },
      { status: 500 }
    );
  }
}
