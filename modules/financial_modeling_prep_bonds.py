"""
Financial Modeling Prep Bonds — Corporate & Government Bond Data

FMP offers API access to corporate and government bond data, including treasury rates,
credit ratings, yields, and credit spreads. Covers US and international bonds.

Source: https://site.financialmodelingprep.com/developer/docs/bonds-api
Free tier: 250 requests/day, limited to US data

Use cases:
- Treasury yield curve analysis
- Credit rating monitoring
- Corporate bond screening
- Fixed income portfolio research
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json
import os

CACHE_DIR = Path(__file__).parent.parent / "cache" / "fmp_bonds"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://financialmodelingprep.com/api"
API_KEY = os.getenv("FMP_API_KEY", "demo")


def _make_request(endpoint: str, params: Optional[Dict] = None, cache_hours: int = 24) -> Optional[Dict]:
    """
    Make API request with caching.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters (apikey added automatically)
        cache_hours: Cache validity in hours
    
    Returns:
        API response data or None on error
    """
    # Build cache key from endpoint and params
    cache_key = endpoint.replace("/", "_")
    if params:
        cache_key += "_" + "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build URL and params
    url = f"{BASE_URL}{endpoint}"
    if params is None:
        params = {}
    params["apikey"] = API_KEY
    
    # Fetch from API
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching from {endpoint}: {e}")
        # Return stale cache if available
        if cache_path.exists():
            print(f"Using stale cache from {cache_path}")
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_treasury_rates(from_date: Optional[str] = None, to_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get US Treasury rates across maturities.
    
    Args:
        from_date: Start date (YYYY-MM-DD), defaults to 30 days ago
        to_date: End date (YYYY-MM-DD), defaults to today
    
    Returns:
        DataFrame with columns: date, month1, month2, month3, month6, year1, year2, year3, year5, year7, year10, year20, year30
    """
    # Default date range
    if to_date is None:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if from_date is None:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {"from": from_date, "to": to_date}
    data = _make_request("/v4/treasury", params=params, cache_hours=6)
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Clean up column names
    if not df.empty and 'date' in df.columns:
        # Sort by date descending (most recent first)
        df = df.sort_values('date', ascending=False).reset_index(drop=True)
    
    return df


def get_credit_rating(ticker: str) -> Dict:
    """
    Get S&P, Moody's, and Fitch credit ratings for a company.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict with rating info or empty dict on error
    """
    data = _make_request(f"/v3/rating/{ticker.upper()}", cache_hours=24)
    
    if not data or not isinstance(data, list) or len(data) == 0:
        return {}
    
    # Return the most recent rating
    return data[0]


def get_corporate_bonds(ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Get corporate bond listings with yields and spreads.
    
    Args:
        ticker: Optional stock ticker to filter bonds (e.g., 'AAPL')
    
    Returns:
        DataFrame with bond details
    """
    endpoint = "/v4/corporate-bond"
    params = {}
    if ticker:
        params["symbol"] = ticker.upper()
    
    data = _make_request(endpoint, params=params, cache_hours=12)
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    return df


def get_bond_screener(
    min_yield: Optional[float] = None,
    max_yield: Optional[float] = None,
    rating: Optional[str] = None
) -> pd.DataFrame:
    """
    Screen corporate bonds by yield and credit rating.
    
    Args:
        min_yield: Minimum yield percentage (e.g., 3.5)
        max_yield: Maximum yield percentage (e.g., 8.0)
        rating: Credit rating filter (e.g., 'AAA', 'BBB', 'BB')
    
    Returns:
        Filtered DataFrame of corporate bonds
    """
    # Get all corporate bonds
    df = get_corporate_bonds()
    
    if df.empty:
        return df
    
    # Apply filters
    if min_yield is not None and 'yield' in df.columns:
        df = df[df['yield'] >= min_yield]
    
    if max_yield is not None and 'yield' in df.columns:
        df = df[df['yield'] <= max_yield]
    
    if rating is not None and 'rating' in df.columns:
        df = df[df['rating'].str.contains(rating, case=False, na=False)]
    
    return df


def cli_treasury_rates(days: int = 30):
    """CLI: Display current treasury yield curve."""
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    df = get_treasury_rates(from_date, to_date)
    
    if df.empty:
        print("No treasury rate data available")
        return
    
    print(f"\n=== US Treasury Yield Curve (Last {days} Days) ===")
    print(f"Most Recent: {df['date'].iloc[0] if 'date' in df.columns else 'N/A'}")
    
    # Display latest rates
    if not df.empty:
        latest = df.iloc[0]
        print("\nCurrent Rates:")
        
        maturity_cols = [c for c in df.columns if 'month' in c or 'year' in c]
        for col in maturity_cols:
            if col in latest and pd.notna(latest[col]):
                print(f"  {col:10s}: {latest[col]:.3f}%")
    
    print(f"\nTotal records: {len(df)}")


def cli_credit_rating(ticker: str):
    """CLI: Display credit rating for a company."""
    rating = get_credit_rating(ticker)
    
    if not rating:
        print(f"No credit rating data found for {ticker}")
        return
    
    print(f"\n=== Credit Rating: {ticker.upper()} ===")
    
    for key, value in rating.items():
        if value:
            print(f"{key:20s}: {value}")


def cli_corporate_bonds(ticker: Optional[str] = None):
    """CLI: Display corporate bond listings."""
    df = get_corporate_bonds(ticker)
    
    if df.empty:
        print(f"No corporate bond data available{' for ' + ticker if ticker else ''}")
        return
    
    title = f"Corporate Bonds{' - ' + ticker.upper() if ticker else ''}"
    print(f"\n=== {title} ===")
    print(f"Total bonds: {len(df)}")
    
    # Display first 10 bonds
    display_cols = [c for c in ['symbol', 'name', 'yield', 'maturity', 'rating', 'coupon'] if c in df.columns]
    if display_cols:
        print(f"\n{df[display_cols].head(10).to_string(index=False)}")
    else:
        print(f"\n{df.head(10).to_string(index=False)}")


def cli_bond_screener(min_yield: Optional[float] = None, max_yield: Optional[float] = None, rating: Optional[str] = None):
    """CLI: Screen corporate bonds."""
    df = get_bond_screener(min_yield, max_yield, rating)
    
    if df.empty:
        print("No bonds match the criteria")
        return
    
    filters = []
    if min_yield:
        filters.append(f"Yield ≥ {min_yield}%")
    if max_yield:
        filters.append(f"Yield ≤ {max_yield}%")
    if rating:
        filters.append(f"Rating: {rating}")
    
    filter_str = ", ".join(filters) if filters else "No filters"
    
    print(f"\n=== Bond Screener ({filter_str}) ===")
    print(f"Matching bonds: {len(df)}")
    
    display_cols = [c for c in ['symbol', 'name', 'yield', 'maturity', 'rating', 'coupon'] if c in df.columns]
    if display_cols:
        print(f"\n{df[display_cols].head(15).to_string(index=False)}")
    else:
        print(f"\n{df.head(15).to_string(index=False)}")


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        cli_treasury_rates()
        sys.exit(0)
    
    command = args[0]
    
    if command == "fmp-treasury":
        days = int(args[1]) if len(args) > 1 else 30
        cli_treasury_rates(days)
    elif command == "fmp-rating":
        if len(args) < 2:
            print("Usage: fmp-rating <ticker>")
            sys.exit(1)
        cli_credit_rating(args[1])
    elif command == "fmp-bonds":
        ticker = args[1] if len(args) > 1 else None
        cli_corporate_bonds(ticker)
    elif command == "fmp-bond-screener":
        # Parse optional arguments
        min_yield = None
        max_yield = None
        rating = None
        
        i = 1
        while i < len(args):
            if args[i] == "--min-yield" and i + 1 < len(args):
                min_yield = float(args[i + 1])
                i += 2
            elif args[i] == "--max-yield" and i + 1 < len(args):
                max_yield = float(args[i + 1])
                i += 2
            elif args[i] == "--rating" and i + 1 < len(args):
                rating = args[i + 1]
                i += 2
            else:
                i += 1
        
        cli_bond_screener(min_yield, max_yield, rating)
    else:
        print(f"Unknown command: {command}")
        print("Available commands:")
        print("  fmp-treasury [days]")
        print("  fmp-rating <ticker>")
        print("  fmp-bonds [ticker]")
        print("  fmp-bond-screener [--min-yield N] [--max-yield N] [--rating RATING]")
        sys.exit(1)
