import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const dynamic = "force-dynamic";

const QUANTCLAW_DATA_DIR = "/home/quant/apps/quantclaw-data";
const PYTHON = "python3";

/**
 * Neural Price Prediction API — LSTM/Statistical forecasting with uncertainty quantification
 * 
 * Endpoints:
 * - GET /api/v1/neural-prediction?action=predict&ticker=AAPL&horizon=5d — Price forecast
 * - GET /api/v1/neural-prediction?action=confidence&ticker=TSLA — Uncertainty analysis
 * - GET /api/v1/neural-prediction?action=comparison&ticker=NVDA — Model comparison
 * - GET /api/v1/neural-prediction?action=backtest&ticker=MSFT&years=1 — Historical accuracy
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get("action") || "predict";
  const ticker = request.nextUrl.searchParams.get("ticker") || "";
  const horizon = request.nextUrl.searchParams.get("horizon") || "5d";
  const years = request.nextUrl.searchParams.get("years") || "1";
  
  try {
    if (!ticker) {
      return NextResponse.json(
        { error: "ticker parameter required" },
        { status: 400 }
      );
    }
    
    let command: string;
    
    switch (action) {
      case "predict":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/neural_prediction.py predict-price ${ticker} --horizon ${horizon} --json`;
        break;
      
      case "confidence":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/neural_prediction.py prediction-confidence ${ticker} --json`;
        break;
      
      case "comparison":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/neural_prediction.py model-comparison ${ticker} --json`;
        break;
      
      case "backtest":
        command = `${PYTHON} ${QUANTCLAW_DATA_DIR}/modules/neural_prediction.py prediction-backtest ${ticker} --years ${years} --json`;
        break;
      
      default:
        return NextResponse.json(
          { 
            error: `Unknown action: ${action}`,
            available: ["predict", "confidence", "comparison", "backtest"]
          },
          { status: 400 }
        );
    }
    
    const { stdout, stderr } = await execAsync(command, { 
      timeout: 60000, // 60 seconds for ML models
      maxBuffer: 5 * 1024 * 1024 // 5MB buffer
    });
    
    if (stderr) {
      console.error("Neural Prediction Module stderr:", stderr);
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
    console.error("Neural Prediction API Error:", errorMessage);
    
    return NextResponse.json(
      { 
        error: errorMessage,
        action,
        ticker,
        horizon,
        years
      },
      { status: 500 }
    );
  }
}
