import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Live Earnings Transcription API — Real-time Signal Extraction
 * 
 * Stream earnings calls, transcribe with Whisper, and extract trading signals in real-time.
 * Framework for:
 * - Upcoming earnings calendar (Yahoo Finance)
 * - Transcript signal extraction (sentiment, guidance changes, red flags)
 * - Earnings countdown tracking
 * - Quarter-over-quarter transcript comparison
 * 
 * Endpoints:
 * - GET /api/v1/live-transcription?action=schedule&days=7 — Upcoming earnings calendar
 * - GET /api/v1/live-transcription?action=signals&ticker=AAPL — Extract signals from latest transcript
 * - GET /api/v1/live-transcription?action=countdown&ticker=TSLA — Days until next earnings
 * - GET /api/v1/live-transcription?action=compare&ticker=MSFT — Compare latest vs prior transcript
 * 
 * Phase: 82
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "schedule";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const days = request.nextUrl.searchParams.get("days") || "7";
  
  try {
    let command: string;
    
    switch (action) {
      case "schedule":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py earnings-schedule ${days}`;
        break;
      
      case "signals":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py transcript-signals ${ticker}`;
        break;
      
      case "countdown":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py earnings-countdown ${ticker}`;
        break;
      
      case "compare":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py transcript-compare ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["schedule", "signals", "countdown", "compare"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Live Transcription stderr:", stderr);
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
    console.error("Live Transcription API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker: ticker || "N/A",
        days: action === "schedule" ? days : undefined
      },
      { status: 500 }
    );
  }
}
