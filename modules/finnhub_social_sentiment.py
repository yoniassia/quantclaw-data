#!/usr/bin/env python3
"""
Finnhub Social Sentiment — Real-Time Social Media Sentiment for Stocks

Data Source: Finnhub.io API (Free tier: 60 calls/min)
Update: Real-time aggregation from StockTwits, Reddit, Twitter
Free: Yes (API key required via FINNHUB_API_KEY env var)

Provides:
- Stock-specific social sentiment scores (bullish/bearish)
- Mention volume from Reddit, StockTwits, Twitter
- Historical sentiment trends
- Sentiment momentum for meme stock detection

Usage:
    from modules import finnhub_social_sentiment
    
    # Get recent sentiment
    sentiment = finnhub_social_sentiment.get_sentiment('AAPL')
    
    # Get sentiment for multiple stocks
    df = finnhub_social_sentiment.get_batch_sentiment(['AAPL', 'TSLA', 'GME'])
    
    # Get historical sentiment
    hist = finnhub_social_sentiment.get_historical_sentiment('AMC', days=30)
"""

import os
import requests
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "finnhub_social"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load API key from environment
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

BASE_URL = "https://finnhub.io/api/v1"


def get_sentiment(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None, use_cache: bool = True) -> Optional[Dict]:
    """
    Get social sentiment data for a symbol.
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA', 'GME')
        from_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        to_date: End date in YYYY-MM-DD format (default: today)
        use_cache: Use cached data if available and fresh (< 6 hours)
    
    Returns:
        Dict with keys:
        - symbol: str
        - reddit: Dict with mention, positiveScore, negativeScore, score
        - twitter: Dict with mention, positiveScore, negativeScore, score
        - data: List of daily sentiment entries
    """
    if not FINNHUB_API_KEY:
        print("Warning: FINNHUB_API_KEY not set. Using demo key (limited)")
        api_key = "demo"
    else:
        api_key = FINNHUB_API_KEY
    
    # Default date range: last 7 days
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')
    
    cache_key = f"{symbol}_{from_date}_{to_date}"
    cache_path = CACHE_DIR / f"sentiment_{cache_key.replace('.', '_')}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=6):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/stock/social-sentiment"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'error' in data:
            print(f"No sentiment data for {symbol}")
            return None
        
        # Add metadata
        data['fetched_at'] = datetime.now().isoformat()
        data['from_date'] = from_date
        data['to_date'] = to_date
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching sentiment for {symbol}: {e}")
        return None


def get_latest_sentiment(symbol: str) -> Optional[Dict]:
    """
    Get latest sentiment scores for a symbol (last 24 hours).
    
    Returns:
        Dict with aggregated sentiment metrics
    """
    sentiment = get_sentiment(symbol, from_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    
    if not sentiment or 'data' not in sentiment:
        return None
    
    # Aggregate latest data
    reddit = sentiment.get('reddit', {})
    twitter = sentiment.get('twitter', {})
    
    return {
        'symbol': symbol,
        'reddit_mentions': reddit.get('mention', 0),
        'reddit_score': reddit.get('score', 0),
        'reddit_positive_score': reddit.get('positiveScore', 0),
        'reddit_negative_score': reddit.get('negativeScore', 0),
        'twitter_mentions': twitter.get('mention', 0),
        'twitter_score': twitter.get('score', 0),
        'twitter_positive_score': twitter.get('positiveScore', 0),
        'twitter_negative_score': twitter.get('negativeScore', 0),
        'overall_mentions': reddit.get('mention', 0) + twitter.get('mention', 0),
        'fetched_at': sentiment.get('fetched_at')
    }


def get_batch_sentiment(symbols: List[str], use_cache: bool = True) -> pd.DataFrame:
    """
    Get sentiment for multiple symbols.
    
    Args:
        symbols: List of stock tickers
        use_cache: Use cached data when available
    
    Returns:
        DataFrame with sentiment metrics per symbol
    """
    results = []
    
    for symbol in symbols:
        sentiment = get_latest_sentiment(symbol)
        if sentiment:
            results.append(sentiment)
    
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Calculate sentiment momentum (bullish if positive > negative)
    df['sentiment_momentum'] = (
        (df['reddit_positive_score'] + df['twitter_positive_score']) - 
        (df['reddit_negative_score'] + df['twitter_negative_score'])
    )
    
    return df


def get_historical_sentiment(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Get historical sentiment time series.
    
    Args:
        symbol: Stock ticker
        days: Number of days to fetch (max 365)
    
    Returns:
        DataFrame with daily sentiment scores
    """
    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    to_date = datetime.now().strftime('%Y-%m-%d')
    
    sentiment = get_sentiment(symbol, from_date=from_date, to_date=to_date)
    
    if not sentiment or 'data' not in sentiment:
        return pd.DataFrame()
    
    # Parse daily data
    records = []
    for entry in sentiment['data']:
        records.append({
            'symbol': symbol,
            'date': entry.get('atTime'),
            'reddit_mentions': entry.get('mention', 0),
            'reddit_positive_score': entry.get('positiveScore', 0),
            'reddit_negative_score': entry.get('negativeScore', 0),
            'reddit_score': entry.get('score', 0)
        })
    
    df = pd.DataFrame(records)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    
    return df


def get_data(symbols: Optional[List[str]] = None, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Main entry point - get sentiment data.
    
    Args:
        symbols: List of tickers to fetch (for batch mode)
        symbol: Single ticker (for single mode)
    
    Returns:
        DataFrame with sentiment data
    """
    if symbol:
        symbols = [symbol]
    elif not symbols:
        # Default to popular meme stocks and tech
        symbols = ['AAPL', 'TSLA', 'GME', 'AMC', 'NVDA']
    
    return get_batch_sentiment(symbols)


if __name__ == "__main__":
    # Test the module
    print("Testing Finnhub Social Sentiment module...\n")
    
    # Test 1: Single stock latest sentiment
    print("1. Fetching latest sentiment for AAPL:")
    sentiment = get_latest_sentiment('AAPL')
    if sentiment:
        print(f"  Reddit mentions: {sentiment['reddit_mentions']}")
        print(f"  Reddit score: {sentiment['reddit_score']:.2f}")
        print(f"  Twitter mentions: {sentiment['twitter_mentions']}")
        print(f"  Overall mentions: {sentiment['overall_mentions']}")
    
    # Test 2: Batch sentiment
    print("\n2. Batch sentiment for meme stocks:")
    df = get_data(symbols=['AAPL', 'TSLA', 'GME'])
    if not df.empty:
        print(df[['symbol', 'overall_mentions', 'sentiment_momentum']].to_string(index=False))
    
    # Test 3: Historical sentiment
    print("\n3. Historical sentiment for TSLA (last 7 days):")
    hist = get_historical_sentiment('TSLA', days=7)
    if not hist.empty:
        print(hist[['date', 'reddit_mentions', 'reddit_score']].tail(3).to_string(index=False))
    
    print("\n✓ Module test complete")
