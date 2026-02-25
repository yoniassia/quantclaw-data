import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Factor Timing Model API (Phase 73)
 * Regime detection for when factors work, adaptive factor rotation
 * 
 * Endpoints:
 * - GET /api/v1/factor-timing?action=factor-timing
 * - GET /api/v1/factor-timing?action=factor-rotation
 * - GET /api/v1/factor-timing?action=factor-performance&period=1y
 * - GET /api/v1/factor-timing?action=factor-regime-history&days=60
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get("action") || "factor-timing";
  const period = searchParams.get("period") || "1y";
  const days = searchParams.get("days") || "60";

  try {
    let command = "";

    switch (action) {
      case "factor-timing":
        command = `python3 modules/factor_timing.py factor-timing`;
        break;

      case "factor-rotation":
        command = `python3 modules/factor_timing.py factor-rotation`;
        break;

      case "factor-performance":
        command = `python3 modules/factor_timing.py factor-performance ${period}`;
        break;

      case "factor-regime-history":
        command = `python3 modules/factor_timing.py factor-regime-history --days ${days}`;
        break;

      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}. Valid actions: factor-timing, factor-rotation, factor-performance, factor-regime-history` 
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 30000, // 30s timeout
    });

    if (stderr && !stderr.includes("Warning") && !stderr.includes("FutureWarning")) {
      console.error("Factor Timing stderr:", stderr);
    }

    // Parse CLI output to JSON
    // Since the CLI outputs formatted text, we need to capture and structure it
    // For now, return raw output - can be enhanced to parse structured data
    const result = {
      raw_output: stdout,
      timestamp: new Date().toISOString()
    };

    return NextResponse.json({
      success: true,
      action,
      data: result,
      params: {
        period: action === "factor-performance" ? period : undefined,
        days: action === "factor-regime-history" ? days : undefined
      }
    });
  } catch (error: any) {
    console.error("Factor Timing API error:", error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || "Failed to execute factor timing analysis",
        action,
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  return NextResponse.json(
    { error: "POST not supported. Use GET with query parameters." },
    { status: 405 }
  );
}
