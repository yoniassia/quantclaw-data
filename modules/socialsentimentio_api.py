#!/usr/bin/env python3
"""
SocialSentiment.io API — Multi-Platform Social Sentiment Aggregator

Data Source: SocialSentiment.io API (Free tier: 50 calls/hour)
Update: Hourly aggregation from Twitter/X, Reddit, and forums
Free: Yes (API key required via SOCIALSENTIMENT_API_KEY env var)

Provides:
- Multi-platform sentiment scores (Twitter, Reddit, forums)
- Asset-specific buzz and trend tracking
- Sentiment polarity metrics
- Historical sentiment time series

Usage:
    from modules import socialsentimentio_api
    
    # Get sentiment for a symbol
    sentiment = socialsentimentio_api.get_sentiment('AMC')
    
    # Get sentiment across multiple platforms
    multi = socialsentimentio_api.get_multi_platform_sentiment('GME')
    
    # Batch query
    df = socialsentimentio_api.get_batch_sentiment(['AAPL', 'TSLA', 'AMC'])
"""

import os
import requests
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "socialsentiment"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load API key from environment
SOCIALSENTIMENT_API_KEY = os.getenv('SOCIALSENTIMENT_API_KEY', '')

BASE_URL = "https://api.socialsentiment.io/v1"


def get_sentiment(symbol: str, platform: str = 'all', use_cache: bool = True) -> Optional[Dict]:
    """
    Get social sentiment for a symbol.
    
    Args:
        symbol: Stock ticker or crypto symbol (e.g., 'AMC', 'BTC')
        platform: Platform to query ('twitter', 'reddit', 'all')
        use_cache: Use cached data if available and fresh (< 1 hour)
    
    Returns:
        Dict with sentiment_score, mention_volume, polarity, platform breakdown
    """
    if not SOCIALSENTIMENT_API_KEY:
        print("Warning: SOCIALSENTIMENT_API_KEY not set. Set via environment variable.")
        return None
    
    cache_key = f"{symbol}_{platform}"
    cache_path = CACHE_DIR / f"sentiment_{cache_key.replace('.', '_')}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=1):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/sentiment"
    params = {
        "symbol": symbol,
        "platform": platform,
        "key": SOCIALSENTIMENT_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'error' in data:
            print(f"No sentiment data for {symbol} on {platform}")
            return None
        
        # Add metadata
        data['symbol'] = symbol
        data['platform'] = platform
        data['fetched_at'] = datetime.now().isoformat()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"Authentication failed - check SOCIALSENTIMENT_API_KEY")
        elif e.response.status_code == 429:
            print(f"Rate limit exceeded - free tier allows 50 calls/hour")
        else:
            print(f"HTTP error fetching sentiment for {symbol}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching sentiment for {symbol}: {e}")
        return None


def get_multi_platform_sentiment(symbol: str) -> pd.DataFrame:
    """
    Get sentiment across all platforms for a symbol.
    
    Args:
        symbol: Stock ticker
    
    Returns:
        DataFrame with platform-specific sentiment metrics
    """
    platforms = ['twitter', 'reddit', 'all']
    results = []
    
    for platform in platforms:
        sentiment = get_sentiment(symbol, platform=platform)
        if sentiment:
            results.append({
                'symbol': symbol,
                'platform': platform,
                'sentiment_score': sentiment.get('sentiment_score', 0),
                'mention_volume': sentiment.get('mention_volume', 0),
                'positive_mentions': sentiment.get('positive_mentions', 0),
                'negative_mentions': sentiment.get('negative_mentions', 0),
                'polarity': sentiment.get('polarity', 0),
                'fetched_at': sentiment.get('fetched_at')
            })
    
    return pd.DataFrame(results)


def get_batch_sentiment(symbols: List[str], platform: str = 'all', use_cache: bool = True) -> pd.DataFrame:
    """
    Get sentiment for multiple symbols.
    
    Args:
        symbols: List of stock tickers
        platform: Platform to query
        use_cache: Use cached data when available
    
    Returns:
        DataFrame with sentiment metrics per symbol
    """
    results = []
    
    for symbol in symbols:
        sentiment = get_sentiment(symbol, platform=platform, use_cache=use_cache)
        if sentiment:
            results.append({
                'symbol': symbol,
                'platform': platform,
                'sentiment_score': sentiment.get('sentiment_score', 0),
                'mention_volume': sentiment.get('mention_volume', 0),
                'positive_mentions': sentiment.get('positive_mentions', 0),
                'negative_mentions': sentiment.get('negative_mentions', 0),
                'polarity': sentiment.get('polarity', 0),
                'net_sentiment': sentiment.get('positive_mentions', 0) - sentiment.get('negative_mentions', 0),
                'fetched_at': sentiment.get('fetched_at')
            })
    
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Rank by mention volume and sentiment
    if not df.empty:
        df['buzz_rank'] = df['mention_volume'].rank(ascending=False)
        df['sentiment_rank'] = df['sentiment_score'].rank(ascending=False)
    
    return df


def get_data(symbols: Optional[List[str]] = None, symbol: Optional[str] = None, platform: str = 'all') -> pd.DataFrame:
    """
    Main entry point - get sentiment data.
    
    Args:
        symbols: List of tickers to fetch (for batch mode)
        symbol: Single ticker (for single mode)
        platform: Platform filter
    
    Returns:
        DataFrame with sentiment data
    """
    if symbol:
        symbols = [symbol]
    elif not symbols:
        # Default to popular meme stocks
        symbols = ['AMC', 'GME', 'TSLA', 'AAPL', 'NVDA']
    
    return get_batch_sentiment(symbols, platform=platform)


if __name__ == "__main__":
    # Test the module
    print("Testing SocialSentiment.io API module...\n")
    
    if not SOCIALSENTIMENT_API_KEY:
        print("⚠️  SOCIALSENTIMENT_API_KEY not set.")
        print("   Set via: export SOCIALSENTIMENT_API_KEY='your_key_here'")
        print("   Sign up at: https://socialsentiment.io\n")
        print("Module structure is valid. Exiting test due to missing API key.")
    else:
        # Test 1: Single symbol sentiment
        print("1. Fetching sentiment for AMC:")
        sentiment = get_sentiment('AMC', platform='all')
        if sentiment:
            print(f"  Sentiment score: {sentiment.get('sentiment_score', 0)}")
            print(f"  Mentions: {sentiment.get('mention_volume', 0)}")
            print(f"  Polarity: {sentiment.get('polarity', 0)}")
        
        # Test 2: Multi-platform sentiment
        print("\n2. Multi-platform sentiment for GME:")
        multi_df = get_multi_platform_sentiment('GME')
        if not multi_df.empty:
            print(multi_df[['platform', 'sentiment_score', 'mention_volume']].to_string(index=False))
        
        # Test 3: Batch sentiment
        print("\n3. Batch sentiment for meme stocks:")
        df = get_data(symbols=['AMC', 'GME', 'TSLA'])
        if not df.empty:
            print(df[['symbol', 'sentiment_score', 'mention_volume', 'net_sentiment']].to_string(index=False))
    
    print("\n✓ Module test complete")
