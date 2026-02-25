import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Tax Loss Harvesting API — Identify Opportunities, Track Wash Sale Rules, Estimate Tax Savings
 * 
 * Endpoints:
 * - GET /api/v1/tax-loss?action=scan&tickers=AAPL,TSLA,MSFT — Scan portfolio for TLH opportunities
 * - GET /api/v1/tax-loss?action=wash-sale-check&ticker=TSLA&date=2025-01-15 — Check wash sale window
 * - GET /api/v1/tax-loss?action=tax-savings&ticker=AAPL&cost_basis=180&shares=100&tax_rate=0.25 — Estimate tax savings
 * - GET /api/v1/tax-loss?action=replacements&ticker=TSLA — Suggest sector replacement securities
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "scan";
  
  try {
    let command: string;
    
    switch (action) {
      case "scan": {
        const tickers = request.nextUrl.searchParams.get("tickers");
        if (!tickers) {
          return NextResponse.json(
            { error: "Missing required parameter: tickers (comma-separated)" },
            { status: 400 }
          );
        }
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} cli.py tlh-scan ${tickers}`;
        break;
      }
      
      case "wash-sale-check": {
        const ticker = request.nextUrl.searchParams.get("ticker");
        const date = request.nextUrl.searchParams.get("date");
        
        if (!ticker || !date) {
          return NextResponse.json(
            { error: "Missing required parameters: ticker, date (YYYY-MM-DD)" },
            { status: 400 }
          );
        }
        
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} cli.py wash-sale-check ${ticker} ${date}`;
        break;
      }
      
      case "tax-savings": {
        const ticker = request.nextUrl.searchParams.get("ticker");
        const costBasis = request.nextUrl.searchParams.get("cost_basis");
        const shares = request.nextUrl.searchParams.get("shares");
        const taxRate = request.nextUrl.searchParams.get("tax_rate") || "0.25";
        
        if (!ticker || !costBasis || !shares) {
          return NextResponse.json(
            { error: "Missing required parameters: ticker, cost_basis, shares" },
            { status: 400 }
          );
        }
        
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} cli.py tax-savings ${ticker} --cost-basis ${costBasis} --shares ${shares} --tax-rate ${taxRate}`;
        break;
      }
      
      case "replacements": {
        const ticker = request.nextUrl.searchParams.get("ticker");
        if (!ticker) {
          return NextResponse.json(
            { error: "Missing required parameter: ticker" },
            { status: 400 }
          );
        }
        command = `cd ${QUANTCLAW_DATA_DIR} && ${PYTHON} cli.py tlh-replacements ${ticker}`;
        break;
      }
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["scan", "wash-sale-check", "tax-savings", "replacements"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000, // TLH can take longer for multiple tickers
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    });
    
    if (stderr) {
      console.error("Tax Loss Harvesting Module stderr:", stderr);
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
    console.error("Tax Loss Harvesting API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action
      },
      { status: 500 }
    );
  }
}
