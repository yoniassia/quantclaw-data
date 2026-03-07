"""
CNN Fear & Greed Index — Market Sentiment Indicator

Tracks market sentiment from extreme fear (0) to extreme greed (100).
Data: https://production.dataviz.cnn.io/index/fearandgreed/graphdata

Use cases:
- Contrarian trading signals
- Market sentiment analysis
- Risk appetite tracking
- Multi-factor sentiment modeling
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "cnn_fear_greed"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


def _fetch_cnn_data(use_cache: bool = True) -> Optional[Dict]:
    """Internal function to fetch CNN Fear & Greed data with caching."""
    cache_path = CACHE_DIR / "fear_greed_latest.json"
    
    # Check cache (4-hour expiry since market data updates frequently)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=4):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching CNN Fear & Greed data: {e}")
        
        # Try to return stale cache if available
        if cache_path.exists():
            print("Returning stale cached data...")
            with open(cache_path, 'r') as f:
                return json.load(f)
        
        return None


def get_fear_greed_index(use_cache: bool = True) -> Optional[Dict]:
    """
    Get current Fear & Greed Index score.
    
    Returns:
        Dict with keys:
        - score: float (0-100)
        - rating: str (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
        - timestamp: str (ISO format)
        - previous_close: float (previous day's score)
        - previous_week: float (1 week ago)
        - previous_month: float (1 month ago)
        - previous_year: float (1 year ago)
    """
    data = _fetch_cnn_data(use_cache)
    if not data:
        return None
    
    try:
        fear_greed = data.get('fear_and_greed', {})
        
        result = {
            'score': float(fear_greed.get('score', 0)),
            'rating': fear_greed.get('rating', 'Unknown'),
            'timestamp': fear_greed.get('timestamp', datetime.now().isoformat()),
            'previous_close': float(fear_greed.get('previous_close', 0)),
            'previous_week': float(fear_greed.get('previous_1_week', 0)),
            'previous_month': float(fear_greed.get('previous_1_month', 0)),
            'previous_year': float(fear_greed.get('previous_1_year', 0))
        }
        
        return result
    except Exception as e:
        print(f"Error parsing Fear & Greed index: {e}")
        return None


def get_fear_greed_history(days: int = 30, use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Get historical Fear & Greed Index scores.
    
    Args:
        days: Number of days of history to return (default 30, max available in data)
        use_cache: Whether to use cached data
    
    Returns:
        List of dicts with keys:
        - timestamp: str (ISO format date)
        - score: float (0-100)
        - rating: str (sentiment rating)
    """
    data = _fetch_cnn_data(use_cache)
    if not data:
        return None
    
    try:
        # Historical data is at top level under 'fear_and_greed_historical'
        historical_data = data.get('fear_and_greed_historical', {})
        data_points = historical_data.get('data', [])
        
        if not data_points:
            return []
        
        # Sort by timestamp descending and limit to requested days
        sorted_history = sorted(data_points, key=lambda x: x.get('x', 0), reverse=True)
        limited_history = sorted_history[:days]
        
        # Format results (convert milliseconds timestamp to ISO date)
        result = []
        for point in limited_history:
            timestamp_ms = point.get('x', 0)
            # Convert milliseconds to datetime
            dt = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
            
            result.append({
                'timestamp': dt.strftime('%Y-%m-%d'),
                'score': float(point.get('y', 0)),
                'rating': point.get('rating', 'Unknown')
            })
        
        return result
    except Exception as e:
        print(f"Error parsing Fear & Greed history: {e}")
        return None


def get_fear_greed_components(use_cache: bool = True) -> Optional[Dict]:
    """
    Get individual component scores that make up the Fear & Greed Index.
    
    Components:
    - Market Momentum (S&P 500 vs 125-day MA)
    - Stock Price Strength (52-week highs vs lows)
    - Stock Price Breadth (advancing vs declining volume)
    - Put/Call Options (put/call ratio)
    - Junk Bond Demand (spread between junk & investment grade)
    - Market Volatility (VIX)
    - Safe Haven Demand (stocks vs bonds)
    
    Returns:
        Dict with component names as keys, each containing:
        - score: float (0-100)
        - rating: str (sentiment rating)
    """
    data = _fetch_cnn_data(use_cache)
    if not data:
        return None
    
    try:
        # Components are at top level, not nested under fear_and_greed
        component_keys = [
            'market_momentum_sp500',
            'stock_price_strength',
            'stock_price_breadth',
            'put_call_options',
            'junk_bond_demand',
            'market_volatility_vix',
            'safe_haven_demand'
        ]
        
        components = {}
        for key in component_keys:
            component_data = data.get(key, {})
            if component_data and isinstance(component_data, dict):
                # Use readable name (remove prefixes, convert underscores)
                display_name = key.replace('_sp500', '').replace('_vix', '')
                components[display_name] = {
                    'score': float(component_data.get('score', 0)),
                    'rating': component_data.get('rating', 'Unknown')
                }
        
        return components
    except Exception as e:
        print(f"Error parsing Fear & Greed components: {e}")
        return None


# Convenience function for quick checks
def get_current_sentiment() -> str:
    """
    Quick check: returns current sentiment as a string.
    
    Returns:
        str: "Extreme Fear (23)" or "N/A" if unavailable
    """
    index = get_fear_greed_index()
    if index:
        return f"{index['rating']} ({index['score']:.0f})"
    return "N/A"
