#!/usr/bin/env python3
"""
Finnhub IPO Calendar — Upcoming & Recent IPOs with Performance Tracking

Data Source: Finnhub.io IPO Calendar API (Free tier: 60 calls/min)
Update: Real-time IPO calendar data
Free: Yes (API key required, free tier available)

Provides:
- Upcoming IPOs (next 30 days)
- Recent IPOs (last 30 days)
- IPO pricing and share details
- Performance tracking (IPO price vs current price)
- Exchange and date filtering

Usage:
    from modules import finnhub_ipo_calendar
    
    # Get upcoming IPOs
    df = finnhub_ipo_calendar.get_data(period='upcoming')
    
    # Get recent IPOs with performance
    df = finnhub_ipo_calendar.get_data(period='recent', days=30)
    
    # Custom date range
    df = finnhub_ipo_calendar.get_data(from_date='2026-01-01', to_date='2026-03-31')
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# API key from environment
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 4 * 3600  # 4 hours (IPOs update frequently)

# API configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def get_api_key() -> Optional[str]:
    """
    Get Finnhub API key from environment variable.
    Falls back to demo key if not set.
    
    Returns API key or demo key.
    """
    # Use environment variable (loaded from .env via dotenv)
    if FINNHUB_API_KEY:
        return FINNHUB_API_KEY
    
    # Use demo key as fallback (limited rate)
    return "demo"  # Finnhub provides a demo key for testing


def fetch_ipo_calendar(from_date: str, to_date: str, api_key: str) -> List[Dict]:
    """
    Fetch IPO calendar data from Finnhub API.
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        api_key: Finnhub API key
        
    Returns:
        List of IPO entries
    """
    url = f"{FINNHUB_BASE_URL}/calendar/ipo"
    params = {
        'from': from_date,
        'to': to_date,
        'token': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Finnhub returns {"ipoCalendar": [...]}
        return data.get('ipoCalendar', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IPO calendar: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return []


def get_current_price(symbol: str, api_key: str) -> Optional[float]:
    """
    Get current stock price using Finnhub quote endpoint.
    
    Args:
        symbol: Stock ticker symbol
        api_key: Finnhub API key
        
    Returns:
        Current price or None if not available
    """
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {
        'symbol': symbol,
        'token': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Current price is in 'c' field
        current_price = data.get('c')
        return float(current_price) if current_price and current_price > 0 else None
    except Exception:
        return None


def calculate_performance(ipos: List[Dict], api_key: str, fetch_prices: bool = True) -> List[Dict]:
    """
    Enrich IPO data with performance metrics.
    
    Args:
        ipos: List of IPO entries
        api_key: Finnhub API key
        fetch_prices: Whether to fetch current prices (can be slow)
        
    Returns:
        Enriched IPO list with performance data
    """
    enriched = []
    
    for ipo in ipos:
        entry = {
            'company': ipo.get('name', 'N/A'),
            'symbol': ipo.get('symbol', 'N/A'),
            'date': ipo.get('date', 'N/A'),
            'exchange': ipo.get('exchange', 'N/A'),
            'shares': ipo.get('totalSharesValue', 'N/A'),
            'price_range': f"{ipo.get('priceFrom', 'N/A')}-{ipo.get('priceTo', 'N/A')}",
            'status': ipo.get('status', 'N/A'),
            'ipo_price': None,
            'current_price': None,
            'return_pct': None
        }
        
        # IPO price is typically the midpoint or 'price' field
        price_from = ipo.get('priceFrom')
        price_to = ipo.get('priceTo')
        if price_from and price_to:
            try:
                entry['ipo_price'] = (float(price_from) + float(price_to)) / 2
            except (ValueError, TypeError):
                entry['ipo_price'] = ipo.get('price')
        else:
            entry['ipo_price'] = ipo.get('price')
        
        # Fetch current price if requested and symbol is valid
        symbol = entry['symbol']
        if fetch_prices and symbol and symbol != 'N/A' and entry['ipo_price']:
            time.sleep(0.1)  # Rate limiting (60 calls/min = ~1 per second safe)
            current_price = get_current_price(symbol, api_key)
            if current_price:
                entry['current_price'] = current_price
                try:
                    ipo_price = float(entry['ipo_price'])
                    entry['return_pct'] = ((current_price - ipo_price) / ipo_price) * 100
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
        
        enriched.append(entry)
    
    return enriched


def get_data(
    ticker: Optional[str] = None,
    period: str = 'upcoming',
    days: int = 30,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    exchange: Optional[str] = None,
    company_name: Optional[str] = None,
    fetch_prices: bool = True,
    **kwargs
) -> pd.DataFrame:
    """
    Fetch IPO calendar data from Finnhub.
    
    Args:
        ticker: Filter by specific ticker symbol (optional)
        period: 'upcoming' (next 30 days) or 'recent' (last 30 days)
        days: Number of days to look ahead/back (default: 30)
        from_date: Custom start date (YYYY-MM-DD)
        to_date: Custom end date (YYYY-MM-DD)
        exchange: Filter by exchange (e.g., 'NASDAQ', 'NYSE')
        company_name: Filter by company name (partial match)
        fetch_prices: Whether to fetch current prices for performance tracking
        
    Returns:
        DataFrame with columns: company, symbol, date, exchange, shares,
                                price_range, status, ipo_price, current_price, return_pct
    """
    # Get API key
    api_key = get_api_key()
    if not api_key:
        return pd.DataFrame({
            "error": ["No Finnhub API key found. Set FINNHUB_API_KEY env var or add to ~/.credentials/finnhub.json"]
        })
    
    # Determine date range
    if from_date and to_date:
        # Custom date range
        cache_key = f"{from_date}_{to_date}"
    elif period == 'upcoming':
        from_date = datetime.now().strftime('%Y-%m-%d')
        to_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        cache_key = f"upcoming_{days}"
    elif period == 'recent':
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        cache_key = f"recent_{days}"
    else:
        return pd.DataFrame({
            "error": [f"Invalid period: {period}. Use 'upcoming' or 'recent'"]
        })
    
    # Check cache
    cache_file = os.path.join(CACHE_DIR, f"finnhub_ipo_{cache_key}.json")
    if os.path.exists(cache_file):
        cache_age = time.time() - os.path.getmtime(cache_file)
        if cache_age < CACHE_TTL:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                df = pd.DataFrame(cached_data)
                # Apply filters
                df = apply_filters(df, ticker, exchange, company_name)
                return df
    
    # Fetch from API
    ipos = fetch_ipo_calendar(from_date, to_date, api_key)
    
    if not ipos:
        return pd.DataFrame({
            "message": [f"No IPOs found for period {from_date} to {to_date}"]
        })
    
    # Enrich with performance data
    enriched_ipos = calculate_performance(ipos, api_key, fetch_prices)
    
    # Create DataFrame
    df = pd.DataFrame(enriched_ipos)
    
    # Sort by date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date', ascending=(period == 'upcoming'))
    
    # Add fetch timestamp
    df['fetch_time'] = datetime.now().isoformat()
    
    # Cache the results
    cache_data = df.to_dict('records')
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, default=str)
    
    # Apply filters
    df = apply_filters(df, ticker, exchange, company_name)
    
    return df


def apply_filters(
    df: pd.DataFrame,
    ticker: Optional[str] = None,
    exchange: Optional[str] = None,
    company_name: Optional[str] = None
) -> pd.DataFrame:
    """Apply filters to the IPO DataFrame."""
    if df.empty or 'error' in df.columns or 'message' in df.columns:
        return df
    
    if ticker and 'symbol' in df.columns:
        df = df[df['symbol'].str.contains(ticker, case=False, na=False)]
    
    if exchange and 'exchange' in df.columns:
        df = df[df['exchange'].str.contains(exchange, case=False, na=False)]
    
    if company_name and 'company' in df.columns:
        df = df[df['company'].str.contains(company_name, case=False, na=False)]
    
    return df


if __name__ == "__main__":
    import sys
    
    # CLI test interface
    if len(sys.argv) > 1:
        if sys.argv[1] == 'upcoming':
            print("=== Upcoming IPOs (next 30 days) ===")
            result = get_data(period='upcoming')
        elif sys.argv[1] == 'recent':
            print("=== Recent IPOs (last 30 days) ===")
            result = get_data(period='recent')
        elif sys.argv[1] == 'test':
            print("=== Testing Finnhub IPO Calendar Module ===")
            print("\n1. Checking API key...")
            api_key = get_api_key()
            print(f"   API key found: {'Yes' if api_key else 'No'}")
            
            print("\n2. Fetching upcoming IPOs (without price tracking for speed)...")
            result = get_data(period='upcoming', days=30, fetch_prices=False)
            print(f"   Found {len(result)} upcoming IPOs")
            
            print("\n3. Fetching recent IPOs...")
            result = get_data(period='recent', days=30, fetch_prices=False)
            print(f"   Found {len(result)} recent IPOs")
            
            if not result.empty and 'error' not in result.columns:
                print("\n=== Sample Data ===")
                print(result.head(5).to_string())
        else:
            ticker = sys.argv[1]
            print(f"=== Searching for ticker: {ticker} ===")
            result = get_data(ticker=ticker, fetch_prices=False)
    else:
        print("=== Finnhub IPO Calendar - Default View ===")
        result = get_data(period='upcoming', fetch_prices=False)
    
    if not result.empty:
        print(result.to_json(orient='records', date_format='iso', indent=2))
    else:
        print("No data returned")
