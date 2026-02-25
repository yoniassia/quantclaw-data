import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Live Earnings Transcription API — Real-Time Earnings Call Analysis
 * 
 * Stream earnings calls, transcribe with Whisper, extract signals in real-time.
 * 
 * Features:
 * - Upcoming earnings calendar with call schedules
 * - Real-time transcription via OpenAI Whisper
 * - Live signal extraction (sentiment, keywords, tone)
 * - Management confidence scoring
 * - Trading alert generation
 * 
 * Endpoints:
 * - GET /api/v1/live-earnings?action=calendar&days=30 — Upcoming earnings calendar
 * - GET /api/v1/live-earnings?action=status — Live earnings calls today
 * - GET /api/v1/live-earnings?action=simulate&ticker=AAPL — Simulate live call analysis
 * - POST /api/v1/live-earnings?action=transcribe — Transcribe audio file (requires file upload)
 * 
 * Phase: 82
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "calendar";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const days = request.nextUrl.searchParams.get("days") || "30";
  
  try {
    let command: string;
    
    switch (action) {
      case "calendar":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py calendar --days ${days}`;
        break;
      
      case "status":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py status`;
        break;
      
      case "simulate":
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py simulate ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["calendar", "status", "simulate"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000, // 60 seconds for longer operations
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Live Earnings stderr:", stderr);
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
    console.error("Live Earnings API Error:", errorMessage);
    
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
 * POST endpoint for audio file transcription
 * Requires multipart/form-data with audio file
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const audioFile = formData.get("audio");
    const ticker = formData.get("ticker") || "UNKNOWN";
    
    if (!audioFile || !(audioFile instanceof File)) {
      return NextResponse.json(
        { error: "Missing audio file" },
        { status: 400 }
      );
    }
    
    // Save uploaded file temporarily
    const tempPath = `/tmp/earnings_${Date.now()}.${audioFile.name.split('.').pop()}`;
    const buffer = Buffer.from(await audioFile.arrayBuffer());
    await require("fs").promises.writeFile(tempPath, buffer);
    
    // Transcribe
    const command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py transcribe ${tempPath} --ticker ${ticker}`;
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 600000, // 10 minutes for transcription
      maxBuffer: 20 * 1024 * 1024 // 20MB buffer
    });
    
    // Clean up temp file
    await require("fs").promises.unlink(tempPath).catch(() => {});
    
    if (stderr) {
      console.error("Transcription stderr:", stderr);
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
    console.error("Live Earnings Transcription Error:", errorMessage);
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}
