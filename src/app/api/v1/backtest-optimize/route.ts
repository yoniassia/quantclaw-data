import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * POST /api/v1/backtest-optimize — Optimize strategy parameters
 * Body: { strategy, ticker, start, end, method?, metric?, n_trials? }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      strategy,
      ticker,
      start,
      end,
      method = "grid",
      metric = "sharpe_ratio",
      n_trials = 100
    } = body;

    if (!strategy || !ticker || !start || !end) {
      return NextResponse.json(
        { error: "strategy, ticker, start, and end are required" },
        { status: 400 }
      );
    }

    let command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-optimize ${strategy} ${ticker} --start ${start} --end ${end} --method ${method} --metric ${metric}`;
    
    if (method === "random") {
      command += ` --n-trials ${n_trials}`;
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR,
      maxBuffer: 20 * 1024 * 1024, // 20MB for optimization results
      timeout: 300000 // 5 minutes timeout
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Optimization stderr:", stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error("Optimization error:", error);
    return NextResponse.json(
      { 
        error: "Failed to optimize parameters",
        details: error.message,
        stderr: error.stderr
      },
      { status: 500 }
    );
  }
}
