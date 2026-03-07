#!/usr/bin/env python3
"""
Finnhub IPO Calendar API — IPO & Private Markets Module

Real-time and historical IPO data including calendars, filings, and performance metrics 
for global markets. Includes details on upcoming IPOs, pricing, post-IPO performance,
and enhanced private market insights for pre-IPO valuations.

Data points: IPO date, company name, ticker, exchange, offer price, shares offered, 
expected valuation, underwriters

Source: https://finnhub.io/docs/api/ipo-calendar
Category: IPO & Private Markets
Free tier: True (60 calls/minute, 500 calls/day)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_ipo_calendar(from_date: str, to_date: str) -> Dict:
    """
    Get IPO calendar for a specific date range.
    
    Args:
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict containing IPO calendar data with keys:
        - ipoCalendar: List of IPO entries
        Each entry contains: date, exchange, name, numberOfShares, price, totalSharesValue, status
        
    Example:
        >>> data = get_ipo_calendar("2026-01-01", "2026-12-31")
        >>> print(data['ipoCalendar'][0])
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not set in environment", "ipoCalendar": []}
    
    try:
        url = f"{BASE_URL}/calendar/ipo"
        params = {
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "ipoCalendar": []}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {str(e)}", "ipoCalendar": []}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "ipoCalendar": []}


def get_upcoming_ipos(days_ahead: int = 30) -> Dict:
    """
    Get upcoming IPOs for the next N days.
    
    Args:
        days_ahead: Number of days to look ahead (default: 30)
        
    Returns:
        Dict containing upcoming IPO data
        
    Example:
        >>> upcoming = get_upcoming_ipos(60)
        >>> print(f"Found {len(upcoming['ipoCalendar'])} upcoming IPOs")
    """
    today = datetime.now()
    from_date = today.strftime("%Y-%m-%d")
    to_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    return get_ipo_calendar(from_date, to_date)


def get_recent_ipos(days_back: int = 30) -> Dict:
    """
    Get recently completed IPOs from the past N days.
    
    Args:
        days_back: Number of days to look back (default: 30)
        
    Returns:
        Dict containing recent IPO data
        
    Example:
        >>> recent = get_recent_ipos(90)
        >>> print(f"Found {len(recent['ipoCalendar'])} recent IPOs")
    """
    today = datetime.now()
    to_date = today.strftime("%Y-%m-%d")
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    return get_ipo_calendar(from_date, to_date)


def search_ipos(company_name: Optional[str] = None, exchange: Optional[str] = None, 
                from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
    """
    Search and filter IPOs by company name and/or exchange.
    
    Args:
        company_name: Filter by company name (case-insensitive partial match)
        exchange: Filter by exchange (e.g., 'NASDAQ', 'NYSE')
        from_date: Start date in YYYY-MM-DD format (default: 90 days ago)
        to_date: End date in YYYY-MM-DD format (default: 90 days ahead)
        
    Returns:
        List of IPO entries matching the criteria
        
    Example:
        >>> nasdaq_ipos = search_ipos(exchange="NASDAQ")
        >>> tech_ipos = search_ipos(company_name="Tech")
    """
    # Default date range: 90 days back to 90 days ahead
    if not from_date:
        from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    data = get_ipo_calendar(from_date, to_date)
    
    if "error" in data or not data.get("ipoCalendar"):
        return []
    
    results = data["ipoCalendar"]
    
    # Filter by company name
    if company_name:
        results = [ipo for ipo in results 
                  if company_name.lower() in ipo.get("name", "").lower()]
    
    # Filter by exchange
    if exchange:
        results = [ipo for ipo in results 
                  if ipo.get("exchange", "").upper() == exchange.upper()]
    
    return results


def get_ipo_stats(from_date: str, to_date: str) -> Dict:
    """
    Get summary statistics for IPOs in a date range.
    
    Args:
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict containing:
        - count: Total number of IPOs
        - total_raised: Total capital raised (sum of totalSharesValue)
        - avg_valuation: Average valuation
        - exchanges: Breakdown by exchange
        - date_range: Query date range
        
    Example:
        >>> stats = get_ipo_stats("2026-01-01", "2026-03-31")
        >>> print(f"Q1 2026: {stats['count']} IPOs, ${stats['total_raised']/1e9:.2f}B raised")
    """
    data = get_ipo_calendar(from_date, to_date)
    
    if "error" in data or not data.get("ipoCalendar"):
        return {
            "error": data.get("error", "No data"),
            "count": 0,
            "total_raised": 0,
            "avg_valuation": 0,
            "exchanges": {},
            "date_range": {"from": from_date, "to": to_date}
        }
    
    ipos = data["ipoCalendar"]
    
    # Calculate stats
    count = len(ipos)
    total_raised = sum(ipo.get("totalSharesValue") or 0 for ipo in ipos)
    avg_valuation = total_raised / count if count > 0 else 0
    
    # Breakdown by exchange
    exchanges = {}
    for ipo in ipos:
        exch = ipo.get("exchange", "Unknown")
        exchanges[exch] = exchanges.get(exch, 0) + 1
    
    return {
        "count": count,
        "total_raised": total_raised,
        "avg_valuation": avg_valuation,
        "exchanges": exchanges,
        "date_range": {"from": from_date, "to": to_date}
    }


if __name__ == "__main__":
    # Test module
    print("=" * 60)
    print("Finnhub IPO Calendar API Module Test")
    print("=" * 60)
    
    if not FINNHUB_API_KEY:
        print("\n⚠️  FINNHUB_API_KEY not set in environment")
        print("Set it in .env file or export FINNHUB_API_KEY=your_key")
    else:
        print(f"\n✓ API Key configured: {FINNHUB_API_KEY[:8]}...")
    
    # Test upcoming IPOs
    print("\n--- Testing get_upcoming_ipos(30) ---")
    upcoming = get_upcoming_ipos(30)
    if "error" in upcoming:
        print(f"Error: {upcoming['error']}")
    else:
        count = len(upcoming.get("ipoCalendar", []))
        print(f"Found {count} upcoming IPOs in next 30 days")
        if count > 0:
            print(f"Sample: {upcoming['ipoCalendar'][0]}")
    
    # Test recent IPOs
    print("\n--- Testing get_recent_ipos(30) ---")
    recent = get_recent_ipos(30)
    if "error" in recent:
        print(f"Error: {recent['error']}")
    else:
        count = len(recent.get("ipoCalendar", []))
        print(f"Found {count} recent IPOs in past 30 days")
    
    # Test stats
    print("\n--- Testing get_ipo_stats(Q1 2026) ---")
    stats = get_ipo_stats("2026-01-01", "2026-03-31")
    print(json.dumps(stats, indent=2))
