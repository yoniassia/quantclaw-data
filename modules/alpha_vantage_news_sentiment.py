#!/usr/bin/env python3
"""
Alpha Vantage News Sentiment — Phase 1126 NightBuilder
=======================================================
Real-time news sentiment analysis for stocks, including ticker-specific sentiment scores
derived from financial news articles and social feeds. Provides relevance, event sentiment,
and topic-based breakdowns for trading signals. Essential for event-driven strategies and
momentum alpha generation.

Data source: https://www.alphavantage.co/documentation/#news-sentiment
Update frequency: Real-time
Free tier: 25 API calls/day (no credit card required)

Key Metrics:
- Overall sentiment score (-1 to +1, bearish to bullish)
- Ticker relevance score (0 to 1)
- Topic tags (e.g., "Earnings", "M&A", "IPO")
- Source diversity (article count)
- Sentiment label (Bearish, Neutral, Bullish)

Use Cases:
- Event-driven trade signals
- Earnings surprise prediction
- Risk monitoring (negative news spike)
- Sentiment momentum factor

References:
- Tetlock, P. C. (2007). "Giving content to investor sentiment" JF
- Loughran, T., & McDonald, B. (2011). "When is a liability not a liability?" JF
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import time

# API config
API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

# Rate limiting
_last_call_time = 0
MIN_CALL_INTERVAL = 2.5  # 25 calls/day = ~2.5s between calls to be safe


def _rate_limit():
    """Enforce rate limit (25 calls/day = ~1 call per hour safe, but we'll space them out)"""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


def get_news_sentiment(
    tickers: Optional[str] = None,
    topics: Optional[str] = None,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    sort: str = "LATEST",
    limit: int = 50
) -> Dict:
    """
    Fetch news sentiment data from Alpha Vantage.
    
    Parameters:
    -----------
    tickers : str, optional
        Comma-separated list of stock tickers (e.g., "AAPL,TSLA")
    topics : str, optional
        Topic filter (e.g., "technology", "earnings")
    time_from : str, optional
        Start time in YYYYMMDDTHHMM format
    time_to : str, optional
        End time in YYYYMMDDTHHMM format
    sort : str
        Sort order: LATEST (default), EARLIEST, RELEVANCE
    limit : int
        Number of articles to return (max 1000)
    
    Returns:
    --------
    dict with keys:
        - items: list of articles with sentiment data
        - feed: metadata about the feed
        - sentiment_score_definition: explanation of scores
    
    Example:
    --------
    >>> sentiment = get_news_sentiment(tickers="AAPL", limit=10)
    >>> for article in sentiment['feed']:
    ...     print(f"{article['title']}: {article['overall_sentiment_label']}")
    """
    _rate_limit()
    
    params = {
        "function": "NEWS_SENTIMENT",
        "apikey": API_KEY,
        "sort": sort,
        "limit": limit
    }
    
    if tickers:
        params["tickers"] = tickers
    if topics:
        params["topics"] = topics
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            return {"error": data["Error Message"]}
        if "Note" in data:
            return {"error": "Rate limit exceeded", "note": data["Note"]}
        
        return data
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}"}


def get_ticker_sentiment_summary(ticker: str, days_back: int = 7) -> Dict:
    """
    Get aggregated sentiment summary for a single ticker over recent days.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    days_back : int
        Number of days to look back (default 7)
    
    Returns:
    --------
    dict with:
        - ticker: stock symbol
        - article_count: number of articles found
        - avg_sentiment: average sentiment score
        - bullish_count: number of bullish articles
        - bearish_count: number of bearish articles
        - neutral_count: number of neutral articles
        - top_topics: most mentioned topics
        - latest_headline: most recent article title
    """
    time_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%dT0000")
    
    data = get_news_sentiment(tickers=ticker, time_from=time_from, limit=200)
    
    if "error" in data:
        return data
    
    if "feed" not in data or len(data["feed"]) == 0:
        return {
            "ticker": ticker,
            "article_count": 0,
            "error": "No articles found"
        }
    
    articles = data["feed"]
    
    # Calculate aggregates
    sentiments = []
    labels = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
    topics = {}
    
    for article in articles:
        # Overall sentiment
        if "overall_sentiment_score" in article:
            sentiments.append(float(article["overall_sentiment_score"]))
        
        # Sentiment label
        label = article.get("overall_sentiment_label", "Neutral")
        labels[label] = labels.get(label, 0) + 1
        
        # Topics
        for topic in article.get("topics", []):
            topic_name = topic.get("topic", "Unknown")
            topics[topic_name] = topics.get(topic_name, 0) + 1
    
    # Top topics
    top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "ticker": ticker,
        "article_count": len(articles),
        "avg_sentiment": sum(sentiments) / len(sentiments) if sentiments else 0,
        "bullish_count": labels["Bullish"],
        "bearish_count": labels["Bearish"],
        "neutral_count": labels["Neutral"],
        "top_topics": [{"topic": t[0], "count": t[1]} for t in top_topics],
        "latest_headline": articles[0].get("title", "N/A") if articles else "N/A",
        "latest_time": articles[0].get("time_published", "N/A") if articles else "N/A"
    }


def get_multi_ticker_sentiment(tickers: List[str]) -> List[Dict]:
    """
    Get sentiment summaries for multiple tickers.
    
    WARNING: Uses 1 API call per ticker. With 25 calls/day limit, use sparingly.
    
    Parameters:
    -----------
    tickers : list of str
        List of stock ticker symbols
    
    Returns:
    --------
    list of dict: sentiment summaries for each ticker
    """
    results = []
    for ticker in tickers:
        summary = get_ticker_sentiment_summary(ticker)
        results.append(summary)
        time.sleep(MIN_CALL_INTERVAL)  # Rate limit between tickers
    return results


def get_latest_headlines(limit: int = 20) -> List[Dict]:
    """
    Get latest financial news headlines with sentiment.
    
    Parameters:
    -----------
    limit : int
        Number of headlines to return (max 200)
    
    Returns:
    --------
    list of dict: simplified headline data
    """
    data = get_news_sentiment(limit=limit)
    
    if "error" in data or "feed" not in data:
        return []
    
    headlines = []
    for article in data["feed"]:
        headlines.append({
            "title": article.get("title", "N/A"),
            "time": article.get("time_published", "N/A"),
            "source": article.get("source", "N/A"),
            "sentiment": article.get("overall_sentiment_label", "Neutral"),
            "sentiment_score": article.get("overall_sentiment_score", 0),
            "url": article.get("url", "N/A"),
            "tickers": [t.get("ticker") for t in article.get("ticker_sentiment", [])]
        })
    return headlines


def test_module():
    """Test the module with real API calls"""
    print("Testing Alpha Vantage News Sentiment module...")
    print("=" * 60)
    
    # Test 1: Get latest headlines
    print("\n1. Latest headlines:")
    headlines = get_latest_headlines(limit=5)
    if headlines:
        for i, h in enumerate(headlines[:3], 1):
            print(f"   {i}. {h['title'][:60]}... [{h['sentiment']}]")
    else:
        print("   No headlines retrieved")
    
    # Test 2: Get sentiment for a single ticker
    print("\n2. Sentiment summary for AAPL:")
    summary = get_ticker_sentiment_summary("AAPL", days_back=7)
    if "error" not in summary:
        print(f"   Articles: {summary['article_count']}")
        print(f"   Avg Sentiment: {summary['avg_sentiment']:.3f}")
        print(f"   Bullish: {summary['bullish_count']}, "
              f"Bearish: {summary['bearish_count']}, "
              f"Neutral: {summary['neutral_count']}")
        if summary['top_topics']:
            print(f"   Top topic: {summary['top_topics'][0]['topic']}")
    else:
        print(f"   Error: {summary['error']}")
    
    print("\n" + "=" * 60)
    print("Module test complete")
    return True


if __name__ == "__main__":
    # Run test when executed directly
    test_module()
