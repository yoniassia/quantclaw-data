import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * GET /api/v1/backtest-results?run_id=1 — Get results for a specific run
 */
export async function GET(request: NextRequest) {
  try {
    const runId = request.nextUrl.searchParams.get("run_id");
    
    if (!runId) {
      return NextResponse.json(
        { error: "run_id parameter is required" },
        { status: 400 }
      );
    }

    const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-report ${runId}`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR,
      maxBuffer: 10 * 1024 * 1024
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Backtest results stderr:", stderr);
    }

    return NextResponse.json({ 
      run_id: parseInt(runId),
      report: stdout 
    });

  } catch (error: any) {
    console.error("Backtest results error:", error);
    return NextResponse.json(
      { 
        error: "Failed to get backtest results",
        details: error.message
      },
      { status: 500 }
    );
  }
}
