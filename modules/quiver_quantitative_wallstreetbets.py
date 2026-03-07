#!/usr/bin/env python3
"""
Quiver Quantitative WallStreetBets — Social Sentiment & Retail Trader Activity

Core Quiver Quant integration for WallStreetBets data including:
- Real-time ticker mentions and trending stocks
- Sentiment analysis (bullish/bearish/neutral)
- Historical mention volume tracking
- Daily WSB activity summaries
- Rank and popularity metrics

Source: https://www.quiverquant.com/sources/wallstreetbets
Category: Social Sentiment & Alternative Data
Free tier: False (requires QUIVER_QUANT_API_KEY env var, falls back to Reddit JSON)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import re

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Quiver Quantitative API Configuration
QUIVER_BASE_URL = "https://api.quiverquant.com/beta"
QUIVER_API_KEY = os.environ.get("QUIVER_QUANT_API_KEY", "")

# Reddit JSON fallback endpoints (no auth needed)
REDDIT_BASE_URL = "https://www.reddit.com"
WSB_SUBREDDIT = "wallstreetbets"


def _extract_tickers_from_text(text: str) -> List[str]:
    """
    Extract stock ticker symbols from text using regex.
    
    Args:
        text: Input text to scan for tickers
        
    Returns:
        List of uppercase ticker symbols found
    """
    # Match $TICKER or standalone 1-5 uppercase letters not part of common words
    pattern = r'\$([A-Z]{1,5})\b|(?<!\w)([A-Z]{2,5})(?!\w)'
    matches = re.findall(pattern, text.upper())
    
    # Flatten tuple results and filter common non-ticker words
    exclude = {
        'THE', 'WSB', 'DD', 'YOLO', 'CEO', 'IPO', 'ATH', 'ATL', 'IMO', 'TLDR', 'ELI5', 'FUD', 'HODL', 
        'BUY', 'SELL', 'TO', 'IN', 'ON', 'AT', 'FOR', 'AND', 'OR', 'IS', 'IT', 'OF', 'IF', 'BUT', 'BY',
        'AS', 'BE', 'SO', 'NO', 'NOT', 'CAN', 'GET', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL', 'WOULD',
        'THIS', 'THAT', 'FROM', 'WITH', 'HAVE', 'ARE', 'WAS', 'WERE', 'BEEN', 'HIS', 'HER', 'YOU', 'ME',
        'MY', 'OUR', 'THEIR', 'THEM', 'ALL', 'SOME', 'ANY', 'MANY', 'MUCH', 'MORE', 'MOST', 'FEW', 'LESS',
        'SHOULD', 'COULD', 'MAY', 'MIGHT', 'MUST', 'SHALL', 'NEED', 'WANT', 'LIKE', 'MAKE', 'TAKE', 'USE',
        'KNOW', 'THINK', 'SEE', 'LOOK', 'WANT', 'GIVE', 'TELL', 'CALL', 'TRY', 'ASK', 'WORK', 'SEEM', 'FEEL',
        'LEAVE', 'PUT', 'MEAN', 'KEEP', 'LET', 'BEGIN', 'HELP', 'SHOW', 'HEAR', 'PLAY', 'RUN', 'MOVE', 'LIVE',
        'BELIEVE', 'BRING', 'HAPPEN', 'WRITE', 'SIT', 'STAND', 'LOSE', 'PAY', 'MEET', 'INCLUDE', 'CONTINUE',
        'SET', 'LEARN', 'CHANGE', 'LEAD', 'UNDERSTAND', 'WATCH', 'FOLLOW', 'STOP', 'CREATE', 'SPEAK', 'READ',
        'ALLOW', 'ADD', 'SPEND', 'GROW', 'OPEN', 'WALK', 'WIN', 'OFFER', 'REMEMBER', 'LOVE', 'CONSIDER', 'APPEAR',
        'ACTUALLY', 'PROBABLY', 'REALLY', 'JUST', 'ONLY', 'STILL', 'ALSO', 'EVEN', 'WELL', 'BACK', 'AFTER', 'BEFORE',
        'THROUGH', 'OVER', 'UNDER', 'BETWEEN', 'OUT', 'UP', 'DOWN', 'OFF', 'ABOVE', 'BELOW', 'INTO', 'ONTO',
        'AN', 'THAN', 'THEN', 'WHEN', 'WHERE', 'WHY', 'HOW', 'WHO', 'WHAT', 'WHICH', 'SUCH', 'BOTH', 'EACH',
        'OTHER', 'ANOTHER', 'SAME', 'DIFFERENT', 'NEW', 'OLD', 'FIRST', 'LAST', 'LONG', 'SHORT', 'HIGH', 'LOW',
        'GOOD', 'BAD', 'BEST', 'WORST', 'BETTER', 'WORSE', 'GREAT', 'SMALL', 'LARGE', 'BIG', 'LITTLE', 'EARLY',
        'LATE', 'NEXT', 'PREVIOUS', 'RIGHT', 'WRONG', 'TRUE', 'FALSE', 'YES', 'NEVER', 'ALWAYS', 'SOMETIMES',
        'OFTEN', 'SOON', 'NOW', 'TODAY', 'TOMORROW', 'YESTERDAY', 'TONIGHT', 'WEEK', 'MONTH', 'YEAR', 'DAY',
        'TIME', 'PEOPLE', 'WAY', 'MAN', 'WOMAN', 'CHILD', 'WORLD', 'LIFE', 'HAND', 'PART', 'PLACE', 'CASE',
        'POINT', 'GOVERNMENT', 'COMPANY', 'NUMBER', 'GROUP', 'PROBLEM', 'FACT', 'HTTPS', 'COM', 'WWW', 'HTTP',
        'HERE', 'THERE', 'CALLS', 'PUTS', 'ABOUT', 'STOCK', 'STOCKS', 'MARKET', 'TRADE', 'TRADING', 'INVESTOR',
        'INVESTMENT', 'MONEY', 'PRICE', 'PRICES', 'VALUE', 'WORTH', 'COST', 'COSTS', 'AMP', 'MARCH', 'APRIL',
        'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER', 'JANUARY', 'FEBRUARY', 'ITS',
        'WE', 'THEY', 'FULL', 'WAR', 'OIL', 'BEING', 'GOING', 'HAVING', 'DOING', 'SAYING', 'GETTING', 'MAKING',
        'COMING', 'USING', 'TAKING', 'FINDING', 'GIVING', 'TELLING', 'WORKING', 'CALLING', 'TRYING', 'ASKING',
        'FEELING', 'BECOMING', 'LEAVING', 'PUTTING'
    }
    tickers = [m[0] or m[1] for m in matches if (m[0] or m[1]) not in exclude]
    
    return list(set(tickers))


def _fetch_wsb_reddit(endpoint: str = 'hot', limit: int = 100, search_query: str = None) -> List[Dict]:
    """
    Fetch posts from r/wallstreetbets using Reddit's public JSON API.
    
    Args:
        endpoint: Reddit endpoint ('hot', 'new', 'top', 'search')
        limit: Number of posts to fetch (default: 100)
        search_query: Search query for 'search' endpoint
        
    Returns:
        List of post dictionaries with title, selftext, score, created_utc, etc.
    """
    try:
        if endpoint == 'search' and search_query:
            url = f"{REDDIT_BASE_URL}/r/{WSB_SUBREDDIT}/search.json"
            params = {'q': search_query, 'restrict_sr': 1, 'limit': limit, 'sort': 'relevance'}
        else:
            url = f"{REDDIT_BASE_URL}/r/{WSB_SUBREDDIT}/{endpoint}.json"
            params = {'limit': limit}
        
        headers = {'User-Agent': 'QuantClaw/1.0'}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        posts = [child['data'] for child in data.get('data', {}).get('children', [])]
        
        return posts
        
    except Exception as e:
        return []


def get_wsb_mentions(symbol: str = 'GME') -> Dict:
    """
    Get current mention count and trend for a ticker on WallStreetBets.
    
    Args:
        symbol: Stock ticker symbol (default: 'GME')
    
    Returns:
        Dict with keys: symbol, mention_count, rank, sentiment_score, 
                       positive_mentions, negative_mentions, timestamp
    
    Example:
        >>> mentions = get_wsb_mentions('GME')
        >>> print(f"{mentions['symbol']}: {mentions['mention_count']} mentions")
    """
    try:
        symbol = symbol.upper()
        
        # Try Quiver Quant API first
        if QUIVER_API_KEY:
            url = f"{QUIVER_BASE_URL}/live/wallstreetbets"
            params = {'symbol': symbol, 'key': QUIVER_API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                latest = data[0] if isinstance(data, list) else data
                return {
                    'symbol': symbol,
                    'mention_count': latest.get('mentions', 0),
                    'rank': latest.get('rank', None),
                    'sentiment_score': latest.get('sentiment', 0.0),
                    'positive_mentions': latest.get('positive', 0),
                    'negative_mentions': latest.get('negative', 0),
                    'date': latest.get('date', datetime.now().date().isoformat()),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'quiver_quant'
                }
        
        # Fallback to Reddit JSON scraping
        posts = _fetch_wsb_reddit('hot', limit=100)
        posts.extend(_fetch_wsb_reddit('new', limit=50))
        
        mention_count = 0
        positive = 0
        negative = 0
        
        positive_words = ['bullish', 'moon', 'rocket', 'calls', 'long', 'buy', 'gains', 'tendies', 'diamond']
        negative_words = ['bearish', 'puts', 'short', 'sell', 'loss', 'rip', 'dead', 'crash']
        
        for post in posts:
            title = post.get('title', '').upper()
            selftext = post.get('selftext', '').upper()
            combined = f"{title} {selftext}"
            
            if symbol in _extract_tickers_from_text(combined) or f'${symbol}' in combined or f' {symbol} ' in combined:
                mention_count += 1
                
                # Simple sentiment analysis
                text_lower = combined.lower()
                if any(word in text_lower for word in positive_words):
                    positive += 1
                elif any(word in text_lower for word in negative_words):
                    negative += 1
        
        sentiment_score = (positive - negative) / max(mention_count, 1)
        
        return {
            'symbol': symbol,
            'mention_count': mention_count,
            'rank': None,  # Not available from Reddit scraping
            'sentiment_score': round(sentiment_score, 3),
            'positive_mentions': positive,
            'negative_mentions': negative,
            'date': datetime.now().date().isoformat(),
            'timestamp': datetime.now().isoformat(),
            'source': 'reddit_json'
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_wsb_trending(limit: int = 20) -> Dict:
    """
    Get top mentioned tickers on WallStreetBets right now.
    
    Args:
        limit: Number of top tickers to return (default: 20)
    
    Returns:
        Dict with 'tickers' list containing ticker, mentions, rank, sentiment
    
    Example:
        >>> trending = get_wsb_trending(10)
        >>> for t in trending['tickers'][:5]:
        ...     print(f"{t['symbol']}: {t['mentions']} mentions")
    """
    try:
        # Try Quiver Quant API first
        if QUIVER_API_KEY:
            url = f"{QUIVER_BASE_URL}/live/wallstreetbets"
            params = {'key': QUIVER_API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                sorted_data = sorted(data, key=lambda x: x.get('mentions', 0), reverse=True)[:limit]
                return {
                    'tickers': [
                        {
                            'symbol': item.get('ticker', 'N/A'),
                            'mentions': item.get('mentions', 0),
                            'rank': item.get('rank', idx + 1),
                            'sentiment': item.get('sentiment', 0.0)
                        }
                        for idx, item in enumerate(sorted_data)
                    ],
                    'timestamp': datetime.now().isoformat(),
                    'source': 'quiver_quant'
                }
        
        # Fallback to Reddit JSON scraping
        posts = _fetch_wsb_reddit('hot', limit=100)
        posts.extend(_fetch_wsb_reddit('new', limit=100))
        
        ticker_counts = {}
        
        for post in posts:
            title = post.get('title', '')
            selftext = post.get('selftext', '')
            combined = f"{title} {selftext}"
            
            tickers = _extract_tickers_from_text(combined)
            for ticker in tickers:
                if len(ticker) >= 2:  # Filter single letters
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
        
        # Sort and limit
        sorted_tickers = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            'tickers': [
                {
                    'symbol': ticker,
                    'mentions': count,
                    'rank': idx + 1,
                    'sentiment': None  # Not calculated in bulk
                }
                for idx, (ticker, count) in enumerate(sorted_tickers)
            ],
            'timestamp': datetime.now().isoformat(),
            'source': 'reddit_json'
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def get_wsb_sentiment(symbol: str = 'AAPL') -> Dict:
    """
    Get sentiment breakdown (bullish/bearish/neutral) for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'AAPL')
    
    Returns:
        Dict with symbol, bullish_count, bearish_count, neutral_count, 
             sentiment_score, total_mentions
    
    Example:
        >>> sentiment = get_wsb_sentiment('TSLA')
        >>> print(f"Sentiment: {sentiment['sentiment_score']:.2f}")
    """
    try:
        symbol = symbol.upper()
        
        # Use mentions function which already calculates sentiment
        mentions_data = get_wsb_mentions(symbol)
        
        if 'error' in mentions_data:
            return mentions_data
        
        total = mentions_data.get('mention_count', 0)
        positive = mentions_data.get('positive_mentions', 0)
        negative = mentions_data.get('negative_mentions', 0)
        neutral = max(0, total - positive - negative)
        
        return {
            'symbol': symbol,
            'bullish_count': positive,
            'bearish_count': negative,
            'neutral_count': neutral,
            'sentiment_score': mentions_data.get('sentiment_score', 0.0),
            'total_mentions': total,
            'timestamp': datetime.now().isoformat(),
            'source': mentions_data.get('source', 'unknown')
        }
        
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_wsb_history(symbol: str = 'GME', days: int = 30) -> Dict:
    """
    Get historical mention volume over time for a ticker.
    
    Args:
        symbol: Stock ticker symbol (default: 'GME')
        days: Number of days of history to fetch (default: 30)
    
    Returns:
        Dict with symbol, history list of {date, mentions, sentiment}
    
    Example:
        >>> history = get_wsb_history('GME', days=7)
        >>> for day in history['history'][:3]:
        ...     print(f"{day['date']}: {day['mentions']} mentions")
    """
    try:
        symbol = symbol.upper()
        
        # Try Quiver Quant API first (historical data)
        if QUIVER_API_KEY:
            url = f"{QUIVER_BASE_URL}/historical/wallstreetbets/{symbol}"
            params = {'key': QUIVER_API_KEY}
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                # Filter to requested days
                cutoff_date = (datetime.now() - timedelta(days=days)).date()
                filtered = [
                    {
                        'date': item.get('date'),
                        'mentions': item.get('mentions', 0),
                        'sentiment': item.get('sentiment', 0.0),
                        'rank': item.get('rank', None)
                    }
                    for item in data
                    if datetime.fromisoformat(item.get('date', '2000-01-01')).date() >= cutoff_date
                ]
                
                return {
                    'symbol': symbol,
                    'history': sorted(filtered, key=lambda x: x['date'], reverse=True),
                    'days': days,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'quiver_quant'
                }
        
        # Fallback: Limited historical from Reddit (only shows current snapshot)
        current = get_wsb_mentions(symbol)
        
        return {
            'symbol': symbol,
            'history': [
                {
                    'date': datetime.now().date().isoformat(),
                    'mentions': current.get('mention_count', 0),
                    'sentiment': current.get('sentiment_score', 0.0),
                    'rank': None
                }
            ],
            'days': 1,  # Only current day available from free Reddit API
            'timestamp': datetime.now().isoformat(),
            'source': 'reddit_json',
            'note': 'Historical data requires Quiver Quant API key. Showing current day only.'
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'symbol': symbol}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'symbol': symbol}


def get_wsb_daily_summary() -> Dict:
    """
    Get daily digest of WallStreetBets activity.
    
    Returns:
        Dict with top_tickers, total_posts, most_bullish, most_bearish, 
             trending_topics
    
    Example:
        >>> summary = get_wsb_daily_summary()
        >>> print(f"Top ticker: {summary['top_tickers'][0]['symbol']}")
    """
    try:
        # Get trending tickers
        trending = get_wsb_trending(limit=10)
        
        if 'error' in trending:
            return trending
        
        top_tickers = trending.get('tickers', [])
        
        # Get sentiment for top 3 tickers
        sentiments = []
        for ticker_info in top_tickers[:3]:
            symbol = ticker_info.get('symbol')
            if symbol:
                sent = get_wsb_sentiment(symbol)
                if 'error' not in sent:
                    sentiments.append(sent)
        
        # Find most bullish/bearish
        most_bullish = max(sentiments, key=lambda x: x.get('sentiment_score', -999), default=None)
        most_bearish = min(sentiments, key=lambda x: x.get('sentiment_score', 999), default=None)
        
        # Fetch recent posts to count
        posts = _fetch_wsb_reddit('hot', limit=25)
        
        return {
            'top_tickers': top_tickers[:10],
            'total_posts_sampled': len(posts),
            'most_bullish': {
                'symbol': most_bullish.get('symbol') if most_bullish else None,
                'sentiment_score': most_bullish.get('sentiment_score') if most_bullish else None
            },
            'most_bearish': {
                'symbol': most_bearish.get('symbol') if most_bearish else None,
                'sentiment_score': most_bearish.get('sentiment_score') if most_bearish else None
            },
            'date': datetime.now().date().isoformat(),
            'timestamp': datetime.now().isoformat(),
            'source': trending.get('source', 'unknown')
        }
        
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


# Module-level metadata
__version__ = "1.0.0"
__author__ = "QuantClaw Data NightBuilder"
__all__ = [
    'get_wsb_mentions',
    'get_wsb_trending',
    'get_wsb_sentiment',
    'get_wsb_history',
    'get_wsb_daily_summary'
]
