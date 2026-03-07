"""
Finnhub Bond Yield API — Global Bond Market Data

Data Source: Finnhub.io
Update: Real-time during market hours
Coverage: US, EU, JP, UK, CN + major government & corporate bonds
Free tier: 60 calls/minute with free API key

Provides:
- Government bond yield curves (multiple maturities)
- Corporate bond yields by credit rating
- Yield spreads (e.g., 2Y-10Y for recession signals)
- Historical yield trends for technical analysis

Usage as Indicator:
- Inverted yield curve (2Y > 10Y) → Recession warning
- Rising corporate spreads → Credit stress
- Falling yields → Flight to safety
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# API Configuration
API_BASE = "https://finnhub.io/api/v1"
API_KEY = os.environ.get("FINNHUB_API_KEY", "sandbox")

# Standard maturity mappings for yield curves
MATURITY_MAP = {
    "1M": "1 Month",
    "3M": "3 Month", 
    "6M": "6 Month",
    "1Y": "1 Year",
    "2Y": "2 Year",
    "3Y": "3 Year",
    "5Y": "5 Year",
    "7Y": "7 Year",
    "10Y": "10 Year",
    "20Y": "20 Year",
    "30Y": "30 Year"
}

def _make_request(endpoint: str, params: Dict) -> Dict:
    """
    Internal helper to make Finnhub API requests with error handling.
    
    Args:
        endpoint: API endpoint path (e.g., '/bond/yield-curve')
        params: Query parameters dict
        
    Returns:
        Parsed JSON response or error dict
    """
    params['token'] = API_KEY
    url = f"{API_BASE}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "endpoint": endpoint}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}", "endpoint": endpoint}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "endpoint": endpoint}


def get_yield_curve(country: str = "US") -> Dict:
    """
    Get government bond yield curve for specified country.
    
    Args:
        country: ISO 2-letter country code (US, GB, JP, DE, etc.)
        
    Returns:
        Dict with yield curve data:
        {
            "country": "US",
            "date": "2026-03-07",
            "yields": {
                "1M": 4.25,
                "3M": 4.35,
                "6M": 4.40,
                "1Y": 4.45,
                "2Y": 4.50,
                "5Y": 4.60,
                "10Y": 4.65,
                "30Y": 4.80
            },
            "inverted": false,
            "spread_2y_10y": 0.15
        }
    """
    data = _make_request("/bond/yield-curve", {"country": country.upper()})
    
    if "error" in data:
        return data
    
    # Finnhub returns array of yield points
    # Structure: [{"maturity": "1M", "yield": 4.25}, ...]
    yields = {}
    for point in data.get("data", []):
        maturity = point.get("maturity", "")
        yield_value = point.get("yield")
        if maturity and yield_value is not None:
            yields[maturity] = yield_value
    
    # Calculate key metrics
    y2 = yields.get("2Y")
    y10 = yields.get("10Y")
    spread_2y_10y = None
    inverted = False
    
    if y2 is not None and y10 is not None:
        spread_2y_10y = round(y10 - y2, 2)
        inverted = spread_2y_10y < 0
    
    return {
        "country": country.upper(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "yields": yields,
        "inverted": inverted,
        "spread_2y_10y": spread_2y_10y,
        "source": "finnhub"
    }


def get_government_bond_yield(country: str = "US") -> Dict:
    """
    Get current government bond yields (alias for get_yield_curve with cleaner output).
    
    Args:
        country: ISO 2-letter country code
        
    Returns:
        Dict with current yields across all maturities
    """
    curve_data = get_yield_curve(country)
    
    if "error" in curve_data:
        return curve_data
    
    return {
        "country": curve_data["country"],
        "date": curve_data["date"],
        "yields": curve_data["yields"],
        "benchmark_10y": curve_data["yields"].get("10Y"),
        "inverted": curve_data["inverted"],
        "source": "finnhub"
    }


def get_corporate_bond_yield(rating: Optional[str] = None) -> Dict:
    """
    Get corporate bond yield data by credit rating.
    
    Note: Finnhub free tier may have limited corporate bond data.
    This function attempts to fetch via bond profile endpoint.
    
    Args:
        rating: Credit rating filter (AAA, AA, A, BBB, BB, B, CCC, etc.)
        
    Returns:
        Dict with corporate yield data or message about data availability
    """
    # Finnhub's corporate bond data is primarily via bond profile endpoint
    # which requires specific ISIN codes. For free tier, we return a structured
    # response indicating data limitations.
    
    return {
        "rating": rating,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "message": "Corporate bond yields require specific ISIN codes via /bond/profile endpoint",
        "note": "Free tier has limited corporate bond coverage. Consider using /bond/profile with specific ISINs",
        "example_isins": {
            "US_Treasury": "US912828ZT42",
            "Corporate": "Contact Finnhub for corporate ISIN database"
        },
        "source": "finnhub"
    }


def get_yield_spread(short_term: str = "2Y", long_term: str = "10Y", country: str = "US") -> Dict:
    """
    Calculate yield spread between two maturities (e.g., 2Y-10Y for recession signal).
    
    Args:
        short_term: Short maturity (e.g., "2Y", "3M")
        long_term: Long maturity (e.g., "10Y", "30Y")
        country: Country code
        
    Returns:
        Dict with spread calculation and signal:
        {
            "spread": 0.15,
            "short_term": {"maturity": "2Y", "yield": 4.50},
            "long_term": {"maturity": "10Y", "yield": 4.65},
            "inverted": false,
            "signal": "normal"
        }
    """
    curve_data = get_yield_curve(country)
    
    if "error" in curve_data:
        return curve_data
    
    yields = curve_data.get("yields", {})
    short_yield = yields.get(short_term.upper())
    long_yield = yields.get(long_term.upper())
    
    if short_yield is None or long_yield is None:
        return {
            "error": f"Missing yield data for {short_term} or {long_term}",
            "available_maturities": list(yields.keys()),
            "country": country.upper()
        }
    
    spread = round(long_yield - short_yield, 2)
    inverted = spread < 0
    
    # Signal interpretation
    if inverted:
        signal = "inverted_curve_recession_warning"
    elif spread < 0.25:
        signal = "flattening_watch"
    elif spread > 1.5:
        signal = "steep_curve_growth_mode"
    else:
        signal = "normal"
    
    return {
        "country": country.upper(),
        "date": curve_data["date"],
        "spread": spread,
        "short_term": {
            "maturity": short_term.upper(),
            "yield": short_yield
        },
        "long_term": {
            "maturity": long_term.upper(),
            "yield": long_yield
        },
        "inverted": inverted,
        "signal": signal,
        "source": "finnhub"
    }


def get_historical_yields(country: str = "US", months: int = 12) -> List[Dict]:
    """
    Get historical yield curve data (note: requires time-series endpoint access).
    
    Args:
        country: Country code
        months: Number of months of historical data
        
    Returns:
        List of historical yield snapshots
        
    Note: Finnhub free tier may have limited historical data access.
    This function returns a structured response indicating data availability.
    """
    # Finnhub's historical bond data typically requires premium access
    # For free tier, we provide current snapshot and guidance
    
    current = get_yield_curve(country)
    
    return [
        {
            "date": current.get("date"),
            "yields": current.get("yields"),
            "note": "Historical yield data requires Finnhub premium tier or time-series endpoints",
            "current_data_only": True,
            "requested_months": months,
            "source": "finnhub"
        }
    ]


def get_latest() -> Dict:
    """
    Get summary of latest bond market metrics across key indicators.
    
    Returns:
        Dict with key bond metrics:
        - US yield curve
        - Inversion status
        - 2Y-10Y spread
        - Key yield levels
    """
    us_curve = get_yield_curve("US")
    spread_2y_10y = get_yield_spread("2Y", "10Y", "US")
    
    if "error" in us_curve:
        return {
            "error": "Unable to fetch latest bond data",
            "details": us_curve.get("error"),
            "timestamp": datetime.now().isoformat()
        }
    
    yields = us_curve.get("yields", {})
    
    return {
        "timestamp": datetime.now().isoformat(),
        "date": us_curve.get("date"),
        "us_treasury": {
            "3M": yields.get("3M"),
            "2Y": yields.get("2Y"),
            "10Y": yields.get("10Y"),
            "30Y": yields.get("30Y")
        },
        "spreads": {
            "2Y_10Y": spread_2y_10y.get("spread"),
            "inverted": spread_2y_10y.get("inverted"),
            "signal": spread_2y_10y.get("signal")
        },
        "curve_shape": "inverted" if us_curve.get("inverted") else "normal",
        "source": "finnhub",
        "api_key_status": "configured" if API_KEY != "sandbox" else "sandbox_mode"
    }


# CLI test interface
if __name__ == "__main__":
    print("Testing Finnhub Bond Yield API Module")
    print("=" * 50)
    
    # Test 1: Get latest summary
    print("\n1. Latest bond metrics:")
    latest = get_latest()
    print(json.dumps(latest, indent=2))
    
    # Test 2: Yield curve
    print("\n2. US Yield Curve:")
    curve = get_yield_curve("US")
    print(json.dumps(curve, indent=2))
    
    # Test 3: Yield spread
    print("\n3. 2Y-10Y Spread:")
    spread = get_yield_spread("2Y", "10Y")
    print(json.dumps(spread, indent=2))
