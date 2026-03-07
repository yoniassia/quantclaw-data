#!/usr/bin/env python3
"""
Polygon.io Ticker News — Real-time Financial News by Ticker

Polygon.io provides real-time and historical news articles related to specific stocks,
including headlines, summaries, publisher details, and sentiment data. Tailored for
financial analysis, enabling NLP for sentiment and event detection in trading algorithms.

Source: https://polygon.io/docs/stocks/get_v2_reference_news
Category: News & NLP
Free tier: 5 API calls per minute (demo key), limited historical access
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Polygon.io API Configuration
POLYGON_BASE_URL = "https://api.polygon.io/v2/reference/news"
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "demo")


def get_ticker_news(
    ticker: str,
    limit: int = 10,
    order: str = "desc",
    api_key: Optional[str] = None
) -> Dict:
    """
    Get news articles for a specific ticker
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        limit: Number of articles to return (max 1000, default 10)
        order: Sort order 'asc' or 'desc' by published_utc (default 'desc')
        api_key: Optional Polygon API key (defaults to env POLYGON_API_KEY or 'demo')
    
    Returns:
        Dict with news articles, metadata, and ticker info
    """
    try:
        params = {
            "ticker": ticker.upper(),
            "limit": min(limit, 1000),
            "order": order,
            "sort": "published_utc",
            "apiKey": api_key or POLYGON_API_KEY
        }
        
        response = requests.get(POLYGON_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "OK":
            return {
                "success": False,
                "error": data.get("error", "API returned non-OK status"),
                "ticker": ticker
            }
        
        results = data.get("results", [])
        
        if not results:
            return {
                "success": False,
                "error": "No news articles found",
                "ticker": ticker
            }
        
        # Extract key info from articles
        articles = []
        for article in results:
            articles.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "author": article.get("author"),
                "published_utc": article.get("published_utc"),
                "article_url": article.get("article_url"),
                "publisher": article.get("publisher", {}).get("name"),
                "publisher_url": article.get("publisher", {}).get("homepage_url"),
                "description": article.get("description", ""),
                "keywords": article.get("keywords", []),
                "tickers": article.get("tickers", []),
                "image_url": article.get("image_url"),
                "amp_url": article.get("amp_url")
            })
        
        return {
            "success": True,
            "ticker": ticker,
            "count": len(articles),
            "articles": articles,
            "timestamp": datetime.now().isoformat(),
            "request_id": data.get("request_id")
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }


def search_news(
    query: Optional[str] = None,
    ticker: Optional[str] = None,
    published_after: Optional[str] = None,
    limit: int = 10,
    order: str = "desc",
    api_key: Optional[str] = None
) -> Dict:
    """
    Search news articles with flexible filters
    
    Args:
        query: Search query for title/description (optional)
        ticker: Filter by ticker symbol (optional)
        published_after: ISO date string for filtering (e.g., '2024-01-01', optional)
        limit: Number of articles to return (max 1000, default 10)
        order: Sort order 'asc' or 'desc' by published_utc (default 'desc')
        api_key: Optional Polygon API key (defaults to env POLYGON_API_KEY or 'demo')
    
    Returns:
        Dict with matching news articles and search metadata
    """
    try:
        params = {
            "limit": min(limit, 1000),
            "order": order,
            "sort": "published_utc",
            "apiKey": api_key or POLYGON_API_KEY
        }
        
        if ticker:
            params["ticker"] = ticker.upper()
        
        if published_after:
            params["published_utc.gte"] = published_after
        
        response = requests.get(POLYGON_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "OK":
            return {
                "success": False,
                "error": data.get("error", "API returned non-OK status"),
                "query": query,
                "ticker": ticker
            }
        
        results = data.get("results", [])
        
        # Apply client-side query filter if provided (Polygon API doesn't support query param directly)
        if query and results:
            query_lower = query.lower()
            results = [
                r for r in results
                if query_lower in r.get("title", "").lower() or query_lower in r.get("description", "").lower()
            ]
        
        if not results:
            return {
                "success": False,
                "error": "No matching articles found",
                "query": query,
                "ticker": ticker
            }
        
        # Extract key info from articles
        articles = []
        for article in results:
            articles.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "author": article.get("author"),
                "published_utc": article.get("published_utc"),
                "article_url": article.get("article_url"),
                "publisher": article.get("publisher", {}).get("name"),
                "description": article.get("description", ""),
                "keywords": article.get("keywords", []),
                "tickers": article.get("tickers", [])
            })
        
        return {
            "success": True,
            "query": query,
            "ticker": ticker,
            "published_after": published_after,
            "count": len(articles),
            "articles": articles,
            "timestamp": datetime.now().isoformat(),
            "request_id": data.get("request_id")
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "query": query
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def get_market_news(
    limit: int = 20,
    order: str = "desc",
    api_key: Optional[str] = None
) -> Dict:
    """
    Get broad market news (no ticker filter)
    Returns general financial news across all markets
    
    Args:
        limit: Number of articles to return (max 1000, default 20)
        order: Sort order 'asc' or 'desc' by published_utc (default 'desc')
        api_key: Optional Polygon API key (defaults to env POLYGON_API_KEY or 'demo')
    
    Returns:
        Dict with market news articles and metadata
    """
    try:
        params = {
            "limit": min(limit, 1000),
            "order": order,
            "sort": "published_utc",
            "apiKey": api_key or POLYGON_API_KEY
        }
        
        response = requests.get(POLYGON_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "OK":
            return {
                "success": False,
                "error": data.get("error", "API returned non-OK status")
            }
        
        results = data.get("results", [])
        
        if not results:
            return {
                "success": False,
                "error": "No market news found"
            }
        
        # Extract key info from articles
        articles = []
        for article in results:
            articles.append({
                "id": article.get("id"),
                "title": article.get("title"),
                "author": article.get("author"),
                "published_utc": article.get("published_utc"),
                "article_url": article.get("article_url"),
                "publisher": article.get("publisher", {}).get("name"),
                "description": article.get("description", ""),
                "keywords": article.get("keywords", []),
                "tickers": article.get("tickers", []),
                "image_url": article.get("image_url")
            })
        
        # Aggregate ticker mentions
        ticker_mentions = {}
        for article in results:
            for ticker in article.get("tickers", []):
                ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1
        
        # Sort tickers by mention frequency
        top_tickers = sorted(ticker_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles,
            "top_tickers": [{"ticker": t[0], "mentions": t[1]} for t in top_tickers],
            "timestamp": datetime.now().isoformat(),
            "request_id": data.get("request_id")
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_latest(limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Convenience wrapper for latest market news
    Alias for get_market_news() with default limit
    
    Args:
        limit: Number of articles to return (default 10)
        api_key: Optional Polygon API key
    
    Returns:
        Dict with latest market news
    """
    return get_market_news(limit=limit, api_key=api_key)


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Polygon.io Ticker News API - QuantClaw Data Module")
    print("=" * 60)
    
    print("\n1. Testing get_ticker_news('AAPL')...")
    aapl_news = get_ticker_news("AAPL", limit=3)
    print(f"   Success: {aapl_news.get('success')}")
    print(f"   Count: {aapl_news.get('count', 0)}")
    if aapl_news.get('success') and aapl_news.get('articles'):
        print(f"   Latest headline: {aapl_news['articles'][0].get('title', 'N/A')[:80]}...")
    
    print("\n2. Testing get_market_news()...")
    market_news = get_market_news(limit=5)
    print(f"   Success: {market_news.get('success')}")
    print(f"   Count: {market_news.get('count', 0)}")
    if market_news.get('success') and market_news.get('top_tickers'):
        print(f"   Top ticker mentions: {market_news['top_tickers'][:3]}")
    
    print("\n3. Testing get_latest()...")
    latest = get_latest(limit=3)
    print(f"   Success: {latest.get('success')}")
    print(f"   Count: {latest.get('count', 0)}")
    
    print("\n4. Full output sample (AAPL news):")
    print(json.dumps(aapl_news, indent=2))
