#!/usr/bin/env python3
"""
Finnhub Stock News API Module

Real-time news headlines, summaries, and sources for stocks and markets.
Supports company news, market news, sentiment analysis, and news search.
Designed for algorithmic trading and news-driven strategies.

Source: https://finnhub.io/docs/api/company-news
Category: News & NLP
Free tier: True (60 API calls per minute, daily limits)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")


def get_company_news(symbol: str, from_date: str, to_date: str) -> Dict[str, Any]:
    """
    Fetch news articles for a specific company/ticker.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict with 'data' key containing list of news articles, or 'error' key on failure.
        Each article includes: category, datetime, headline, id, image, related, source, summary, url
    
    Example:
        >>> news = get_company_news("AAPL", "2024-01-01", "2024-01-31")
        >>> if 'data' in news:
        ...     for article in news['data']:
        ...         print(article['headline'])
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not set in environment"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            "symbol": symbol.upper(),
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return {
            "data": data,
            "symbol": symbol,
            "from_date": from_date,
            "to_date": to_date,
            "count": len(data) if isinstance(data, list) else 0
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_market_news(category: str = "general") -> Dict[str, Any]:
    """
    Fetch general market news articles.
    
    Args:
        category: News category. Options: 'general', 'forex', 'crypto', 'merger'
        
    Returns:
        Dict with 'data' key containing list of news articles, or 'error' key on failure.
        Each article includes: category, datetime, headline, id, image, related, source, summary, url
    
    Example:
        >>> news = get_market_news("crypto")
        >>> if 'data' in news:
        ...     print(f"Found {news['count']} crypto news articles")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not set in environment"}
    
    valid_categories = ['general', 'forex', 'crypto', 'merger']
    if category not in valid_categories:
        return {"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}
    
    try:
        url = f"{FINNHUB_BASE_URL}/news"
        params = {
            "category": category,
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return {
            "data": data,
            "category": category,
            "count": len(data) if isinstance(data, list) else 0,
            "fetched_at": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_news_sentiment(symbol: str) -> Dict[str, Any]:
    """
    Fetch news sentiment data for a specific company.
    
    Note: Finnhub's sentiment data is part of their premium tier.
    This function attempts to derive basic sentiment from recent news headlines.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        
    Returns:
        Dict with 'data' key containing sentiment analysis, or 'error' key on failure.
        Includes: symbol, news_count, recent_headlines, sentiment_score (if available)
    
    Example:
        >>> sentiment = get_news_sentiment("TSLA")
        >>> if 'data' in sentiment:
        ...     print(f"Recent news count: {sentiment['data']['news_count']}")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not set in environment"}
    
    try:
        # Fetch recent news (last 7 days) for sentiment analysis
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        news_result = get_company_news(symbol, from_date, to_date)
        
        if 'error' in news_result:
            return news_result
        
        articles = news_result.get('data', [])
        
        # Extract headlines for basic sentiment indication
        headlines = [article.get('headline', '') for article in articles[:10]]
        
        return {
            "data": {
                "symbol": symbol,
                "news_count": len(articles),
                "recent_headlines": headlines,
                "date_range": f"{from_date} to {to_date}",
                "note": "Basic news aggregation. Full sentiment analysis requires premium tier."
            }
        }
        
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def search_news(query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Search news articles by keyword across all sources.
    
    Note: This function searches company news for tickers matching the query.
    For more advanced news search, consider using the market news endpoint with filters.
    
    Args:
        query: Search query (ticker symbol or company name)
        from_date: Optional start date in YYYY-MM-DD format (defaults to 7 days ago)
        to_date: Optional end date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Dict with 'data' key containing matching news articles, or 'error' key on failure.
    
    Example:
        >>> results = search_news("Tesla", "2024-01-01", "2024-01-31")
        >>> if 'data' in results:
        ...     print(f"Found {results['count']} articles")
    """
    if not FINNHUB_API_KEY:
        return {"error": "FINNHUB_API_KEY not set in environment"}
    
    try:
        # Set default date range if not provided
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Treat query as ticker symbol for company news search
        # Note: For better results, query should be a valid ticker
        news_result = get_company_news(query.upper(), from_date, to_date)
        
        if 'error' in news_result:
            # If direct ticker search fails, try market news
            market_result = get_market_news("general")
            if 'error' in market_result:
                return {"error": f"Search failed for query '{query}'"}
            
            # Filter market news by query keyword in headline or summary
            all_news = market_result.get('data', [])
            filtered = [
                article for article in all_news
                if query.lower() in article.get('headline', '').lower() or
                   query.lower() in article.get('summary', '').lower()
            ]
            
            return {
                "data": filtered,
                "query": query,
                "count": len(filtered),
                "date_range": f"{from_date} to {to_date}",
                "search_type": "market_news_filtered"
            }
        
        return news_result
        
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# ========== UTILITY FUNCTIONS ==========

def get_api_status() -> Dict[str, Any]:
    """
    Check if Finnhub API key is configured and accessible.
    
    Returns:
        Dict with status information
    """
    if not FINNHUB_API_KEY:
        return {
            "status": "error",
            "message": "FINNHUB_API_KEY not set in environment"
        }
    
    try:
        # Test with a simple market news request
        result = get_market_news("general")
        if 'error' in result:
            return {
                "status": "error",
                "message": result['error']
            }
        
        return {
            "status": "ok",
            "message": "Finnhub API key is valid and working",
            "base_url": FINNHUB_BASE_URL
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"API test failed: {str(e)}"
        }


if __name__ == "__main__":
    # Test module functionality
    print("=== Finnhub Stock News API Module ===\n")
    
    status = get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}\n")
    
    if status['status'] == 'ok':
        # Test company news
        print("Testing get_company_news('AAPL', last 7 days)...")
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        news = get_company_news("AAPL", from_date, to_date)
        if 'data' in news:
            print(f"✓ Found {news['count']} articles")
            if news['data']:
                print(f"  Latest: {news['data'][0].get('headline', 'N/A')[:80]}...")
        else:
            print(f"✗ Error: {news.get('error')}")
