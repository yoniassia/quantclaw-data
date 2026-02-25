import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const PIPELINE_DIR = "/home/quant/.openclaw/workspace/skills/financial-data-pipeline";
const PYTHON = "/home/quant/.openclaw/fin-pipeline-env/bin/python";

const TOOL_MAP: Record<string, string> = {
  price: "price", options: "options", technicals: "technicals", news: "news",
  earnings: "earnings", dividends: "dividends", macro: "macro", crypto: "crypto",
  commodity: "commodity", forex: "forex", profile: "profile", ratings: "ratings",
  sec: "sec", social: "social", "short-interest": "short-interest",
  "etf-holdings": "etf", screener: "screen", esg: "esg",
  "fama-french": "fama-french", "factor-attribution": "factor-attribution",
  "factor-returns": "factor-returns",
  "13f": "13f", "13f-changes": "13f-changes", "smart-money": "smart-money",
  "top-funds": "top-funds",
  gex: "gex", "pin-risk": "pin-risk", "hedging-flow": "hedging-flow",
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tool: string }> }
) {
  const { tool } = await params;
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const cmd = TOOL_MAP[tool];
  if (!cmd) return NextResponse.json({ error: `Unknown tool: ${tool}`, available: Object.keys(TOOL_MAP) }, { status: 404 });
  try {
    const { stdout } = await execAsync(`${PYTHON} ${PIPELINE_DIR}/cli.py ${cmd} ${ticker} 2>/dev/null`, { timeout: 30000 });
    try { return NextResponse.json(JSON.parse(stdout)); } catch { return NextResponse.json({ result: stdout.trim() }); }
  } catch (e: unknown) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}
