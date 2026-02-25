import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * AI Earnings Call Analyzer API — Real-time Tone Detection, Hesitation Patterns, Confidence Scoring
 * 
 * Advanced linguistic analysis of earnings call transcripts using LLM-style techniques:
 * - Real-time tone detection with contextual sentiment analysis
 * - Hesitation pattern recognition (fillers, pauses, corrections)
 * - Executive confidence scoring via multi-factor analysis
 * - Quarter-over-quarter language shift detection
 * - Advanced hedging language detection with categorization
 * 
 * Endpoints:
 * - GET /api/v1/ai-earnings?action=tone&ticker=AAPL — Real-time tone detection with LLM-style analysis
 * - GET /api/v1/ai-earnings?action=confidence&ticker=TSLA — Executive confidence scoring
 * - GET /api/v1/ai-earnings?action=language-shift&ticker=MSFT — Quarter-over-quarter language changes
 * - GET /api/v1/ai-earnings?action=hedging&ticker=NVDA — Advanced hedging language detection
 * 
 * Phase: 76
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "tone";
  const ticker = request.nextUrl.searchParams.get("ticker");
  
  if (!ticker) {
    return NextResponse.json(
      { error: "Missing required parameter: ticker" },
      { status: 400 }
    );
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "tone":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py earnings-tone ${ticker}`;
        break;
      
      case "confidence":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py confidence-score ${ticker}`;
        break;
      
      case "language-shift":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py language-shift ${ticker}`;
        break;
      
      case "hedging":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py hedging-detector ${ticker}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["tone", "confidence", "language-shift", "hedging"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("AI Earnings Analyzer stderr:", stderr);
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
    console.error("AI Earnings Analyzer API Error:", errorMessage);
    
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
