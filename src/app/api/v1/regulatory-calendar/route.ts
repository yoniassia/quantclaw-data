import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Regulatory Event Calendar API (Phase 78)
 * Track FOMC, CPI, GDP, NFP releases with market reaction backtests and volatility forecasts
 * 
 * Endpoints:
 * - GET /api/v1/regulatory-calendar?action=econ-calendar
 * - GET /api/v1/regulatory-calendar?action=event-reaction&eventType=CPI&years=5
 * - GET /api/v1/regulatory-calendar?action=event-volatility&eventType=FOMC
 * - GET /api/v1/regulatory-calendar?action=event-backtest&eventType=NFP&years=5
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get("action") || "econ-calendar";
  const eventType = searchParams.get("eventType") || searchParams.get("event_type") || "";
  const years = searchParams.get("years") || "5";

  try {
    let command = "";

    switch (action) {
      case "econ-calendar":
        command = `python3 modules/regulatory_calendar.py econ-calendar`;
        break;

      case "event-reaction":
        if (!eventType) {
          return NextResponse.json(
            { error: "eventType parameter required (CPI, NFP, GDP, FOMC, PCE, RETAIL, UMICH)" },
            { status: 400 }
          );
        }
        command = `python3 modules/regulatory_calendar.py event-reaction ${eventType} --years ${years}`;
        break;

      case "event-volatility":
        if (!eventType) {
          return NextResponse.json(
            { error: "eventType parameter required (CPI, NFP, GDP, FOMC)" },
            { status: 400 }
          );
        }
        command = `python3 modules/regulatory_calendar.py event-volatility ${eventType}`;
        break;

      case "event-backtest":
        if (!eventType) {
          return NextResponse.json(
            { error: "eventType parameter required (CPI, NFP, GDP, FOMC)" },
            { status: 400 }
          );
        }
        command = `python3 modules/regulatory_calendar.py event-backtest ${eventType} --years ${years}`;
        break;

      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}. Valid actions: econ-calendar, event-reaction, event-volatility, event-backtest` 
          },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 45000, // 45s timeout (market data can be slow)
    });

    if (stderr && !stderr.includes("Warning") && !stderr.includes("FutureWarning")) {
      console.error("Regulatory Calendar stderr:", stderr);
    }

    // Parse CLI output to JSON
    // Since the CLI outputs formatted text, we return raw output
    // Can be enhanced to parse structured data
    const result = {
      raw_output: stdout,
      timestamp: new Date().toISOString()
    };

    return NextResponse.json({
      success: true,
      action,
      data: result,
      params: {
        eventType: eventType || undefined,
        years: (action === "event-reaction" || action === "event-backtest") ? years : undefined
      }
    });
  } catch (error: any) {
    console.error("Regulatory Calendar API error:", error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || "Failed to execute regulatory calendar analysis",
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
