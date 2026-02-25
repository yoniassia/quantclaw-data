#!/usr/bin/env python3
"""
Fed Policy Prediction Module — FOMC Analysis & Rate Hike Probability Scoring

Data Sources:
- FRED API: Fed funds rate, treasury yields, GDP, unemployment
- Yahoo Finance: Fed fund futures (ZQ=F) for implied rate probabilities
- Web scraping: FOMC calendar from federalreserve.gov
- Yield curve analysis: Implied rate path from treasury term structure

CME FedWatch-style probability calculation using fed fund futures
Dot plot analysis and consensus projection tracking

Author: QUANTCLAW DATA Build Agent
Phase: 45
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import sys
import re
from bs4 import BeautifulSoup


# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = ""  # Public access for basic queries

# FRED Series IDs for Fed Policy Data
FRED_SERIES = {
    "DFF": "Federal Funds Effective Rate",
    "DFEDTARU": "Federal Funds Target Rate - Upper Limit",
    "DFEDTARL": "Federal Funds Target Rate - Lower Limit",
    "DGS1": "1-Year Treasury Constant Maturity Rate",
    "DGS2": "2-Year Treasury Constant Maturity Rate",
    "DGS5": "5-Year Treasury Constant Maturity Rate",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DGS30": "30-Year Treasury Constant Maturity Rate",
    "T10Y2Y": "10-Year Treasury Minus 2-Year (Yield Curve)",
    "T10Y3M": "10-Year Treasury Minus 3-Month (Recession Indicator)",
    "UNRATE": "Unemployment Rate",
    "CPIAUCSL": "Consumer Price Index for All Urban Consumers",
    "GDP": "Gross Domestic Product",
}

# Fed Funds Futures Symbols (CME)
# ZQ=F is the front month fed funds futures
FED_FUTURES_SYMBOLS = ["ZQ=F", "ZQG25.CBT", "ZQH25.CBT", "ZQM25.CBT"]

# FOMC Meeting Schedule URL
FOMC_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"


def get_fred_series(series_id: str, lookback_days: int = 365) -> Dict:
    """
    Fetch FRED time series data
    Returns latest value and historical data
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
        }
        
        # Add API key if available
        if FRED_API_KEY:
            params["api_key"] = FRED_API_KEY
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "observations" in data:
                obs = [o for o in data["observations"] if o["value"] != "."]
                if obs:
                    latest = obs[-1]
                    
                    # Calculate change over period
                    if len(obs) > 1:
                        first_val = float(obs[0]["value"])
                        latest_val = float(latest["value"])
                        change = latest_val - first_val
                        change_pct = (change / first_val) * 100 if first_val != 0 else 0
                    else:
                        change = 0
                        change_pct = 0
                    
                    return {
                        "series_id": series_id,
                        "name": FRED_SERIES.get(series_id, series_id),
                        "value": float(latest["value"]),
                        "date": latest["date"],
                        "change": round(change, 4),
                        "change_pct": round(change_pct, 2),
                        "count": len(obs),
                        "history": [{"date": o["date"], "value": float(o["value"])} for o in obs[-30:]]  # Last 30 points
                    }
        
        return {"error": f"Failed to fetch {series_id}", "status_code": response.status_code}
    
    except Exception as e:
        return {"error": str(e), "series_id": series_id}


def get_current_fed_funds_rate() -> Dict:
    """
    Get current effective fed funds rate and target range
    """
    try:
        effective = get_fred_series("DFF", lookback_days=90)
        target_upper = get_fred_series("DFEDTARU", lookback_days=90)
        target_lower = get_fred_series("DFEDTARL", lookback_days=90)
        
        return {
            "effective_rate": effective.get("value"),
            "effective_date": effective.get("date"),
            "target_upper": target_upper.get("value"),
            "target_lower": target_lower.get("value"),
            "target_range": f"{target_lower.get('value')}-{target_upper.get('value')}%",
            "effective_change_30d": effective.get("change"),
            "data": {
                "effective": effective,
                "target_upper": target_upper,
                "target_lower": target_lower
            }
        }
    except Exception as e:
        return {"error": str(e)}


def get_yield_curve() -> Dict:
    """
    Fetch treasury yield curve and analyze for rate expectations
    Inverted curve signals recession risk
    """
    try:
        yields = {}
        maturities = {
            "DGS1": "1Y",
            "DGS2": "2Y",
            "DGS5": "5Y",
            "DGS10": "10Y",
            "DGS30": "30Y"
        }
        
        for series_id, label in maturities.items():
            data = get_fred_series(series_id, lookback_days=30)
            if "value" in data:
                yields[label] = {
                    "rate": data["value"],
                    "date": data["date"]
                }
        
        # Get spread indicators
        spread_10y2y = get_fred_series("T10Y2Y", lookback_days=30)
        spread_10y3m = get_fred_series("T10Y3M", lookback_days=30)
        
        # Determine curve shape
        if spread_10y2y.get("value", 0) < 0:
            curve_shape = "INVERTED (recession signal)"
        elif spread_10y2y.get("value", 0) < 0.25:
            curve_shape = "FLAT (caution)"
        else:
            curve_shape = "NORMAL (healthy)"
        
        return {
            "yields": yields,
            "spreads": {
                "10Y-2Y": {
                    "value": spread_10y2y.get("value"),
                    "date": spread_10y2y.get("date"),
                    "interpretation": curve_shape
                },
                "10Y-3M": {
                    "value": spread_10y3m.get("value"),
                    "date": spread_10y3m.get("date")
                }
            },
            "curve_shape": curve_shape,
            "rate_path_signal": _analyze_rate_path(yields)
        }
    except Exception as e:
        return {"error": str(e)}


def _analyze_rate_path(yields: Dict) -> str:
    """
    Analyze yield curve shape to determine implied rate path
    """
    if not yields or len(yields) < 3:
        return "Insufficient data"
    
    # Extract rates
    rates = {k: v["rate"] for k, v in yields.items() if "rate" in v}
    
    if "2Y" in rates and "10Y" in rates:
        if rates["2Y"] > rates["10Y"]:
            return "Market expects rate CUTS (inverted curve)"
        elif rates["10Y"] - rates["2Y"] > 1.0:
            return "Market expects rate HIKES (steep curve)"
        else:
            return "Market expects STABLE rates (flat curve)"
    
    return "Analysis pending"


def get_fed_funds_futures() -> Dict:
    """
    Fetch fed funds futures prices to calculate implied rate probabilities
    CME FedWatch-style calculation
    
    Formula: Implied Rate = 100 - Futures Price
    Probability of rate change = based on price movements
    """
    try:
        # Try ZQ=F (30-Day Federal Funds futures)
        ticker = yf.Ticker("ZQ=F")
        hist = ticker.history(period="1mo")
        
        if hist.empty:
            return {"error": "No futures data available", "note": "ZQ=F may not have live data"}
        
        latest_price = hist['Close'][-1]
        implied_rate = 100 - latest_price
        
        # Calculate change over last 5 days
        if len(hist) >= 5:
            price_5d_ago = hist['Close'][-5]
            rate_5d_ago = 100 - price_5d_ago
            rate_change = implied_rate - rate_5d_ago
        else:
            rate_change = 0
        
        # Get current effective rate for comparison
        current_rate_data = get_current_fed_funds_rate()
        current_rate = current_rate_data.get("effective_rate", 0)
        
        # Calculate probability of rate change
        # Simplified model: larger price movements suggest higher probability
        rate_diff = implied_rate - current_rate
        
        if abs(rate_diff) < 0.125:  # Less than 12.5 bps
            probability = {"hold": 85, "hike": 10, "cut": 5}
            scenario = "HOLD likely"
        elif rate_diff > 0.125:  # Implies higher future rate
            hike_prob = min(70, int(abs(rate_diff) * 100))
            probability = {"hold": 100 - hike_prob, "hike": hike_prob, "cut": 0}
            scenario = "HIKE expected"
        else:  # Implies lower future rate
            cut_prob = min(70, int(abs(rate_diff) * 100))
            probability = {"hold": 100 - cut_prob, "hike": 0, "cut": cut_prob}
            scenario = "CUT expected"
        
        return {
            "futures_price": round(latest_price, 4),
            "implied_rate": round(implied_rate, 4),
            "current_effective_rate": current_rate,
            "rate_differential": round(rate_diff, 4),
            "rate_change_5d": round(rate_change, 4),
            "probability": probability,
            "scenario": scenario,
            "date": hist.index[-1].strftime("%Y-%m-%d"),
            "data_source": "ZQ=F (30-Day Fed Funds Futures)"
        }
    except Exception as e:
        return {"error": str(e), "note": "Fed funds futures data may be limited"}


def scrape_fomc_calendar() -> Dict:
    """
    Scrape FOMC meeting calendar from Federal Reserve website
    """
    try:
        response = requests.get(FOMC_CALENDAR_URL, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find meeting dates (this is a simplified parser)
        # The Fed's site structure may change, so this is a best-effort scrape
        meetings = []
        
        # Look for panels or divs containing meeting information
        # Federal Reserve typically lists dates in specific formats
        date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}[-–]\d{1,2},?\s+\d{4}')
        
        text = soup.get_text()
        matches = date_pattern.findall(text)
        
        current_year = datetime.now().year
        
        for match in matches[:8]:  # Limit to next 8 meetings
            # Parse the date string
            date_str = match.strip()
            meetings.append({
                "date_range": date_str,
                "year": current_year,
                "type": "Scheduled FOMC Meeting"
            })
        
        # If scraping fails, provide fallback with typical schedule
        if not meetings:
            meetings = _get_typical_fomc_schedule()
        
        return {
            "upcoming_meetings": meetings,
            "next_meeting": meetings[0] if meetings else None,
            "total_meetings_per_year": 8,
            "source": "Federal Reserve Website",
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        # Fallback to typical schedule
        return {
            "upcoming_meetings": _get_typical_fomc_schedule(),
            "error": str(e),
            "note": "Using typical FOMC schedule as fallback"
        }


def _get_typical_fomc_schedule() -> List[Dict]:
    """
    FOMC typically meets 8 times per year, roughly every 6 weeks
    This is a fallback when scraping fails
    """
    current_date = datetime.now()
    meetings = []
    
    # FOMC typically meets in late Jan, mid-March, early May, mid-June, 
    # late July, mid-Sept, early Nov, mid-Dec
    typical_months = [
        (1, "late January"),
        (3, "mid-March"),
        (5, "early May"),
        (6, "mid-June"),
        (7, "late July"),
        (9, "mid-September"),
        (11, "early November"),
        (12, "mid-December")
    ]
    
    for month, description in typical_months:
        meeting_date = datetime(current_date.year, month, 15)
        if meeting_date > current_date:
            meetings.append({
                "date_range": description + f" {current_date.year}",
                "year": current_date.year,
                "type": "Typical FOMC Schedule (estimated)",
                "note": "Exact dates to be confirmed by Federal Reserve"
            })
    
    return meetings[:6]  # Return next 6 meetings


def get_dot_plot_analysis() -> Dict:
    """
    Analyze Fed's Summary of Economic Projections (SEP) dot plot
    The dot plot shows FOMC members' projections for fed funds rate
    
    Note: Actual dot plot data requires parsing Fed's quarterly SEP PDFs
    This provides a framework for analysis
    """
    try:
        # Get current rate
        current_data = get_current_fed_funds_rate()
        current_rate = current_data.get("effective_rate", 0)
        
        # Get implied future rate from futures
        futures_data = get_fed_funds_futures()
        implied_rate = futures_data.get("implied_rate", current_rate)
        
        # Analyze yield curve for long-term expectations
        yield_curve = get_yield_curve()
        long_term_signal = yield_curve.get("rate_path_signal", "")
        
        # Get macro indicators that influence Fed policy
        cpi = get_fred_series("CPIAUCSL", lookback_days=365)
        unemployment = get_fred_series("UNRATE", lookback_days=365)
        
        # Calculate inflation rate (year-over-year)
        if cpi.get("history") and len(cpi["history"]) >= 12:
            current_cpi = cpi["value"]
            cpi_12mo_ago = cpi["history"][0]["value"]
            inflation_rate = ((current_cpi - cpi_12mo_ago) / cpi_12mo_ago) * 100
        else:
            inflation_rate = None
        
        # Consensus projection (simplified model)
        if inflation_rate and inflation_rate > 3.0:
            consensus = "Hawkish (likely hikes ahead)"
            terminal_rate = current_rate + 0.50 if current_rate else 5.0
        elif inflation_rate and inflation_rate < 2.0 and unemployment.get("value", 4.0) > 4.5:
            consensus = "Dovish (likely cuts ahead)"
            terminal_rate = current_rate - 0.50 if current_rate else 4.0
        else:
            consensus = "Neutral (rates stable)"
            terminal_rate = current_rate if current_rate else 4.5
        
        return {
            "current_rate": current_rate,
            "implied_rate_from_futures": implied_rate,
            "consensus_projection": consensus,
            "terminal_rate_estimate": round(terminal_rate, 2) if terminal_rate else None,
            "inflation_rate_yoy": round(inflation_rate, 2) if inflation_rate else None,
            "unemployment_rate": unemployment.get("value"),
            "yield_curve_signal": long_term_signal,
            "data": {
                "cpi": cpi,
                "unemployment": unemployment
            },
            "note": "Actual dot plot data requires Fed SEP quarterly reports. Limited by FRED API access."
        }
    except Exception as e:
        return {"error": str(e)}


def fed_watch_comprehensive() -> Dict:
    """
    Comprehensive Fed policy watch combining all data sources
    """
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "fed_funds": get_current_fed_funds_rate(),
            "futures_probabilities": get_fed_funds_futures(),
            "yield_curve": get_yield_curve(),
            "fomc_calendar": scrape_fomc_calendar(),
            "dot_plot_analysis": get_dot_plot_analysis()
        }
    except Exception as e:
        return {"error": str(e)}


# CLI Interface
def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "fed-watch":
        # Comprehensive Fed policy watch
        data = fed_watch_comprehensive()
        print(json.dumps(data, indent=2))
        
    elif command == "rate-probability":
        # Calculate rate hike/cut probabilities from futures
        data = get_fed_funds_futures()
        print(json.dumps(data, indent=2))
        
    elif command == "fomc-calendar":
        # Show upcoming FOMC meetings
        data = scrape_fomc_calendar()
        print(json.dumps(data, indent=2))
        
    elif command == "dot-plot":
        # Dot plot analysis
        data = get_dot_plot_analysis()
        print(json.dumps(data, indent=2))
        
    elif command == "yield-curve":
        # Yield curve analysis
        data = get_yield_curve()
        print(json.dumps(data, indent=2))
        
    elif command == "current-rate":
        # Current fed funds rate
        data = get_current_fed_funds_rate()
        print(json.dumps(data, indent=2))
        
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return 1
    
    return 0


def print_help():
    """Print CLI help"""
    print("""
Fed Policy Prediction Module (Phase 45)

Commands:
  python cli.py fed-watch              # Comprehensive Fed policy analysis
  python cli.py rate-probability       # Calculate rate hike/cut probabilities
  python cli.py fomc-calendar          # Show upcoming FOMC meeting dates
  python cli.py dot-plot               # Dot plot consensus analysis
  python cli.py yield-curve            # Treasury yield curve analysis
  python cli.py current-rate           # Current fed funds rate & target range

Examples:
  python cli.py fed-watch              # Full Fed policy dashboard
  python cli.py rate-probability       # See probability of next rate change
  python cli.py fomc-calendar          # When is the next FOMC meeting?

Data Sources:
  - FRED API: Fed funds rate, treasury yields, macro indicators
  - Yahoo Finance: Fed funds futures (ZQ=F) for implied probabilities
  - Federal Reserve: FOMC meeting calendar
  - Yield Curve: Implied rate path from treasury term structure
""")


if __name__ == "__main__":
    sys.exit(main())
