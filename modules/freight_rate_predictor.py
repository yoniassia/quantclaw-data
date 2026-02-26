"""Freight Rate Predictor — ML-based freight rate forecasting using free data.

Roadmap #331: Predicts freight rates using Baltic Dry Index from FRED,
container shipping indices, and simple ML models for trend forecasting.
"""

import json
import urllib.request
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Free FRED series for shipping/freight
FREIGHT_SERIES = {
    "DCOILBRENTEU": "Brent Crude Oil (fuel cost proxy)",
    "GSCPTOTL": "Global Supply Chain Pressure Index",
}

# Baltic indices from alternative free sources
BALTIC_DESCRIPTIONS = {
    "BDI": "Baltic Dry Index — dry bulk shipping rates",
    "BCI": "Baltic Capesize Index",
    "BPI": "Baltic Panamax Index",
    "BSI": "Baltic Supramax Index",
    "BHSI": "Baltic Handysize Index",
}


def get_freight_indicator(series_id: str, fred_api_key: str = "DEMO_KEY",
                          periods: int = 60) -> Dict:
    """Fetch a freight/shipping cost indicator from FRED.
    
    Args:
        series_id: FRED series ID
        fred_api_key: FRED API key
        periods: Number of observations
    
    Returns:
        Dict with time series data, trend, and forecast.
    """
    try:
        url = (f"{FRED_BASE}?series_id={series_id}"
               f"&api_key={fred_api_key}&file_type=json"
               f"&sort_order=desc&limit={periods}")
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        obs = data.get("observations", [])
        values = []
        for o in obs:
            try:
                values.append({"date": o["date"], "value": float(o["value"])})
            except (ValueError, KeyError):
                continue
        
        values.reverse()
        
        if not values:
            return {"series_id": series_id, "error": "No data"}
        
        latest = values[-1]["value"]
        
        # Simple moving averages
        vals = [v["value"] for v in values]
        sma_10 = sum(vals[-10:]) / min(len(vals), 10) if vals else None
        sma_30 = sum(vals[-30:]) / min(len(vals), 30) if len(vals) >= 10 else None
        
        # Linear regression forecast
        forecast = _linear_forecast(vals, periods_ahead=5)
        
        return {
            "series_id": series_id,
            "name": FREIGHT_SERIES.get(series_id, series_id),
            "latest": {"date": values[-1]["date"], "value": latest},
            "sma_10": round(sma_10, 2) if sma_10 else None,
            "sma_30": round(sma_30, 2) if sma_30 else None,
            "trend": "bullish" if sma_10 and sma_30 and sma_10 > sma_30 else "bearish",
            "forecast_5d": forecast,
            "observations": values[-30:],
            "source": "FRED"
        }
    except Exception as e:
        return {"series_id": series_id, "error": str(e)}


def supply_chain_pressure_index(fred_api_key: str = "DEMO_KEY") -> Dict:
    """Get the NY Fed Global Supply Chain Pressure Index.
    
    This is a key leading indicator for freight rates and shipping costs.
    Positive values = above-average pressure. Negative = below-average.
    
    Args:
        fred_api_key: FRED API key
    
    Returns:
        Dict with GSCPI data, interpretation, and forecast.
    """
    result = get_freight_indicator("GSCPTOTL", fred_api_key, periods=60)
    
    if "error" not in result and result.get("latest"):
        val = result["latest"]["value"]
        if val > 2:
            result["interpretation"] = "SEVERE supply chain stress — expect freight rate spikes"
        elif val > 1:
            result["interpretation"] = "ELEVATED pressure — freight rates likely rising"
        elif val > 0:
            result["interpretation"] = "ABOVE AVERAGE pressure — moderate freight cost risk"
        elif val > -1:
            result["interpretation"] = "BELOW AVERAGE — favorable shipping conditions"
        else:
            result["interpretation"] = "VERY LOW pressure — cheap freight rates expected"
        
        result["signal"] = "short_shippers" if val > 1.5 else "long_shippers" if val < -0.5 else "neutral"
    
    return result


def freight_rate_dashboard(fred_api_key: str = "DEMO_KEY") -> Dict:
    """Comprehensive freight rate dashboard combining multiple indicators.
    
    Args:
        fred_api_key: FRED API key
    
    Returns:
        Dict with all freight indicators and composite outlook.
    """
    indicators = {}
    
    for series_id in FREIGHT_SERIES:
        indicators[series_id] = get_freight_indicator(series_id, fred_api_key, 30)
    
    # Composite signal
    bullish = sum(1 for v in indicators.values() if v.get("trend") == "bullish")
    bearish = sum(1 for v in indicators.values() if v.get("trend") == "bearish")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "indicators": indicators,
        "composite_outlook": "rates_rising" if bullish > bearish else "rates_falling" if bearish > bullish else "mixed",
        "bullish_count": bullish,
        "bearish_count": bearish,
        "investable_signals": {
            "container_lines": "Overweight if rates rising (ZIM, MATX, DAC)",
            "shippers": "Overweight if rates falling (AMZN, WMT logistics benefit)",
            "air_freight": "Alternative play if ocean rates spike (ATSG, AAWW)",
        },
        "source": "FRED + QuantClaw Models"
    }


def _linear_forecast(values: List[float], periods_ahead: int = 5) -> List[Dict]:
    """Simple linear regression forecast."""
    n = len(values)
    if n < 5:
        return []
    
    # Use last 20 points for regression
    recent = values[-20:]
    n_r = len(recent)
    x_mean = (n_r - 1) / 2
    y_mean = sum(recent) / n_r
    
    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
    den = sum((i - x_mean) ** 2 for i in range(n_r))
    
    slope = num / den if den != 0 else 0
    intercept = y_mean - slope * x_mean
    
    forecasts = []
    for i in range(1, periods_ahead + 1):
        pred = intercept + slope * (n_r - 1 + i)
        forecasts.append({
            "period_ahead": i,
            "predicted_value": round(pred, 2),
            "direction": "up" if slope > 0 else "down"
        })
    
    return forecasts
