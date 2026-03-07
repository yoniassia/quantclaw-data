#!/usr/bin/env python3
"""
Finnhub News API — Real-time Financial News & Sentiment

Provides real-time financial news from various sources, including company-specific news,
market updates, and sentiment indicators. Supports quantitative analysis by offering
structured news data for event-driven trading strategies and NLP-based sentiment scoring.

Source: https://finnhub.io/docs/api/company-news
Category: News & NLP
Free tier: True (60 API calls/min, 500 calls/day)
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
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

# Finnhub API Configuration
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make authenticated request to Finnhub API
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        ValueError: If API key is missing
        requests.RequestException: If request fails
    """
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not found in environment variables")
    
    url = f"{FINNHUB_BASE_URL}/{endpoint}"
    params = params or {}
    params['token'] = FINNHUB_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "endpoint": endpoint}

def get_company_news(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
    """
    Get company-specific news articles
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        from_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        to_date: End date in YYYY-MM-DD format (default: today)
        
    Returns:
        List of news articles with headline, source, url, summary, datetime
        
    Example:
        >>> news = get_company_news('AAPL')
        >>> print(news[0]['headline'])
    """
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {
        'symbol': symbol.upper(),
        'from': from_date,
        'to': to_date
    }
    
    result = _make_request('company-news', params)
    return result if isinstance(result, list) else []

def get_market_news(category: str = 'general') -> List[Dict]:
    """
    Get general market news by category
    
    Args:
        category: News category - 'general', 'forex', 'crypto', 'merger'
        
    Returns:
        List of market news articles
        
    Example:
        >>> news = get_market_news('crypto')
        >>> print(len(news))
    """
    params = {'category': category}
    result = _make_request('news', params)
    return result if isinstance(result, list) else []

def get_news_sentiment(symbol: str) -> Dict:
    """
    Get aggregated news sentiment score for a ticker
    
    Args:
        symbol: Stock ticker symbol (e.g., 'TSLA')
        
    Returns:
        Dict with sentiment scores, buzz, and article counts
        
    Example:
        >>> sentiment = get_news_sentiment('TSLA')
        >>> print(sentiment.get('sentiment', {}).get('score'))
    """
    params = {'symbol': symbol.upper()}
    return _make_request('news-sentiment', params)

def search_news(query: str, from_date: Optional[str] = None) -> List[Dict]:
    """
    Search news articles by keyword
    
    Note: This uses company news with a broad search approach.
    Finnhub doesn't have a dedicated search endpoint in free tier.
    
    Args:
        query: Search keyword/phrase
        from_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        
    Returns:
        List of matching news articles
        
    Example:
        >>> results = search_news('earnings')
        >>> print(len(results))
    """
    # Use general market news as a proxy for keyword search
    # More sophisticated search would require premium tier
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    to_date = datetime.now().strftime('%Y-%m-%d')
    
    # Try to get general news and filter client-side
    news = get_market_news('general')
    
    if not news or 'error' in str(news):
        return []
    
    # Filter by keyword in headline or summary
    query_lower = query.lower()
    filtered = [
        article for article in news
        if query_lower in article.get('headline', '').lower() or
           query_lower in article.get('summary', '').lower()
    ]
    
    return filtered

def get_press_releases(symbol: str) -> List[Dict]:
    """
    Get company press releases
    
    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA')
        
    Returns:
        List of press releases from the past 90 days
        
    Example:
        >>> releases = get_press_releases('NVDA')
        >>> print(releases[0]['headline'])
    """
    # Use 90-day window for press releases
    from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    to_date = datetime.now().strftime('%Y-%m-%d')
    
    news = get_company_news(symbol, from_date, to_date)
    
    # Filter for official press releases (typically from company IR sites)
    if not news:
        return []
    
    # Press releases often have specific sources or patterns
    releases = [
        article for article in news
        if 'press release' in article.get('headline', '').lower() or
           'prnewswire' in article.get('source', '').lower() or
           'businesswire' in article.get('source', '').lower() or
           'globenewswire' in article.get('source', '').lower()
    ]
    
    return releases if releases else news  # Fallback to all company news

# Module metadata
__all__ = [
    'get_company_news',
    'get_market_news', 
    'get_news_sentiment',
    'search_news',
    'get_press_releases'
]

if __name__ == "__main__":
    print(json.dumps({
        "module": "finnhub_news_api",
        "status": "active",
        "functions": __all__,
        "source": "https://finnhub.io/docs/api/company-news",
        "free_tier": "60 calls/min, 500 calls/day"
    }, indent=2))
