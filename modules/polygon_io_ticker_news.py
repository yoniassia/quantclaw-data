#!/usr/bin/env python3
"""
Polygon.io News API — Financial News & Sentiment Module

Core Polygon.io integration for financial news data including:
- Ticker-specific news articles
- Market-wide news
- News search by keyword
- Basic sentiment analysis

Source: https://api.polygon.io/v2/reference/news
Category: News & NLP
Free tier: True (requires POLYGON_API_KEY env var)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Polygon.io API Configuration
POLYGON_BASE_URL = "https://api.polygon.io/v2/reference"
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")

# Basic sentiment word lists
POSITIVE_WORDS = {
    'gain', 'gains', 'up', 'rise', 'surge', 'rally', 'strong', 'growth', 'profit',
    'positive', 'bull', 'bullish', 'beat', 'beats', 'outperform', 'upgrade', 'record',
    'high', 'increase', 'soar', 'climb', 'advance', 'success', 'win', 'boost'
}

NEGATIVE_WORDS = {
    'loss', 'losses', 'down', 'fall', 'drop', 'decline', 'weak', 'negative', 'bear',
    'bearish', 'miss', 'misses', 'underperform', 'downgrade', 'low', 'decrease',
    'plunge', 'tumble', 'slump', 'fail', 'risk', 'concern', 'worry', 'cut', 'crisis'
}


def get_ticker_news(ticker: str = 'AAPL', limit: int = 10) -> Dict:
    """
    Get news articles for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol (default: 'AAPL')
        limit: Number of results to return (default: 10, max: 1000)
    
    Returns:
        Dict with 'results' key containing array of news articles with:
        id, publisher, title, author, published_utc, article_url, tickers, etc.
    
    Example:
        >>> news = get_ticker_news('AAPL', limit=5)
        >>> for article in news['results']:
        ...     print(f"{article['title']} - {article['published_utc']}")
    """
    try:
        url = f"{POLYGON_BASE_URL}/news"
        params = {
            'ticker': ticker.upper(),
            'limit': limit,
            'order': 'desc',
            'sort': 'published_utc',
            'apiKey': POLYGON_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['ticker'] = ticker.upper()
        data['fetched_at'] = datetime.now().isoformat()
        data['count'] = len(data.get('results', []))
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'ticker': ticker}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'ticker': ticker}


def get_market_news(limit: int = 10) -> Dict:
    """
    Get general market news (no ticker filter).
    
    Args:
        limit: Number of results to return (default: 10, max: 1000)
    
    Returns:
        Dict with 'results' key containing array of market news articles
    
    Example:
        >>> news = get_market_news(limit=5)
        >>> print(f"Found {news['count']} market news articles")
    """
    try:
        url = f"{POLYGON_BASE_URL}/news"
        params = {
            'limit': limit,
            'order': 'desc',
            'sort': 'published_utc',
            'apiKey': POLYGON_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['fetched_at'] = datetime.now().isoformat()
        data['count'] = len(data.get('results', []))
        data['type'] = 'market_news'
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def search_news(query: str, limit: int = 10) -> Dict:
    """
    Search news by keyword.
    
    Args:
        query: Search keyword/phrase
        limit: Number of results to return (default: 10, max: 1000)
    
    Returns:
        Dict with 'results' key containing array of matching news articles
    
    Example:
        >>> news = search_news('artificial intelligence', limit=5)
        >>> for article in news['results']:
        ...     print(article['title'])
    """
    try:
        url = f"{POLYGON_BASE_URL}/news"
        params = {
            'limit': limit,
            'order': 'desc',
            'sort': 'published_utc',
            'apiKey': POLYGON_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Client-side filtering by query (Polygon doesn't have native search)
        if 'results' in data and query:
            query_lower = query.lower()
            filtered_results = [
                article for article in data['results']
                if query_lower in article.get('title', '').lower() or
                   query_lower in article.get('description', '').lower()
            ]
            data['results'] = filtered_results[:limit]
        
        # Add metadata
        data['query'] = query
        data['fetched_at'] = datetime.now().isoformat()
        data['count'] = len(data.get('results', []))
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'query': query}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'query': query}


def get_news_sentiment(ticker: str, limit: int = 20) -> Dict:
    """
    Fetch news and compute basic sentiment (positive/negative/neutral word counting).
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of articles to analyze (default: 20)
    
    Returns:
        Dict with sentiment analysis including:
        - overall_sentiment: 'positive', 'negative', or 'neutral'
        - sentiment_score: Positive score - negative score
        - positive_count: Number of positive words found
        - negative_count: Number of negative words found
        - articles: List of articles with individual sentiment scores
    
    Example:
        >>> sentiment = get_news_sentiment('AAPL')
        >>> print(f"Overall: {sentiment['overall_sentiment']}, Score: {sentiment['sentiment_score']}")
    """
    try:
        # Fetch ticker news
        news_data = get_ticker_news(ticker, limit=limit)
        
        if 'error' in news_data:
            return news_data
        
        articles = news_data.get('results', [])
        
        if not articles:
            return {
                'ticker': ticker.upper(),
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'positive_count': 0,
                'negative_count': 0,
                'articles_analyzed': 0,
                'articles': []
            }
        
        total_positive = 0
        total_negative = 0
        analyzed_articles = []
        
        for article in articles:
            # Combine title and description for analysis
            text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            words = text.split()
            
            # Count sentiment words
            pos_count = sum(1 for word in words if word in POSITIVE_WORDS)
            neg_count = sum(1 for word in words if word in NEGATIVE_WORDS)
            
            article_score = pos_count - neg_count
            article_sentiment = 'neutral'
            
            if article_score > 0:
                article_sentiment = 'positive'
            elif article_score < 0:
                article_sentiment = 'negative'
            
            total_positive += pos_count
            total_negative += neg_count
            
            analyzed_articles.append({
                'title': article.get('title'),
                'published_utc': article.get('published_utc'),
                'article_url': article.get('article_url'),
                'sentiment': article_sentiment,
                'sentiment_score': article_score,
                'positive_words': pos_count,
                'negative_words': neg_count
            })
        
        # Calculate overall sentiment
        overall_score = total_positive - total_negative
        overall_sentiment = 'neutral'
        
        if overall_score > 2:
            overall_sentiment = 'positive'
        elif overall_score < -2:
            overall_sentiment = 'negative'
        
        return {
            'ticker': ticker.upper(),
            'overall_sentiment': overall_sentiment,
            'sentiment_score': overall_score,
            'positive_count': total_positive,
            'negative_count': total_negative,
            'articles_analyzed': len(articles),
            'articles': analyzed_articles,
            'fetched_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Sentiment analysis error: {str(e)}', 'ticker': ticker}


# ========== CLI INTERFACE ==========

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "ticker" and len(sys.argv) > 2:
            ticker = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            result = get_ticker_news(ticker, limit)
        elif command == "market":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            result = get_market_news(limit)
        elif command == "search" and len(sys.argv) > 2:
            query = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            result = search_news(query, limit)
        elif command == "sentiment" and len(sys.argv) > 2:
            ticker = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            result = get_news_sentiment(ticker, limit)
        else:
            result = {
                "module": "polygon_io_ticker_news",
                "version": "1.0",
                "usage": "python polygon_io_ticker_news.py [ticker|market|search|sentiment] <args>",
                "functions": [
                    "get_ticker_news(ticker, limit=10)",
                    "get_market_news(limit=10)",
                    "search_news(query, limit=10)",
                    "get_news_sentiment(ticker, limit=20)"
                ]
            }
    else:
        result = {
            "module": "polygon_io_ticker_news",
            "status": "ready",
            "api_key_set": bool(POLYGON_API_KEY),
            "functions": 4
        }
    
    print(json.dumps(result, indent=2))
