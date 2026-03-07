#!/usr/bin/env python3
"""
Financial Modeling Prep IPO Calendar Module

Provides comprehensive IPO calendar data including:
- Upcoming and recent IPO listings
- Confirmed IPO filings
- IPO prospectus and S-1 data
- IPO market statistics and trends

Source: https://site.financialmodelingprep.com/developer/docs/ipo-calendar-api
Category: IPO & Private Markets
Free tier: 250 API calls per day
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

# FMP API Configuration
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict | List]:
    """
    Make authenticated request to FMP API.
    
    Args:
        endpoint: API endpoint path (e.g., 'ipo_calendar')
        params: Optional query parameters
    
    Returns:
        JSON response as dict or list, None on error
    """
    if not FMP_API_KEY:
        raise ValueError("FMP_API_KEY not found in environment. Add to .env file.")
    
    url = f"{FMP_BASE_URL}/{endpoint}"
    request_params = params or {}
    request_params['apikey'] = FMP_API_KEY
    
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"FMP API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"FMP API response parse failed: {e}")
        return None


def get_ipo_calendar(from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
    """
    Get IPO calendar with upcoming and recent IPOs.
    
    Args:
        from_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        to_date: End date in YYYY-MM-DD format (default: 90 days from now)
    
    Returns:
        List of IPO events with details:
        - symbol: Stock ticker
        - company: Company name
        - exchange: Listing exchange
        - price: IPO price
        - priceRange: Expected price range
        - shares: Number of shares
        - date: IPO date
    
    Example:
        >>> ipos = get_ipo_calendar(from_date='2024-01-01', to_date='2024-12-31')
        >>> print(f"Found {len(ipos)} IPOs")
    """
    params = {}
    
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    
    params['from'] = from_date
    params['to'] = to_date
    
    result = _make_request('ipo_calendar', params)
    return result if isinstance(result, list) else []


def get_ipo_confirmed(from_date: Optional[str] = None) -> List[Dict]:
    """
    Get confirmed upcoming IPOs with filed prospectuses.
    
    Args:
        from_date: Start date in YYYY-MM-DD format (default: today)
    
    Returns:
        List of confirmed IPOs with:
        - symbol: Stock ticker
        - company: Company name
        - expectedPriceFrom: Lower price bound
        - expectedPriceTo: Upper price bound
        - numberOfShares: Shares to be offered
        - filingDate: SEC filing date
        - expectedDate: Expected listing date
    
    Example:
        >>> confirmed = get_ipo_confirmed()
        >>> for ipo in confirmed[:5]:
        ...     print(f"{ipo['company']}: ${ipo['expectedPriceFrom']}-${ipo['expectedPriceTo']}")
    """
    params = {}
    
    if not from_date:
        from_date = datetime.now().strftime('%Y-%m-%d')
    
    params['from'] = from_date
    
    result = _make_request('ipo-calendar-confirmed', params)
    return result if isinstance(result, list) else []


def get_ipo_prospectus(symbol: str) -> Dict:
    """
    Get IPO prospectus and S-1 filing data for a specific symbol.
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dict with prospectus details:
        - symbol: Stock ticker
        - company: Company name
        - filingDate: S-1 filing date
        - priceFrom: Lower price range
        - priceTo: Upper price range
        - shares: Number of shares
        - url: SEC filing URL
    
    Example:
        >>> prospectus = get_ipo_prospectus('ABNB')
        >>> print(f"Filed: {prospectus.get('filingDate')}")
    """
    if not symbol:
        raise ValueError("Symbol is required")
    
    result = _make_request(f'ipo-prospectus/{symbol.upper()}')
    return result if isinstance(result, dict) else {}


def get_recent_ipos(limit: int = 20) -> List[Dict]:
    """
    Get most recent IPO listings.
    
    Args:
        limit: Number of recent IPOs to retrieve (default: 20)
    
    Returns:
        List of recent IPOs sorted by date with:
        - symbol: Stock ticker
        - company: Company name
        - date: Listing date
        - price: IPO price
        - shares: Shares offered
        - exchange: Listing exchange
    
    Example:
        >>> recent = get_recent_ipos(limit=10)
        >>> for ipo in recent:
        ...     print(f"{ipo['company']} ({ipo['symbol']}): ${ipo['price']} on {ipo['date']}")
    """
    # Get IPOs from last 90 days
    from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    to_date = datetime.now().strftime('%Y-%m-%d')
    
    result = get_ipo_calendar(from_date=from_date, to_date=to_date)
    
    # Filter only completed IPOs (have price set) and sort by date
    completed = [ipo for ipo in result if ipo.get('price')]
    completed.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return completed[:limit]


def get_ipo_stats(year: Optional[int] = None) -> Dict:
    """
    Get IPO market statistics summary for a given year.
    
    Args:
        year: Year for statistics (default: current year)
    
    Returns:
        Dict with IPO statistics:
        - total_ipos: Total number of IPOs
        - total_raised: Total capital raised
        - avg_price: Average IPO price
        - median_price: Median IPO price
        - top_ipos: List of largest IPOs by valuation
        - by_exchange: Breakdown by exchange
        - by_month: Monthly distribution
    
    Example:
        >>> stats = get_ipo_stats(year=2024)
        >>> print(f"Total IPOs in 2024: {stats['total_ipos']}")
    """
    if not year:
        year = datetime.now().year
    
    from_date = f"{year}-01-01"
    to_date = f"{year}-12-31"
    
    ipos = get_ipo_calendar(from_date=from_date, to_date=to_date)
    
    if not ipos:
        return {
            'year': year,
            'total_ipos': 0,
            'message': 'No data available for this year'
        }
    
    # Calculate statistics
    completed_ipos = [ipo for ipo in ipos if ipo.get('price')]
    
    stats = {
        'year': year,
        'total_ipos': len(ipos),
        'completed_ipos': len(completed_ipos),
        'pending_ipos': len(ipos) - len(completed_ipos),
    }
    
    if completed_ipos:
        prices = [float(ipo['price']) for ipo in completed_ipos if ipo.get('price')]
        if prices:
            stats['avg_price'] = sum(prices) / len(prices)
            stats['median_price'] = sorted(prices)[len(prices) // 2]
            stats['min_price'] = min(prices)
            stats['max_price'] = max(prices)
        
        # Top IPOs by shares * price
        valued_ipos = []
        for ipo in completed_ipos:
            if ipo.get('shares') and ipo.get('price'):
                try:
                    shares = float(ipo['shares'])
                    price = float(ipo['price'])
                    valued_ipos.append({
                        'symbol': ipo.get('symbol'),
                        'company': ipo.get('company'),
                        'date': ipo.get('date'),
                        'valuation': shares * price
                    })
                except (ValueError, TypeError):
                    continue
        
        if valued_ipos:
            valued_ipos.sort(key=lambda x: x['valuation'], reverse=True)
            stats['top_ipos'] = valued_ipos[:10]
        
        # Exchange breakdown
        exchanges = {}
        for ipo in completed_ipos:
            exchange = ipo.get('exchange', 'Unknown')
            exchanges[exchange] = exchanges.get(exchange, 0) + 1
        stats['by_exchange'] = exchanges
        
        # Monthly breakdown
        monthly = {}
        for ipo in completed_ipos:
            if ipo.get('date'):
                month = ipo['date'][:7]  # YYYY-MM
                monthly[month] = monthly.get(month, 0) + 1
        stats['by_month'] = monthly
    
    return stats


if __name__ == "__main__":
    # Test module functionality
    print(json.dumps({
        "module": "financial_modeling_prep_ipo_calendar",
        "status": "active",
        "functions": [
            "get_ipo_calendar",
            "get_ipo_confirmed", 
            "get_ipo_prospectus",
            "get_recent_ipos",
            "get_ipo_stats"
        ],
        "source": "https://site.financialmodelingprep.com/developer/docs/ipo-calendar-api"
    }, indent=2))
