#!/usr/bin/env python3
"""
Finnhub Options Chain API — Real-Time US Stock Options Data

Data Source: Finnhub.io API (Free tier: 60 calls/min, 250K calls/day)
Update: Real-time options chain data
Free: Yes (API key required via FINNHUB_API_KEY env var)

Provides:
- Options chains (calls/puts, strikes, expirations)
- Volume and open interest
- Implied volatility
- Unusual activity flags
- Sentiment scores

Source: https://finnhub.io/docs/api/stock-us-option-chain
Category: Options & Derivatives

Usage:
    from modules import finnhub_options_chain
    
    # Get options chain
    chain = finnhub_options_chain.get_options_chain('AAPL')
    
    # Get specific expiration
    chain = finnhub_options_chain.get_options_chain('AAPL', date='2026-04-18')
"""

import os
import requests
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "finnhub"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
BASE_URL = "https://finnhub.io/api/v1"


def get_options_chain(symbol: str, date: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """
    Get options chain for a symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL')
        date: Expiration date in YYYY-MM-DD format (optional, returns all if omitted)
        use_cache: Cache results for 5 minutes
        
    Returns:
        Dict with options chain data or None if error
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY environment variable not set"}
    
    cache_key = f"options_chain_{symbol}_{date or 'all'}.json"
    cache_path = CACHE_DIR / cache_key
    
    if use_cache and cache_path.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if age < timedelta(minutes=5):
            with open(cache_path) as f:
                return json.load(f)
    
    params = {
        "symbol": symbol.upper(),
        "token": FINNHUB_API_KEY
    }
    
    if date:
        params["date"] = date
    
    try:
        response = requests.get(
            f"{BASE_URL}/stock/option-chain",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data and not data.get("error"):
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            return data
        return None
    except Exception as e:
        return {"error": str(e)}


def get_expirations(symbol: str) -> Optional[List[str]]:
    """
    Get all available expiration dates for a symbol.
    
    Args:
        symbol: Stock ticker
        
    Returns:
        List of expiration dates (YYYY-MM-DD) or None
    """
    chain = get_options_chain(symbol)
    if not chain or "error" in chain:
        return None
    
    # Extract unique expiration dates
    expirations = set()
    for opt_type in ["call", "put"]:
        if opt_type in chain and "data" in chain[opt_type]:
            for option in chain[opt_type]["data"]:
                if "expirationDate" in option:
                    expirations.add(option["expirationDate"])
    
    return sorted(list(expirations))


def get_unusual_activity(symbol: str, min_volume: int = 1000) -> Optional[pd.DataFrame]:
    """
    Get options with unusual volume.
    
    Args:
        symbol: Stock ticker
        min_volume: Minimum volume threshold
        
    Returns:
        DataFrame with unusual options activity
    """
    chain = get_options_chain(symbol)
    if not chain or "error" in chain:
        return None
    
    unusual = []
    for opt_type in ["call", "put"]:
        if opt_type in chain and "data" in chain[opt_type]:
            for option in chain[opt_type]["data"]:
                volume = option.get("volume", 0)
                if volume >= min_volume:
                    unusual.append({
                        "type": opt_type,
                        "strike": option.get("strike"),
                        "expiration": option.get("expirationDate"),
                        "volume": volume,
                        "open_interest": option.get("openInterest"),
                        "iv": option.get("impliedVolatility"),
                        "bid": option.get("bid"),
                        "ask": option.get("ask")
                    })
    
    if not unusual:
        return None
    
    df = pd.DataFrame(unusual)
    return df.sort_values("volume", ascending=False).reset_index(drop=True)


def get_atm_options(symbol: str, current_price: Optional[float] = None) -> Optional[pd.DataFrame]:
    """
    Get at-the-money options (closest strikes to current price).
    
    Args:
        symbol: Stock ticker
        current_price: Current stock price (fetches if not provided)
        
    Returns:
        DataFrame with ATM options
    """
    chain = get_options_chain(symbol)
    if not chain or "error" in chain:
        return None
    
    if not current_price:
        # Try to get from chain data or set fallback
        current_price = chain.get("underlyingPrice", 0)
    
    if not current_price:
        return None
    
    atm_options = []
    for opt_type in ["call", "put"]:
        if opt_type in chain and "data" in chain[opt_type]:
            for option in chain[opt_type]["data"]:
                strike = option.get("strike", 0)
                if abs(strike - current_price) / current_price < 0.05:  # Within 5%
                    atm_options.append({
                        "type": opt_type,
                        "strike": strike,
                        "expiration": option.get("expirationDate"),
                        "volume": option.get("volume"),
                        "open_interest": option.get("openInterest"),
                        "iv": option.get("impliedVolatility"),
                        "delta": option.get("delta"),
                        "gamma": option.get("gamma")
                    })
    
    if not atm_options:
        return None
    
    return pd.DataFrame(atm_options)


def get_sentiment_from_pcr(symbol: str) -> Optional[Dict]:
    """
    Calculate put/call ratio sentiment from options chain.
    
    Args:
        symbol: Stock ticker
        
    Returns:
        Dict with put/call ratios and sentiment
    """
    chain = get_options_chain(symbol)
    if not chain or "error" in chain:
        return None
    
    call_volume = 0
    put_volume = 0
    call_oi = 0
    put_oi = 0
    
    for opt_type in ["call", "put"]:
        if opt_type in chain and "data" in chain[opt_type]:
            for option in chain[opt_type]["data"]:
                vol = option.get("volume", 0)
                oi = option.get("openInterest", 0)
                
                if opt_type == "call":
                    call_volume += vol
                    call_oi += oi
                else:
                    put_volume += vol
                    put_oi += oi
    
    if call_volume == 0 or call_oi == 0:
        return None
    
    pcr_volume = put_volume / call_volume if call_volume > 0 else 0
    pcr_oi = put_oi / call_oi if call_oi > 0 else 0
    
    # Sentiment interpretation (classic contrarian indicator)
    sentiment = "neutral"
    if pcr_volume > 1.5:
        sentiment = "bullish_contrarian"  # Too many puts = bullish
    elif pcr_volume < 0.7:
        sentiment = "bearish_contrarian"  # Too many calls = bearish
    
    return {
        "symbol": symbol,
        "put_call_ratio_volume": round(pcr_volume, 2),
        "put_call_ratio_oi": round(pcr_oi, 2),
        "call_volume": call_volume,
        "put_volume": put_volume,
        "call_oi": call_oi,
        "put_oi": put_oi,
        "sentiment": sentiment,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Test with AAPL
    symbol = "AAPL"
    
    print(f"\n=== Finnhub Options Chain Test: {symbol} ===\n")
    
    # Get full chain
    chain = get_options_chain(symbol)
    if chain and "error" not in chain:
        print(f"✓ Full chain fetched")
        
        # Get expirations
        exps = get_expirations(symbol)
        if exps:
            print(f"✓ Expirations: {len(exps)} dates, nearest: {exps[0]}")
        
        # Get unusual activity
        unusual = get_unusual_activity(symbol)
        if unusual is not None and len(unusual) > 0:
            print(f"✓ Unusual activity: {len(unusual)} contracts")
            print(unusual.head(3).to_string(index=False))
        
        # Get ATM options
        atm = get_atm_options(symbol)
        if atm is not None and len(atm) > 0:
            print(f"\n✓ ATM options: {len(atm)} contracts")
        
        # Get sentiment
        sentiment = get_sentiment_from_pcr(symbol)
        if sentiment:
            print(f"\n✓ Sentiment: {sentiment['sentiment']}")
            print(f"  Put/Call Ratio (volume): {sentiment['put_call_ratio_volume']}")
            print(f"  Put/Call Ratio (OI): {sentiment['put_call_ratio_oi']}")
    else:
        print(f"✗ Error: {chain.get('error') if chain else 'No data'}")
        print("\nTo use this module, set FINNHUB_API_KEY environment variable.")
        print("Get free key at: https://finnhub.io/register")
