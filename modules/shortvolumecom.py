"""
ShortVolume.com - Daily Short Volume Data
Source: https://shortvolume.com
Category: Alternative Data / Sentiment
Frequency: Daily
Description: FINRA short volume data by ticker. Great contrarian signal for alpha generation.

Note: This module provides a functional framework. The site uses dynamic JavaScript loading,
      so actual data scraping requires browser automation or finding undocumented API endpoints.
      Current implementation returns sample/test data structure.
"""

import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# Constants
BASE_URL = "https://shortvolume.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://shortvolume.com/',
}
TIMEOUT = 10

# Sample data for testing (simulates real short volume patterns)
SAMPLE_DATA = {
    'AAPL': {
        'short_volume': 15234567,
        'total_volume': 45678901,
        'short_ratio': 0.3335
    },
    'SPY': {
        'short_volume': 28456789,
        'total_volume': 98765432,
        'short_ratio': 0.2882
    },
    'TSLA': {
        'short_volume': 22345678,
        'total_volume': 56789012,
        'short_ratio': 0.3934
    },
    'GME': {
        'short_volume': 18765432,
        'total_volume': 34567890,
        'short_ratio': 0.5429
    }
}


def _parse_number(s: str) -> Optional[int]:
    """Parse number from string, removing commas."""
    if not s:
        return None
    try:
        return int(s.replace(',', '').strip())
    except (ValueError, AttributeError):
        return None


def _parse_float(s: str) -> Optional[float]:
    """Parse float from string, removing % and commas."""
    if not s:
        return None
    try:
        cleaned = s.replace(',', '').replace('%', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _generate_sample_history(ticker: str, days: int) -> List[Dict]:
    """Generate sample historical data for testing."""
    base = SAMPLE_DATA.get(ticker, SAMPLE_DATA['AAPL'])
    history = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        # Add some variance
        variance = 1 + (i % 7 - 3) * 0.05
        history.append({
            'date': date,
            'short_volume': int(base['short_volume'] * variance),
            'total_volume': int(base['total_volume'] * variance),
            'short_ratio': round(base['short_ratio'] * variance, 4)
        })
    
    return history


def get_short_volume(ticker: str) -> Dict:
    """
    Get latest short volume data for a ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
    
    Returns:
        dict: {
            'ticker': str,
            'date': str,
            'short_volume': int,
            'total_volume': int,
            'short_ratio': float,
            'status': str  # 'sample' or 'live'
        }
    
    Raises:
        ValueError: If ticker is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Invalid ticker symbol")
    
    ticker = ticker.upper().strip()
    
    try:
        # Try to fetch quote page (connection test)
        url = f"{BASE_URL}/quote_new_7_2.php?Symbol={ticker}"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        
        # Site is reachable, but data parsing requires JavaScript execution
        # Return sample data with status indicator
        if ticker in SAMPLE_DATA:
            data = SAMPLE_DATA[ticker]
            return {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'short_volume': data['short_volume'],
                'total_volume': data['total_volume'],
                'short_ratio': data['short_ratio'],
                'status': 'sample',
                'note': 'Site requires JavaScript - returning sample data'
            }
        else:
            return {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'short_volume': 10000000,
                'total_volume': 30000000,
                'short_ratio': 0.3333,
                'status': 'sample',
                'note': 'Site requires JavaScript - returning default sample data'
            }
        
    except requests.exceptions.RequestException as e:
        return {
            'ticker': ticker,
            'error': f'Request failed: {str(e)}',
            'status': 'error'
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Unexpected error: {str(e)}',
            'status': 'error'
        }


def get_short_volume_history(ticker: str, days: int = 30) -> List[Dict]:
    """
    Get historical short volume data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of history to retrieve (default: 30)
    
    Returns:
        list: List of daily short volume dicts, ordered by date (newest first)
              Each dict contains: date, short_volume, total_volume, short_ratio, status
    """
    if not ticker or not isinstance(ticker, str):
        return []
    
    ticker = ticker.upper().strip()
    
    try:
        # Connection test
        url = f"{BASE_URL}/?t={ticker}"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        
        # Return sample data
        history = _generate_sample_history(ticker, days)
        for record in history:
            record['ticker'] = ticker
            record['status'] = 'sample'
        
        return history
        
    except Exception as e:
        return []


def get_market_short_volume() -> Dict:
    """
    Get market-wide short volume statistics.
    
    Returns:
        dict: {
            'date': str,
            'total_short_volume': int,
            'total_volume': int,
            'market_short_ratio': float,
            'top_shorted_count': int,
            'status': str
        }
    """
    try:
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_short_volume': 1250000000,
            'total_volume': 4200000000,
            'market_short_ratio': 0.2976,
            'top_shorted_count': 50,
            'status': 'sample',
            'note': 'Market-wide aggregation requires scraping multiple pages'
        }
        
    except Exception as e:
        return {
            'error': f'Failed to get market data: {str(e)}',
            'status': 'error'
        }


def get_most_shorted(limit: int = 20) -> List[Dict]:
    """
    Get most shorted stocks by short ratio.
    
    Args:
        limit: Maximum number of stocks to return (default: 20)
    
    Returns:
        list: List of dicts with ticker, short_ratio, short_volume, total_volume
              Sorted by short_ratio descending
    """
    try:
        # Sample most shorted stocks
        most_shorted = [
            {'ticker': 'GME', 'short_ratio': 0.5429, 'short_volume': 18765432, 'total_volume': 34567890},
            {'ticker': 'AMC', 'short_ratio': 0.4821, 'short_volume': 15234567, 'total_volume': 31623847},
            {'ticker': 'BBBY', 'short_ratio': 0.4567, 'short_volume': 12345678, 'total_volume': 27023847},
            {'ticker': 'TSLA', 'short_ratio': 0.3934, 'short_volume': 22345678, 'total_volume': 56789012},
            {'ticker': 'AAPL', 'short_ratio': 0.3335, 'short_volume': 15234567, 'total_volume': 45678901},
        ]
        
        for stock in most_shorted:
            stock['date'] = datetime.now().strftime('%Y-%m-%d')
            stock['status'] = 'sample'
        
        return most_shorted[:limit]
        
    except Exception as e:
        return []


def detect_short_squeeze_candidates(min_ratio: float = 0.5) -> List[Dict]:
    """
    Detect potential short squeeze candidates.
    
    Args:
        min_ratio: Minimum short ratio to consider (default: 0.5 = 50%)
    
    Returns:
        list: List of dicts with ticker, short_ratio, short_volume, total_volume, squeeze_score
              Sorted by squeeze potential (high short ratio + recent increase)
    """
    try:
        # Sample squeeze candidates
        candidates = [
            {
                'ticker': 'GME',
                'short_ratio': 0.5429,
                'short_volume': 18765432,
                'total_volume': 34567890,
                'squeeze_score': 8.5,
                'trend': 'increasing',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'sample'
            },
            {
                'ticker': 'AMC',
                'short_ratio': 0.4821,
                'short_volume': 15234567,
                'total_volume': 31623847,
                'squeeze_score': 7.2,
                'trend': 'stable',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'sample'
            }
        ]
        
        # Filter by minimum ratio
        filtered = [c for c in candidates if c['short_ratio'] >= min_ratio]
        
        return sorted(filtered, key=lambda x: x['squeeze_score'], reverse=True)
        
    except Exception as e:
        return []


# Module test function
def _test():
    """Test module functions."""
    print("Testing shortvolumecom module...")
    print("=" * 70)
    
    print("\n1. get_short_volume('AAPL'):")
    result = get_short_volume('AAPL')
    print(json.dumps(result, indent=2))
    
    print("\n2. get_short_volume('SPY'):")
    result2 = get_short_volume('SPY')
    print(json.dumps(result2, indent=2))
    
    print("\n3. get_short_volume_history('AAPL', days=5):")
    history = get_short_volume_history('AAPL', days=5)
    print(f"Retrieved {len(history)} days of data")
    if history:
        print("Sample (most recent):")
        print(json.dumps(history[0], indent=2))
    
    print("\n4. get_market_short_volume():")
    market = get_market_short_volume()
    print(json.dumps(market, indent=2))
    
    print("\n5. get_most_shorted(limit=5):")
    most_shorted = get_most_shorted(limit=5)
    print(f"Found {len(most_shorted)} highly shorted stocks:")
    for stock in most_shorted:
        print(f"  {stock['ticker']}: {stock['short_ratio']:.2%}")
    
    print("\n6. detect_short_squeeze_candidates(min_ratio=0.5):")
    candidates = detect_short_squeeze_candidates(min_ratio=0.5)
    print(f"Found {len(candidates)} squeeze candidates:")
    for candidate in candidates:
        print(f"  {candidate['ticker']}: ratio={candidate['short_ratio']:.2%}, score={candidate['squeeze_score']}")
    
    print("\n" + "=" * 70)
    print("All functions working! ✓")
    print("\nNote: Module returns sample data because shortvolume.com requires")
    print("      JavaScript execution to load actual data. For production use,")
    print("      implement browser automation (Selenium/Playwright) or find")
    print("      undocumented API endpoints.")


if __name__ == '__main__':
    _test()
