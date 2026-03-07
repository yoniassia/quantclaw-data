#!/usr/bin/env python3
"""
Finnhub Bond API — Bonds, Yields & Fixed Income Data

Delivers bond profiles, historical prices, yield curves, and search across global fixed income markets.
Covers U.S. Treasuries, corporate bonds, municipals, and sovereign debt.

Key endpoints:
- /bond/profile?isin=... (coupon, maturity, ratings)
- /bond/price?isin=...&from=...&to=... (historical prices)
- /bond/yield-curve?country=... (yield curves)
- /search?q=... (bond search)

Source: https://finnhub.io/docs/api/bond-data
Category: Fixed Income & Bonds
Free tier: 60 calls/min (FINNHUB_API_KEY required)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load .env from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

def _api_call(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Internal API request helper with error handling
    """
    if not FINNHUB_API_KEY:
        return {"success": False, "error": "FINNHUB_API_KEY not found in .env"}
    
    if params is None:
        params = {}
    params["token"] = FINNHUB_API_KEY
    
    try:
        response = requests.get(f"{BASE_URL}/{endpoint.lstrip('/')}", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Finnhub error format
        if "error" in data:
            return {"success": False, "error": data.get("error", "API error")}
        
        return {"success": True, "data": data}
    
    except requests.RequestException as e:
        return {"success": False, "error": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON response"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_bond_profile(isin: str) -> Dict[str, Any]:
    """
    Get bond details: coupon, maturity date, ratings, issuer, etc.
    
    Args:
        isin: Bond ISIN (e.g., "US912828M802")
    
    Returns:
        Dict with profile data or error
    """
    return _api_call("bond/profile", {"isin": isin})

def get_bond_price(isin: str, from_timestamp: int, to_timestamp: int) -> Dict[str, Any]:
    """
    Get historical bond prices/yields.
    
    Args:
        isin: Bond ISIN
        from_timestamp: Unix timestamp (seconds)
        to_timestamp: Unix timestamp (seconds)
    
    Returns:
        Dict with price history list or error
    """
    return _api_call("bond/price", {
        "isin": isin,
        "from": from_timestamp,
        "to": to_timestamp
    })

def get_bond_yield_curve(country: str = "US") -> Dict[str, Any]:
    """
    Get treasury yield curve data for a country.
    
    Args:
        country: Country code (e.g., "US", "DE")
    
    Returns:
        Dict with yield curve data or error
    """
    return _api_call("bond/yield-curve", {"country": country})

def search_bonds(query: str) -> Dict[str, Any]:
    """
    Search bonds by name, issuer, or symbol.
    
    Args:
        query: Search term (e.g., "treasury", "Apple")
    
    Returns:
        Dict with result list (filtered to bonds) or error
    """
    result = _api_call("search", {"q": query})
    if result["success"]:
        # Filter to bonds if possible
        bonds = [item for item in result["data"].get("result", []) 
                if item.get("type") == "bond" or "bond" in item.get("symbol", "").lower()]
        result["data"] = {"bonds": bonds}
    return result

def date_to_unix(date_str: str) -> int:
    """
    Helper: Convert YYYY-MM-DD to Unix timestamp
    """
    return int(datetime.fromisoformat(f"{date_str}T00:00:00").timestamp())

def get_recent_prices(isin: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Convenience: Get recent prices (last N days)
    """
    now = int(datetime.now().timestamp())
    from_ts = int((datetime.now() - timedelta(days=days_back)).timestamp())
    return get_bond_price(isin, from_ts, now)

# Popular US Treasuries for testing
POPULAR_ISINS = {
    "US_10Y": "US91282CKQ2",  # Example 10Y Treasury
    "US912828M802": "US912828M802"
}

def list_popular_bonds() -> Dict[str, str]:
    """List popular bond ISINs"""
    return POPULAR_ISINS

if __name__ == "__main__":
    print("Finnhub Bond API - Ready")
    print(f"API Key loaded: {'Yes' if FINNHUB_API_KEY else 'No'}")
    print("\nAvailable functions:", [
        "get_bond_profile(isin)",
        "get_bond_price(isin, from_ts, to_ts)",
        "get_bond_yield_curve(country='US')",
        "search_bonds(query)",
        "get_recent_prices(isin, days=30)"
    ])
    print("\nTest US Treasury profile:")
    print(json.dumps(get_bond_profile("US912828M802"), indent=2, default=str))
