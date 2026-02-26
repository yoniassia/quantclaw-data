"""Job Posting Analyzer — Track hiring trends as economic signals from free sources.

Roadmap #324: Analyzes job posting trends from Indeed/LinkedIn proxies using
free BLS JOLTS data, FRED hiring indicators, and public job board APIs.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Key FRED series for labor market / hiring signals
HIRING_SERIES = {
    "JTSJOL": "JOLTS Job Openings (Total Nonfarm)",
    "JTSQUL": "JOLTS Quits (Total Nonfarm)",
    "JTSHIL": "JOLTS Hires (Total Nonfarm)",
    "ICSA": "Initial Jobless Claims (Weekly)",
    "CCSA": "Continued Claims",
    "PAYEMS": "Total Nonfarm Payrolls",
    "UNRATE": "Unemployment Rate",
    "LNS14000006": "Black/African American Unemployment Rate",
    "CEU0500000003": "Average Hourly Earnings (Private)",
    "AWHNONAG": "Average Weekly Hours (Nonfarm)",
}

# Sector mapping for JOLTS
SECTOR_JOLTS = {
    "technology": "JTS510000000000000JOL",
    "healthcare": "JTS620000000000000JOL",
    "finance": "JTS520000000000000JOL",
    "manufacturing": "JTS300000000000000JOL",
    "retail": "JTS440000000000000JOL",
    "construction": "JTS230000000000000JOL",
    "government": "JTS900000000000000JOL",
}


def get_hiring_indicator(series_id: str, fred_api_key: str = "DEMO_KEY",
                         periods: int = 24) -> Dict:
    """Fetch a hiring/labor market indicator from FRED.
    
    Args:
        series_id: FRED series ID (e.g. 'JTSJOL' for JOLTS openings)
        fred_api_key: FRED API key (free at fred.stlouisfed.org)
        periods: Number of recent observations to return
    
    Returns:
        Dict with series data, latest value, and trend.
    """
    try:
        url = (f"{FRED_BASE}?series_id={series_id}"
               f"&api_key={fred_api_key}&file_type=json"
               f"&sort_order=desc&limit={periods}")
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        obs = data.get("observations", [])
        if not obs:
            return {"series_id": series_id, "error": "No data returned"}
        
        values = []
        for o in obs:
            try:
                values.append({"date": o["date"], "value": float(o["value"])})
            except (ValueError, KeyError):
                continue
        
        values.reverse()  # Chronological order
        
        latest = values[-1] if values else None
        prev = values[-2] if len(values) >= 2 else None
        
        mom_change = None
        if latest and prev and prev["value"] != 0:
            mom_change = round((latest["value"] - prev["value"]) / prev["value"] * 100, 2)
        
        return {
            "series_id": series_id,
            "name": HIRING_SERIES.get(series_id, series_id),
            "latest": latest,
            "previous": prev,
            "mom_change_pct": mom_change,
            "trend": "improving" if mom_change and mom_change > 0 else "weakening" if mom_change and mom_change < 0 else "flat",
            "observations": values[-12:],  # Last 12 for charting
            "total_fetched": len(values)
        }
    except Exception as e:
        return {"series_id": series_id, "error": str(e)}


def labor_market_dashboard(fred_api_key: str = "DEMO_KEY") -> Dict:
    """Get a comprehensive labor market dashboard from FRED data.
    
    Returns latest values for all key hiring indicators.
    
    Args:
        fred_api_key: FRED API key
    
    Returns:
        Dict with all indicators and an overall health assessment.
    """
    indicators = {}
    positive_signals = 0
    negative_signals = 0
    
    for series_id, name in HIRING_SERIES.items():
        result = get_hiring_indicator(series_id, fred_api_key, periods=6)
        indicators[series_id] = result
        
        if result.get("trend") == "improving":
            # For unemployment/claims, improving means going DOWN
            if series_id in ("UNRATE", "ICSA", "CCSA", "LNS14000006"):
                negative_signals += 1  # Higher unemployment = negative
            else:
                positive_signals += 1
        elif result.get("trend") == "weakening":
            if series_id in ("UNRATE", "ICSA", "CCSA", "LNS14000006"):
                positive_signals += 1  # Lower unemployment = positive
            else:
                negative_signals += 1
    
    total = positive_signals + negative_signals
    health = "strong" if total > 0 and positive_signals / total > 0.6 else \
             "weak" if total > 0 and negative_signals / total > 0.6 else "mixed"
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "indicators": indicators,
        "positive_signals": positive_signals,
        "negative_signals": negative_signals,
        "overall_health": health,
        "source": "FRED (Federal Reserve Economic Data)"
    }


def sector_job_openings(sector: str, fred_api_key: str = "DEMO_KEY",
                        periods: int = 24) -> Dict:
    """Get JOLTS job openings for a specific sector.
    
    Args:
        sector: Sector name (technology, healthcare, finance, manufacturing, retail, construction, government)
        fred_api_key: FRED API key
        periods: Number of observations
    
    Returns:
        Dict with sector hiring data and trend.
    """
    sector_lower = sector.lower()
    series_id = SECTOR_JOLTS.get(sector_lower)
    
    if not series_id:
        return {
            "error": f"Unknown sector: {sector}",
            "available_sectors": list(SECTOR_JOLTS.keys())
        }
    
    result = get_hiring_indicator(series_id, fred_api_key, periods)
    result["sector"] = sector_lower
    return result
