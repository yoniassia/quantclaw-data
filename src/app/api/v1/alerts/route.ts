import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(process.cwd());

/**
 * Smart Alerts API - Phase 40
 * Multi-channel alert delivery with rate limiting
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "list";

  try {
    let command = "";

    switch (action) {
      case "list":
        const activeOnly = searchParams.get("active") === "true";
        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-list${
          activeOnly ? " --active" : ""
        }`;
        break;

      case "stats":
        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-stats`;
        break;

      case "history":
        const symbol = searchParams.get("symbol");
        const limit = searchParams.get("limit") || "50";
        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-history --limit ${limit}${
          symbol ? ` --symbol ${symbol}` : ""
        }`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: PROJECT_ROOT,
    });

    if (stderr) {
      console.error("Python stderr:", stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Alert API error:", error);
    return NextResponse.json(
      {
        error: "Failed to execute alert command",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;

    let command = "";

    switch (action) {
      case "create":
        const { symbol, condition, channels, cooldown, maxPerHour } = params;
        if (!symbol || !condition) {
          return NextResponse.json(
            { error: "Missing required fields: symbol, condition" },
            { status: 400 }
          );
        }

        const channelStr = channels?.join(",") || "console";
        const cooldownMin = cooldown || 60;
        const maxHourly = maxPerHour || 3;

        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-create ${symbol} --condition "${condition}" --channels ${channelStr} --cooldown ${cooldownMin} --max-per-hour ${maxHourly}`;
        break;

      case "check":
        const symbols = params.symbols || [];
        const symbolStr = symbols.join(",");
        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-check${
          symbolStr ? ` --symbols ${symbolStr}` : ""
        }`;
        break;

      case "delete":
        const alertId = params.alertId;
        if (!alertId) {
          return NextResponse.json(
            { error: "Missing alertId" },
            { status: 400 }
          );
        }
        command = `python3 ${PROJECT_ROOT}/modules/smart_alerts.py alert-delete ${alertId}`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: PROJECT_ROOT,
    });

    if (stderr) {
      console.error("Python stderr:", stderr);
    }

    const result = JSON.parse(stdout);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error("Alert API error:", error);
    return NextResponse.json(
      {
        error: "Failed to execute alert command",
        details: error.message,
      },
      { status: 500 }
    );
  }
}

/**
 * API Examples:
 *
 * GET /api/v1/alerts?action=list
 * GET /api/v1/alerts?action=list&active=true
 * GET /api/v1/alerts?action=stats
 * GET /api/v1/alerts?action=history&symbol=AAPL&limit=20
 *
 * POST /api/v1/alerts
 * {
 *   "action": "create",
 *   "symbol": "AAPL",
 *   "condition": "price>200",
 *   "channels": ["console", "file", "webhook"],
 *   "cooldown": 60,
 *   "maxPerHour": 3
 * }
 *
 * POST /api/v1/alerts
 * {
 *   "action": "check",
 *   "symbols": ["AAPL", "TSLA", "NVDA"]
 * }
 *
 * POST /api/v1/alerts
 * {
 *   "action": "delete",
 *   "alertId": "abc123"
 * }
 */
