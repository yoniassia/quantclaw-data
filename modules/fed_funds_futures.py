"""
Fed Funds Futures Implied Rates — Module #217

Calculates implied Fed Funds target rates from CME Fed Funds futures prices.
Uses free FRED data for current effective rate and futures-implied probabilities.
Covers FOMC meeting expectations and rate path projections.
"""

import datetime
import json
import urllib.request
from typing import Dict, List, Optional


FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = "DEMO_KEY"

# FRED series for Fed Funds
SERIES = {
    "EFFR": "DFF",           # Daily effective federal funds rate
    "TARGET_UPPER": "DFEDTARU",  # Target range upper
    "TARGET_LOWER": "DFEDTARL",  # Target range lower
    "IORB": "IORB",          # Interest on reserve balances
}


def get_fed_funds_rate(api_key: str = FRED_API_KEY) -> Dict:
    """
    Fetch current effective federal funds rate and target range from FRED.
    
    Returns dict with effective_rate, target_upper, target_lower, as_of_date.
    """
    results = {}
    for label, series_id in SERIES.items():
        try:
            url = (
                f"{FRED_BASE}?series_id={series_id}"
                f"&api_key={api_key}&file_type=json"
                f"&sort_order=desc&limit=1"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                obs = data.get("observations", [])
                if obs and obs[0].get("value") != ".":
                    results[label.lower()] = float(obs[0]["value"])
                    results[f"{label.lower()}_date"] = obs[0]["date"]
        except Exception:
            results[label.lower()] = None
    return results


def implied_rate_from_futures_price(futures_price: float) -> float:
    """
    Convert Fed Funds futures price to implied rate.
    
    Formula: Implied Rate = 100 - Futures Price
    Example: Price of 95.25 implies 4.75% rate.
    
    Args:
        futures_price: The settlement/last price of the Fed Funds futures contract.
        
    Returns:
        Implied federal funds rate as a percentage.
    """
    return round(100.0 - futures_price, 4)


def rate_hike_probability(
    current_rate: float,
    implied_rate: float,
    hike_size: float = 0.25
) -> Dict[str, float]:
    """
    Calculate probability of a rate hike/cut at an FOMC meeting.
    
    Uses the simple CME FedWatch methodology:
    P(hike) = (implied_rate - current_rate) / hike_size
    
    Args:
        current_rate: Current effective or target midpoint rate.
        implied_rate: Rate implied by futures for the meeting month.
        hike_size: Standard rate move increment (default 25bp).
        
    Returns:
        Dict with probabilities for hold, hike, and cut scenarios.
    """
    diff = implied_rate - current_rate
    p_hike = max(0, min(1, diff / hike_size))
    p_cut = max(0, min(1, -diff / hike_size))
    p_hold = max(0, 1 - p_hike - p_cut)
    
    return {
        "current_rate": current_rate,
        "implied_rate": implied_rate,
        "probability_hold": round(p_hold * 100, 2),
        "probability_hike_25bp": round(p_hike * 100, 2),
        "probability_cut_25bp": round(p_cut * 100, 2),
        "expected_move_bp": round(diff * 100, 2),
    }


def build_rate_path(
    current_rate: float,
    futures_prices: List[Dict[str, float]],
) -> List[Dict]:
    """
    Build projected rate path from a series of monthly futures prices.
    
    Args:
        current_rate: Starting effective rate.
        futures_prices: List of dicts with 'month' (YYYY-MM) and 'price'.
        
    Returns:
        List of dicts with month, implied_rate, cumulative_change_bp.
    """
    path = []
    for fp in sorted(futures_prices, key=lambda x: x["month"]):
        implied = implied_rate_from_futures_price(fp["price"])
        change = round((implied - current_rate) * 100, 2)
        path.append({
            "month": fp["month"],
            "implied_rate": implied,
            "cumulative_change_bp": change,
            "implied_moves_25bp": round(change / 25, 1),
        })
    return path


def fomc_meeting_dates(year: int) -> List[str]:
    """
    Return scheduled FOMC meeting dates for a given year.
    Based on the standard 8-meeting-per-year schedule.
    
    Args:
        year: Calendar year.
        
    Returns:
        List of date strings (approximate, last day of 2-day meeting).
    """
    # Approximate FOMC schedule (actual dates vary)
    typical_months = [1, 3, 5, 6, 7, 9, 11, 12]
    # Meetings typically in the third week
    dates = []
    for month in typical_months:
        # Third Wednesday approximation
        d = datetime.date(year, month, 15)
        while d.weekday() != 2:  # Wednesday
            d += datetime.timedelta(days=1)
        dates.append(d.isoformat())
    return dates


def get_rate_expectations_summary(api_key: str = FRED_API_KEY) -> Dict:
    """
    Generate a summary of current Fed Funds rate and basic expectations.
    
    Returns:
        Dict with current rates, target range, and FOMC schedule.
    """
    rates = get_fed_funds_rate(api_key)
    now = datetime.datetime.now()
    schedule = fomc_meeting_dates(now.year)
    
    upper = rates.get("target_upper")
    lower = rates.get("target_lower")
    midpoint = None
    if upper is not None and lower is not None:
        midpoint = round((upper + lower) / 2, 4)
    
    return {
        "effective_rate": rates.get("effr"),
        "target_upper": upper,
        "target_lower": lower,
        "target_midpoint": midpoint,
        "iorb": rates.get("iorb"),
        "as_of_date": rates.get("effr_date"),
        "fomc_meetings_this_year": schedule,
        "next_meeting": next((d for d in schedule if d > now.strftime("%Y-%m-%d")), None),
    }
