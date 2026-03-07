#!/usr/bin/env python3
"""
Reddit Data API (Finance Sentiment Feed) — Public JSON API Implementation
Scrapes WallStreetBets, stocks, and other finance subreddits using Reddit's public JSON endpoints.
No OAuth required. Extracts ticker mentions and sentiment indicators.

Source: https://www.reddit.com/dev/api/
Category: Alternative Data — Social & Sentiment
Free tier: true - Public JSON API, rate limited
Update frequency: real-time
"""

import requests
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# User-Agent to avoid 429 rate limits
USER_AGENT = "QuantClawData/1.0 (Finance Research Bot)"
HEADERS = {"User-Agent": USER_AGENT}

# Ticker extraction patterns
TICKER_PATTERN_DOLLAR = re.compile(r'\$([A-Z]{1,5})\b')  # $TSLA
TICKER_PATTERN_PLAIN = re.compile(r'\b([A-Z]{2,5})\b')   # TSLA (2-5 chars to avoid false positives)

# Common words to exclude from plain ticker extraction
EXCLUDE_WORDS = {
    'A', 'I', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'AT', 'TO', 'IN', 'ON',
    'UP', 'DOWN', 'OUT', 'ALL', 'NEW', 'NOW', 'GET', 'GOT', 'HAS', 'HAD',
    'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN', 'AM', 'DO', 'DOES', 'DID',
    'WILL', 'CAN', 'MAY', 'MIGHT', 'MUST', 'SHALL', 'SHOULD', 'WOULD',
    'COULD', 'HAVE', 'HAS', 'HAD', 'DD', 'YOLO', 'FD', 'WSB', 'CEO', 'CFO',
    'IPO', 'ETF', 'USA', 'US', 'UK', 'EU', 'IT', 'AI', 'AR', 'VR', 'PR',
    'HR', 'IR', 'RH', 'PM', 'AM', 'TD', 'JP', 'MS', 'GS', 'CS', 'DB'
}


def get_subreddit_posts(subreddit: str, sort: str = 'hot', limit: int = 25) -> List[Dict]:
    """
    Fetch posts from a subreddit using public JSON API.
    
    Args:
        subreddit: Subreddit name (e.g., 'wallstreetbets')
        sort: Sort order ('hot', 'new', 'top', 'rising')
        limit: Number of posts to fetch (max 100)
    
    Returns:
        List of post dictionaries with keys: title, url, score, comments, created, author, text
    """
    try:
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for child in data.get('data', {}).get('children', []):
            post_data = child.get('data', {})
            posts.append({
                'title': post_data.get('title', ''),
                'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                'score': post_data.get('score', 0),
                'comments': post_data.get('num_comments', 0),
                'created': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                'author': post_data.get('author', '[deleted]'),
                'text': post_data.get('selftext', '')[:500],  # Truncate long text
                'flair': post_data.get('link_flair_text', ''),
                'upvote_ratio': post_data.get('upvote_ratio', 0.0)
            })
        
        return posts
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching r/{subreddit}: {e}")
        return []
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response from r/{subreddit}: {e}")
        return []


def get_wsb_posts(limit: int = 25) -> List[Dict]:
    """
    Fetch latest posts from r/wallstreetbets.
    
    Args:
        limit: Number of posts to fetch
    
    Returns:
        List of post dictionaries
    """
    return get_subreddit_posts('wallstreetbets', sort='new', limit=limit)


def get_stocks_posts(limit: int = 25) -> List[Dict]:
    """
    Fetch hot posts from r/stocks.
    
    Args:
        limit: Number of posts to fetch
    
    Returns:
        List of post dictionaries
    """
    return get_subreddit_posts('stocks', sort='hot', limit=limit)


def extract_tickers(posts: List[Dict]) -> Dict[str, int]:
    """
    Extract ticker mentions from post titles and text.
    
    Args:
        posts: List of post dictionaries
    
    Returns:
        Dictionary mapping tickers to mention counts
    """
    ticker_counts = Counter()
    
    for post in posts:
        text = f"{post.get('title', '')} {post.get('text', '')}"
        
        # Extract $TICKER format (high confidence)
        dollar_tickers = TICKER_PATTERN_DOLLAR.findall(text)
        for ticker in dollar_tickers:
            ticker_counts[ticker] += 2  # Weight dollar signs higher
        
        # Extract plain TICKER format (lower confidence, filter common words)
        plain_tickers = TICKER_PATTERN_PLAIN.findall(text)
        for ticker in plain_tickers:
            if ticker not in EXCLUDE_WORDS and ticker not in dollar_tickers:
                ticker_counts[ticker] += 1
    
    return dict(ticker_counts)


def get_ticker_mentions(ticker: str, subreddits: Optional[List[str]] = None, limit: int = 25) -> Dict:
    """
    Search for mentions of a specific ticker across finance subreddits.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'TSLA')
        subreddits: List of subreddits to search (default: ['wallstreetbets', 'stocks'])
        limit: Posts per subreddit
    
    Returns:
        Dictionary with ticker, total_mentions, posts_found, and detailed mentions
    """
    if subreddits is None:
        subreddits = ['wallstreetbets', 'stocks']
    
    ticker_upper = ticker.upper()
    all_posts = []
    total_mentions = 0
    
    for subreddit in subreddits:
        posts = get_subreddit_posts(subreddit, sort='new', limit=limit)
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('text', '')}"
            # Count mentions (case-insensitive)
            mentions = len(re.findall(rf'\b{ticker_upper}\b|\${ticker_upper}\b', text, re.IGNORECASE))
            
            if mentions > 0:
                post['mentions'] = mentions
                post['subreddit'] = subreddit
                all_posts.append(post)
                total_mentions += mentions
    
    return {
        'ticker': ticker_upper,
        'total_mentions': total_mentions,
        'posts_found': len(all_posts),
        'posts': sorted(all_posts, key=lambda x: x['mentions'], reverse=True)[:10]  # Top 10
    }


def get_sentiment_summary(subreddits: Optional[List[str]] = None, limit: int = 50) -> Dict:
    """
    Get sentiment summary across finance subreddits with top tickers and trending posts.
    
    Args:
        subreddits: List of subreddits to analyze
        limit: Posts per subreddit
    
    Returns:
        Dictionary with top tickers, trending posts, and aggregate stats
    """
    if subreddits is None:
        subreddits = ['wallstreetbets', 'stocks', 'investing', 'options']
    
    all_posts = []
    all_tickers = Counter()
    
    for subreddit in subreddits:
        posts = get_subreddit_posts(subreddit, sort='hot', limit=limit)
        
        for post in posts:
            post['subreddit'] = subreddit
            all_posts.append(post)
        
        # Extract tickers from this subreddit
        subreddit_tickers = extract_tickers(posts)
        all_tickers.update(subreddit_tickers)
    
    # Sort posts by engagement score
    trending_posts = sorted(all_posts, key=lambda x: x['score'] + x['comments'], reverse=True)[:20]
    
    return {
        'timestamp': datetime.now().isoformat(),
        'subreddits_analyzed': subreddits,
        'total_posts': len(all_posts),
        'top_tickers': dict(all_tickers.most_common(20)),
        'trending_posts': trending_posts,
        'avg_score': sum(p['score'] for p in all_posts) / len(all_posts) if all_posts else 0,
        'total_comments': sum(p['comments'] for p in all_posts)
    }


def demo() -> None:
    """
    Demonstrate module functionality with sample queries.
    """
    print("=" * 70)
    print("Reddit Finance Sentiment Feed — Demo")
    print("=" * 70)
    
    # 1. Get WSB posts
    print("\n[1] Latest r/wallstreetbets posts:")
    wsb_posts = get_wsb_posts(limit=5)
    for i, post in enumerate(wsb_posts, 1):
        print(f"  {i}. {post['title'][:60]}... (↑{post['score']}, 💬{post['comments']})")
    
    # 2. Extract tickers
    print("\n[2] Ticker mentions in WSB:")
    tickers = extract_tickers(wsb_posts)
    for ticker, count in sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  ${ticker}: {count} mentions")
    
    # 3. Search specific ticker
    print("\n[3] Searching for TSLA mentions:")
    tsla_data = get_ticker_mentions('TSLA', limit=10)
    print(f"  Total mentions: {tsla_data['total_mentions']}")
    print(f"  Posts found: {tsla_data['posts_found']}")
    if tsla_data['posts']:
        print(f"  Top post: {tsla_data['posts'][0]['title'][:50]}...")
    
    # 4. Sentiment summary
    print("\n[4] Overall sentiment summary:")
    summary = get_sentiment_summary(limit=25)
    print(f"  Posts analyzed: {summary['total_posts']}")
    print(f"  Top 5 tickers: {list(summary['top_tickers'].keys())[:5]}")
    print(f"  Avg engagement: {summary['avg_score']:.0f} upvotes")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()
