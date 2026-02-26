"""
Wage Growth Tracker — Module #280

Tracks wage growth metrics across multiple sources: Atlanta Fed Wage Growth Tracker,
BLS Employment Cost Index (ECI), Average Hourly Earnings, and real wage calculations.
Critical for inflation forecasting and Fed policy analysis.
"""

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = "DEMO_KEY"

# Key wage-related FRED series
WAGE_SERIES = {
    "avg_hourly_earnings": "CES0500000003",        # Avg hourly earnings, all private
    "avg_hourly_earnings_yoy": "CES0500000003",    # (compute YoY from this)
    "eci_total": "ECIALLCIV",                       # Employment Cost Index
    "eci_wages": "ECIWAG",                          # ECI - wages & salaries
    "eci_benefits": "ECIBEN",                       # ECI - benefits
    "real_earnings": "LES1252881600Q",              # Real median weekly earnings
    "unit_labor_costs": "ULCNFB",                   # Unit labor costs (nonfarm)
    "labor_productivity": "OPHNFB",                 # Output per hour (nonfarm)
    "median_usual_weekly": "LES1252881500Q",        # Median usual weekly earnings
    "cpi_urban": "CPIAUCSL",                        # CPI for real wage calc
}


def fetch_fred_series(
    series_id: str,
    api_key: str = FRED_API_KEY,
    limit: int = 60,
    frequency: Optional[str] = None,
) -> List[Dict]:
    """
    Fetch time series data from FRED.
    
    Args:
        series_id: FRED series identifier.
        api_key: FRED API key.
        limit: Number of observations.
        frequency: Optional frequency filter (m, q, a).
        
    Returns:
        List of dicts with date and value.
    """
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&api_key={api_key}&file_type=json"
        f"&sort_order=desc&limit={limit}"
    )
    if frequency:
        url += f"&frequency={frequency}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            observations = data.get("observations", [])
            return [
                {"date": obs["date"], "value": float(obs["value"])}
                for obs in observations
                if obs.get("value") not in (None, ".", "")
            ]
    except Exception as e:
        return [{"error": str(e)}]


def compute_yoy_change(series: List[Dict]) -> List[Dict]:
    """
    Compute year-over-year percentage change from a monthly/quarterly series.
    
    Args:
        series: List of dicts with date and value, sorted descending.
        
    Returns:
        List of dicts with date, value, and yoy_pct_change.
    """
    # Build lookup by date
    by_date = {obs["date"]: obs["value"] for obs in series if "value" in obs}
    results = []
    
    for obs in series:
        if "value" not in obs:
            continue
        date_str = obs["date"]
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year_ago = dt.replace(year=dt.year - 1)
            year_ago_str = year_ago.strftime("%Y-%m-%d")
            
            if year_ago_str in by_date and by_date[year_ago_str] > 0:
                yoy = ((obs["value"] / by_date[year_ago_str]) - 1) * 100
                results.append({
                    "date": date_str,
                    "value": obs["value"],
                    "yoy_pct_change": round(yoy, 2),
                })
        except (ValueError, KeyError):
            continue
    
    return results


def get_wage_dashboard(api_key: str = FRED_API_KEY) -> Dict:
    """
    Build comprehensive wage growth dashboard from FRED data.
    
    Returns:
        Dict with latest readings for all major wage metrics.
    """
    dashboard = {"computed_at": datetime.now().isoformat(), "metrics": {}}
    
    key_series = {
        "avg_hourly_earnings": "CES0500000003",
        "eci_total_comp": "ECIALLCIV",
        "eci_wages_salaries": "ECIWAG",
        "unit_labor_costs": "ULCNFB",
        "labor_productivity": "OPHNFB",
    }
    
    for label, sid in key_series.items():
        data = fetch_fred_series(sid, api_key, limit=24)
        if data and "error" not in data[0]:
            latest = data[0]
            yoy = compute_yoy_change(data)
            dashboard["metrics"][label] = {
                "latest_value": latest["value"],
                "latest_date": latest["date"],
                "yoy_change": yoy[0]["yoy_pct_change"] if yoy else None,
            }
    
    return dashboard


def real_wage_growth(api_key: str = FRED_API_KEY) -> Dict:
    """
    Calculate real (inflation-adjusted) wage growth.
    
    Compares nominal average hourly earnings growth vs CPI inflation
    to determine whether workers' purchasing power is increasing.
    
    Returns:
        Dict with nominal wage growth, CPI, and real wage growth.
    """
    wages = fetch_fred_series("CES0500000003", api_key, limit=24)
    cpi = fetch_fred_series("CPIAUCSL", api_key, limit=24)
    
    wage_yoy = compute_yoy_change(wages)
    cpi_yoy = compute_yoy_change(cpi)
    
    if not wage_yoy or not cpi_yoy:
        return {"error": "Insufficient data for real wage calculation"}
    
    nominal_growth = wage_yoy[0]["yoy_pct_change"]
    inflation = cpi_yoy[0]["yoy_pct_change"]
    real_growth = round(nominal_growth - inflation, 2)
    
    return {
        "nominal_wage_growth_yoy": nominal_growth,
        "cpi_inflation_yoy": inflation,
        "real_wage_growth_yoy": real_growth,
        "purchasing_power": "increasing" if real_growth > 0 else "decreasing",
        "wage_date": wage_yoy[0]["date"],
        "cpi_date": cpi_yoy[0]["date"],
        "computed_at": datetime.now().isoformat(),
    }


def wage_inflation_spiral_risk(api_key: str = FRED_API_KEY) -> Dict:
    """
    Assess wage-price spiral risk by comparing wage growth trends
    vs productivity growth and inflation expectations.
    
    Returns:
        Dict with spiral risk assessment metrics.
    """
    wages = fetch_fred_series("CES0500000003", api_key, limit=48)
    productivity = fetch_fred_series("OPHNFB", api_key, limit=24)
    ulc = fetch_fred_series("ULCNFB", api_key, limit=24)
    
    wage_yoy = compute_yoy_change(wages)
    ulc_yoy = compute_yoy_change(ulc)
    
    latest_wage = wage_yoy[0]["yoy_pct_change"] if wage_yoy else None
    latest_ulc = ulc_yoy[0]["yoy_pct_change"] if ulc_yoy else None
    
    # Simple spiral risk heuristic
    risk = "low"
    if latest_wage and latest_ulc:
        if latest_wage > 5 and latest_ulc > 4:
            risk = "high"
        elif latest_wage > 4 or latest_ulc > 3:
            risk = "moderate"
    
    return {
        "wage_growth_yoy": latest_wage,
        "unit_labor_cost_yoy": latest_ulc,
        "spiral_risk": risk,
        "note": "High risk = wages > 5% AND unit labor costs > 4% YoY",
        "computed_at": datetime.now().isoformat(),
    }
