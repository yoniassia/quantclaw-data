#!/usr/bin/env python3
"""
EODHD Government Bonds — Historical & EOD Government Bond Data

EODHD provides historical and end-of-day data for government bonds worldwide, 
including yields and prices. Covers major markets like US, EU, and Asia.

Source: https://eodhd.com/financial-apis/government-bonds-data-api/
Category: Fixed Income & Credit
Free tier: true - 100 requests per day, historical data up to 1 year
Update frequency: daily
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

# EODHD API Configuration
EODHD_BASE_URL = "https://eodhd.com/api"
EODHD_API_KEY = os.environ.get("EODHD_API_KEY", "demo")

# ========== GOVERNMENT BOND TICKER REGISTRY ==========

BOND_TICKERS = {
    # ===== US TREASURIES =====
    'US_TREASURIES': {
        'US1M.GBOND': '1-Month US Treasury',
        'US3M.GBOND': '3-Month US Treasury',
        'US6M.GBOND': '6-Month US Treasury',
        'US1Y.GBOND': '1-Year US Treasury',
        'US2Y.GBOND': '2-Year US Treasury',
        'US3Y.GBOND': '3-Year US Treasury',
        'US5Y.GBOND': '5-Year US Treasury',
        'US7Y.GBOND': '7-Year US Treasury',
        'US10Y.GBOND': '10-Year US Treasury',
        'US20Y.GBOND': '20-Year US Treasury',
        'US30Y.GBOND': '30-Year US Treasury',
    },
    
    # ===== EUROPEAN BONDS =====
    'EUROPEAN_BONDS': {
        'DE1Y.GBOND': '1-Year German Bund',
        'DE2Y.GBOND': '2-Year German Bund',
        'DE5Y.GBOND': '5-Year German Bund',
        'DE10Y.GBOND': '10-Year German Bund',
        'DE30Y.GBOND': '30-Year German Bund',
        'GB2Y.GBOND': '2-Year UK Gilt',
        'GB5Y.GBOND': '5-Year UK Gilt',
        'GB10Y.GBOND': '10-Year UK Gilt',
        'GB30Y.GBOND': '30-Year UK Gilt',
        'FR10Y.GBOND': '10-Year French OAT',
        'IT10Y.GBOND': '10-Year Italian BTP',
        'ES10Y.GBOND': '10-Year Spanish Bond',
    },
    
    # ===== ASIAN BONDS =====
    'ASIAN_BONDS': {
        'JP2Y.GBOND': '2-Year Japanese JGB',
        'JP5Y.GBOND': '5-Year Japanese JGB',
        'JP10Y.GBOND': '10-Year Japanese JGB',
        'JP30Y.GBOND': '30-Year Japanese JGB',
        'CN10Y.GBOND': '10-Year Chinese Bond',
        'AU10Y.GBOND': '10-Year Australian Bond',
    },
}


def get_bond_yield(ticker: str, period: str = "d") -> Optional[Dict]:
    """
    Fetch latest bond yield data for a specific ticker.
    
    Args:
        ticker: Bond ticker symbol (e.g., 'US10Y.GBOND')
        period: Data period - 'd' (daily), 'w' (weekly), 'm' (monthly)
        
    Returns:
        Dict with latest yield data including date, open, high, low, close, adjusted_close
        Returns None if request fails
        
    Example:
        >>> data = get_bond_yield('US10Y.GBOND')
        >>> print(data['close'])  # Latest 10Y Treasury yield
    """
    try:
        url = f"{EODHD_BASE_URL}/eod/{ticker}"
        params = {
            'api_token': EODHD_API_KEY,
            'period': period,
            'fmt': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            return None
            
        # Return the latest data point
        latest = data[-1]
        return {
            'ticker': ticker,
            'date': latest.get('date'),
            'open': latest.get('open'),
            'high': latest.get('high'),
            'low': latest.get('low'),
            'close': latest.get('close'),
            'adjusted_close': latest.get('adjusted_close'),
            'volume': latest.get('volume', 0),
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bond yield for {ticker}: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Error parsing bond yield data for {ticker}: {e}")
        return None


def get_us_treasury_yields() -> Dict[str, Optional[float]]:
    """
    Fetch current yields for all major US Treasury maturities.
    
    Returns:
        Dict mapping maturity labels to current yields
        
    Example:
        >>> yields = get_us_treasury_yields()
        >>> print(f"10Y: {yields['10Y']}%, 2Y: {yields['2Y']}%")
    """
    maturities = {
        '1M': 'US1M.GBOND',
        '3M': 'US3M.GBOND',
        '6M': 'US6M.GBOND',
        '1Y': 'US1Y.GBOND',
        '2Y': 'US2Y.GBOND',
        '3Y': 'US3Y.GBOND',
        '5Y': 'US5Y.GBOND',
        '7Y': 'US7Y.GBOND',
        '10Y': 'US10Y.GBOND',
        '20Y': 'US20Y.GBOND',
        '30Y': 'US30Y.GBOND',
    }
    
    yields = {}
    for label, ticker in maturities.items():
        data = get_bond_yield(ticker)
        yields[label] = data['close'] if data else None
        
    return yields


def get_global_bond_yields() -> Dict[str, Dict[str, Optional[float]]]:
    """
    Fetch current 10-year government bond yields for major economies.
    
    Returns:
        Dict mapping country codes to yield data
        
    Example:
        >>> yields = get_global_bond_yields()
        >>> print(f"US: {yields['US']['yield']}%")
        >>> print(f"Germany: {yields['DE']['yield']}%")
    """
    benchmarks = {
        'US': 'US10Y.GBOND',
        'DE': 'DE10Y.GBOND',
        'GB': 'GB10Y.GBOND',
        'JP': 'JP10Y.GBOND',
        'FR': 'FR10Y.GBOND',
        'IT': 'IT10Y.GBOND',
        'ES': 'ES10Y.GBOND',
        'CN': 'CN10Y.GBOND',
        'AU': 'AU10Y.GBOND',
    }
    
    results = {}
    for country, ticker in benchmarks.items():
        data = get_bond_yield(ticker)
        results[country] = {
            'ticker': ticker,
            'yield': data['close'] if data else None,
            'date': data['date'] if data else None,
        }
        
    return results


def get_yield_spread(ticker1: str, ticker2: str) -> Optional[Dict]:
    """
    Calculate the yield spread between two bonds.
    
    Args:
        ticker1: First bond ticker (e.g., 'US10Y.GBOND')
        ticker2: Second bond ticker (e.g., 'US2Y.GBOND')
        
    Returns:
        Dict with spread data and component yields
        Returns None if either fetch fails
        
    Example:
        >>> spread = get_yield_spread('US10Y.GBOND', 'US2Y.GBOND')
        >>> print(f"10Y-2Y spread: {spread['spread']} bps")
    """
    data1 = get_bond_yield(ticker1)
    data2 = get_bond_yield(ticker2)
    
    if not data1 or not data2:
        return None
        
    spread = data1['close'] - data2['close']
    spread_bps = spread * 100  # Convert to basis points
    
    return {
        'ticker1': ticker1,
        'ticker2': ticker2,
        'yield1': data1['close'],
        'yield2': data2['close'],
        'spread': spread,
        'spread_bps': spread_bps,
        'date1': data1['date'],
        'date2': data2['date'],
    }


def get_yield_history(ticker: str, start_date: str, end_date: Optional[str] = None, period: str = "d") -> Optional[List[Dict]]:
    """
    Fetch historical bond yield data for a date range.
    
    Args:
        ticker: Bond ticker symbol (e.g., 'US10Y.GBOND')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
        period: Data period - 'd' (daily), 'w' (weekly), 'm' (monthly)
        
    Returns:
        List of dicts with historical yield data
        Returns None if request fails
        
    Example:
        >>> history = get_yield_history('US10Y.GBOND', '2024-01-01', '2024-12-31')
        >>> avg_yield = sum(d['close'] for d in history) / len(history)
    """
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        url = f"{EODHD_BASE_URL}/eod/{ticker}"
        params = {
            'api_token': EODHD_API_KEY,
            'period': period,
            'fmt': 'json',
            'from': start_date,
            'to': end_date,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            return None
            
        # Format results
        history = []
        for point in data:
            history.append({
                'date': point.get('date'),
                'open': point.get('open'),
                'high': point.get('high'),
                'low': point.get('low'),
                'close': point.get('close'),
                'adjusted_close': point.get('adjusted_close'),
                'volume': point.get('volume', 0),
            })
            
        return history
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching yield history for {ticker}: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing yield history data for {ticker}: {e}")
        return None


def get_yield_curve(country: str = 'US', date: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Construct a yield curve for a specific country.
    
    Args:
        country: Country code ('US', 'DE', 'GB', 'JP')
        date: Date for historical curve (defaults to latest)
        
    Returns:
        Dict mapping maturities to yields
        
    Example:
        >>> curve = get_yield_curve('US')
        >>> print(f"Curve slope (10Y-2Y): {curve['10Y'] - curve['2Y']} bps")
    """
    if country == 'US':
        return get_us_treasury_yields()
    
    # For other countries, fetch available maturities
    maturity_map = {
        'DE': ['1Y', '2Y', '5Y', '10Y', '30Y'],
        'GB': ['2Y', '5Y', '10Y', '30Y'],
        'JP': ['2Y', '5Y', '10Y', '30Y'],
    }
    
    if country not in maturity_map:
        print(f"Country {country} not supported. Use: US, DE, GB, JP")
        return None
        
    curve = {}
    for maturity in maturity_map[country]:
        ticker = f"{country}{maturity}.GBOND"
        data = get_bond_yield(ticker)
        curve[maturity] = data['close'] if data else None
        
    return curve


# ========== CLI FOR TESTING ==========

if __name__ == "__main__":
    print("=" * 60)
    print("EODHD Government Bonds Module - Test Suite")
    print("=" * 60)
    
    # Test 1: Single bond yield
    print("\n[Test 1] US 10Y Treasury Yield:")
    us10y = get_bond_yield('US10Y.GBOND')
    if us10y:
        print(json.dumps(us10y, indent=2))
    else:
        print("Failed to fetch US10Y data")
    
    # Test 2: US Treasury curve
    print("\n[Test 2] US Treasury Yield Curve:")
    us_curve = get_us_treasury_yields()
    for maturity, yld in us_curve.items():
        if yld:
            print(f"  {maturity:>3s}: {yld:>6.3f}%")
    
    # Test 3: Global 10Y yields
    print("\n[Test 3] Global 10Y Government Bond Yields:")
    global_yields = get_global_bond_yields()
    for country, data in global_yields.items():
        if data['yield']:
            print(f"  {country}: {data['yield']:>6.3f}% (as of {data['date']})")
    
    # Test 4: Yield spread
    print("\n[Test 4] US 10Y-2Y Yield Spread:")
    spread = get_yield_spread('US10Y.GBOND', 'US2Y.GBOND')
    if spread:
        print(f"  10Y: {spread['yield1']:.3f}%")
        print(f"  2Y:  {spread['yield2']:.3f}%")
        print(f"  Spread: {spread['spread']:.3f}% ({spread['spread_bps']:.1f} bps)")
    else:
        print("Failed to calculate spread")
    
    # Test 5: Historical data (last 30 days)
    print("\n[Test 5] US 10Y Historical Data (last 30 days):")
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    history = get_yield_history('US10Y.GBOND', start)
    if history:
        print(f"  Retrieved {len(history)} data points")
        print(f"  First: {history[0]['date']} - {history[0]['close']:.3f}%")
        print(f"  Last:  {history[-1]['date']} - {history[-1]['close']:.3f}%")
        avg = sum(d['close'] for d in history) / len(history)
        print(f"  Average: {avg:.3f}%")
    else:
        print("Failed to fetch historical data")
    
    print("\n" + "=" * 60)
    print("Module Status: ✅ OPERATIONAL")
    print("=" * 60)
