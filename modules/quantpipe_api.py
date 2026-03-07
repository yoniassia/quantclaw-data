#!/usr/bin/env python3
"""
QuantPipe API — QuantClaw Data Module
QuantPipe is a 2026-launched free API for ML data pipelines tailored to factor-based investing.

Source: https://quantpipe.org/api-docs
Category: Quant Tools & ML
Free tier: true

Sample endpoint: GET https://api.quantpipe.org/factors?symbol=AAPL&model_type=ml_regression&start_date=2025-01-01
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "https://api.quantpipe.org"

def _make_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Internal request helper with error handling."""
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params or {}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "endpoint": endpoint,
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }

def get_factors(symbol: str, model_type: str = "ml_regression", start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch factors for symbol.
    
    Args:
        symbol: Stock ticker (e.g., AAPL)
        model_type: e.g., ml_regression
        start_date: YYYY-MM-DD
    
    Returns:
        Dict with factors data or error.
    """
    params = {"symbol": symbol, "model_type": model_type}
    if start_date:
        params["start_date"] = start_date
    return _make_request("factors", params)

def get_ml_predictions(symbol: str) -> Dict[str, Any]:
    """Fetch ML predictions for symbol."""
    return _make_request("ml_predictions", {"symbol": symbol})

def get_factor_returns(model_type: str) -> Dict[str, Any]:
    """Fetch factor returns for model type."""
    return _make_request("factor_returns", {"model_type": model_type})

def get_risk_decomposition(symbol: str) -> Dict[str, Any]:
    """Fetch risk decomposition for symbol."""
    return _make_request("risk_decomposition", {"symbol": symbol})

def get_sector_factors() -> Dict[str, Any]:
    """Fetch sector factors."""
    return _make_request("sector_factors")

def fetch_data() -> Dict[str, Any]:
    """Legacy fetch_data - use specific functions."""
    return {"status": "use specific functions like get_factors()"}

def get_latest() -> Dict[str, Any]:
    """Get latest data point - defaults to AAPL factors."""
    return get_factors("AAPL")

if __name__ == "__main__":
    print(json.dumps({"module": "quantpipe_api", "status": "ready"}, indent=2))
