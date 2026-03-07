#!/usr/bin/env python3
"""
EODHD News and Sentiment Module

Real-time and historical news with NLP-powered sentiment scores for stocks, forex, and crypto.
Provides tagged news articles with sentiment polarity for trading signals and market analysis.

Source: https://eodhd.com/financial-apis/news-api-real-time-and-historical-stock-news/
Category: News & NLP
Free tier: 100 calls/day with limited symbols
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

# EODHD API Configuration
EODHD_BASE_URL = "https://eodhd.com/api/news"
EODHD_API_KEY = os.environ.get("EODHD_API_KEY", "demo")


def get_news(symbol: str, limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get latest news articles for a specific ticker symbol
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA', 'MSFT')
        limit: Maximum number of articles to return (default 10)
        api_key: Optional EODHD API key (uses env var if not provided)
    
    Returns:
        Dict with news articles, each containing title, content, sentiment, source, and published date
    
    Example:
        >>> news = get_news('AAPL', limit=5)
        >>> print(news['articles'][0]['title'])
    """
    try:
        params = {
            'api_token': api_key or EODHD_API_KEY,
            's': symbol.upper(),
            'limit': min(limit, 1000),  # API max
            'offset': 0
        }
        
        response = requests.get(EODHD_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        articles = response.json()
        
        if not isinstance(articles, list):
            return {
                'success': False,
                'error': 'Unexpected response format',
                'symbol': symbol
            }
        
        # Parse and enrich articles
        parsed_articles = []
        for article in articles[:limit]:
            parsed_articles.append({
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'published_at': article.get('date', ''),
                'source': article.get('link', ''),
                'sentiment': article.get('sentiment', {}),
                'tags': article.get('tags', []),
                'symbols': article.get('symbols', [])
            })
        
        return {
            'success': True,
            'symbol': symbol.upper(),
            'count': len(parsed_articles),
            'articles': parsed_articles,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'symbol': symbol
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol
        }


def get_news_sentiment(symbol: str, limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get news articles with detailed sentiment analysis for a ticker
    Returns news with sentiment scores (positive, negative, neutral) and polarity
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA', 'MSFT')
        limit: Maximum number of articles to return (default 10)
        api_key: Optional EODHD API key (uses env var if not provided)
    
    Returns:
        Dict with articles, aggregate sentiment metrics, and sentiment breakdown
    
    Example:
        >>> sentiment = get_news_sentiment('TSLA', limit=20)
        >>> print(f"Average sentiment: {sentiment['aggregate']['avg_polarity']}")
    """
    try:
        # Get news articles (same endpoint provides sentiment)
        news_result = get_news(symbol, limit, api_key)
        
        if not news_result['success']:
            return news_result
        
        articles = news_result['articles']
        
        # Calculate aggregate sentiment metrics
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        polarity_scores = []
        
        for article in articles:
            sentiment = article.get('sentiment', {})
            
            # Extract sentiment polarity
            polarity = sentiment.get('polarity', 'neutral')
            if polarity in sentiment_counts:
                sentiment_counts[polarity] += 1
            
            # Extract sentiment score if available
            score = sentiment.get('neg', 0) if polarity == 'negative' else sentiment.get('pos', 0)
            if score:
                polarity_scores.append(score)
        
        # Calculate aggregate metrics
        total_articles = len(articles)
        avg_polarity = sum(polarity_scores) / len(polarity_scores) if polarity_scores else 0
        
        sentiment_breakdown = {
            'positive_pct': (sentiment_counts['positive'] / total_articles * 100) if total_articles > 0 else 0,
            'negative_pct': (sentiment_counts['negative'] / total_articles * 100) if total_articles > 0 else 0,
            'neutral_pct': (sentiment_counts['neutral'] / total_articles * 100) if total_articles > 0 else 0
        }
        
        # Determine overall sentiment
        if sentiment_breakdown['positive_pct'] > 60:
            overall = 'Strongly Positive'
        elif sentiment_breakdown['positive_pct'] > 40:
            overall = 'Positive'
        elif sentiment_breakdown['negative_pct'] > 60:
            overall = 'Strongly Negative'
        elif sentiment_breakdown['negative_pct'] > 40:
            overall = 'Negative'
        else:
            overall = 'Neutral'
        
        return {
            'success': True,
            'symbol': symbol.upper(),
            'count': total_articles,
            'articles': articles,
            'aggregate': {
                'overall_sentiment': overall,
                'avg_polarity': round(avg_polarity, 3),
                'sentiment_counts': sentiment_counts,
                'sentiment_breakdown': {k: round(v, 1) for k, v in sentiment_breakdown.items()}
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol
        }


def get_market_news(topic: str = 'general', limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Get general market news or news by topic category
    
    Args:
        topic: News topic/category (e.g., 'general', 'forex', 'crypto', 'commodities')
        limit: Maximum number of articles to return (default 10)
        api_key: Optional EODHD API key (uses env var if not provided)
    
    Returns:
        Dict with market news articles, topics, and sentiment
    
    Example:
        >>> market = get_market_news('crypto', limit=15)
        >>> for article in market['articles'][:3]:
        ...     print(article['title'])
    """
    try:
        params = {
            'api_token': api_key or EODHD_API_KEY,
            'limit': min(limit, 1000),
            'offset': 0
        }
        
        # Add topic filter if not general
        if topic and topic.lower() != 'general':
            params['t'] = topic.lower()
        
        response = requests.get(EODHD_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        articles = response.json()
        
        if not isinstance(articles, list):
            return {
                'success': False,
                'error': 'Unexpected response format',
                'topic': topic
            }
        
        # Parse articles
        parsed_articles = []
        topics_seen = set()
        
        for article in articles[:limit]:
            tags = article.get('tags', [])
            topics_seen.update(tags)
            
            parsed_articles.append({
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'published_at': article.get('date', ''),
                'source': article.get('link', ''),
                'sentiment': article.get('sentiment', {}),
                'tags': tags,
                'symbols': article.get('symbols', [])
            })
        
        return {
            'success': True,
            'topic': topic,
            'count': len(parsed_articles),
            'articles': parsed_articles,
            'topics_covered': sorted(list(topics_seen)),
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'topic': topic
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'topic': topic
        }


def search_news(query: str, limit: int = 10, api_key: Optional[str] = None) -> Dict:
    """
    Search news articles by keyword or phrase
    
    Args:
        query: Search keyword or phrase (e.g., 'Federal Reserve', 'earnings beat')
        limit: Maximum number of articles to return (default 10)
        api_key: Optional EODHD API key (uses env var if not provided)
    
    Returns:
        Dict with matching news articles and relevance information
    
    Example:
        >>> results = search_news('AI semiconductor', limit=10)
        >>> print(f"Found {results['count']} articles matching 'AI semiconductor'")
    """
    try:
        params = {
            'api_token': api_key or EODHD_API_KEY,
            'limit': min(limit, 1000),
            'offset': 0
        }
        
        # Add search query
        if query:
            params['q'] = query
        
        response = requests.get(EODHD_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        articles = response.json()
        
        if not isinstance(articles, list):
            return {
                'success': False,
                'error': 'Unexpected response format',
                'query': query
            }
        
        # Parse and rank articles by relevance (simple keyword matching)
        parsed_articles = []
        query_lower = query.lower()
        
        for article in articles[:limit]:
            title = article.get('title', '')
            content = article.get('content', '')
            
            # Simple relevance scoring
            relevance = 0
            relevance += title.lower().count(query_lower) * 3  # Title matches worth more
            relevance += content.lower().count(query_lower)
            
            parsed_articles.append({
                'title': title,
                'content': content,
                'published_at': article.get('date', ''),
                'source': article.get('link', ''),
                'sentiment': article.get('sentiment', {}),
                'tags': article.get('tags', []),
                'symbols': article.get('symbols', []),
                'relevance_score': relevance
            })
        
        # Sort by relevance
        parsed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'success': True,
            'query': query,
            'count': len(parsed_articles),
            'articles': parsed_articles,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'query': query
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("EODHD News and Sentiment Module")
    print("=" * 60)
    
    # Test with demo data
    test_symbol = 'AAPL'
    
    print(f"\n1. Latest news for {test_symbol}:")
    news = get_news(test_symbol, limit=3)
    print(json.dumps(news, indent=2)[:500] + "...")
    
    print(f"\n2. Sentiment analysis for {test_symbol}:")
    sentiment = get_news_sentiment(test_symbol, limit=5)
    if sentiment['success']:
        print(f"  Overall: {sentiment['aggregate']['overall_sentiment']}")
        print(f"  Breakdown: {sentiment['aggregate']['sentiment_breakdown']}")
    
    print("\n3. General market news:")
    market = get_market_news('general', limit=3)
    print(f"  Found {market.get('count', 0)} articles")
    
    print("\n4. Search example:")
    search = search_news('Federal Reserve', limit=3)
    print(f"  Found {search.get('count', 0)} articles matching query")
