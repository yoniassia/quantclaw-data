"""
CBOE LiveVol Data API — Options Analytics & Unusual Activity

Data Source: CBOE LiveVol (https://datashop.cboe.com/livevol-api)
Update: Real-time
Free Tier: 100 queries per day (basic analytics)
Launched: 2025 (free developer tier)

Provides:
- Unusual options activity detection
- Volatility indices and skew data
- Trade alerts for high-volume options
- Historical options flow metrics
- Proprietary analytics on institutional flow

Usage:
- Identify unusual call/put buying (smart money signals)
- Track volatility skew changes (risk reversals)
- Detect large block trades ahead of events
- Monitor options flow for sentiment

Note: Requires free API key registration at CBOE DataShop
      https://datashop.cboe.com/account/register
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/cboe_livevol")
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = "https://api.livevol.com/v1"

def get_api_key() -> Optional[str]:
    """
    Get API key from environment or config.
    Set via: export CBOE_LIVEVOL_API_KEY=your_key
    """
    return os.environ.get("CBOE_LIVEVOL_API_KEY")

def get_unusual_activity(symbol: str, days_back: int = 1) -> Dict:
    """
    Fetch unusual options activity for a symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'SPY', 'AAPL')
        days_back: Number of days to look back (default 1)
    
    Returns:
        Dict with unusual activity data including:
        - Large block trades
        - High volume relative to open interest
        - Unusual call/put ratios
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "error": "API key required",
            "instructions": "Set CBOE_LIVEVOL_API_KEY environment variable",
            "register_at": "https://datashop.cboe.com/account/register"
        }
    
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_unusual_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Check cache (refresh hourly for real-time data)
    if os.path.exists(cache_file):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if cache_age < timedelta(hours=1):
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        endpoint = f"{BASE_URL}/live/options/unusual-activity"
        params = {
            'symbol': symbol,
            'days': days_back
        }
        
        response = requests.post(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse and structure response
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "unusual_trades": data.get("trades", []),
            "summary": {
                "total_unusual_volume": sum(t.get("volume", 0) for t in data.get("trades", [])),
                "call_volume": sum(t.get("volume", 0) for t in data.get("trades", []) if t.get("type") == "call"),
                "put_volume": sum(t.get("volume", 0) for t in data.get("trades", []) if t.get("type") == "put"),
                "avg_premium": data.get("avg_premium", 0)
            },
            "signal": analyze_flow(data.get("trades", []))
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return {"error": "Invalid API key", "status_code": 401}
        elif e.response.status_code == 429:
            return {"error": "Rate limit exceeded (100 queries/day)", "status_code": 429}
        else:
            return {"error": f"HTTP error: {e}", "status_code": e.response.status_code}
    except Exception as e:
        return {"error": f"Fetch failed: {str(e)}"}

def get_volatility_skew(symbol: str, expiration: Optional[str] = None) -> Dict:
    """
    Get volatility skew data for options chain.
    
    Args:
        symbol: Stock ticker
        expiration: Expiration date (YYYY-MM-DD) or None for nearest
    
    Returns:
        Skew metrics showing put vs call IV differences
    """
    api_key = get_api_key()
    if not api_key:
        return {"error": "API key required"}
    
    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        endpoint = f"{BASE_URL}/live/options/skew"
        params = {'symbol': symbol}
        
        if expiration:
            params['expiration'] = expiration
        
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "symbol": symbol,
            "expiration": data.get("expiration"),
            "skew_index": data.get("skew_index", 0),
            "call_iv_avg": data.get("call_iv_avg", 0),
            "put_iv_avg": data.get("put_iv_avg", 0),
            "put_call_skew": data.get("put_iv_avg", 0) - data.get("call_iv_avg", 0),
            "interpretation": interpret_skew(data)
        }
        
    except Exception as e:
        return {"error": f"Fetch failed: {str(e)}"}

def analyze_flow(trades: List[Dict]) -> str:
    """
    Analyze options flow for trading signals.
    
    Returns:
        Signal interpretation (BULLISH, BEARISH, NEUTRAL)
    """
    if not trades:
        return "NEUTRAL"
    
    call_volume = sum(t.get("volume", 0) for t in trades if t.get("type") == "call")
    put_volume = sum(t.get("volume", 0) for t in trades if t.get("type") == "put")
    
    if call_volume == 0 and put_volume == 0:
        return "NEUTRAL"
    
    call_put_ratio = call_volume / (put_volume + 1)  # Avoid division by zero
    
    if call_put_ratio > 2.0:
        return "BULLISH - Heavy call buying"
    elif call_put_ratio < 0.5:
        return "BEARISH - Heavy put buying"
    else:
        return "NEUTRAL - Balanced flow"

def interpret_skew(data: Dict) -> str:
    """Interpret volatility skew for trading signals."""
    put_call_skew = data.get("put_iv_avg", 0) - data.get("call_iv_avg", 0)
    
    if put_call_skew > 5:
        return "High put skew - Market expects downside risk"
    elif put_call_skew < -5:
        return "Negative skew - Unusual call demand, possible bullish setup"
    else:
        return "Normal skew - Balanced volatility expectations"

def get_trade_alerts(min_volume: int = 1000) -> List[Dict]:
    """
    Get real-time trade alerts for large options transactions.
    
    Args:
        min_volume: Minimum volume threshold for alert
    
    Returns:
        List of alert events
    """
    api_key = get_api_key()
    if not api_key:
        return [{"error": "API key required"}]
    
    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        endpoint = f"{BASE_URL}/live/alerts"
        params = {'min_volume': min_volume}
        
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json().get("alerts", [])
        
    except Exception as e:
        return [{"error": f"Fetch failed: {str(e)}"}]

# Convenience functions
def spy_flow() -> Dict:
    """Quick check of SPY options flow."""
    return get_unusual_activity("SPY")

def qqq_flow() -> Dict:
    """Quick check of QQQ options flow."""
    return get_unusual_activity("QQQ")

def check_symbol(symbol: str) -> Dict:
    """
    Full options analytics for a symbol.
    
    Returns unusual activity + volatility skew in one call.
    """
    return {
        "unusual_activity": get_unusual_activity(symbol),
        "volatility_skew": get_volatility_skew(symbol)
    }

if __name__ == "__main__":
    # Test module
    result = spy_flow()
    print(json.dumps(result, indent=2))
