import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * POST /api/v1/backtest-walkforward — Run walk-forward optimization
 * Body: { strategy, ticker, start, end, train_months?, test_months?, metric? }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      strategy,
      ticker,
      start,
      end,
      train_months = 12,
      test_months = 3,
      metric = "sharpe_ratio"
    } = body;

    if (!strategy || !ticker || !start || !end) {
      return NextResponse.json(
        { error: "strategy, ticker, start, and end are required" },
        { status: 400 }
      );
    }

    const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-walkforward ${strategy} ${ticker} --start ${start} --end ${end} --train-months ${train_months} --test-months ${test_months} --metric ${metric}`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR,
      maxBuffer: 20 * 1024 * 1024, // 20MB
      timeout: 600000 // 10 minutes timeout for walk-forward
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Walk-forward stderr:", stderr);
    }

    // Extract JSON from stdout (skip the window progress lines)
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
    console.error("Walk-forward error:", error);
    return NextResponse.json(
      { 
        error: "Failed to run walk-forward optimization",
        details: error.message,
        stderr: error.stderr
      },
      { status: 500 }
    );
  }
}
