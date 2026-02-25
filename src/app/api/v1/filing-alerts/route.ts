import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(process.cwd());

/**
 * 13D/13G Filing Alerts API - Phase 68
 * Real-time SEC EDGAR RSS notifications for activist filings and stake changes
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "recent";

  try {
    let command = "";

    switch (action) {
      case "recent":
        const hours = searchParams.get("hours") || "24";
        const type = searchParams.get("type");
        command = `python3 ${PROJECT_ROOT}/modules/filing_alerts.py recent --hours ${hours}${
          type ? ` --type "${type}"` : ""
        }`;
        break;

      case "search":
        const company = searchParams.get("company");
        if (!company) {
          return NextResponse.json(
            { error: "Company name required for search" },
            { status: 400 }
          );
        }
        const searchType = searchParams.get("type");
        command = `python3 ${PROJECT_ROOT}/modules/filing_alerts.py search "${company}"${
          searchType ? ` --type "${searchType}"` : ""
        }`;
        break;

      case "activists":
        const minFilings = searchParams.get("min_filings") || "2";
        command = `python3 ${PROJECT_ROOT}/modules/filing_alerts.py activists --min-filings ${minFilings}`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}. Valid actions: recent, search, activists` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: PROJECT_ROOT,
      timeout: 30000, // 30 second timeout
    });

    if (stderr && stderr.includes("Error")) {
      console.error("Python stderr:", stderr);
      return NextResponse.json(
        { error: "Python module error", details: stderr },
        { status: 500 }
      );
    }

    // Try to parse as JSON, otherwise return raw text
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch {
      // If not JSON, return structured response with raw output
      return NextResponse.json({
        success: true,
        action,
        output: stdout,
      });
    }
  } catch (error: any) {
    console.error("Filing Alerts API error:", error);
    return NextResponse.json(
      {
        error: "Failed to execute filing alerts command",
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

    if (action === "watch") {
      // For watch action, return a message explaining it's for CLI only
      return NextResponse.json({
        error: "Watch action is designed for CLI use only",
        message:
          "The watch command runs continuously and is not suitable for HTTP API. Use the CLI: python cli.py filing-alerts watch",
      });
    }

    return NextResponse.json(
      { error: `POST method not supported for action: ${action}` },
      { status: 405 }
    );
  } catch (error: any) {
    console.error("Filing Alerts POST error:", error);
    return NextResponse.json(
      {
        error: "Failed to process filing alerts POST request",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
