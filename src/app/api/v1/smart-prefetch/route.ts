import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Smart Data Prefetching API — ML-based Predictive Data Caching
 * 
 * Machine learning predicts which data will be requested next and preloads during idle periods.
 * Tracks usage patterns across tickers, modules, time-of-day, and day-of-week to optimize cache hit rates.
 * 
 * Features:
 * - Usage pattern tracking and analysis
 * - Time-weighted prediction (market hours, after-hours, overnight)
 * - Automatic cache warming based on confidence scores
 * - Real-time cache hit rate monitoring
 * - Configurable prefetch pool size and confidence thresholds
 * 
 * Endpoints:
 * - GET /api/v1/smart-prefetch?action=stats — Show usage patterns and predictions
 * - GET /api/v1/smart-prefetch?action=warmup — Warm cache with predicted data
 * - GET /api/v1/smart-prefetch?action=status — Show cache hit rates and statistics
 * - GET /api/v1/smart-prefetch?action=config — Get current configuration
 * - POST /api/v1/smart-prefetch?action=config — Update configuration (top_n, min_confidence, enabled)
 * - POST /api/v1/smart-prefetch?action=record — Record a query (for integration)
 * 
 * Phase: 83
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "status";
  
  try {
    let command: string;
    
    switch (action) {
      case "stats":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py prefetch-stats`;
        break;
      
      case "warmup":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py prefetch-warmup`;
        break;
      
      case "status":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py cache-status`;
        break;
      
      case "config":
        // Return current config as JSON
        command = `cat ${QUANTCLAW_DATA_DIR}/data/prefetch_config.json`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["stats", "warmup", "status", "config"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Smart Prefetch stderr:", stderr);
    }
    
    // Try to parse as JSON first
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      // If not JSON, return as text
      return NextResponse.json({ 
        result: stdout.trim(),
        action
      });
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Smart Prefetch API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}

/**
 * POST handler for configuration updates and query recording
 */
export async function POST(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action");
  
  if (!action) {
    return NextResponse.json(
      { error: "Missing required parameter: action" },
      { status: 400 }
    );
  }
  
  try {
    if (action === "config") {
      // Update configuration
      const body = await request.json();
      const { top_n, min_confidence, enabled } = body;
      
      let command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py prefetch-config`;
      
      if (top_n !== undefined) {
        command += ` --top ${top_n}`;
      }
      
      if (min_confidence !== undefined) {
        command += ` --confidence ${min_confidence}`;
      }
      
      if (enabled !== undefined) {
        command += ` --enable ${enabled}`;
      }
      
      const { stdout, stderr } = await execAsync(command, { 
        timeout: 10000 
      });
      
      if (stderr) {
        console.error("Config update stderr:", stderr);
      }
      
      return NextResponse.json({ 
        status: "success",
        message: stdout.trim()
      });
      
    } else if (action === "record") {
      // Record a query for pattern analysis
      const body = await request.json();
      const { ticker, module, hit } = body;
      
      if (!ticker || !module) {
        return NextResponse.json(
          { error: "Missing required fields: ticker, module" },
          { status: 400 }
        );
      }
      
      const hitFlag = hit ? "--hit" : "";
      const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/smart_prefetch.py record-query ${ticker} ${module} ${hitFlag}`;
      
      const { stdout, stderr } = await execAsync(command, { 
        timeout: 5000 
      });
      
      if (stderr) {
        console.error("Record query stderr:", stderr);
      }
      
      return NextResponse.json({ 
        status: "recorded",
        ticker,
        module,
        hit: hit || false
      });
      
    } else {
      return NextResponse.json(
        { 
          error: `Unknown POST action: ${action}`,
          available: ["config", "record"]
        },
        { status: 400 }
      );
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e);
    console.error("Smart Prefetch POST Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
