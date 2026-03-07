"""
Trading Economics Bond Yields API — Government Bond Yields Worldwide

Provides access to global government bond yields, yield curves, and spreads
via Trading Economics API with web scraping fallback for public data.

Source: https://api.tradingeconomics.com/bonds
Category: Fixed Income & Credit

Use cases:
- Track 10Y government bond yields globally
- Compare yield spreads between countries
- Monitor yield curve changes
- Analyze fixed income market sentiment
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

CACHE_DIR = Path(__file__).parent.parent / "cache" / "trading_economics_bonds"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.tradingeconomics.com"
WEB_URL = "https://tradingeconomics.com"
API_KEY = os.getenv("TRADING_ECONOMICS_API_KEY", "guest:guest")


def _fetch_with_cache(endpoint: str, cache_name: str, cache_hours: int = 6, use_cache: bool = True) -> Optional[Dict | List]:
    """Helper function to fetch data with caching."""
    cache_path = CACHE_DIR / f"{cache_name}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=cache_hours):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}{endpoint}"
    separator = '&' if '?' in url else '?'
    url = f"{url}{separator}c={API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {endpoint}: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def _scrape_bonds_page(use_cache: bool = True) -> Optional[List[Dict]]:
    """Fallback: scrape public bonds page."""
    cache_path = CACHE_DIR / "bonds_scrape.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=6):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    try:
        response = requests.get(f"{WEB_URL}/bonds", timeout=15)
        response.raise_for_status()
        html = response.text
        
        # Parse bond data from HTML table (simplified)
        bonds = []
        
        # Look for common patterns in bond data
        # Pattern: Country name followed by yield percentage
        country_pattern = r'<td[^>]*>([^<]+)</td>\s*<td[^>]*>([\d.]+)%?</td>'
        matches = re.findall(country_pattern, html)
        
        for country, value in matches:
            if country and value:
                bonds.append({
                    'Country': country.strip(),
                    'Last': float(value),
                    'Symbol': f"{country.strip().replace(' ', '')[:2].upper()}10Y",
                    'LastUpdate': datetime.now().isoformat()
                })
        
        if bonds:
            # Cache the scraped data
            with open(cache_path, 'w') as f:
                json.dump(bonds, f, indent=2)
        
        return bonds if bonds else None
    except Exception as e:
        print(f"Error scraping bonds page: {e}")
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None


def get_bond_yields(country: str = 'united states', use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get bond yields for a specific country.
    
    Args:
        country: Country name (e.g., 'united states', 'germany', 'japan')
        use_cache: Whether to use cached data
        
    Returns:
        List of bond yield data dictionaries with symbol, value, date
    """
    # Try API first with bonds endpoint
    endpoint = f"/bonds"
    data = _fetch_with_cache(endpoint, "all_bonds", cache_hours=6, use_cache=use_cache)
    
    # Fallback to scraping
    if not data:
        data = _scrape_bonds_page(use_cache=use_cache)
    
    if not data:
        return None
    
    # Filter for specific country
    country_lower = country.lower()
    results = [item for item in data if country_lower in item.get('Country', '').lower()]
    
    return results if results else None


def get_global_yields(use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get global government bond yields overview.
    
    Returns:
        List of major countries' 10Y bond yields
    """
    # Try API first
    endpoint = "/bonds"
    data = _fetch_with_cache(endpoint, "all_bonds", cache_hours=6, use_cache=use_cache)
    
    # Fallback to scraping
    if not data:
        data = _scrape_bonds_page(use_cache=use_cache)
    
    if not data:
        return None
    
    # Filter for major countries
    major_countries = ['united states', 'germany', 'japan', 'united kingdom', 'france', 'italy', 'spain', 'canada', 'australia', 'china']
    
    results = []
    for item in data:
        country = item.get('Country', '').lower()
        if any(major in country for major in major_countries):
            results.append({
                'country': item.get('Country'),
                'symbol': item.get('Symbol', ''),
                'yield': item.get('Last'),
                'date': item.get('LastUpdate')
            })
    
    return results[:10] if results else None


def get_yield_by_maturity(country: str, maturity: str = '10y', use_cache: bool = True) -> Optional[Dict]:
    """
    Get specific maturity bond yield for a country.
    
    Args:
        country: Country name
        maturity: Maturity (e.g., '2y', '5y', '10y', '30y')
        use_cache: Whether to use cached data
        
    Returns:
        Bond yield data for specified maturity
    """
    yields = get_bond_yields(country, use_cache=use_cache)
    
    if not yields:
        return None
    
    # For now, return first match (most APIs default to 10Y)
    # TODO: Add maturity filtering when available
    return yields[0] if yields else None


def get_yield_spread(country1: str, country2: str, maturity: str = '10y', use_cache: bool = True) -> Optional[Dict]:
    """
    Calculate yield spread between two countries.
    
    Args:
        country1: First country
        country2: Second country
        maturity: Bond maturity to compare
        use_cache: Whether to use cached data
        
    Returns:
        Dictionary with spread data
    """
    yield1 = get_yield_by_maturity(country1, maturity, use_cache=use_cache)
    yield2 = get_yield_by_maturity(country2, maturity, use_cache=use_cache)
    
    if not yield1 or not yield2:
        return None
    
    spread = yield1.get('Last', 0) - yield2.get('Last', 0)
    
    return {
        'country1': country1.title(),
        'country2': country2.title(),
        'maturity': maturity,
        'yield1': yield1.get('Last'),
        'yield2': yield2.get('Last'),
        'spread': spread,
        'spread_bps': round(spread * 100, 2),
        'symbol1': yield1.get('Symbol'),
        'symbol2': yield2.get('Symbol'),
        'date': yield1.get('LastUpdate')
    }


def get_yield_history(symbol: str, days: int = 30, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get historical bond yield data for a symbol.
    
    Args:
        symbol: Bond symbol (e.g., 'US10Y', 'DE10Y')
        days: Number of days of history
        use_cache: Whether to use cached data
        
    Returns:
        List of historical yield data points
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Try different historical endpoints
    endpoints = [
        f"/historical/symbol/{symbol}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
        f"/historical/bonds/{symbol}",
        f"/bonds/historical/{symbol}"
    ]
    
    for endpoint in endpoints:
        cache_name = f"history_{symbol}_{days}d"
        data = _fetch_with_cache(endpoint, cache_name, cache_hours=24, use_cache=use_cache)
        if data:
            return data
    
    return None


def demo() -> None:
    """Demonstrate module capabilities."""
    print("=" * 60)
    print("Trading Economics Bond Yields API Demo")
    print("=" * 60)
    
    # Test 1: US bond yields
    print("\n1. US Government Bond Yields:")
    us_yields = get_bond_yields('united states')
    if us_yields:
        for bond in us_yields[:3]:
            print(f"   {bond.get('Symbol', 'N/A')}: {bond.get('Last', 'N/A')}%")
    else:
        print("   No data available")
    
    # Test 2: Global 10Y yields
    print("\n2. Global 10Y Bond Yields:")
    global_yields = get_global_yields()
    if global_yields:
        for item in global_yields:
            print(f"   {item['country']}: {item['yield']}%")
    else:
        print("   No data available")
    
    # Test 3: Specific maturity
    print("\n3. Germany 10Y Yield:")
    de10y = get_yield_by_maturity('germany', '10y')
    if de10y:
        print(f"   {de10y.get('Symbol', 'DE10Y')}: {de10y.get('Last', 'N/A')}%")
    else:
        print("   No data available")
    
    # Test 4: Yield spread
    print("\n4. US-Germany 10Y Spread:")
    spread = get_yield_spread('united states', 'germany')
    if spread:
        print(f"   {spread['symbol1']} - {spread['symbol2']}: {spread['spread_bps']} bps")
    else:
        print("   No data available")
    
    # Test 5: Historical data
    print("\n5. US10Y 30-Day History:")
    history = get_yield_history('US10Y', days=30)
    if history:
        print(f"   Retrieved {len(history)} data points")
        if len(history) > 0:
            latest = history[-1] if isinstance(history, list) else history
            print(f"   Latest: {latest.get('Value', 'N/A')}%")
    else:
        print("   No historical data available")
    
    print("\n" + "=" * 60)
    print(f"API Key: {API_KEY}")
    print(f"Cache Directory: {CACHE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
