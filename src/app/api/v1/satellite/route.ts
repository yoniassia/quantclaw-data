import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Satellite Imagery Proxies API — Economic Activity Indicators
 * 
 * Endpoints:
 * - GET /api/v1/satellite?action=proxy&ticker=WMT — Company-specific satellite proxy
 * - GET /api/v1/satellite?action=shipping — Baltic Dry Index / shipping activity
 * - GET /api/v1/satellite?action=construction — Construction activity tracking
 * - GET /api/v1/satellite?action=foot-traffic&ticker=AAPL — Google Trends foot traffic
 * - GET /api/v1/satellite?action=economic-index — Composite economic activity index
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "economic-index";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  
  try {
    let command: string;
    
    switch (action) {
      case "proxy":
        if (!ticker) {
          return NextResponse.json(
            { error: "ticker parameter required for proxy action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/satellite_proxies.py satellite-proxy ${ticker}`;
        break;
      
      case "shipping":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/satellite_proxies.py shipping-index`;
        break;
      
      case "construction":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/satellite_proxies.py construction-activity`;
        break;
      
      case "foot-traffic":
        if (!ticker) {
          return NextResponse.json(
            { error: "ticker parameter required for foot-traffic action" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/satellite_proxies.py foot-traffic ${ticker}`;
        break;
      
      case "economic-index":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/satellite_proxies.py economic-index`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["proxy", "shipping", "construction", "foot-traffic", "economic-index"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000, // Google Trends can be slower
      maxBuffer: 5 * 1024 * 1024
    });
    
    if (stderr) {
      console.error("Satellite Module stderr:", stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({ 
        result: stdout.trim(),
        warning: "Response was not valid JSON"
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Satellite API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker
      },
      { status: 500 }
    );
  }
}
