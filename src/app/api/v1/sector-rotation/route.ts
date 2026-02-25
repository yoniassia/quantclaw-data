import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Sector Rotation Model API — Economic Cycle Indicators & Relative Strength
 * 
 * Endpoints:
 * - GET /api/v1/sector-rotation?action=rotation&lookback=60 — Full rotation signals with cycle context
 * - GET /api/v1/sector-rotation?action=momentum&lookback=90 — Sector momentum rankings only
 * - GET /api/v1/sector-rotation?action=cycle — Economic cycle analysis
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "rotation";
  const lookback = request.nextUrl.searchParams.get("lookback") || "60";
  
  try {
    let command: string;
    
    switch (action) {
      case "rotation":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/sector_rotation.py sector-rotation ${lookback}`;
        break;
      
      case "momentum":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/sector_rotation.py sector-momentum ${lookback}`;
        break;
      
      case "cycle":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/sector_rotation.py economic-cycle`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["rotation", "momentum", "cycle"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000,  // Longer timeout for multiple API calls
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Sector Rotation Module stderr:", stderr);
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
    console.error("Sector Rotation API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        lookback
      },
      { status: 500 }
    );
  }
}
