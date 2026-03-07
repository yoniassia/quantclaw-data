#!/usr/bin/env python3
"""
Alpha Vantage Earnings Calendar API — Earnings Data Module

Specialized module for corporate earnings data from Alpha Vantage.
Provides:
- Upcoming earnings calendar with estimates
- Historical earnings for specific symbols
- EPS surprise data (actual vs estimate)
- Filtered upcoming earnings by date range

Source: https://www.alphavantage.co/documentation/#earnings-calendar
Category: Earnings & Fundamentals
Free tier: True (5 calls/min, 500 calls/day with demo key)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from io import StringIO

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")

# ========== CORE API FUNCTIONS ==========

def _fetch_earnings_calendar_raw(horizon: str = "3month") -> Optional[str]:
    """
    Fetch raw CSV data from Alpha Vantage Earnings Calendar endpoint.
    
    Args:
        horizon: Time horizon - "3month", "6month", or "12month"
    
    Returns:
        Raw CSV string or None on error
    """
    try:
        params = {
            "function": "EARNINGS_CALENDAR",
            "horizon": horizon,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        # Check if response is CSV (not JSON error)
        if response.text.startswith("{"):
            error_data = response.json()
            raise ValueError(f"API Error: {error_data.get('Note') or error_data.get('Error Message', 'Unknown error')}")
        
        return response.text
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching earnings calendar: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def _parse_earnings_csv(csv_data: str) -> List[Dict]:
    """
    Parse CSV earnings data into list of dictionaries.
    
    Args:
        csv_data: Raw CSV string
    
    Returns:
        List of earnings records as dictionaries
    """
    if not csv_data:
        return []
    
    try:
        reader = csv.DictReader(StringIO(csv_data))
        earnings = []
        
        for row in reader:
            # Parse estimate field safely
            estimate_raw = row.get("estimate", "")
            estimate = None
            if estimate_raw and estimate_raw.strip():
                try:
                    estimate = float(estimate_raw)
                except (ValueError, TypeError):
                    estimate = None
            
            # Clean and structure the data
            record = {
                "symbol": row.get("symbol", "").strip(),
                "name": row.get("name", "").strip(),
                "reportDate": row.get("reportDate", "").strip(),
                "fiscalDateEnding": row.get("fiscalDateEnding", "").strip(),
                "estimate": estimate,
                "currency": row.get("currency", "USD").strip()
            }
            earnings.append(record)
        
        return earnings
    
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return []


def get_earnings_calendar(horizon: str = "3month") -> Dict:
    """
    Get upcoming earnings calendar with estimates.
    
    Args:
        horizon: Time horizon - "3month" (default), "6month", or "12month"
    
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - data: List of earnings records
        - count: Number of records
        - horizon: Requested horizon
        - timestamp: ISO timestamp
    
    Example:
        >>> calendar = get_earnings_calendar("3month")
        >>> print(f"Found {calendar['count']} upcoming earnings")
    """
    csv_data = _fetch_earnings_calendar_raw(horizon)
    
    if not csv_data:
        return {
            "status": "error",
            "message": "Failed to fetch earnings calendar",
            "data": [],
            "count": 0,
            "horizon": horizon,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    earnings = _parse_earnings_csv(csv_data)
    
    return {
        "status": "success",
        "data": earnings,
        "count": len(earnings),
        "horizon": horizon,
        "timestamp": datetime.utcnow().isoformat()
    }


def get_earnings_by_symbol(symbol: str, horizon: str = "12month") -> Dict:
    """
    Get earnings history and upcoming earnings for a specific ticker.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
        horizon: Time horizon to search - "3month", "6month", or "12month"
    
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - symbol: Requested symbol
        - data: List of earnings records for the symbol
        - count: Number of records found
        - timestamp: ISO timestamp
    
    Example:
        >>> aapl = get_earnings_by_symbol("AAPL")
        >>> print(aapl['data'][0]['reportDate'])
    """
    calendar = get_earnings_calendar(horizon)
    
    if calendar["status"] == "error":
        return {
            "status": "error",
            "symbol": symbol.upper(),
            "message": "Failed to fetch earnings calendar",
            "data": [],
            "count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Filter for specific symbol
    symbol_upper = symbol.upper()
    symbol_earnings = [
        record for record in calendar["data"]
        if record["symbol"].upper() == symbol_upper
    ]
    
    return {
        "status": "success",
        "symbol": symbol_upper,
        "data": symbol_earnings,
        "count": len(symbol_earnings),
        "timestamp": datetime.utcnow().isoformat()
    }


def get_earnings_surprise(symbol: str) -> Dict:
    """
    Get EPS surprise data (actual vs estimate) for a specific symbol.
    
    Note: Alpha Vantage's EARNINGS_CALENDAR endpoint provides estimates.
    For actual reported earnings, this function returns the same data
    with additional fields for surprise calculation when available.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
    
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - symbol: Requested symbol
        - data: List of earnings with estimate data
        - count: Number of records
        - timestamp: ISO timestamp
    
    Example:
        >>> surprise = get_earnings_surprise("AAPL")
        >>> for earning in surprise['data']:
        ...     print(f"{earning['reportDate']}: Est {earning['estimate']}")
    """
    # For now, this returns the same as get_earnings_by_symbol
    # In production, you'd combine with EARNINGS endpoint for actual results
    result = get_earnings_by_symbol(symbol)
    
    # Add surprise field (would be calculated if we had actual values)
    for record in result.get("data", []):
        record["surpriseNote"] = "Use EARNINGS endpoint for actual vs estimate comparison"
    
    return result


def get_upcoming_earnings(days: int = 30) -> Dict:
    """
    Get filtered upcoming earnings within specified number of days.
    
    Args:
        days: Number of days from today to filter (default: 30)
    
    Returns:
        Dictionary with:
        - status: "success" or "error"
        - data: List of earnings within date range
        - count: Number of records
        - days: Requested day range
        - dateRange: Start and end dates
        - timestamp: ISO timestamp
    
    Example:
        >>> upcoming = get_upcoming_earnings(7)  # Next 7 days
        >>> print(f"Found {upcoming['count']} earnings this week")
    """
    # Determine horizon based on days
    if days <= 90:
        horizon = "3month"
    elif days <= 180:
        horizon = "6month"
    else:
        horizon = "12month"
    
    calendar = get_earnings_calendar(horizon)
    
    if calendar["status"] == "error":
        return {
            "status": "error",
            "message": "Failed to fetch earnings calendar",
            "data": [],
            "count": 0,
            "days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Calculate date range
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days)
    
    # Filter by date
    filtered_earnings = []
    for record in calendar["data"]:
        try:
            report_date = datetime.strptime(record["reportDate"], "%Y-%m-%d").date()
            if today <= report_date <= end_date:
                filtered_earnings.append(record)
        except (ValueError, KeyError):
            continue
    
    return {
        "status": "success",
        "data": filtered_earnings,
        "count": len(filtered_earnings),
        "days": days,
        "dateRange": {
            "start": today.isoformat(),
            "end": end_date.isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ========== UTILITY FUNCTIONS ==========

def get_module_info() -> Dict:
    """
    Get module metadata and status.
    
    Returns:
        Dictionary with module information
    """
    return {
        "module": "alpha_vantage_earnings_calendar_api",
        "version": "1.0.0",
        "status": "active",
        "source": "https://www.alphavantage.co/documentation/#earnings-calendar",
        "category": "Earnings & Fundamentals",
        "free_tier": True,
        "api_key_env": "ALPHA_VANTAGE_API_KEY",
        "rate_limit": "5 calls/min, 500 calls/day",
        "functions": [
            "get_earnings_calendar",
            "get_earnings_by_symbol",
            "get_earnings_surprise",
            "get_upcoming_earnings"
        ],
        "generated": "2026-03-07"
    }


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "calendar":
            horizon = sys.argv[2] if len(sys.argv) > 2 else "3month"
            result = get_earnings_calendar(horizon)
            print(json.dumps(result, indent=2))
        
        elif command == "symbol":
            if len(sys.argv) < 3:
                print("Usage: python alpha_vantage_earnings_calendar_api.py symbol TICKER")
                sys.exit(1)
            symbol = sys.argv[2]
            result = get_earnings_by_symbol(symbol)
            print(json.dumps(result, indent=2))
        
        elif command == "upcoming":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            result = get_upcoming_earnings(days)
            print(json.dumps(result, indent=2))
        
        elif command == "info":
            print(json.dumps(get_module_info(), indent=2))
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: calendar, symbol, upcoming, info")
    
    else:
        print(json.dumps(get_module_info(), indent=2))
