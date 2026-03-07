#!/usr/bin/env python3
"""
Sentiment Investor API — Social Sentiment & Retail Trading Metrics

Aggregates sentiment data from Reddit (e.g., WallStreetBets) and StockTwits,
offering metrics like hype scores and sentiment trends for stocks.
Designed for quantitative analysis of retail investor behavior.

Source: https://sentimentinvestor.com/developer
Category: Alternative Data — Social & Sentiment
Free tier: True (100 calls/day with basic metrics)
Author: QuantClaw Data NightBuilder
Update frequency: Daily
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Sentiment Investor API Configuration
SENTIMENT_BASE_URL = "https://api.sentimentinvestor.com/v4"
SENTIMENT_API_KEY = os.environ.get("SENTIMENT_INVESTOR_API_KEY", "")

# Default timeout for API requests
DEFAULT_TIMEOUT = 15


def get_stock_sentiment(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get current sentiment metrics for a stock symbol
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GME')
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with sentiment score, volume, and trend indicators
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/stock"
        params = {"symbol": symbol.upper()}
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "sentiment": data,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Symbol {symbol} not found or no sentiment data available",
                "symbol": symbol.upper()
            }
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code}",
            "symbol": symbol.upper()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "symbol": symbol.upper()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol.upper()
        }


def get_trending_stocks(limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get trending stocks by social sentiment volume
    
    Args:
        limit: Maximum number of trending stocks to return (default 10)
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with list of trending stocks and their sentiment metrics
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/trending"
        params = {"limit": min(limit, 50)}  # Cap at 50
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "trending_stocks": data,
            "count": len(data) if isinstance(data, list) else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_sentiment_history(symbol: str, days: int = 30, api_key: Optional[str] = None) -> Dict:
    """
    Get historical sentiment data for a stock
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GME')
        days: Number of days of history to fetch (default 30)
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with time series sentiment data and trend analysis
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/stock/history"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "symbol": symbol.upper(),
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Calculate trend if we have data
        trend_analysis = None
        if isinstance(data, list) and len(data) >= 2:
            recent_avg = sum(d.get('sentiment', 0) for d in data[-7:]) / min(7, len(data))
            older_avg = sum(d.get('sentiment', 0) for d in data[:7]) / min(7, len(data))
            
            trend_analysis = {
                "recent_avg_7d": round(recent_avg, 2),
                "older_avg_7d": round(older_avg, 2),
                "trend": "bullish" if recent_avg > older_avg else "bearish",
                "change": round(recent_avg - older_avg, 2)
            }
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "history": data,
            "days_requested": days,
            "data_points": len(data) if isinstance(data, list) else 0,
            "trend_analysis": trend_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"No historical data available for {symbol}",
                "symbol": symbol.upper()
            }
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code}",
            "symbol": symbol.upper()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "symbol": symbol.upper()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol.upper()
        }


def get_hype_score(symbol: str, api_key: Optional[str] = None) -> Dict:
    """
    Get hype score for a stock (retail investor attention metric)
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GME')
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with hype score, rank, and social volume metrics
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/stock"
        params = {
            "symbol": symbol.upper(),
            "metric": "hype"
        }
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Interpret hype score
        hype_value = data.get('hype_score', 0) if isinstance(data, dict) else 0
        interpretation = "low"
        if hype_value > 75:
            interpretation = "extreme"
        elif hype_value > 50:
            interpretation = "high"
        elif hype_value > 25:
            interpretation = "moderate"
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "hype_data": data,
            "interpretation": interpretation,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"No hype data available for {symbol}",
                "symbol": symbol.upper()
            }
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code}",
            "symbol": symbol.upper()
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "symbol": symbol.upper()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol.upper()
        }


def get_reddit_mentions(symbol: str, subreddit: str = "wallstreetbets", api_key: Optional[str] = None) -> Dict:
    """
    Get Reddit mention count and sentiment for a stock
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GME')
        subreddit: Subreddit to search (default 'wallstreetbets')
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with mention count, sentiment breakdown, top posts
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/reddit"
        params = {
            "symbol": symbol.upper(),
            "subreddit": subreddit
        }
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "subreddit": subreddit,
            "reddit_data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "symbol": symbol.upper(),
            "subreddit": subreddit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol.upper(),
            "subreddit": subreddit
        }


def list_available_symbols(api_key: Optional[str] = None) -> Dict:
    """
    Get list of all symbols with sentiment data available
    
    Args:
        api_key: Optional API key for authenticated requests
    
    Returns:
        Dict with list of available symbols
    """
    try:
        url = f"{SENTIMENT_BASE_URL}/symbols"
        
        headers = {}
        if api_key or SENTIMENT_API_KEY:
            headers["Authorization"] = f"Bearer {api_key or SENTIMENT_API_KEY}"
        
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "symbols": data,
            "count": len(data) if isinstance(data, list) else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Sentiment Investor API - Social Sentiment & Retail Metrics")
    print("=" * 60)
    
    # Test with popular meme stocks
    test_symbols = ["GME", "AAPL"]
    
    for symbol in test_symbols:
        print(f"\n--- {symbol} Sentiment ---")
        sentiment = get_stock_sentiment(symbol)
        print(json.dumps(sentiment, indent=2))
        
        print(f"\n--- {symbol} Hype Score ---")
        hype = get_hype_score(symbol)
        print(json.dumps(hype, indent=2))
    
    print("\n--- Trending Stocks ---")
    trending = get_trending_stocks(limit=5)
    print(json.dumps(trending, indent=2))
    
    print("\n--- GME 30-Day Sentiment History ---")
    history = get_sentiment_history("GME", days=30)
    print(json.dumps(history, indent=2))
