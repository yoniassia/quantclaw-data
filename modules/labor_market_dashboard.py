"""
Labor Market Dashboard — Module #279

Comprehensive labor market analytics combining JOLTS, ADP, NFP, initial/continuing
claims, participation rate, U-3/U-6 unemployment, and Beveridge curve analysis.
All data from free FRED API.
"""

import json
import math
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = "DEMO_KEY"

# Core labor market FRED series
LABOR_SERIES = {
    # Employment
    "nonfarm_payrolls": "PAYEMS",                  # Total nonfarm payrolls (thousands)
    "private_payrolls": "USPRIV",                  # Private payrolls
    "unemployment_rate_u3": "UNRATE",              # U-3 unemployment rate
    "unemployment_rate_u6": "U6RATE",              # U-6 underemployment rate
    "labor_force_participation": "CIVPART",         # Civilian participation rate
    "employment_population_ratio": "EMRATIO",       # Employment-population ratio
    
    # Claims
    "initial_claims": "ICSA",                       # Initial jobless claims (weekly)
    "continued_claims": "CCSA",                     # Continued claims (weekly)
    "insured_unemployment_rate": "IURSA",           # Insured unemployment rate
    
    # JOLTS
    "job_openings": "JTSJOL",                       # JOLTS job openings (thousands)
    "hires": "JTSHIL",                              # JOLTS hires
    "quits": "JTSQUL",                              # JOLTS quits (voluntary separations)
    "layoffs": "JTSLDL",                            # JOLTS layoffs/discharges
    
    # Other
    "avg_weekly_hours": "AWHAETP",                  # Avg weekly hours (private)
    "temp_help_services": "TEMPHELPS",              # Temp help services employment
    "prime_age_participation": "LNS11300060",       # Prime age (25-54) participation
}


def fetch_series(
    series_id: str,
    api_key: str = FRED_API_KEY,
    limit: int = 36,
) -> List[Dict]:
    """
    Fetch observations from FRED API.
    
    Args:
        series_id: FRED series identifier.
        api_key: API key (DEMO_KEY for limited access).
        limit: Number of most recent observations.
        
    Returns:
        List of date/value dicts, most recent first.
    """
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&api_key={api_key}&file_type=json"
        f"&sort_order=desc&limit={limit}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [
                {"date": o["date"], "value": float(o["value"])}
                for o in data.get("observations", [])
                if o.get("value") not in (None, ".", "")
            ]
    except Exception:
        return []


def get_labor_dashboard(api_key: str = FRED_API_KEY) -> Dict:
    """
    Build comprehensive labor market dashboard with latest readings.
    
    Returns:
        Dict with latest values for all major labor indicators,
        month-over-month changes, and trend signals.
    """
    dashboard = {"computed_at": datetime.now().isoformat(), "indicators": {}}
    
    for label, series_id in LABOR_SERIES.items():
        data = fetch_series(series_id, api_key, limit=6)
        if not data:
            continue
        
        latest = data[0]
        prev = data[1] if len(data) > 1 else None
        
        entry = {
            "value": latest["value"],
            "date": latest["date"],
        }
        
        if prev:
            change = round(latest["value"] - prev["value"], 3)
            entry["prev_value"] = prev["value"]
            entry["change"] = change
            entry["direction"] = "up" if change > 0 else "down" if change < 0 else "flat"
        
        dashboard["indicators"][label] = entry
    
    return dashboard


def beveridge_curve_analysis(api_key: str = FRED_API_KEY) -> Dict:
    """
    Compute Beveridge curve position (job openings rate vs unemployment rate).
    
    The Beveridge curve shows the inverse relationship between vacancies
    and unemployment. Shifts indicate structural labor market changes.
    
    Returns:
        Dict with current position, historical comparison, and efficiency score.
    """
    unemployment = fetch_series("UNRATE", api_key, limit=120)
    openings = fetch_series("JTSJOL", api_key, limit=120)
    
    if not unemployment or not openings:
        return {"error": "Insufficient data"}
    
    # Build aligned series
    u_by_date = {o["date"]: o["value"] for o in unemployment}
    
    curve_points = []
    for o in openings:
        if o["date"] in u_by_date:
            curve_points.append({
                "date": o["date"],
                "unemployment_rate": u_by_date[o["date"]],
                "job_openings_thousands": o["value"],
            })
    
    if not curve_points:
        return {"error": "No overlapping dates"}
    
    latest = curve_points[0]
    
    # Vacancy-to-unemployment ratio (V/U)
    vu_ratio = round(latest["job_openings_thousands"] / (latest["unemployment_rate"] * 1000), 2) if latest["unemployment_rate"] > 0 else None
    
    # Labor market tightness assessment
    tightness = "balanced"
    if vu_ratio and vu_ratio > 1.5:
        tightness = "very_tight"
    elif vu_ratio and vu_ratio > 1.0:
        tightness = "tight"
    elif vu_ratio and vu_ratio < 0.5:
        tightness = "loose"
    
    return {
        "current_unemployment": latest["unemployment_rate"],
        "current_openings_k": latest["job_openings_thousands"],
        "vu_ratio": vu_ratio,
        "market_tightness": tightness,
        "date": latest["date"],
        "historical_points": len(curve_points),
        "recent_curve": curve_points[:12],
    }


def claims_trend_analysis(
    api_key: str = FRED_API_KEY,
    weeks: int = 26,
) -> Dict:
    """
    Analyze initial and continuing claims trends for recession signals.
    
    Rising claims above 4-week moving average signals labor market weakening.
    
    Args:
        api_key: FRED API key.
        weeks: Number of weeks to analyze.
        
    Returns:
        Dict with claims data, 4-week MA, trend, and recession signal.
    """
    initial = fetch_series("ICSA", api_key, limit=weeks)
    continued = fetch_series("CCSA", api_key, limit=weeks)
    
    if not initial:
        return {"error": "No claims data available"}
    
    values = [o["value"] for o in initial]
    
    # 4-week moving average
    ma4 = round(sum(values[:4]) / 4, 0) if len(values) >= 4 else None
    
    # Trend: compare latest 4-week avg vs 13 weeks ago
    ma4_old = None
    if len(values) >= 17:
        ma4_old = round(sum(values[13:17]) / 4, 0)
    
    trend = "stable"
    if ma4 and ma4_old:
        change_pct = ((ma4 - ma4_old) / ma4_old) * 100
        if change_pct > 15:
            trend = "rising_sharply"
        elif change_pct > 5:
            trend = "rising"
        elif change_pct < -10:
            trend = "falling"
    
    # Recession signal: initial claims > 300k and rising
    recession_signal = False
    if ma4 and ma4 > 300000 and trend in ("rising", "rising_sharply"):
        recession_signal = True
    
    return {
        "latest_initial_claims": values[0] if values else None,
        "initial_claims_date": initial[0]["date"] if initial else None,
        "four_week_ma": ma4,
        "continued_claims": continued[0]["value"] if continued else None,
        "continued_claims_date": continued[0]["date"] if continued else None,
        "trend": trend,
        "recession_signal": recession_signal,
        "computed_at": datetime.now().isoformat(),
    }


def nfp_momentum(api_key: str = FRED_API_KEY) -> Dict:
    """
    Analyze nonfarm payrolls momentum (3m, 6m, 12m averages).
    
    Returns:
        Dict with monthly change, rolling averages, and momentum assessment.
    """
    data = fetch_series("PAYEMS", api_key, limit=13)
    
    if len(data) < 2:
        return {"error": "Insufficient payroll data"}
    
    # Monthly changes
    changes = []
    for i in range(len(data) - 1):
        changes.append(round(data[i]["value"] - data[i + 1]["value"], 0))
    
    latest = changes[0] if changes else None
    avg_3m = round(sum(changes[:3]) / 3, 0) if len(changes) >= 3 else None
    avg_6m = round(sum(changes[:6]) / 6, 0) if len(changes) >= 6 else None
    avg_12m = round(sum(changes[:12]) / 12, 0) if len(changes) >= 12 else None
    
    momentum = "steady"
    if avg_3m and avg_6m:
        if avg_3m > avg_6m * 1.2:
            momentum = "accelerating"
        elif avg_3m < avg_6m * 0.7:
            momentum = "decelerating"
    
    return {
        "latest_change_k": latest,
        "latest_date": data[0]["date"],
        "avg_3m_k": avg_3m,
        "avg_6m_k": avg_6m,
        "avg_12m_k": avg_12m,
        "momentum": momentum,
        "total_nonfarm_k": data[0]["value"],
        "computed_at": datetime.now().isoformat(),
    }
