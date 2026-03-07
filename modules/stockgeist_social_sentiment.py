#!/usr/bin/env python3
"""
StockGeist Social Sentiment — Real-time social media sentiment analysis

Provides sentiment scores, message volumes, and anomaly detection for stocks
based on Twitter, StockTwits, and Reddit data.

Source: https://stockgeist.ai/api
Category: Alternative Data — Social & Sentiment
Free tier: 500 messages/day with registration
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# StockGeist API Configuration
STOCKGEIST_API_BASE = "https://api.stockgeist.ai"
STOCKGEIST_API_KEY = os.environ.get("STOCKGEIST_API_KEY", "")


def _get_headers() -> Dict[str, str]:
    """Get authentication headers for StockGeist API"""
    if STOCKGEIST_API_KEY:
        return {
            "Authorization": f"Bearer {STOCKGEIST_API_KEY}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to StockGeist API
    
    Args:
        endpoint: API endpoint path (e.g., '/stock/sentiment')
        params: Optional query parameters
    
    Returns:
        Dict with success status and data or error
    """
    if not STOCKGEIST_API_KEY:
        return {
            "success": False,
            "error": "STOCKGEIST_API_KEY not set. Get API key at https://stockgeist.ai",
            "fallback": True
        }
    
    try:
        url = f"{STOCKGEIST_API_BASE}{endpoint}"
        response = requests.get(url, headers=_get_headers(), params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            "status_code": e.response.status_code
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_sentiment(symbol: str) -> Dict:
    """
    Get current sentiment score for a stock symbol
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing:
        - sentiment_score: Float between -1 (bearish) and 1 (bullish)
        - message_count: Number of messages analyzed
        - timestamp: When the sentiment was calculated
        
    Example:
        >>> result = get_sentiment('AAPL')
        >>> if result['success']:
        ...     print(f"Sentiment: {result['data']['sentiment_score']}")
    """
    result = _make_request("/stock/sentiment", {"symbol": symbol.upper()})
    
    # Fallback to sample data if no API key
    if result.get("fallback"):
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "sentiment_score": 0.35,
                "message_count": 1247,
                "bullish_pct": 58.2,
                "bearish_pct": 41.8,
                "timestamp": datetime.now().isoformat()
            },
            "source": "sample_data",
            "note": "Set STOCKGEIST_API_KEY for real data"
        }
    
    return result


def get_message_volume(symbol: str) -> Dict:
    """
    Get message volume statistics for a stock symbol
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dict containing:
        - current_volume: Messages in the last hour
        - daily_volume: Messages in the last 24 hours
        - volume_change_pct: Percentage change vs previous period
        
    Example:
        >>> result = get_message_volume('TSLA')
        >>> if result['success']:
        ...     print(f"24h volume: {result['data']['daily_volume']}")
    """
    result = _make_request("/stock/volume", {"symbol": symbol.upper()})
    
    # Fallback to sample data if no API key
    if result.get("fallback"):
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "current_volume": 342,
                "daily_volume": 5821,
                "weekly_volume": 28934,
                "volume_change_pct": 15.3,
                "avg_daily_volume": 4200,
                "timestamp": datetime.now().isoformat()
            },
            "source": "sample_data",
            "note": "Set STOCKGEIST_API_KEY for real data"
        }
    
    return result


def get_anomalies(symbol: str = 'all') -> Dict:
    """
    Detect anomalous spikes in social media activity
    
    Args:
        symbol: Stock ticker or 'all' for market-wide anomalies
    
    Returns:
        Dict containing list of detected anomalies with:
        - symbol: Ticker symbol
        - anomaly_score: Strength of the anomaly (0-100)
        - volume_spike: Percentage increase in volume
        - sentiment_shift: Change in sentiment score
        
    Example:
        >>> result = get_anomalies()
        >>> for anomaly in result['data']['anomalies']:
        ...     print(f"{anomaly['symbol']}: {anomaly['anomaly_score']}")
    """
    params = {} if symbol == 'all' else {"symbol": symbol.upper()}
    result = _make_request("/stock/anomaly", params)
    
    # Fallback to sample data if no API key
    if result.get("fallback"):
        return {
            "success": True,
            "data": {
                "anomalies": [
                    {
                        "symbol": "NVDA",
                        "anomaly_score": 87.5,
                        "volume_spike": 234.5,
                        "sentiment_shift": 0.42,
                        "trigger": "volume_spike",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "symbol": "GME",
                        "anomaly_score": 76.2,
                        "volume_spike": 189.3,
                        "sentiment_shift": -0.18,
                        "trigger": "sentiment_shift",
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "timestamp": datetime.now().isoformat()
            },
            "source": "sample_data",
            "note": "Set STOCKGEIST_API_KEY for real data"
        }
    
    return result


def get_trending_tickers(limit: int = 10) -> Dict:
    """
    Get the most talked-about stocks on social media
    
    Args:
        limit: Maximum number of trending tickers to return (default: 10)
    
    Returns:
        Dict containing list of trending stocks with:
        - symbol: Ticker symbol
        - message_count: Number of messages
        - sentiment_score: Overall sentiment
        - rank: Trending rank
        
    Example:
        >>> result = get_trending_tickers(5)
        >>> for ticker in result['data']['trending']:
        ...     print(f"{ticker['rank']}. {ticker['symbol']}: {ticker['message_count']} msgs")
    """
    result = _make_request("/stock/trending", {"limit": limit})
    
    # Fallback to sample data if no API key
    if result.get("fallback"):
        trending_symbols = [
            ("NVDA", 8924, 0.62),
            ("TSLA", 7832, 0.45),
            ("AAPL", 6543, 0.28),
            ("GME", 5421, -0.12),
            ("AMD", 4987, 0.51),
            ("MSFT", 4234, 0.33),
            ("META", 3891, 0.19),
            ("AMZN", 3567, 0.24),
            ("GOOGL", 3245, 0.17),
            ("SPY", 2987, 0.08)
        ]
        
        return {
            "success": True,
            "data": {
                "trending": [
                    {
                        "rank": i + 1,
                        "symbol": sym,
                        "message_count": count,
                        "sentiment_score": sent,
                        "timestamp": datetime.now().isoformat()
                    }
                    for i, (sym, count, sent) in enumerate(trending_symbols[:limit])
                ],
                "period": "24h",
                "timestamp": datetime.now().isoformat()
            },
            "source": "sample_data",
            "note": "Set STOCKGEIST_API_KEY for real data"
        }
    
    return result


def get_sentiment_history(symbol: str, days: int = 7) -> Dict:
    """
    Get historical sentiment data for a stock
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        days: Number of days of history (default: 7, max: 30)
    
    Returns:
        Dict containing time series of sentiment scores:
        - history: List of daily sentiment scores
        - avg_sentiment: Average sentiment over the period
        - sentiment_trend: 'bullish', 'bearish', or 'neutral'
        
    Example:
        >>> result = get_sentiment_history('AAPL', days=14)
        >>> for day in result['data']['history']:
        ...     print(f"{day['date']}: {day['sentiment_score']}")
    """
    days = min(days, 30)  # Cap at 30 days
    params = {
        "symbol": symbol.upper(),
        "start": (datetime.now() - timedelta(days=days)).isoformat(),
        "end": datetime.now().isoformat()
    }
    result = _make_request("/stock/sentiment/history", params)
    
    # Fallback to sample data if no API key
    if result.get("fallback"):
        history = []
        base_sentiment = 0.25
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            # Simulate some variance
            variance = (i % 3 - 1) * 0.15
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "sentiment_score": round(base_sentiment + variance, 2),
                "message_count": 1200 + (i * 50) + ((i % 5) * 200)
            })
        
        avg_sentiment = sum(h["sentiment_score"] for h in history) / len(history)
        trend = "bullish" if avg_sentiment > 0.3 else "bearish" if avg_sentiment < -0.1 else "neutral"
        
        return {
            "success": True,
            "data": {
                "symbol": symbol.upper(),
                "history": history,
                "avg_sentiment": round(avg_sentiment, 2),
                "sentiment_trend": trend,
                "days": days,
                "timestamp": datetime.now().isoformat()
            },
            "source": "sample_data",
            "note": "Set STOCKGEIST_API_KEY for real data"
        }
    
    return result


def demo() -> None:
    """
    Demonstrate all module capabilities with sample queries
    
    Runs example queries for sentiment, volume, anomalies, trending,
    and historical data to showcase the module's functionality.
    """
    print("=" * 70)
    print("StockGeist Social Sentiment Module Demo")
    print("=" * 70)
    print()
    
    # Check API key status
    if STOCKGEIST_API_KEY:
        print(f"✓ API Key: Configured ({STOCKGEIST_API_KEY[:8]}...)")
    else:
        print("⚠ API Key: Not set (using sample data)")
        print("  Set STOCKGEIST_API_KEY environment variable for real data")
    print()
    
    # Test 1: Get sentiment for AAPL
    print("1. Current Sentiment - AAPL")
    print("-" * 70)
    result = get_sentiment("AAPL")
    if result["success"]:
        data = result["data"]
        print(f"Symbol: {data.get('symbol', 'N/A')}")
        print(f"Sentiment Score: {data.get('sentiment_score', 'N/A')}")
        print(f"Message Count: {data.get('message_count', 'N/A')}")
        print(f"Bullish: {data.get('bullish_pct', 'N/A')}% | Bearish: {data.get('bearish_pct', 'N/A')}%")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 2: Message volume for TSLA
    print("2. Message Volume - TSLA")
    print("-" * 70)
    result = get_message_volume("TSLA")
    if result["success"]:
        data = result["data"]
        print(f"Symbol: {data.get('symbol', 'N/A')}")
        print(f"Current Hour: {data.get('current_volume', 'N/A')} messages")
        print(f"Daily Volume: {data.get('daily_volume', 'N/A')} messages")
        print(f"Volume Change: {data.get('volume_change_pct', 'N/A')}%")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 3: Anomaly detection
    print("3. Market-Wide Anomalies")
    print("-" * 70)
    result = get_anomalies()
    if result["success"]:
        anomalies = result["data"].get("anomalies", [])
        for anomaly in anomalies[:3]:  # Show top 3
            print(f"{anomaly.get('symbol', 'N/A')} - Score: {anomaly.get('anomaly_score', 'N/A')}")
            print(f"  Volume Spike: +{anomaly.get('volume_spike', 'N/A')}%")
            print(f"  Sentiment Shift: {anomaly.get('sentiment_shift', 'N/A')}")
            print(f"  Trigger: {anomaly.get('trigger', 'N/A')}")
            print()
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 4: Trending tickers
    print("4. Top 5 Trending Tickers")
    print("-" * 70)
    result = get_trending_tickers(5)
    if result["success"]:
        trending = result["data"].get("trending", [])
        for ticker in trending:
            print(f"{ticker.get('rank', 'N/A')}. {ticker.get('symbol', 'N/A')} - "
                  f"{ticker.get('message_count', 'N/A')} msgs (Sentiment: {ticker.get('sentiment_score', 'N/A')})")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 5: Sentiment history
    print("5. Sentiment History - NVDA (7 days)")
    print("-" * 70)
    result = get_sentiment_history("NVDA", days=7)
    if result["success"]:
        data = result["data"]
        print(f"Symbol: {data.get('symbol', 'N/A')}")
        print(f"Avg Sentiment: {data.get('avg_sentiment', 'N/A')}")
        print(f"Trend: {data.get('sentiment_trend', 'N/A').upper()}")
        print()
        print("Daily History:")
        for day in data.get("history", [])[-7:]:
            print(f"  {day.get('date', 'N/A')}: {day.get('sentiment_score', 'N/A')} "
                  f"({day.get('message_count', 'N/A')} msgs)")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()
    
    print("=" * 70)
    print("Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    demo()
