#!/usr/bin/env python3
"""
TwelveData Stock Sentiment API Module

TwelveData sentiment analysis integration for stock market sentiment tracking:
- Real-time sentiment scores and breakdowns
- Historical sentiment trends
- Batch sentiment analysis for multiple symbols
- Trending sentiment movers
- News-specific sentiment analysis

Source: https://twelvedata.com/docs#sentiment
Category: Market Sentiment & Analytics
Free tier: True (requires TWELVE_DATA_API_KEY env var)
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

# TwelveData API Configuration
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")


def get_sentiment(symbol: str = 'AAPL') -> Dict:
    """
    Get current sentiment score and breakdown for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with keys: symbol, sentiment_score, positive_percentage, 
                       negative_percentage, neutral_percentage, volume, timestamp
    
    Example:
        >>> sentiment = get_sentiment('AAPL')
        >>> print(f"Sentiment: {sentiment.get('sentiment_score')}, Positive: {sentiment.get('positive_percentage')}%")
    """
    try:
        if not TWELVE_DATA_API_KEY:
            return {"error": "TWELVE_DATA_API_KEY not set in environment"}
        
        url = f"{TWELVE_DATA_BASE_URL}/sentiment"
        params = {
            "symbol": symbol,
            "apikey": TWELVE_DATA_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if "status" in data and data["status"] == "error":
            return {"error": data.get("message", "API error"), "symbol": symbol}
        
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "symbol": symbol}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {str(e)}", "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_sentiment_history(symbol: str = 'AAPL', days: int = 30) -> Dict:
    """
    Get historical sentiment data over time for a symbol.
    
    Note: TwelveData API may have limited historical sentiment data.
    This function attempts to fetch time series sentiment if available.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
        days: Number of days of history to fetch (default: 30)
    
    Returns:
        Dict with historical sentiment data or current sentiment with metadata
    
    Example:
        >>> history = get_sentiment_history('TSLA', days=7)
        >>> print(f"History for {history.get('symbol')}: {len(history.get('data', []))} records")
    """
    try:
        if not TWELVE_DATA_API_KEY:
            return {"error": "TWELVE_DATA_API_KEY not set in environment"}
        
        # TwelveData sentiment endpoint may not support historical queries directly
        # We'll fetch current sentiment and note the limitation
        url = f"{TWELVE_DATA_BASE_URL}/sentiment"
        params = {
            "symbol": symbol,
            "apikey": TWELVE_DATA_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "status" in data and data["status"] == "error":
            return {"error": data.get("message", "API error"), "symbol": symbol}
        
        # Wrap in historical format
        return {
            "symbol": symbol,
            "days_requested": days,
            "note": "TwelveData sentiment API provides current snapshot; historical data may require premium tier",
            "current_sentiment": data,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "symbol": symbol}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON response: {str(e)}", "symbol": symbol}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "symbol": symbol}


def get_sentiment_batch(symbols: List[str]) -> Dict:
    """
    Get sentiment data for multiple stock symbols at once.
    
    Args:
        symbols: List of stock ticker symbols (e.g., ['AAPL', 'TSLA', 'MSFT'])
    
    Returns:
        Dict with sentiment data for each symbol
    
    Example:
        >>> batch = get_sentiment_batch(['AAPL', 'GOOGL', 'MSFT'])
        >>> for sym, data in batch.get('results', {}).items():
        ...     print(f"{sym}: {data.get('sentiment_score')}")
    """
    try:
        if not TWELVE_DATA_API_KEY:
            return {"error": "TWELVE_DATA_API_KEY not set in environment"}
        
        if not symbols or not isinstance(symbols, list):
            return {"error": "symbols must be a non-empty list"}
        
        results = {}
        
        # Fetch sentiment for each symbol
        for symbol in symbols:
            sentiment = get_sentiment(symbol)
            results[symbol] = sentiment
        
        return {
            "symbols": symbols,
            "count": len(symbols),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Batch processing error: {str(e)}"}


def get_trending_sentiment() -> Dict:
    """
    Get the most positive and negative sentiment movers.
    
    Note: This function uses a curated list of popular stocks.
    TwelveData may require premium tier for market-wide sentiment scanning.
    
    Returns:
        Dict with top positive and negative sentiment stocks
    
    Example:
        >>> trending = get_trending_sentiment()
        >>> print(f"Most positive: {trending.get('most_positive', [])[:3]}")
        >>> print(f"Most negative: {trending.get('most_negative', [])[:3]}")
    """
    try:
        if not TWELVE_DATA_API_KEY:
            return {"error": "TWELVE_DATA_API_KEY not set in environment"}
        
        # Popular stocks to scan for sentiment
        popular_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
            'META', 'NVDA', 'JPM', 'V', 'WMT',
            'DIS', 'NFLX', 'BAC', 'INTC', 'AMD'
        ]
        
        sentiment_data = []
        
        for symbol in popular_symbols:
            sentiment = get_sentiment(symbol)
            if "error" not in sentiment and "sentiment_score" in sentiment:
                sentiment_data.append({
                    "symbol": symbol,
                    "sentiment_score": sentiment.get("sentiment_score"),
                    "positive_percentage": sentiment.get("positive_percentage"),
                    "negative_percentage": sentiment.get("negative_percentage")
                })
        
        # Sort by sentiment score
        sentiment_data.sort(key=lambda x: x.get("sentiment_score", 0), reverse=True)
        
        most_positive = sentiment_data[:5]
        most_negative = sentiment_data[-5:]
        
        return {
            "most_positive": most_positive,
            "most_negative": most_negative,
            "scanned_symbols": popular_symbols,
            "total_analyzed": len(sentiment_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Trending sentiment error: {str(e)}"}


def get_news_sentiment(symbol: str = 'AAPL') -> Dict:
    """
    Get news-specific sentiment analysis for a stock symbol.
    
    Note: TwelveData's sentiment endpoint aggregates news sources.
    This function provides the same data as get_sentiment but with 
    explicit focus on news-driven sentiment.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with news sentiment data including sources and breakdown
    
    Example:
        >>> news_sent = get_news_sentiment('TSLA')
        >>> print(f"News sentiment for {news_sent.get('symbol')}: {news_sent.get('sentiment_score')}")
    """
    try:
        if not TWELVE_DATA_API_KEY:
            return {"error": "TWELVE_DATA_API_KEY not set in environment"}
        
        # TwelveData sentiment is primarily news-driven
        sentiment = get_sentiment(symbol)
        
        if "error" in sentiment:
            return sentiment
        
        # Enhance with news context
        sentiment["data_type"] = "news_sentiment"
        sentiment["note"] = "Sentiment aggregated from news sources"
        
        return sentiment
        
    except Exception as e:
        return {"error": f"News sentiment error: {str(e)}", "symbol": symbol}


# Module metadata
__all__ = [
    'get_sentiment',
    'get_sentiment_history',
    'get_sentiment_batch',
    'get_trending_sentiment',
    'get_news_sentiment'
]

__version__ = "1.0.0"
__author__ = "QuantClaw Data NightBuilder"
