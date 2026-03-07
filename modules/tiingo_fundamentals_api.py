"""
Tiingo Fundamentals API — Company Financials & Metrics

Provides access to Tiingo's fundamentals data including financial statements,
daily metrics (PE, market cap, etc.), and earnings dates for US stocks.

Source: https://api.tiingo.com/tiingo/fundamentals/
Free tier: 500 calls/hour, 50,000 calls/day

Use cases:
- Fundamental analysis
- Financial statement screening
- Earnings calendar tracking
- Valuation metrics (PE, PEG, etc.)
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "tiingo_fundamentals"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.tiingo.com/tiingo/fundamentals"
API_KEY = os.getenv("TIINGO_API_KEY", "demo")


def fetch_statements(ticker: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch financial statements (income statement, balance sheet, cash flow).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        use_cache: Use cached data if available (24hr TTL)
    
    Returns:
        DataFrame with quarterly and annual financial statements
    """
    ticker = ticker.upper()
    cache_key = f"statements_{ticker}"
    if start_date:
        cache_key += f"_{start_date}"
    if end_date:
        cache_key += f"_{end_date}"
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Build URL with parameters
    url = f"{BASE_URL}/{ticker}/statements"
    params = {"token": API_KEY}
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return pd.DataFrame()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return pd.DataFrame(data)
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Ticker {ticker} not found")
        else:
            print(f"HTTP error fetching statements for {ticker}: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching statements for {ticker}: {e}")
        return pd.DataFrame()


def get_daily_metrics(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """
    Get current fundamental metrics (PE ratio, market cap, dividends, etc.).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        use_cache: Use cached data if available (24hr TTL)
    
    Returns:
        Dict with daily metrics including PE, marketCap, enterpriseVal, etc.
    """
    ticker = ticker.upper()
    cache_path = CACHE_DIR / f"daily_{ticker}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/{ticker}/daily"
    params = {"token": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None
        
        # Get most recent entry
        latest = data[0] if isinstance(data, list) else data
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(latest, f, indent=2)
        
        return latest
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Ticker {ticker} not found")
        else:
            print(f"HTTP error fetching daily metrics for {ticker}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching daily metrics for {ticker}: {e}")
        return None


def get_earnings_dates(ticker: str, use_cache: bool = True) -> List[Dict]:
    """
    Get earnings announcement dates (past and upcoming).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        use_cache: Use cached data if available (24hr TTL)
    
    Returns:
        List of dicts with earnings dates and metadata
    """
    ticker = ticker.upper()
    cache_path = CACHE_DIR / f"earnings_{ticker}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API - use definitions endpoint which includes earnings metadata
    url = f"{BASE_URL}/{ticker}/definitions"
    params = {"token": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract earnings-related dates
        earnings_data = []
        if isinstance(data, list):
            for entry in data:
                if "date" in entry:
                    earnings_data.append({
                        "date": entry.get("date"),
                        "quarter": entry.get("quarter"),
                        "year": entry.get("year")
                    })
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(earnings_data, f, indent=2)
        
        return earnings_data
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Ticker {ticker} not found")
        else:
            print(f"HTTP error fetching earnings dates for {ticker}: {e}")
        return []
    except Exception as e:
        print(f"Error fetching earnings dates for {ticker}: {e}")
        return []


def search_tickers(query: str, use_cache: bool = True) -> List[Dict]:
    """
    Search for ticker symbols by company name or ticker.
    
    Args:
        query: Search query (company name or partial ticker)
        use_cache: Use cached data if available (24hr TTL)
    
    Returns:
        List of matching tickers with metadata
    """
    query_lower = query.lower()
    cache_path = CACHE_DIR / f"search_{query_lower.replace(' ', '_')}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Tiingo doesn't have a dedicated search endpoint for fundamentals
    # We can use the main /tiingo/utilities/search endpoint
    search_url = "https://api.tiingo.com/tiingo/utilities/search"
    params = {"query": query, "token": API_KEY}
    
    try:
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if isinstance(data, list):
            for item in data:
                results.append({
                    "ticker": item.get("ticker"),
                    "name": item.get("name"),
                    "exchange": item.get("exchange"),
                    "assetType": item.get("assetType")
                })
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    except Exception as e:
        print(f"Error searching tickers for '{query}': {e}")
        return []


# CLI functions
def cli_statements(ticker: str):
    """CLI: Display financial statements for a ticker."""
    df = fetch_statements(ticker)
    if df.empty:
        print(f"No statements data for {ticker}")
        return
    
    print(f"\n=== Financial Statements: {ticker.upper()} ===")
    print(f"\n{df.head(10).to_string()}")
    print(f"\nTotal records: {len(df)}")


def cli_daily_metrics(ticker: str):
    """CLI: Display daily fundamental metrics."""
    data = get_daily_metrics(ticker)
    if not data:
        print(f"No daily metrics for {ticker}")
        return
    
    print(f"\n=== Daily Metrics: {ticker.upper()} ===")
    print(f"Date: {data.get('date', 'N/A')}")
    
    metrics = {
        "Market Cap": data.get("marketCap"),
        "Enterprise Value": data.get("enterpriseVal"),
        "PE Ratio": data.get("peRatio"),
        "PB Ratio": data.get("pbRatio"),
        "Dividend Yield": data.get("divYield"),
        "ROE": data.get("roe"),
        "ROA": data.get("roa")
    }
    
    for name, value in metrics.items():
        if value is not None:
            print(f"{name:20s}: {value}")


def cli_earnings(ticker: str):
    """CLI: Display earnings dates."""
    earnings = get_earnings_dates(ticker)
    if not earnings:
        print(f"No earnings data for {ticker}")
        return
    
    print(f"\n=== Earnings Dates: {ticker.upper()} ===")
    for item in earnings[:10]:
        print(f"Date: {item.get('date')} | Q{item.get('quarter')} {item.get('year')}")


def cli_search(query: str):
    """CLI: Search for tickers."""
    results = search_tickers(query)
    if not results:
        print(f"No results for '{query}'")
        return
    
    print(f"\n=== Search Results: '{query}' ===")
    for item in results[:10]:
        print(f"{item.get('ticker'):10s} | {item.get('name'):40s} | {item.get('exchange')}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        print("Usage: python tiingo_fundamentals_api.py <command> <args>")
        print("Commands: statements, daily, earnings, search")
        sys.exit(0)
    
    command = args[0]
    
    if command == "statements" and len(args) > 1:
        cli_statements(args[1])
    elif command == "daily" and len(args) > 1:
        cli_daily_metrics(args[1])
    elif command == "earnings" and len(args) > 1:
        cli_earnings(args[1])
    elif command == "search" and len(args) > 1:
        cli_search(args[1])
    else:
        print(f"Unknown command or missing args: {' '.join(args)}")
        sys.exit(1)
