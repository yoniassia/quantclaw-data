"""
Financial Modeling Prep (FMP) Earnings API — Company Fundamentals & Earnings Data

Provides earnings calendars, income statements, analyst estimates, and key metrics.
Data: https://financialmodelingprep.com/api/v3

Use cases:
- Earnings calendar tracking
- Income statement analysis
- EPS surprise monitoring
- Analyst consensus estimates
- Valuation metrics (P/E, P/B, EV/EBITDA)
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache" / "fmp_earnings"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://financialmodelingprep.com/api/v3"

# Get API key from environment or use demo key
API_KEY = os.getenv("FMP_API_KEY", "demo")


def get_earnings_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Get upcoming/past earnings dates.
    
    Args:
        from_date: Start date (YYYY-MM-DD), defaults to today
        to_date: End date (YYYY-MM-DD), defaults to +7 days
        use_cache: Use cached data if less than 6 hours old
    
    Returns:
        DataFrame with earnings calendar entries
    """
    # Set defaults
    if not from_date:
        from_date = datetime.now().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    cache_path = CACHE_DIR / f"calendar_{from_date}_{to_date}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=6):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from API
    url = f"{BASE_URL}/earning_calendar"
    params = {
        "from": from_date,
        "to": to_date,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching earnings calendar: {e}")
        return pd.DataFrame()


def get_income_statement(ticker: str, period: str = "annual", limit: int = 5, use_cache: bool = True) -> pd.DataFrame:
    """
    Get income statement data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        limit: Number of periods to fetch (default 5)
        use_cache: Use cached data if less than 24 hours old
    
    Returns:
        DataFrame with income statement data
    """
    cache_path = CACHE_DIR / f"income_{ticker}_{period}_{limit}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from API
    url = f"{BASE_URL}/income-statement/{ticker.upper()}"
    params = {
        "period": period,
        "limit": limit,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching income statement for {ticker}: {e}")
        return pd.DataFrame()


def get_earnings_surprises(ticker: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Get historical EPS surprises for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Use cached data if less than 24 hours old
    
    Returns:
        DataFrame with earnings surprise history
    """
    cache_path = CACHE_DIR / f"surprises_{ticker}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from API
    url = f"{BASE_URL}/earnings-surprises/{ticker.upper()}"
    params = {"apikey": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching earnings surprises for {ticker}: {e}")
        return pd.DataFrame()


def get_analyst_estimates(ticker: str, period: str = "annual", use_cache: bool = True) -> pd.DataFrame:
    """
    Get analyst consensus estimates for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        use_cache: Use cached data if less than 24 hours old
    
    Returns:
        DataFrame with analyst estimates
    """
    cache_path = CACHE_DIR / f"estimates_{ticker}_{period}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from API
    url = f"{BASE_URL}/analyst-estimates/{ticker.upper()}"
    params = {
        "period": period,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching analyst estimates for {ticker}: {e}")
        return pd.DataFrame()


def get_key_metrics(ticker: str, period: str = "annual", use_cache: bool = True) -> pd.DataFrame:
    """
    Get key valuation metrics (P/E, P/B, EV/EBITDA, etc.) for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: "annual" or "quarter"
        use_cache: Use cached data if less than 24 hours old
    
    Returns:
        DataFrame with key metrics
    """
    cache_path = CACHE_DIR / f"metrics_{ticker}_{period}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from API
    url = f"{BASE_URL}/key-metrics/{ticker.upper()}"
    params = {
        "period": period,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    except Exception as e:
        print(f"Error fetching key metrics for {ticker}: {e}")
        return pd.DataFrame()


# CLI functions

def cli_earnings_calendar(days: int = 7):
    """CLI: Display upcoming earnings calendar."""
    from_date = datetime.now().strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    df = get_earnings_calendar(from_date, to_date)
    
    if df.empty:
        print("No earnings data available")
        return
    
    print(f"\n=== Earnings Calendar ({from_date} to {to_date}) ===")
    
    # Select key columns
    cols = ["date", "symbol", "eps", "epsEstimated", "time", "revenue", "revenueEstimated"]
    display_cols = [c for c in cols if c in df.columns]
    
    if display_cols:
        print(f"\n{df[display_cols].to_string(index=False, max_rows=50)}")
        print(f"\nTotal: {len(df)} earnings reports")
    else:
        print(df.head(50).to_string(index=False))


def cli_income_statement(ticker: str, period: str = "annual"):
    """CLI: Display income statement."""
    df = get_income_statement(ticker, period)
    
    if df.empty:
        print(f"No income statement data for {ticker}")
        return
    
    print(f"\n=== Income Statement: {ticker.upper()} ({period}) ===")
    
    # Key metrics to display
    key_fields = ["date", "revenue", "grossProfit", "operatingIncome", "netIncome", "eps"]
    display_fields = [f for f in key_fields if f in df.columns]
    
    if display_fields:
        print(f"\n{df[display_fields].to_string(index=False)}")
    else:
        print(df.head().to_string(index=False))


def cli_earnings_surprises(ticker: str):
    """CLI: Show earnings surprise history."""
    df = get_earnings_surprises(ticker)
    
    if df.empty:
        print(f"No earnings surprise data for {ticker}")
        return
    
    print(f"\n=== Earnings Surprises: {ticker.upper()} ===")
    
    # Calculate surprise percentage if available
    if "actualEarningResult" in df.columns and "estimatedEarning" in df.columns:
        df["surprise_%"] = ((df["actualEarningResult"] - df["estimatedEarning"]) / df["estimatedEarning"].abs() * 100).round(2)
    
    print(f"\n{df.to_string(index=False, max_rows=20)}")


def cli_analyst_estimates(ticker: str, period: str = "annual"):
    """CLI: Display analyst consensus estimates."""
    df = get_analyst_estimates(ticker, period)
    
    if df.empty:
        print(f"No analyst estimates for {ticker}")
        return
    
    print(f"\n=== Analyst Estimates: {ticker.upper()} ({period}) ===")
    print(f"\n{df.to_string(index=False, max_rows=10)}")


def cli_key_metrics(ticker: str, period: str = "annual"):
    """CLI: Display key valuation metrics."""
    df = get_key_metrics(ticker, period)
    
    if df.empty:
        print(f"No key metrics for {ticker}")
        return
    
    print(f"\n=== Key Metrics: {ticker.upper()} ({period}) ===")
    
    # Focus on valuation metrics
    val_metrics = ["date", "peRatio", "priceToBookRatio", "evToEbitda", "marketCap", "debtToEquity"]
    display_metrics = [m for m in val_metrics if m in df.columns]
    
    if display_metrics:
        print(f"\n{df[display_metrics].to_string(index=False)}")
    else:
        print(df.head().to_string(index=False))


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        cli_earnings_calendar()
        sys.exit(0)
    
    command = args[0]
    
    if command == "fmp-calendar":
        days = int(args[1]) if len(args) > 1 else 7
        cli_earnings_calendar(days)
    elif command == "fmp-income":
        if len(args) < 2:
            print("Usage: fmp-income <ticker> [annual|quarter]")
            sys.exit(1)
        ticker = args[1]
        period = args[2] if len(args) > 2 else "annual"
        cli_income_statement(ticker, period)
    elif command == "fmp-surprises":
        if len(args) < 2:
            print("Usage: fmp-surprises <ticker>")
            sys.exit(1)
        cli_earnings_surprises(args[1])
    elif command == "fmp-estimates":
        if len(args) < 2:
            print("Usage: fmp-estimates <ticker> [annual|quarter]")
            sys.exit(1)
        ticker = args[1]
        period = args[2] if len(args) > 2 else "annual"
        cli_analyst_estimates(ticker, period)
    elif command == "fmp-metrics":
        if len(args) < 2:
            print("Usage: fmp-metrics <ticker> [annual|quarter]")
            sys.exit(1)
        ticker = args[1]
        period = args[2] if len(args) > 2 else "annual"
        cli_key_metrics(ticker, period)
    else:
        print(f"Unknown command: {command}")
        print("Available: fmp-calendar, fmp-income, fmp-surprises, fmp-estimates, fmp-metrics")
        sys.exit(1)
