import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Deep Learning Sentiment Analysis API — FinBERT for Financial Text
 * 
 * Advanced NLP using FinBERT (fine-tuned BERT for financial sentiment) to analyze:
 * - Earnings call transcripts with entity-level sentiment
 * - SEC filings (10-K, 10-Q, 8-K) with section-specific sentiment
 * - News articles with topic modeling and sentiment scoring
 * - Entity-level sentiment extraction (products, executives, competitors)
 * 
 * Endpoints:
 * - GET /api/v1/deep-learning-sentiment?action=earnings&ticker=AAPL — Analyze earnings transcripts
 * - GET /api/v1/deep-learning-sentiment?action=sec&ticker=TSLA&form_type=10-K — Analyze SEC filings
 * - GET /api/v1/deep-learning-sentiment?action=news&ticker=MSFT&days=7 — Analyze news sentiment
 * - GET /api/v1/deep-learning-sentiment?action=trend&ticker=NVDA&quarters=4 — Sentiment time series
 * - GET /api/v1/deep-learning-sentiment?action=compare&tickers=AAPL,MSFT,GOOGL&source=news — Compare peers
 * 
 * Phase: 88
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "news";
  const ticker = request.nextUrl.searchParams.get("ticker");
  const tickers = request.nextUrl.searchParams.get("tickers");
  
  // Validate inputs
  if (action === "compare") {
    if (!tickers) {
      return NextResponse.json(
        { error: "Missing required parameter: tickers (comma-separated)" },
        { status: 400 }
      );
    }
  } else {
    if (!ticker) {
      return NextResponse.json(
        { error: "Missing required parameter: ticker" },
        { status: 400 }
      );
    }
  }
  
  try {
    let command: string;
    
    switch (action) {
      case "earnings":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py finbert-earnings ${ticker}`;
        break;
      
      case "sec":
        const formType = request.nextUrl.searchParams.get("form_type") || "10-K";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py finbert-sec ${ticker} ${formType}`;
        break;
      
      case "news":
        const days = request.nextUrl.searchParams.get("days") || "7";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py finbert-news ${ticker} ${days}`;
        break;
      
      case "trend":
        const quarters = request.nextUrl.searchParams.get("quarters") || "4";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py finbert-trend ${ticker} ${quarters}`;
        break;
      
      case "compare":
        const source = request.nextUrl.searchParams.get("source") || "news";
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/cli.py finbert-compare ${tickers} ${source}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["earnings", "sec", "news", "trend", "compare"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000, // 60 seconds for FinBERT model loading
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Deep Learning Sentiment stderr:", stderr);
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
    console.error("Deep Learning Sentiment API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker: ticker || tickers
      },
      { status: 500 }
    );
  }
}
