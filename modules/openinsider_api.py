"""
OpenInsider — SEC Form 4 Insider Trading Data

Scrapes insider trading data from OpenInsider.com. Provides real-time alerts on executive trades
aggregated from SEC Form 4 filings.

Source: http://openinsider.com
Category: Insider & Institutional

Use cases:
- Track insider buying/selling activity
- Identify cluster buying (multiple insiders buying same stock)
- Monitor large insider trades
- Sentiment analysis for quant trading
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
from pathlib import Path
import json
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).parent.parent / "cache" / "openinsider_api"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://openinsider.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def _parse_insider_table(html_content: str) -> List[Dict]:
    """Parse OpenInsider HTML table into list of dicts."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main data table
    table = soup.find('table', {'class': 'tinytable'})
    if not table:
        return []
    
    # Get headers
    headers = []
    header_row = table.find('tr')
    if header_row:
        for th in header_row.find_all(['th', 'td']):
            headers.append(th.get_text(strip=True))
    
    # Parse rows
    records = []
    rows = table.find_all('tr')[1:]  # Skip header row
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 10:  # Need at least basic columns
            continue
        
        try:
            # Extract data - OpenInsider typical columns:
            # X, Filing Date, Trade Date, Ticker, Company, Insider, Title, Trade Type, Price, Qty, Owned, Value
            record = {
                'filing_date': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                'trade_date': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                'ticker': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                'company': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                'insider_name': cols[5].get_text(strip=True) if len(cols) > 5 else '',
                'title': cols[6].get_text(strip=True) if len(cols) > 6 else '',
                'trade_type': cols[7].get_text(strip=True) if len(cols) > 7 else '',
                'price': cols[8].get_text(strip=True) if len(cols) > 8 else '',
                'qty': cols[9].get_text(strip=True) if len(cols) > 9 else '',
                'owned': cols[10].get_text(strip=True) if len(cols) > 10 else '',
                'value': cols[11].get_text(strip=True) if len(cols) > 11 else '',
            }
            records.append(record)
        except Exception as e:
            # Skip malformed rows
            continue
    
    return records


def get_latest_insider_buys(days: int = 7, use_cache: bool = True) -> pd.DataFrame:
    """
    Get recent insider purchase activity.
    
    Args:
        days: Number of days to look back (default: 7)
        use_cache: Use cached data if available and fresh (default: True)
    
    Returns:
        DataFrame with insider buying activity
    """
    cache_path = CACHE_DIR / f"insider_buys_{days}d.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from OpenInsider
    # URL for latest insider buying
    url = f"{BASE_URL}/screener?s=&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        records = _parse_insider_table(response.text)
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error fetching insider buys: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        return pd.DataFrame()


def get_insider_trades_by_ticker(ticker: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Get insider trading activity for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        use_cache: Use cached data if available and fresh (default: True)
    
    Returns:
        DataFrame with insider trades for the ticker
    """
    cache_path = CACHE_DIR / f"ticker_{ticker.upper()}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from OpenInsider
    url = f"{BASE_URL}/screener?s={ticker.upper()}&o=&pl=&ph=&ll=&lh=&fd=730&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=500&page=1"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        records = _parse_insider_table(response.text)
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error fetching trades for {ticker}: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        return pd.DataFrame()


def get_cluster_buys(days: int = 30, use_cache: bool = True) -> pd.DataFrame:
    """
    Get cluster buying activity (2+ insiders buying same stock).
    
    Args:
        days: Number of days to look back (default: 30)
        use_cache: Use cached data if available and fresh (default: True)
    
    Returns:
        DataFrame with cluster buying activity
    """
    cache_path = CACHE_DIR / f"cluster_buys_{days}d.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from OpenInsider - cluster buying screen
    url = f"{BASE_URL}/screener?s=&o=&pl=&ph=&ll=&lh=&fd={days}&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=1&nfl=2&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        records = _parse_insider_table(response.text)
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error fetching cluster buys: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        return pd.DataFrame()


def get_large_trades(min_value: int = 1000000, use_cache: bool = True) -> pd.DataFrame:
    """
    Get large insider trades (by dollar value).
    
    Args:
        min_value: Minimum trade value in USD (default: 1,000,000)
        use_cache: Use cached data if available and fresh (default: True)
    
    Returns:
        DataFrame with large insider trades
    """
    cache_path = CACHE_DIR / f"large_trades_{min_value}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    
    # Fetch from OpenInsider - filter by value
    # vl = value low (in thousands)
    value_thousands = min_value // 1000
    url = f"{BASE_URL}/screener?s=&o=&pl=&ph=&ll=&lh=&fd=30&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&vl={value_thousands}&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        records = _parse_insider_table(response.text)
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error fetching large trades: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        return pd.DataFrame()


# CLI functions
def cli_latest_buys(days: int = 7):
    """CLI: Display recent insider buying activity."""
    df = get_latest_insider_buys(days)
    
    if df.empty:
        print(f"No insider buys found in last {days} days")
        return
    
    print(f"\n=== Insider Buys (Last {days} Days) ===")
    print(f"Total Transactions: {len(df)}\n")
    
    # Show top 10
    display_cols = ['trade_date', 'ticker', 'company', 'insider_name', 'title', 'value', 'qty']
    available_cols = [col for col in display_cols if col in df.columns]
    
    print(df[available_cols].head(10).to_string(index=False))


def cli_ticker_trades(ticker: str):
    """CLI: Show insider trades for specific ticker."""
    df = get_insider_trades_by_ticker(ticker)
    
    if df.empty:
        print(f"No insider trades found for {ticker}")
        return
    
    print(f"\n=== Insider Trades: {ticker.upper()} ===")
    print(f"Total Transactions: {len(df)}\n")
    
    display_cols = ['trade_date', 'insider_name', 'title', 'trade_type', 'value', 'qty', 'price']
    available_cols = [col for col in display_cols if col in df.columns]
    
    print(df[available_cols].head(20).to_string(index=False))


def cli_cluster_buys(days: int = 30):
    """CLI: Show cluster buying activity."""
    df = get_cluster_buys(days)
    
    if df.empty:
        print(f"No cluster buys found in last {days} days")
        return
    
    print(f"\n=== Cluster Buys (Last {days} Days) ===")
    print("Multiple insiders buying same stock\n")
    
    display_cols = ['trade_date', 'ticker', 'company', 'insider_name', 'value']
    available_cols = [col for col in display_cols if col in df.columns]
    
    # Group by ticker to show clustering
    if 'ticker' in df.columns:
        ticker_counts = df['ticker'].value_counts()
        print("Top Clustered Stocks:")
        for ticker, count in ticker_counts.head(10).items():
            print(f"  {ticker}: {count} insiders")
        print()
    
    print(df[available_cols].head(15).to_string(index=False))


def cli_large_trades(min_value: int = 1000000):
    """CLI: Show large insider trades."""
    df = get_large_trades(min_value)
    
    if df.empty:
        print(f"No large trades found (>${min_value:,})")
        return
    
    print(f"\n=== Large Insider Trades (>${min_value:,}) ===")
    print(f"Total Transactions: {len(df)}\n")
    
    display_cols = ['trade_date', 'ticker', 'company', 'insider_name', 'title', 'trade_type', 'value']
    available_cols = [col for col in display_cols if col in df.columns]
    
    print(df[available_cols].head(15).to_string(index=False))


# CLI argument handling
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if not args:
        cli_latest_buys()
        sys.exit(0)
    
    command = args[0]
    
    if command == "openinsider-buys":
        days = int(args[1]) if len(args) > 1 else 7
        cli_latest_buys(days)
    elif command == "openinsider-ticker":
        if len(args) < 2:
            print("Usage: openinsider-ticker TICKER")
            sys.exit(1)
        cli_ticker_trades(args[1])
    elif command == "openinsider-cluster":
        days = int(args[1]) if len(args) > 1 else 30
        cli_cluster_buys(days)
    elif command == "openinsider-large":
        min_value = int(args[1]) if len(args) > 1 else 1000000
        cli_large_trades(min_value)
    else:
        print(f"Unknown command: {command}")
        print("Available: openinsider-buys, openinsider-ticker, openinsider-cluster, openinsider-large")
        sys.exit(1)
