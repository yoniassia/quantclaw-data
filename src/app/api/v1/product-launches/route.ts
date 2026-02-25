import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Product Launch Tracker API — Social Buzz, Pre-Order Velocity, Review Sentiment
 * 
 * Endpoints:
 * - GET /api/v1/product-launches?action=launch-summary&product=iPhone 16
 * - GET /api/v1/product-launches?action=buzz-tracking&product=Tesla Cybertruck
 * - GET /api/v1/product-launches?action=reddit-sentiment&product=PlayStation 5
 * - GET /api/v1/product-launches?action=news-coverage&product=Apple Vision Pro
 * - GET /api/v1/product-launches?action=preorder-velocity&product=Samsung Galaxy S24
 * - GET /api/v1/product-launches?action=trending-products&category=tech
 * 
 * Phase: 50
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "launch-summary";
  const product = request.nextUrl.searchParams.get("product") || "";
  const category = request.nextUrl.searchParams.get("category") || "tech";
  
  try {
    let command: string;
    
    switch (action) {
      case "launch-summary":
        if (!product) {
          return NextResponse.json(
            { error: "Product name required. Use ?product=iPhone 16" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py launch-summary "${product}"`;
        break;
      
      case "buzz-tracking":
        if (!product) {
          return NextResponse.json(
            { error: "Product name required" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py buzz-tracking "${product}"`;
        break;
      
      case "reddit-sentiment":
        if (!product) {
          return NextResponse.json(
            { error: "Product name required" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py reddit-sentiment "${product}"`;
        break;
      
      case "news-coverage":
        if (!product) {
          return NextResponse.json(
            { error: "Product name required" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py news-coverage "${product}"`;
        break;
      
      case "preorder-velocity":
        if (!product) {
          return NextResponse.json(
            { error: "Product name required" },
            { status: 400 }
          );
        }
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py preorder-velocity "${product}"`;
        break;
      
      case "trending-products":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/product_launches.py trending-products ${category}`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["launch-summary", "buzz-tracking", "reddit-sentiment", "news-coverage", "preorder-velocity", "trending-products"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 45000,  // 45 seconds (Google Trends can be slow)
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr && !stderr.includes("Fetching") && !stderr.includes("Analyzing")) {
      console.error("Product Launch Module stderr:", stderr);
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
    console.error("Product Launch API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        product,
        suggestion: "Make sure pytrends is installed: pip install pytrends"
      },
      { status: 500 }
    );
  }
}
