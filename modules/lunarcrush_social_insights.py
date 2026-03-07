#!/usr/bin/env python3
"""LunarCrush Social Insights — Crypto & Stock Social Sentiment Analysis

LunarCrush aggregates social media data from Twitter, Reddit, and other platforms
to provide sentiment analysis, galaxy scores, and social volume metrics for
cryptocurrencies and stocks. Useful for gauging market sentiment in volatile assets.

Data Source: LunarCrush API v2 (https://lunarcrush.com/developers/api)
Free Tier: 1,000 credits/month with API key
Update Frequency: Hourly
Category: Alternative Data — Social & Sentiment

Author: NightBuilder
Built: 2026-03-07
"""

import os
import json
import urllib.request
from datetime import datetime, timezone
from typing import Any


# API Configuration
API_BASE_URL = "https://api.lunarcrush.com/v2"
API_KEY_ENV = "LUNARCRUSH_API_KEY"


def _get_api_key() -> str:
    """Retrieve API key from environment variable.
    
    Returns:
        API key string.
        
    Raises:
        ValueError: If API key is not configured.
    """
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"LunarCrush API key not found. Set {API_KEY_ENV} environment variable. "
            "Get free API key at https://lunarcrush.com/developers/api"
        )
    return api_key


def _make_request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    """Make HTTP request to LunarCrush API.
    
    Args:
        endpoint: API endpoint path (e.g., 'assets', 'market', 'feeds').
        params: Query parameters dictionary.
        
    Returns:
        JSON response as dictionary.
        
    Raises:
        Exception: On HTTP or parsing errors.
    """
    try:
        api_key = _get_api_key()
        params['key'] = api_key
        
        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        query_string = "&".join(query_parts)
        url = f"{API_BASE_URL}?{query_string}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            
        # Check for API errors
        if 'error' in data:
            raise Exception(f"LunarCrush API error: {data.get('error', 'Unknown error')}")
            
        return data
        
    except ValueError as e:
        # Re-raise API key errors
        raise e
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


def get_asset_metrics(symbol: str = 'BTC') -> dict[str, Any]:
    """Fetch comprehensive social metrics for a specific asset.
    
    Retrieves galaxy score, social volume, sentiment, and other social metrics
    for a given cryptocurrency or stock symbol.
    
    Args:
        symbol: Asset ticker symbol (e.g., 'BTC', 'ETH', 'TSLA').
        
    Returns:
        Dictionary containing:
        - symbol: Asset ticker
        - name: Asset name
        - galaxy_score: LunarCrush proprietary score (0-100)
        - social_volume: Number of social mentions
        - social_volume_24h_change: 24h percentage change in mentions
        - sentiment: Sentiment score (1-5, where 5 is very bullish)
        - price_usd: Current price in USD
        - market_cap: Market capitalization
        - social_dominance: Social share percentage
        - interactions_24h: Total social interactions
        - timestamp: ISO timestamp of data
        - error: Error message if request fails
    """
    try:
        params = {
            'data': 'assets',
            'symbol': symbol.upper()
        }
        
        response = _make_request('assets', params)
        
        if 'error' in response:
            return response
    except ValueError as e:
        # API key not configured
        return {"error": str(e), "symbol": symbol, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol, "timestamp": datetime.now(timezone.utc).isoformat()}
        
    try:
        # Extract asset data from response
        asset_data = response.get('data', [{}])[0] if response.get('data') else {}
        
        return {
            "symbol": asset_data.get('symbol', symbol.upper()),
            "name": asset_data.get('name', ''),
            "galaxy_score": asset_data.get('galaxy_score', 0),
            "alt_rank": asset_data.get('alt_rank', 0),
            "social_volume": asset_data.get('social_volume', 0),
            "social_volume_24h_change": asset_data.get('percent_change_24h_volume', 0),
            "sentiment": asset_data.get('average_sentiment', 0),
            "price_usd": asset_data.get('price', 0),
            "price_btc": asset_data.get('price_btc', 0),
            "market_cap": asset_data.get('market_cap', 0),
            "social_dominance": asset_data.get('social_dominance', 0),
            "interactions_24h": asset_data.get('social_score', 0),
            "url_shares": asset_data.get('url_shares', 0),
            "tweet_spam": asset_data.get('tweet_spam', 0),
            "categories": asset_data.get('categories', []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        
    except (KeyError, IndexError, TypeError) as e:
        return {
            "error": f"Failed to parse asset metrics: {str(e)}",
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_trending_assets(limit: int = 10) -> list[dict[str, Any]]:
    """Fetch currently trending assets based on social activity.
    
    Returns assets with the highest social engagement and galaxy scores,
    useful for identifying market attention and momentum.
    
    Args:
        limit: Maximum number of trending assets to return (default 10).
        
    Returns:
        List of dictionaries, each containing:
        - symbol: Asset ticker
        - name: Asset name
        - galaxy_score: Social sentiment score
        - social_volume: Number of mentions
        - price_usd: Current price
        - price_change_24h: 24h price change percentage
        - rank: Trending rank
    """
    try:
        params = {
            'data': 'market',
            'limit': str(limit),
            'sort': 'galaxy_score'
        }
        
        response = _make_request('market', params)
        
        if 'error' in response:
            return []
    except (ValueError, Exception):
        return []
        
    try:
        assets = response.get('data', [])
        trending = []
        
        for idx, asset in enumerate(assets[:limit], 1):
            trending.append({
                "rank": idx,
                "symbol": asset.get('symbol', ''),
                "name": asset.get('name', ''),
                "galaxy_score": asset.get('galaxy_score', 0),
                "alt_rank": asset.get('alt_rank', 0),
                "social_volume": asset.get('social_volume', 0),
                "price_usd": asset.get('price', 0),
                "price_change_24h": asset.get('percent_change_24h', 0),
                "market_cap": asset.get('market_cap', 0),
                "sentiment": asset.get('average_sentiment', 0),
            })
            
        return trending
        
    except (KeyError, TypeError) as e:
        return []


def get_social_feed(symbol: str = 'BTC', limit: int = 20) -> list[dict[str, Any]]:
    """Fetch recent social media posts and discussions about an asset.
    
    Retrieves actual social media posts from Twitter, Reddit, and other platforms
    that mention the specified asset, with engagement metrics.
    
    Args:
        symbol: Asset ticker symbol (e.g., 'BTC', 'ETH').
        limit: Maximum number of posts to return (default 20, max 50).
        
    Returns:
        List of dictionaries, each containing:
        - post_id: Unique post identifier
        - text: Post content/text
        - source: Platform (twitter, reddit, etc.)
        - created_at: Post timestamp
        - user_name: Author username
        - user_followers: Author follower count
        - engagement: Total engagement (likes, retweets, comments)
        - sentiment: Sentiment score for this post
        - url: Link to original post
    """
    try:
        params = {
            'data': 'feeds',
            'symbol': symbol.upper(),
            'limit': str(min(limit, 50))  # API typically caps at 50
        }
        
        response = _make_request('feeds', params)
        
        if 'error' in response:
            return []
    except (ValueError, Exception):
        return []
        
    try:
        feeds = response.get('data', [])
        posts = []
        
        for feed in feeds[:limit]:
            posts.append({
                "post_id": feed.get('id', ''),
                "text": feed.get('tweet', feed.get('text', '')),
                "source": feed.get('source', 'unknown'),
                "created_at": feed.get('created', feed.get('time', 0)),
                "user_name": feed.get('user_name', ''),
                "user_followers": feed.get('user_followers', 0),
                "engagement": feed.get('interactions', 0),
                "sentiment": feed.get('sentiment', 0),
                "url": feed.get('url', ''),
                "spam_score": feed.get('spam', 0),
            })
            
        return posts
        
    except (KeyError, TypeError) as e:
        return []


def get_market_overview() -> dict[str, Any]:
    """Fetch global cryptocurrency market social metrics overview.
    
    Provides aggregate social sentiment data across all tracked assets,
    useful for gauging overall market mood and social activity levels.
    
    Returns:
        Dictionary containing:
        - total_assets: Number of assets tracked
        - total_social_volume: Aggregate social mentions
        - avg_galaxy_score: Average galaxy score across top assets
        - avg_sentiment: Average market sentiment (1-5)
        - top_trending: List of top 5 trending symbols
        - market_mood: Classification (bullish/neutral/bearish)
        - timestamp: ISO timestamp
        - error: Error message if request fails
    """
    try:
        params = {
            'data': 'global',
        }
        
        response = _make_request('global', params)
        
        if 'error' in response:
            return response
    except ValueError as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "timestamp": datetime.now(timezone.utc).isoformat()}
        
    try:
        global_data = response.get('data', [{}])[0] if response.get('data') else {}
        
        # Get top trending for overview
        trending = get_trending_assets(limit=5)
        top_symbols = [asset['symbol'] for asset in trending]
        
        # Calculate average sentiment from trending
        avg_sentiment = sum(asset.get('sentiment', 0) for asset in trending) / len(trending) if trending else 0
        
        # Classify market mood based on sentiment
        if avg_sentiment >= 3.5:
            mood = "bullish"
        elif avg_sentiment >= 2.5:
            mood = "neutral"
        else:
            mood = "bearish"
        
        return {
            "total_assets": global_data.get('num_coins', 0),
            "market_cap_global": global_data.get('market_cap_global', 0),
            "total_social_volume": global_data.get('social_volume_global', 0),
            "avg_sentiment": round(avg_sentiment, 2),
            "top_trending": top_symbols,
            "market_mood": mood,
            "active_markets": global_data.get('active_markets', 0),
            "btc_dominance": global_data.get('btc_dominance', 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        
    except (KeyError, IndexError, TypeError) as e:
        return {
            "error": f"Failed to parse market overview: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Module metadata
__version__ = "1.0.0"
__author__ = "NightBuilder"
__source__ = "https://lunarcrush.com/developers/api"


if __name__ == "__main__":
    """Test module functionality"""
    print("="*60)
    print("LunarCrush Social Insights Module Test")
    print("="*60)
    
    # Test 1: Asset metrics
    print("\n1. Testing get_asset_metrics('BTC')...")
    btc_metrics = get_asset_metrics('BTC')
    if 'error' in btc_metrics:
        print(f"   ⚠️  Error: {btc_metrics['error']}")
    else:
        print(f"   ✓ BTC Galaxy Score: {btc_metrics.get('galaxy_score', 'N/A')}")
        print(f"   ✓ Social Volume: {btc_metrics.get('social_volume', 'N/A')}")
    
    # Test 2: Trending assets
    print("\n2. Testing get_trending_assets(limit=5)...")
    trending = get_trending_assets(limit=5)
    if trending:
        print(f"   ✓ Found {len(trending)} trending assets")
        for asset in trending[:3]:
            print(f"   - {asset['symbol']}: Galaxy Score {asset['galaxy_score']}")
    else:
        print("   ⚠️  No trending data available")
    
    # Test 3: Social feed
    print("\n3. Testing get_social_feed('BTC', limit=5)...")
    feed = get_social_feed('BTC', limit=5)
    if feed:
        print(f"   ✓ Retrieved {len(feed)} social posts")
    else:
        print("   ⚠️  No feed data available")
    
    # Test 4: Market overview
    print("\n4. Testing get_market_overview()...")
    overview = get_market_overview()
    if 'error' in overview:
        print(f"   ⚠️  Error: {overview['error']}")
    else:
        print(f"   ✓ Market Mood: {overview.get('market_mood', 'N/A')}")
        print(f"   ✓ Avg Sentiment: {overview.get('avg_sentiment', 'N/A')}")
    
    print("\n" + "="*60)
    print("Module test complete")
    print("="*60)
