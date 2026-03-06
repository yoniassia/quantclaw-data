"""
Strategic Petroleum Reserve (SPR) Monitor — Track US SPR inventory levels,
weekly changes, historical drawdowns, and estimate days of import coverage.

Uses free EIA (Energy Information Administration) open data API.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


EIA_API_BASE = "https://api.eia.gov/v2"
# Free EIA API key (register at eia.gov — free tier)
DEFAULT_API_KEY = "demo"

SPR_SERIES = {
    "total": "PET.WCSSTUS1.W",        # Weekly US SPR stocks (thousand barrels)
    "sweet": "PET.W_EPC0_SAX_NUS_MBBL.W",  # SPR sweet crude
    "sour": "PET.W_EPC0_SAO_NUS_MBBL.W",   # SPR sour crude
}

# Historical context
HISTORICAL_PEAKS = {
    "all_time_high": {"date": "2010-01", "level_mb": 726.6},
    "pre_ukraine": {"date": "2022-03", "level_mb": 568.3},
    "post_release_low": {"date": "2023-07", "level_mb": 346.8},
}


def get_spr_current_level(api_key: str = DEFAULT_API_KEY) -> Dict:
    """
    Fetch current US Strategic Petroleum Reserve inventory level.

    Args:
        api_key: EIA API key (free registration at eia.gov)

    Returns:
        Dict with current level, weekly change, and historical context
    """
    url = (
        f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
        f"?api_key={api_key}&frequency=weekly&data[0]=value"
        f"&facets[product][]=EPC0&facets[process][]=SAX"
        f"&sort[0][column]=period&sort[0][direction]=desc&length=10"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        records = data.get("response", {}).get("data", [])
        if not records:
            return _fallback_spr_estimate()

        current = float(records[0].get("value", 0))
        previous = float(records[1].get("value", 0)) if len(records) > 1 else current
        weekly_change = current - previous

        return {
            "current_level_mb": round(current, 1),
            "weekly_change_mb": round(weekly_change, 1),
            "period": records[0].get("period", "unknown"),
            "all_time_high_mb": HISTORICAL_PEAKS["all_time_high"]["level_mb"],
            "pct_of_peak": round(current / HISTORICAL_PEAKS["all_time_high"]["level_mb"] * 100, 1),
            "days_import_cover": _estimate_import_cover(current),
            "source": "EIA",
            "retrieved_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return _fallback_spr_estimate()


def get_spr_history(periods: int = 52, api_key: str = DEFAULT_API_KEY) -> List[Dict]:
    """
    Fetch weekly SPR history for the specified number of periods.

    Args:
        periods: Number of weekly data points (default 52 = 1 year)
        api_key: EIA API key

    Returns:
        List of dicts with period and level
    """
    url = (
        f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
        f"?api_key={api_key}&frequency=weekly&data[0]=value"
        f"&facets[product][]=EPC0&facets[process][]=SAX"
        f"&sort[0][column]=period&sort[0][direction]=desc&length={periods}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        records = data.get("response", {}).get("data", [])
        return [
            {"period": r.get("period"), "level_mb": float(r.get("value", 0))}
            for r in records
        ]
    except Exception:
        return [{"error": "Failed to fetch SPR history"}]


def analyze_spr_trend(history: Optional[List[Dict]] = None) -> Dict:
    """
    Analyze SPR fill/draw trend and compute statistics.

    Args:
        history: Optional pre-fetched history; fetches if None

    Returns:
        Dict with trend direction, rate, and projected levels
    """
    if history is None:
        history = get_spr_history(periods=26)

    levels = [h["level_mb"] for h in history if "level_mb" in h and h["level_mb"] > 0]
    if len(levels) < 4:
        return {"error": "Insufficient data for trend analysis"}

    # Most recent first
    recent = levels[0]
    oldest = levels[-1]
    weeks = len(levels) - 1
    weekly_rate = (recent - oldest) / weeks

    if weekly_rate > 0.5:
        trend = "FILLING"
    elif weekly_rate < -0.5:
        trend = "DRAWING"
    else:
        trend = "STABLE"

    return {
        "trend": trend,
        "current_level_mb": round(recent, 1),
        "weekly_rate_mb": round(weekly_rate, 2),
        "annualized_rate_mb": round(weekly_rate * 52, 1),
        "period_high_mb": round(max(levels), 1),
        "period_low_mb": round(min(levels), 1),
        "weeks_analyzed": weeks,
        "projected_6mo_mb": round(recent + weekly_rate * 26, 1),
        "analyzed_at": datetime.utcnow().isoformat(),
    }


def _estimate_import_cover(level_mb: float) -> float:
    """Estimate days of net import coverage at ~6 mb/d net imports."""
    NET_IMPORTS_MBD = 6.0  # approximate US net crude imports
    return round(level_mb / NET_IMPORTS_MBD, 0)


def _fallback_spr_estimate() -> Dict:
    """Provide a fallback estimate when EIA API is unavailable."""
    return {
        "current_level_mb": 395.0,
        "note": "Estimate — EIA API unavailable. Check eia.gov for actuals.",
        "days_import_cover": 66,
        "source": "fallback_estimate",
        "retrieved_at": datetime.utcnow().isoformat(),
    }
