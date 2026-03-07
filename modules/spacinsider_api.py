#!/usr/bin/env python3
"""
SPACInsider API — SPAC Merger & IPO Data Module

SPACInsider offers data on SPAC mergers, IPOs, and de-SPAC events. This module provides
access to SPAC data including merger announcements, redemption rates, and performance
post-merger. Essential for quant strategies around SPAC volatility and private-to-public
transitions.

Source: https://www.spacinsider.com/api
Category: IPO & Private Markets
Free tier: 100 calls/day (API currently unavailable - module returns sample data)
Update frequency: real-time when API is available
Author: QuantClaw Data NightBuilder
Phase: NightBuilder

Note: The SPACInsider API endpoint is currently unavailable or requires authentication.
This module provides a working structure with sample data for testing purposes.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# API Configuration (currently unavailable)
SPACINSIDER_BASE_URL = "https://api.spacinsider.com/v1"
DEFAULT_TIMEOUT = 15


def get_upcoming_spacs(
    status: str = "pending",
    limit: int = 10,
    api_token: Optional[str] = None
) -> Dict:
    """
    Fetch upcoming SPAC IPOs and their status
    
    Args:
        status: Filter by status ('pending', 'announced', 'completed')
        limit: Maximum number of results (default 10)
        api_token: Optional API token for authentication
    
    Returns:
        Dict with SPAC data including IPO dates, targets, and status
    
    Note: API currently unavailable - returns sample data
    """
    try:
        # Attempt API call (currently returns 404)
        url = f"{SPACINSIDER_BASE_URL}/spacs/upcoming"
        params = {
            "status": status,
            "limit": limit
        }
        
        if api_token:
            params["token"] = api_token
        
        # This would work if API was available
        # response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        # response.raise_for_status()
        # return {"success": True, "data": response.json()}
        
        # Return sample data since API is unavailable
        return {
            "success": True,
            "note": "API unavailable - returning sample data",
            "source": "SPACInsider API (stub)",
            "timestamp": datetime.now().isoformat(),
            "count": 3,
            "status_filter": status,
            "data": [
                {
                    "ticker": "SPAC",
                    "name": "Sample SPAC Acquisition Corp",
                    "ipo_date": "2024-01-15",
                    "target_company": "TechTarget Inc",
                    "merger_status": status,
                    "trust_size_millions": 250,
                    "redemption_percentage": 15.3,
                    "warrant_price": 11.25,
                    "merger_announcement_date": "2024-03-10"
                },
                {
                    "ticker": "SPCB",
                    "name": "Second SPAC Corp",
                    "ipo_date": "2024-02-20",
                    "target_company": "CleanEnergy Solutions",
                    "merger_status": status,
                    "trust_size_millions": 400,
                    "redemption_percentage": 8.7,
                    "warrant_price": 10.85,
                    "merger_announcement_date": "2024-04-15"
                },
                {
                    "ticker": "SPCC",
                    "name": "Third SPAC Holdings",
                    "ipo_date": "2023-11-05",
                    "target_company": "FinTech Innovators",
                    "merger_status": status,
                    "trust_size_millions": 300,
                    "redemption_percentage": 22.1,
                    "warrant_price": 9.95,
                    "merger_announcement_date": "2024-02-28"
                }
            ]
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}",
            "note": "SPACInsider API endpoint unavailable"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_spac_by_ticker(ticker: str, api_token: Optional[str] = None) -> Dict:
    """
    Get detailed information for a specific SPAC by ticker
    
    Args:
        ticker: SPAC ticker symbol
        api_token: Optional API token for authentication
    
    Returns:
        Dict with detailed SPAC information
    """
    try:
        return {
            "success": True,
            "note": "API unavailable - returning sample data",
            "ticker": ticker.upper(),
            "timestamp": datetime.now().isoformat(),
            "data": {
                "ticker": ticker.upper(),
                "name": f"{ticker.upper()} Acquisition Corp",
                "ipo_date": "2024-01-15",
                "ipo_price": 10.00,
                "current_price": 10.45,
                "trust_size_millions": 250,
                "sponsor": "Sample Capital Partners",
                "target_company": "Innovation Tech Inc",
                "target_industry": "Technology",
                "merger_status": "announced",
                "merger_announcement_date": "2024-03-10",
                "expected_close_date": "2024-06-30",
                "redemption_percentage": 15.3,
                "redemption_deadline": "2024-06-15",
                "warrant_ticker": f"{ticker.upper()}W",
                "warrant_price": 11.25,
                "warrant_exercise_price": 11.50,
                "pipe_size_millions": 100,
                "post_merger_ticker": "INOV",
                "post_merger_valuation_millions": 1200
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_recent_mergers(days: int = 30, api_token: Optional[str] = None) -> Dict:
    """
    Get SPACs that have recently completed mergers
    
    Args:
        days: Number of days to look back (default 30)
        api_token: Optional API token for authentication
    
    Returns:
        Dict with recently completed SPAC mergers
    """
    try:
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return {
            "success": True,
            "note": "API unavailable - returning sample data",
            "since_date": since_date,
            "days_back": days,
            "timestamp": datetime.now().isoformat(),
            "count": 2,
            "data": [
                {
                    "original_ticker": "SPCD",
                    "original_name": "SPCD Acquisition Corp",
                    "merger_completion_date": "2024-02-15",
                    "new_ticker": "TECH",
                    "new_company_name": "TechCorp Inc",
                    "ipo_date": "2023-06-10",
                    "trust_size_millions": 300,
                    "redemption_percentage": 18.5,
                    "first_day_return_pct": 12.3,
                    "current_price": 11.85,
                    "post_merger_performance_pct": 18.5
                },
                {
                    "original_ticker": "SPCE",
                    "original_name": "SPCE Holdings",
                    "merger_completion_date": "2024-02-28",
                    "new_ticker": "CLEAN",
                    "new_company_name": "CleanEnergy Solutions",
                    "ipo_date": "2023-08-20",
                    "trust_size_millions": 400,
                    "redemption_percentage": 9.2,
                    "first_day_return_pct": -2.1,
                    "current_price": 9.45,
                    "post_merger_performance_pct": -5.5
                }
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_redemption_stats(api_token: Optional[str] = None) -> Dict:
    """
    Get statistics on SPAC redemption rates
    
    Args:
        api_token: Optional API token for authentication
    
    Returns:
        Dict with redemption statistics across all SPACs
    """
    try:
        return {
            "success": True,
            "note": "API unavailable - returning sample data",
            "timestamp": datetime.now().isoformat(),
            "period": "2024-YTD",
            "statistics": {
                "total_spacs_analyzed": 45,
                "average_redemption_pct": 15.8,
                "median_redemption_pct": 12.3,
                "high_redemption_count": 8,  # >50% redemption
                "low_redemption_count": 22,  # <10% redemption
                "total_capital_redeemed_millions": 3420,
                "highest_redemption": {
                    "ticker": "SPCF",
                    "redemption_pct": 87.5,
                    "reason": "Poor target company fundamentals"
                },
                "lowest_redemption": {
                    "ticker": "SPCG",
                    "redemption_pct": 2.1,
                    "reason": "Strong target company interest"
                }
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_market_summary(api_token: Optional[str] = None) -> Dict:
    """
    Get overall SPAC market summary and trends
    
    Args:
        api_token: Optional API token for authentication
    
    Returns:
        Dict with SPAC market overview statistics
    """
    try:
        return {
            "success": True,
            "note": "API unavailable - returning sample data",
            "timestamp": datetime.now().isoformat(),
            "market_summary": {
                "active_spacs": 156,
                "spacs_seeking_targets": 89,
                "spacs_with_announced_targets": 34,
                "completed_mergers_ytd": 23,
                "average_trust_size_millions": 287,
                "total_capital_in_trust_billions": 44.8,
                "average_days_to_merger": 485,
                "average_redemption_rate_pct": 15.8,
                "average_post_merger_return_30d_pct": -3.2,
                "average_post_merger_return_90d_pct": -8.7,
                "top_sectors": [
                    {"sector": "Technology", "count": 45, "pct": 28.8},
                    {"sector": "Healthcare", "count": 31, "pct": 19.9},
                    {"sector": "Financial Services", "count": 28, "pct": 17.9},
                    {"sector": "Clean Energy", "count": 24, "pct": 15.4},
                    {"sector": "Consumer", "count": 18, "pct": 11.5}
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_available_functions() -> Dict:
    """
    List all available functions in this module
    
    Returns:
        Dict with function names and descriptions
    """
    return {
        "module": "spacinsider_api",
        "status": "operational (sample data)",
        "note": "API endpoint unavailable - module returns sample data for testing",
        "source": "https://www.spacinsider.com/api",
        "functions": {
            "get_upcoming_spacs": "Fetch upcoming SPAC IPOs by status",
            "get_spac_by_ticker": "Get detailed info for specific SPAC",
            "get_recent_mergers": "Get recently completed SPAC mergers",
            "get_redemption_stats": "Get SPAC redemption statistics",
            "get_market_summary": "Get overall SPAC market overview",
            "list_available_functions": "List all available functions"
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("SPACInsider API Module - SPAC Merger & IPO Data")
    print("=" * 60)
    
    # List functions
    functions = list_available_functions()
    print(f"\nModule: {functions['module']}")
    print(f"Status: {functions['status']}")
    print(f"Note: {functions['note']}")
    print(f"\nAvailable Functions ({len(functions['functions'])} total):")
    for func, desc in functions['functions'].items():
        print(f"  - {func}: {desc}")
    
    # Demo some functions
    print("\n" + "=" * 60)
    print("Sample Data Output:")
    print("=" * 60)
    
    print("\n1. Market Summary:")
    summary = get_market_summary()
    if summary['success']:
        print(f"   Active SPACs: {summary['market_summary']['active_spacs']}")
        print(f"   Total Capital: ${summary['market_summary']['total_capital_in_trust_billions']}B")
        print(f"   Avg Redemption Rate: {summary['market_summary']['average_redemption_rate_pct']}%")
    
    print("\n2. Upcoming SPACs (pending status):")
    upcoming = get_upcoming_spacs(status="pending", limit=2)
    if upcoming['success']:
        for spac in upcoming['data'][:2]:
            print(f"   {spac['ticker']}: {spac['name']}")
            print(f"      Target: {spac['target_company']}")
            print(f"      Redemption: {spac['redemption_percentage']}%")
    
    print("\n3. Recent Mergers:")
    mergers = get_recent_mergers(days=30)
    if mergers['success']:
        for merger in mergers['data'][:2]:
            print(f"   {merger['original_ticker']} → {merger['new_ticker']}")
            print(f"      Performance: {merger['post_merger_performance_pct']}%")
    
    print("\n" + "=" * 60)
    print("Full JSON output:")
    print(json.dumps(functions, indent=2))
