"""
Trading Economics API — Global Economic Data & Indicators

Provides access to global economic indicators, bond yields, credit ratings,
economic calendars, and market data via Trading Economics free tier API.

Source: https://tradingeconomics.com/api/
Category: Fixed Income & Credit / Macro

Use cases:
- Track government bond yields across countries
- Monitor stock indices, forex, and commodities
- Access economic calendar for upcoming data releases
- Global markets overview in real-time
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "trading_economics"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.tradingeconomics.com"
AUTH_PARAM = "c=guest:guest"


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
    url = f"{url}{separator}{AUTH_PARAM}"
    
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
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_bond_yields(country: Optional[str] = None, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get current government bond yields.
    
    Args:
        country: Country name (optional, filters results if provided)
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of bond yield data or None if error
    """
    data = _fetch_with_cache("/markets/bonds", "bonds_all", cache_hours=1, use_cache=use_cache)
    
    if not data:
        return None
    
    # Filter by country if specified
    if country and isinstance(data, list):
        country_lower = country.lower()
        filtered = [item for item in data if item.get('Country', '').lower() == country_lower]
        return filtered if filtered else data
    
    return data


def get_economic_indicators(symbol: Optional[str] = None, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get economic indicators from the indicators endpoint.
    
    Note: Free tier may have limited access. Returns market indices if available.
    
    Args:
        symbol: Optional symbol to filter (e.g., 'US10Y' for US 10-year yield)
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of indicators or None if error
    """
    # Try to get stock indices as a proxy for economic sentiment
    endpoint = "/markets/index" if not symbol else f"/markets/index/{symbol}"
    cache_name = f"indicators_{symbol if symbol else 'all'}"
    
    data = _fetch_with_cache(endpoint, cache_name, cache_hours=6, use_cache=use_cache)
    
    return data


def get_credit_rating(country: str = 'united states', use_cache: bool = True) -> Optional[Dict]:
    """
    Get sovereign credit ratings for a country.
    
    Note: May require paid tier. Returns cached data if available.
    
    Args:
        country: Country name (default: 'united states')
        use_cache: Use cached data if available (default: True)
    
    Returns:
        Credit rating data or None if error/unavailable
    """
    endpoint = f"/rating/{country.lower()}"
    cache_name = f"rating_{country.lower().replace(' ', '_')}"
    
    # Ratings change infrequently, cache for 1 week
    data = _fetch_with_cache(endpoint, cache_name, cache_hours=168, use_cache=use_cache)
    
    if not data:
        return {"note": f"Credit rating data for {country} not available in free tier"}
    
    return data


def get_calendar(days_ahead: int = 7, country: Optional[str] = None, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get upcoming economic events calendar.
    
    Note: May require paid tier. Uses cached data if API unavailable.
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
        country: Country name (optional)
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of calendar events or None if error
    """
    # Calculate date range
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    if country:
        endpoint = f"/calendar/country/{country.lower()}/{start_date}/{end_date}"
        cache_name = f"calendar_{country.lower().replace(' ', '_')}_{days_ahead}d"
    else:
        endpoint = f"/calendar"
        cache_name = f"calendar_all_{days_ahead}d"
    
    data = _fetch_with_cache(endpoint, cache_name, cache_hours=6, use_cache=use_cache)
    
    if not data:
        return {"note": "Economic calendar not available in free tier. Consider upgrading."}
    
    return data


def get_markets_overview(use_cache: bool = True) -> Optional[Dict]:
    """
    Get major markets overview (stocks, forex, commodities, bonds).
    
    Args:
        use_cache: Use cached data if available (default: True)
    
    Returns:
        Dict with market data organized by category or None if error
    """
    markets_data = {
        'bonds': None,
        'stocks': None,
        'forex': None,
        'commodities': None,
        'crypto': None
    }
    
    # Government bonds
    bonds = _fetch_with_cache("/markets/bonds", "markets_bonds", cache_hours=1, use_cache=use_cache)
    if bonds:
        markets_data['bonds'] = bonds
    
    # Stock indices
    stocks = _fetch_with_cache("/markets/index", "markets_index", cache_hours=1, use_cache=use_cache)
    if stocks:
        markets_data['stocks'] = stocks
    
    # Forex
    forex = _fetch_with_cache("/markets/currency", "markets_currency", cache_hours=1, use_cache=use_cache)
    if forex:
        markets_data['forex'] = forex
    
    # Commodities
    commodities = _fetch_with_cache("/markets/commodities", "markets_commodities", cache_hours=1, use_cache=use_cache)
    if commodities:
        markets_data['commodities'] = commodities
    
    # Crypto
    crypto = _fetch_with_cache("/markets/crypto", "markets_crypto", cache_hours=1, use_cache=use_cache)
    if crypto:
        markets_data['crypto'] = crypto
    
    # Return None if all failed
    if all(v is None for v in markets_data.values()):
        return None
    
    # Add metadata
    markets_data['timestamp'] = datetime.now().isoformat()
    markets_data['source'] = 'tradingeconomics.com'
    
    return markets_data


def get_stock_indices(use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get global stock market indices.
    
    Args:
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of stock indices or None if error
    """
    return _fetch_with_cache("/markets/index", "stock_indices", cache_hours=1, use_cache=use_cache)


def get_forex_rates(use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get foreign exchange rates.
    
    Args:
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of forex rates or None if error
    """
    return _fetch_with_cache("/markets/currency", "forex_rates", cache_hours=1, use_cache=use_cache)


def get_commodities(use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get commodity prices (gold, oil, etc.).
    
    Args:
        use_cache: Use cached data if available (default: True)
    
    Returns:
        List of commodity prices or None if error
    """
    return _fetch_with_cache("/markets/commodities", "commodities", cache_hours=1, use_cache=use_cache)


# CLI functions for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "bonds":
            country = sys.argv[2] if len(sys.argv) > 2 else None
            data = get_bond_yields(country, use_cache=False)
            print(json.dumps(data, indent=2))
        
        elif command == "indicators":
            data = get_economic_indicators(use_cache=False)
            print(json.dumps(data[:5] if data else None, indent=2))
        
        elif command == "rating":
            country = sys.argv[2] if len(sys.argv) > 2 else "united states"
            data = get_credit_rating(country, use_cache=False)
            print(json.dumps(data, indent=2))
        
        elif command == "calendar":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            data = get_calendar(days_ahead=days, use_cache=False)
            print(json.dumps(data, indent=2))
        
        elif command == "markets":
            data = get_markets_overview(use_cache=False)
            if data:
                # Print summary
                print("=== Markets Overview ===")
                for category, items in data.items():
                    if category not in ['timestamp', 'source'] and items:
                        print(f"\n{category.upper()}: {len(items)} items")
            else:
                print("No market data available")
        
        elif command == "stocks":
            data = get_stock_indices(use_cache=False)
            print(json.dumps(data[:10] if data else None, indent=2))
        
        elif command == "forex":
            data = get_forex_rates(use_cache=False)
            print(json.dumps(data[:10] if data else None, indent=2))
        
        elif command == "commodities":
            data = get_commodities(use_cache=False)
            print(json.dumps(data[:10] if data else None, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            print("Available: bonds, indicators, rating, calendar, markets, stocks, forex, commodities")
    else:
        print(json.dumps({
            "module": "trading_economics_api",
            "status": "ready",
            "source": "https://tradingeconomics.com/api/",
            "auth": "guest (free tier)",
            "functions": [
                "get_bond_yields",
                "get_economic_indicators",
                "get_credit_rating",
                "get_calendar",
                "get_markets_overview",
                "get_stock_indices",
                "get_forex_rates",
                "get_commodities"
            ]
        }, indent=2))
