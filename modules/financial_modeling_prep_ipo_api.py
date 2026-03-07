"""
Financial Modeling Prep IPO Calendar API

Tracks upcoming, confirmed, and historical IPOs with valuations via FMP API.
Data: https://financialmodelingprep.com/api/v4/ipo_calender

Use cases:
- IPO pipeline tracking
- Pre-IPO valuation analysis
- Historical IPO performance
- Filing and prospectus monitoring

Free tier: 250 API calls per day
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "fmp_ipo"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://financialmodelingprep.com/api"
API_KEY = os.environ.get("FMP_API_KEY", "demo")


def _fetch_fmp_endpoint(endpoint: str, params: Optional[Dict] = None, cache_hours: int = 24) -> Optional[List[Dict]]:
    """Generic FMP API fetcher with caching."""
    # Build cache key from endpoint and params
    cache_key = endpoint.replace("/", "_")
    if params:
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "apikey")
        cache_key = f"{cache_key}_{param_str}" if param_str else cache_key
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}{endpoint}"
    request_params = params.copy() if params else {}
    request_params["apikey"] = API_KEY
    
    try:
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching FMP data from {endpoint}: {e}")
        # Return cached data if available, even if stale
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_ipo_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get upcoming IPO calendar.
    
    Args:
        from_date: Start date (YYYY-MM-DD). Defaults to today.
        to_date: End date (YYYY-MM-DD). Defaults to 1 year from start.
    
    Returns:
        DataFrame with IPO calendar entries
    """
    # Default date range: today to 1 year ahead
    if not from_date:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    params = {"from": from_date, "to": to_date}
    data = _fetch_fmp_endpoint("/v4/ipo_calender", params, cache_hours=6)
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Standardize column names if present
    if not df.empty:
        # Common FMP IPO fields: symbol, company, exchange, date, priceRange, numberOfShares, marketCap
        if 'date' in df.columns:
            df['ipo_date'] = df['date']
        if 'priceRange' in df.columns:
            df['price_range'] = df['priceRange']
        if 'numberOfShares' in df.columns:
            df['shares_offered'] = df['numberOfShares']
    
    return df


def get_confirmed_ipos(from_date: Optional[str] = None, to_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get confirmed IPOs with dates set.
    
    Args:
        from_date: Start date (YYYY-MM-DD). Defaults to today.
        to_date: End date (YYYY-MM-DD). Defaults to 3 months ahead.
    
    Returns:
        DataFrame with confirmed IPO entries (filtered to only those with confirmed dates)
    """
    # Shorter default window for confirmed IPOs
    if not from_date:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Try v3 endpoint which may have different data
    params = {"from": from_date, "to": to_date}
    data = _fetch_fmp_endpoint("/v3/ipo_calendar", params, cache_hours=6)
    
    if not data:
        # Fallback to v4 if v3 fails
        data = _fetch_fmp_endpoint("/v4/ipo_calender", params, cache_hours=6)
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Filter to only confirmed (those with specific dates, not TBD/pending)
    if not df.empty and 'date' in df.columns:
        # Filter out entries with null/empty dates
        df = df[df['date'].notna() & (df['date'] != '') & (df['date'] != 'TBD')]
        df['ipo_date'] = df['date']
    
    return df


def get_ipo_prospectus(from_date: Optional[str] = None, to_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get IPOs with prospectus filing data.
    
    Args:
        from_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to 90 days ahead.
    
    Returns:
        DataFrame with IPO prospectus entries
    """
    # Default window: recent past to near future for prospectus tracking
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    params = {"from": from_date, "to": to_date}
    data = _fetch_fmp_endpoint("/v4/ipo-calendar-prospectus", params, cache_hours=12)
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Add prospectus-specific fields if present
    if not df.empty:
        if 'filingDate' in df.columns:
            df['filing_date'] = df['filingDate']
        if 'expectedPriceDate' in df.columns:
            df['expected_price_date'] = df['expectedPriceDate']
    
    return df


def get_historical_ipos(year: Optional[int] = None) -> pd.DataFrame:
    """
    Get historical IPO data for a specific year.
    
    Args:
        year: Year to fetch (e.g., 2025). Defaults to current year.
    
    Returns:
        DataFrame with historical IPO data
    """
    if not year:
        year = datetime.now().year
    
    # Fetch full year
    from_date = f"{year}-01-01"
    to_date = f"{year}-12-31"
    
    params = {"from": from_date, "to": to_date}
    data = _fetch_fmp_endpoint("/v4/ipo_calender", params, cache_hours=168)  # Cache 1 week for historical
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Filter to completed IPOs (those in the past)
    if not df.empty and 'date' in df.columns:
        df['ipo_date'] = pd.to_datetime(df['date'], errors='coerce')
        # Only keep IPOs that have occurred
        df = df[df['ipo_date'] < datetime.now()]
        df = df.sort_values('ipo_date', ascending=False)
    
    return df


def cli_ipo_upcoming(days: int = 30):
    """CLI: Display upcoming IPOs."""
    from_date = datetime.now().strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    df = get_ipo_calendar(from_date, to_date)
    
    if df.empty:
        print(f"No upcoming IPOs found in next {days} days")
        return
    
    print(f"\n=== Upcoming IPOs (Next {days} Days) ===\n")
    
    # Display key columns
    display_cols = []
    for col in ['symbol', 'company', 'exchange', 'date', 'priceRange', 'marketCap']:
        if col in df.columns:
            display_cols.append(col)
    
    if display_cols:
        print(df[display_cols].to_string(index=False))
    else:
        print(df.to_string(index=False))
    
    print(f"\nTotal: {len(df)} IPOs")


def cli_ipo_confirmed():
    """CLI: Display confirmed IPOs with set dates."""
    df = get_confirmed_ipos()
    
    if df.empty:
        print("No confirmed IPOs found")
        return
    
    print("\n=== Confirmed IPOs ===\n")
    
    # Display key columns
    display_cols = []
    for col in ['symbol', 'company', 'date', 'exchange', 'priceRange', 'numberOfShares']:
        if col in df.columns:
            display_cols.append(col)
    
    if display_cols:
        print(df[display_cols].to_string(index=False))
    else:
        print(df.to_string(index=False))
    
    print(f"\nTotal: {len(df)} confirmed IPOs")


def cli_ipo_prospectus():
    """CLI: Display IPOs with prospectus filings."""
    df = get_ipo_prospectus()
    
    if df.empty:
        print("No IPO prospectus data found")
        return
    
    print("\n=== IPO Prospectus Filings ===\n")
    
    print(df.to_string(index=False))
    print(f"\nTotal: {len(df)} prospectus filings")


def cli_ipo_historical(year: Optional[int] = None):
    """CLI: Display historical IPOs for a year."""
    if not year:
        year = datetime.now().year
    
    df = get_historical_ipos(year)
    
    if df.empty:
        print(f"No historical IPO data found for {year}")
        return
    
    print(f"\n=== Historical IPOs ({year}) ===\n")
    
    # Display key columns
    display_cols = []
    for col in ['symbol', 'company', 'date', 'exchange', 'priceRange', 'marketCap']:
        if col in df.columns:
            display_cols.append(col)
    
    if display_cols:
        print(df[display_cols].to_string(index=False))
    else:
        print(df.to_string(index=False))
    
    print(f"\nTotal: {len(df)} IPOs in {year}")


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        cli_ipo_upcoming(30)
        sys.exit(0)
    
    command = args[0]
    
    if command == "fmp-ipo-upcoming":
        days = int(args[1]) if len(args) > 1 else 30
        cli_ipo_upcoming(days)
    elif command == "fmp-ipo-confirmed":
        cli_ipo_confirmed()
    elif command == "fmp-ipo-prospectus":
        cli_ipo_prospectus()
    elif command == "fmp-ipo-historical":
        year = int(args[1]) if len(args) > 1 else None
        cli_ipo_historical(year)
    else:
        print(f"Unknown command: {command}")
        print("Available: fmp-ipo-upcoming, fmp-ipo-confirmed, fmp-ipo-prospectus, fmp-ipo-historical")
        sys.exit(1)
