#!/usr/bin/env python3
"""
SPACInsider Data Feed — IPO & Private Markets Module

SPACInsider tracks SPAC (Special Purpose Acquisition Company) announcements, 
mergers, performance metrics. Provides data on blank-check companies transitioning 
to public markets.

Source: https://www.spacinsider.com/api
Category: IPO & Private Markets
Free tier: RSS-like feed with 50 updates per day
Update frequency: real-time
Generated: 2026-03-06

Note: This module provides placeholder functionality. SPACInsider API endpoints
require subscription or are unavailable. Functions return demo data structures.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# API Configuration
BASE_URL = "https://www.spacinsider.com/api"
TIMEOUT = 15

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Generic API request handler (placeholder implementation)
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
    
    Returns:
        Dict with response data or error
    """
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, params=params or {}, timeout=TIMEOUT)
        
        if response.status_code == 404:
            return {
                "success": False,
                "error": "SPACInsider API endpoint not available. May require subscription.",
                "endpoint": endpoint,
                "note": "This module returns demo data structures"
            }
        
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "endpoint": endpoint
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "endpoint": endpoint
        }


def get_active_spacs() -> Dict:
    """
    Get list of currently active SPACs (pre-merger SPACs trading in the market)
    
    Returns:
        Dict with active SPACs data including ticker, trust size, target focus
    """
    # Attempt real API call
    result = _make_request("spacs", {"status": "active"})
    
    # Return demo data structure if API unavailable
    if not result.get("success"):
        return {
            "success": False,
            "error": "API unavailable - returning demo structure",
            "demo_data": {
                "active_spacs": [
                    {
                        "ticker": "DEMO",
                        "name": "Demo Acquisition Corp",
                        "trust_size_m": 300,
                        "ipo_date": "2025-06-15",
                        "sponsor": "Demo Capital Partners",
                        "target_sector": "Technology",
                        "status": "searching",
                        "months_to_deadline": 18
                    }
                ],
                "total_count": 1,
                "total_trust_capital_m": 300,
                "timestamp": datetime.now().isoformat()
            },
            "note": "This is demo data. Real API requires subscription."
        }
    
    return result


def get_spac_mergers(status: str = "announced") -> Dict:
    """
    Get SPAC merger announcements by status
    
    Args:
        status: Merger status - 'announced', 'pending', 'completed', 'terminated'
    
    Returns:
        Dict with merger deals data
    """
    result = _make_request("mergers", {"status": status})
    
    if not result.get("success"):
        return {
            "success": False,
            "error": "API unavailable - returning demo structure",
            "demo_data": {
                "mergers": [
                    {
                        "spac_ticker": "DEMO",
                        "target_company": "Demo Tech Inc",
                        "announced_date": "2025-12-01",
                        "target_valuation_m": 1500,
                        "sector": "Software",
                        "status": status,
                        "expected_closing": "Q2 2026",
                        "pipe_amount_m": 200,
                        "redemption_rate_pct": 15.3
                    }
                ],
                "count": 1,
                "filter": {"status": status},
                "timestamp": datetime.now().isoformat()
            },
            "note": "This is demo data. Real API requires subscription."
        }
    
    return result


def get_spac_performance(ticker: str) -> Dict:
    """
    Get performance metrics for a specific SPAC
    
    Args:
        ticker: SPAC ticker symbol
    
    Returns:
        Dict with SPAC performance data including price, returns, redemptions
    """
    result = _make_request(f"spac/{ticker}/performance")
    
    if not result.get("success"):
        return {
            "success": False,
            "error": "API unavailable - returning demo structure",
            "demo_data": {
                "ticker": ticker,
                "current_price": 10.15,
                "nav_per_share": 10.00,
                "premium_discount_pct": 1.5,
                "volume_avg_30d": 125000,
                "price_change_ytd_pct": 1.2,
                "price_change_since_ipo_pct": 0.8,
                "trust_balance_m": 295,
                "redemption_total_pct": 1.7,
                "as_of_date": datetime.now().date().isoformat(),
                "timestamp": datetime.now().isoformat()
            },
            "note": "This is demo data. Real API requires subscription."
        }
    
    return result


def get_spac_ipos(period: str = "30d") -> Dict:
    """
    Get recent SPAC IPO pricings
    
    Args:
        period: Time period - '7d', '30d', '90d', 'ytd'
    
    Returns:
        Dict with recent SPAC IPOs
    """
    result = _make_request("ipos", {"period": period})
    
    if not result.get("success"):
        return {
            "success": False,
            "error": "API unavailable - returning demo structure",
            "demo_data": {
                "recent_ipos": [
                    {
                        "ticker": "NEWSPAC",
                        "name": "New SPAC Acquisition Corp",
                        "ipo_date": (datetime.now() - timedelta(days=15)).date().isoformat(),
                        "units_offered_m": 30,
                        "price_per_unit": 10.00,
                        "gross_proceeds_m": 300,
                        "sponsor": "New Capital Partners",
                        "underwriters": ["Goldman Sachs", "Morgan Stanley"],
                        "target_focus": "Fintech",
                        "current_price": 10.05
                    }
                ],
                "period": period,
                "count": 1,
                "total_capital_raised_m": 300,
                "timestamp": datetime.now().isoformat()
            },
            "note": "This is demo data. Real API requires subscription."
        }
    
    return result


def get_spac_redemptions() -> Dict:
    """
    Get SPAC redemption rate data (shareholder votes and redemption activity)
    
    Returns:
        Dict with redemption statistics
    """
    result = _make_request("redemptions")
    
    if not result.get("success"):
        return {
            "success": False,
            "error": "API unavailable - returning demo structure",
            "demo_data": {
                "recent_votes": [
                    {
                        "ticker": "VOTESP",
                        "vote_date": (datetime.now() - timedelta(days=5)).date().isoformat(),
                        "vote_type": "merger",
                        "shares_voted_pct": 87.5,
                        "redemption_rate_pct": 42.3,
                        "shares_redeemed_m": 12.7,
                        "trust_remaining_m": 172.8,
                        "outcome": "approved"
                    }
                ],
                "avg_redemption_rate_ytd_pct": 38.2,
                "median_redemption_rate_ytd_pct": 35.7,
                "total_votes_ytd": 156,
                "timestamp": datetime.now().isoformat()
            },
            "note": "This is demo data. Real API requires subscription."
        }
    
    return result


def get_latest() -> Dict:
    """
    Get summary of latest SPAC activity across all categories
    
    Returns:
        Dict with recent SPAC news, deals, IPOs, votes
    """
    return {
        "success": True,
        "latest_activity": {
            "ipos": get_spac_ipos("7d"),
            "mergers": get_spac_mergers("announced"),
            "redemptions": get_spac_redemptions(),
            "active_count": 234,  # Demo count
            "total_trust_capital_b": 70.5,  # Demo total
            "summary": "Latest SPAC market activity (demo data)",
            "timestamp": datetime.now().isoformat()
        },
        "note": "Aggregated demo data from placeholder functions"
    }


def fetch_data(spac_type: str, params: Optional[Dict] = None) -> Dict:
    """
    Generic data fetch function for any SPAC data type
    
    Args:
        spac_type: Type of data - 'active', 'mergers', 'ipos', 'redemptions', 'performance'
        params: Optional parameters (ticker for performance, status for mergers, etc.)
    
    Returns:
        Dict with requested SPAC data
    """
    params = params or {}
    
    if spac_type == "active":
        return get_active_spacs()
    elif spac_type == "mergers":
        return get_spac_mergers(params.get("status", "announced"))
    elif spac_type == "ipos":
        return get_spac_ipos(params.get("period", "30d"))
    elif spac_type == "redemptions":
        return get_spac_redemptions()
    elif spac_type == "performance":
        ticker = params.get("ticker")
        if not ticker:
            return {"success": False, "error": "ticker parameter required for performance data"}
        return get_spac_performance(ticker)
    else:
        return {
            "success": False,
            "error": f"Unknown spac_type: {spac_type}",
            "valid_types": ["active", "mergers", "ipos", "redemptions", "performance"]
        }


if __name__ == "__main__":
    print("=" * 60)
    print("SPACInsider Data Feed - IPO & Private Markets")
    print("=" * 60)
    
    # Demo CLI output
    print("\n1. Latest SPAC Activity Summary:")
    latest = get_latest()
    print(json.dumps(latest, indent=2, default=str))
    
    print("\n2. Active SPACs:")
    active = get_active_spacs()
    print(json.dumps(active, indent=2, default=str))
    
    print("\n3. Recent Merger Announcements:")
    mergers = get_spac_mergers("announced")
    print(json.dumps(mergers, indent=2, default=str))
    
    print("\n4. Module Info:")
    info = {
        "module": "spacinsider_data_feed",
        "category": "IPO & Private Markets",
        "functions": 7,
        "source": "https://www.spacinsider.com/api",
        "status": "demo_mode",
        "note": "API endpoints unavailable - returns placeholder data structures"
    }
    print(json.dumps(info, indent=2))
