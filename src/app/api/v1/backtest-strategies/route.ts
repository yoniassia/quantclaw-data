import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * GET /api/v1/backtest-strategies — List all available backtesting strategies
 */
export async function GET(request: NextRequest) {
  try {
    const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py backtest-strategies`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: QUANTCLAW_DATA_DIR
    });

    if (stderr && !stderr.includes('FutureWarning')) {
      console.error("Backtest strategies stderr:", stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);

  } catch (error: any) {
    console.error("Backtest strategies error:", error);
    return NextResponse.json(
      { 
        error: "Failed to list strategies",
        details: error.message
      },
      { status: 500 }
    );
  }
}
