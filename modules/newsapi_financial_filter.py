#!/usr/bin/env python3
"""
NewsAPI Financial Filter — News & Sentiment Data Module

Financial news aggregation and sentiment analysis from 80,000+ global sources:
- Financial news search with keyword filtering
- Stock-specific news tracking
- Market headlines by country/category
- Crypto news monitoring
- News source discovery
- Basic sentiment analysis

Source: https://newsapi.org/v2/
Category: News & NLP
Free tier: True (100 req/day, 1 month history, requires NEWSAPI_KEY env var)
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

# NewsAPI Configuration
BASE_URL = "https://newsapi.org/v2"
API_KEY = os.environ.get("NEWSAPI_KEY", "")


def get_financial_news(query: str = 'stock market', days: int = 7, language: str = 'en') -> Dict:
    """
    Search financial news articles by keyword with date filtering.
    
    Args:
        query: Search keywords (default: 'stock market')
        days: Number of days to look back (default: 7)
        language: Language code (default: 'en')
    
    Returns:
        Dict with keys: status, totalResults, articles (list of article dicts)
    
    Example:
        >>> news = get_financial_news('Federal Reserve', days=3)
        >>> print(f"Found {news['totalResults']} articles")
    """
    try:
        url = f"{BASE_URL}/everything"
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': query,
            'from': from_date,
            'language': language,
            'sortBy': 'publishedAt',
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['query'] = query
        data['days_back'] = days
        data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'query': query}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'query': query}


def get_stock_news(ticker: str = 'AAPL', days: int = 3) -> Dict:
    """
    Get news articles for a specific stock ticker.
    
    Args:
        ticker: Stock ticker symbol (default: 'AAPL')
        days: Number of days to look back (default: 3)
    
    Returns:
        Dict with news articles mentioning the ticker
    
    Example:
        >>> news = get_stock_news('TSLA', days=1)
        >>> for article in news['articles'][:5]:
        ...     print(article['title'])
    """
    try:
        url = f"{BASE_URL}/everything"
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Build query: ticker OR company name searches
        query = f"{ticker} OR stock OR shares"
        
        params = {
            'q': query,
            'from': from_date,
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['ticker'] = ticker.upper()
        data['days_back'] = days
        data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'ticker': ticker}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'ticker': ticker}


def get_market_headlines(country: str = 'us') -> Dict:
    """
    Get top business/financial headlines for a country.
    
    Args:
        country: 2-letter country code (default: 'us')
    
    Returns:
        Dict with top business headlines
    
    Example:
        >>> headlines = get_market_headlines('us')
        >>> print(f"Top story: {headlines['articles'][0]['title']}")
    """
    try:
        url = f"{BASE_URL}/top-headlines"
        
        params = {
            'country': country.lower(),
            'category': 'business',
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['country'] = country.upper()
        data['category'] = 'business'
        data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'country': country}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'country': country}


def get_crypto_news(coin: str = 'bitcoin', days: int = 7) -> Dict:
    """
    Get news articles about a specific cryptocurrency.
    
    Args:
        coin: Cryptocurrency name (default: 'bitcoin')
        days: Number of days to look back (default: 7)
    
    Returns:
        Dict with crypto news articles
    
    Example:
        >>> news = get_crypto_news('ethereum', days=2)
        >>> print(f"Found {len(news['articles'])} Ethereum articles")
    """
    try:
        url = f"{BASE_URL}/everything"
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Build crypto-specific query
        query = f"{coin} OR cryptocurrency OR crypto"
        
        params = {
            'q': query,
            'from': from_date,
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['coin'] = coin.lower()
        data['days_back'] = days
        data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'coin': coin}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'coin': coin}


def get_sources(category: str = 'business') -> Dict:
    """
    Get available news sources for a category.
    
    Args:
        category: News category (default: 'business')
                  Options: business, technology, general, health, science, sports
    
    Returns:
        Dict with list of news sources and their metadata
    
    Example:
        >>> sources = get_sources('business')
        >>> for src in sources['sources'][:5]:
        ...     print(f"{src['name']} ({src['country']})")
    """
    try:
        url = f"{BASE_URL}/top-headlines/sources"
        
        params = {
            'category': category.lower(),
            'apiKey': API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        data['category'] = category.lower()
        data['fetched_at'] = datetime.now().isoformat()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'category': category}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'category': category}


def simple_sentiment(articles: List[Dict]) -> Dict:
    """
    Basic sentiment analysis using positive/negative word counts.
    
    Args:
        articles: List of article dicts from NewsAPI (must have 'title' and 'description')
    
    Returns:
        Dict with sentiment scores and breakdown
    
    Example:
        >>> news = get_financial_news('stock market crash')
        >>> sentiment = simple_sentiment(news['articles'])
        >>> print(f"Overall sentiment: {sentiment['overall_score']}")
    """
    try:
        # Simple sentiment word lists
        positive_words = {
            'gain', 'gains', 'rise', 'rises', 'rising', 'surge', 'surges', 'surging',
            'rally', 'rallies', 'rallying', 'boom', 'bull', 'bullish', 'positive',
            'growth', 'profit', 'profits', 'strong', 'stronger', 'up', 'high', 'higher',
            'record', 'best', 'beat', 'beats', 'outperform', 'success', 'win', 'wins'
        }
        
        negative_words = {
            'loss', 'losses', 'fall', 'falls', 'falling', 'drop', 'drops', 'dropping',
            'crash', 'crashes', 'crashing', 'slump', 'bear', 'bearish', 'negative',
            'decline', 'declines', 'declining', 'weak', 'weaker', 'down', 'low', 'lower',
            'worst', 'miss', 'misses', 'underperform', 'fail', 'fails', 'warning', 'risk'
        }
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        article_sentiments = []
        
        for article in articles:
            title = (article.get('title', '') or '').lower()
            description = (article.get('description', '') or '').lower()
            text = f"{title} {description}"
            
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            if pos_score > neg_score:
                sentiment = 'positive'
                positive_count += 1
            elif neg_score > pos_score:
                sentiment = 'negative'
                negative_count += 1
            else:
                sentiment = 'neutral'
                neutral_count += 1
            
            article_sentiments.append({
                'title': article.get('title', ''),
                'sentiment': sentiment,
                'pos_score': pos_score,
                'neg_score': neg_score
            })
        
        total = len(articles)
        if total == 0:
            return {'error': 'No articles provided'}
        
        # Calculate overall score (-1 to 1)
        overall_score = (positive_count - negative_count) / total
        
        return {
            'total_articles': total,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'overall_score': round(overall_score, 3),
            'overall_sentiment': 'positive' if overall_score > 0.1 else 'negative' if overall_score < -0.1 else 'neutral',
            'article_breakdown': article_sentiments[:10],  # First 10 for brevity
            'analyzed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Sentiment analysis error: {str(e)}'}


if __name__ == "__main__":
    # Module info
    print(json.dumps({
        "module": "newsapi_financial_filter",
        "status": "ready",
        "source": BASE_URL,
        "api_key_configured": bool(API_KEY),
        "functions": [
            "get_financial_news",
            "get_stock_news",
            "get_market_headlines",
            "get_crypto_news",
            "get_sources",
            "simple_sentiment"
        ]
    }, indent=2))
