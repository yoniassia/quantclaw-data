import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * Political Risk Scoring API (Phase 49)
 * Endpoints:
 * - GET /api/v1/political-risk?action=geopolitical-events&country=USA&hours=48
 * - GET /api/v1/political-risk?action=sanctions-search&entity=Russia&type=country
 * - GET /api/v1/political-risk?action=regulatory-changes&sector=finance&days=30
 * - GET /api/v1/political-risk?action=country-risk&country=USA
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  const action = searchParams.get("action") || "country-risk";
  const country = searchParams.get("country");
  const entity = searchParams.get("entity");
  const type = searchParams.get("type");
  const sector = searchParams.get("sector");
  const keywords = searchParams.get("keywords");
  const hours = searchParams.get("hours") || "48";
  const days = searchParams.get("days") || "30";

  try {
    let command = "";

    switch (action) {
      case "geopolitical-events":
        command = `python3 modules/political_risk.py geopolitical-events`;
        if (country) command += ` --country ${country}`;
        if (keywords) command += ` --keywords "${keywords}"`;
        command += ` --hours ${hours}`;
        break;

      case "sanctions-search":
        command = `python3 modules/political_risk.py sanctions-search`;
        if (entity) command += ` --entity "${entity}"`;
        if (type) command += ` --type ${type}`;
        break;

      case "regulatory-changes":
        command = `python3 modules/political_risk.py regulatory-changes`;
        if (sector) command += ` --sector ${sector}`;
        if (country) command += ` --country ${country}`;
        command += ` --days ${days}`;
        break;

      case "country-risk":
        if (!country) {
          return NextResponse.json(
            { error: "country parameter required for country-risk action" },
            { status: 400 }
          );
        }
        command = `python3 modules/political_risk.py country-risk ${country}`;
        break;

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}. Valid actions: geopolitical-events, sanctions-search, regulatory-changes, country-risk` },
          { status: 400 }
        );
    }

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 30000, // 30s timeout
    });

    if (stderr && !stderr.includes("⚠️")) {
      console.error("Political Risk stderr:", stderr);
    }

    const result = JSON.parse(stdout);

    return NextResponse.json({
      success: true,
      action,
      data: result,
    });
  } catch (error: any) {
    console.error("Political Risk API error:", error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || "Failed to execute political risk analysis",
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
