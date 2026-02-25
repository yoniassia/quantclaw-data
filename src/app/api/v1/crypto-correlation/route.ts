import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Crypto Correlation Indicators API — BTC Dominance, Altcoin Season, DeFi TVL, Crypto-Equity Correlation
 * 
 * Endpoints:
 * - GET /api/v1/crypto-correlation?action=btc-dominance
 * - GET /api/v1/crypto-correlation?action=altcoin-season
 * - GET /api/v1/crypto-correlation?action=defi-tvl-correlation
 * - GET /api/v1/crypto-correlation?action=crypto-equity-corr
 * 
 * Phase: 54
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "btc-dominance";
  
  try {
    let command: string;
    
    switch (action) {
      case "btc-dominance":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/crypto_correlation.py btc-dominance`;
        break;
      
      case "altcoin-season":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/crypto_correlation.py altcoin-season`;
        break;
      
      case "defi-tvl-correlation":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/crypto_correlation.py defi-tvl-correlation`;
        break;
      
      case "crypto-equity-corr":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/crypto_correlation.py crypto-equity-corr`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["btc-dominance", "altcoin-season", "defi-tvl-correlation", "crypto-equity-corr"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 30000,  // 30 seconds
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Crypto Correlation Module stderr:", stderr);
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
    console.error("Crypto Correlation API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        suggestion: "Make sure requests is installed: pip install requests"
      },
      { status: 500 }
    );
  }
}
