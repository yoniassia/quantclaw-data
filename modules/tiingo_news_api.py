#!/usr/bin/env python3
"""
Tiingo News API — Real-time Financial News with NLP Sentiment

Provides real-time and historical financial news for stocks, crypto, and forex
with NLP-derived sentiment scores, event detection, topic tagging, and ticker
extraction. Structured data from multiple sources for quantitative analysis.

Source: https://api.tiingo.com/docs/general/news
Category: News & NLP
Free tier: True (500 calls/day, 50k/month, no credit card)
Update frequency: Real-time
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Tiingo API Configuration
TIINGO_BASE_URL = "https://api.tiingo.com"
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY", "")

# Rate limiting
_last_call_time = 0
MIN_CALL_INTERVAL = 0.2  # 500 calls/day is generous, but be polite


def _rate_limit():
    """Enforce minimum interval between API calls."""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Union[Dict, List]:
    """
    Make authenticated request to Tiingo API.

    Args:
        endpoint: API endpoint path (e.g., '/tiingo/news')
        params: Optional query parameters

    Returns:
        JSON response as dict or list

    Raises:
        ValueError: If API key is missing
        requests.RequestException: If request fails
    """
    if not TIINGO_API_KEY:
        raise ValueError(
            "TIINGO_API_KEY not found in environment variables. "
            "Get a free key at https://api.tiingo.com/account/api/token"
        )

    _rate_limit()

    url = f"{TIINGO_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TIINGO_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, params=params or {}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status == 401:
            return {"error": "Invalid or expired API key", "status": 401}
        elif status == 429:
            return {"error": "Rate limit exceeded (500/day)", "status": 429}
        elif status == 404:
            return {"error": f"Endpoint not found: {endpoint}", "status": 404}
        return {"error": str(e), "status": status}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "endpoint": endpoint}


def get_news(
    tickers: Optional[str] = None,
    tags: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "publishedDate"
) -> List[Dict]:
    """
    Fetch financial news articles with optional filters.

    Args:
        tickers: Comma-separated tickers (e.g., 'AAPL,TSLA' or 'btc')
        tags: Comma-separated topic tags to filter by
        source: News source filter (e.g., 'reuters.com')
        start_date: Start date YYYY-MM-DD (default: 7 days ago)
        end_date: End date YYYY-MM-DD (default: today)
        limit: Max articles to return (default: 50, max: 1000)
        offset: Pagination offset
        sort_by: Sort field — 'publishedDate' or 'crawledDate'

    Returns:
        List of news article dicts with keys:
        - id, title, url, source, publishedDate, crawledDate
        - tickers (list), tags (list), description

    Example:
        >>> articles = get_news(tickers='AAPL', limit=5)
        >>> print(articles[0]['title'])
    """
    params = {
        "limit": min(limit, 1000),
        "offset": offset,
        "sortBy": sort_by,
    }

    if tickers:
        params["tickers"] = tickers
    if tags:
        params["tags"] = tags
    if source:
        params["source"] = source
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    result = _make_request("/iex/news", params=params)

    if isinstance(result, dict) and "error" in result:
        return [result]
    return result if isinstance(result, list) else [result]


def get_ticker_news(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Get news for a specific ticker symbol.

    Args:
        ticker: Stock ticker (e.g., 'AAPL', 'TSLA', 'BTC')
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        limit: Max articles (default: 50)

    Returns:
        List of news articles for the given ticker

    Example:
        >>> news = get_ticker_news('TSLA', limit=10)
        >>> for article in news:
        ...     print(f"{article.get('publishedDate', 'N/A')}: {article.get('title', 'N/A')}")
    """
    return get_news(tickers=ticker, start_date=start_date, end_date=end_date, limit=limit)


def get_crypto_news(
    coins: str = "btc,eth",
    limit: int = 50,
    start_date: Optional[str] = None
) -> List[Dict]:
    """
    Get cryptocurrency-related news.

    Args:
        coins: Comma-separated crypto tickers (e.g., 'btc,eth,sol')
        limit: Max articles (default: 50)
        start_date: Start date YYYY-MM-DD

    Returns:
        List of crypto news articles

    Example:
        >>> crypto_news = get_crypto_news('btc,eth', limit=5)
    """
    return get_news(tickers=coins, start_date=start_date, limit=limit)


def get_bulk_news(
    limit: int = 100,
    source: Optional[str] = None
) -> List[Dict]:
    """
    Get latest bulk news across all tickers (no filter).

    Args:
        limit: Max articles (default: 100)
        source: Optional source filter

    Returns:
        List of latest news articles across the market
    """
    return get_news(limit=limit, source=source)


def search_news(
    query_tickers: List[str],
    days_back: int = 7,
    limit: int = 50
) -> Dict[str, List[Dict]]:
    """
    Search news for multiple tickers and return grouped results.

    Args:
        query_tickers: List of ticker symbols ['AAPL', 'TSLA', 'NVDA']
        days_back: How many days back to search (default: 7)
        limit: Max articles per ticker

    Returns:
        Dict mapping ticker -> list of articles

    Example:
        >>> results = search_news(['AAPL', 'TSLA'], days_back=3)
        >>> for ticker, articles in results.items():
        ...     print(f"{ticker}: {len(articles)} articles")
    """
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    results = {}
    for ticker in query_tickers:
        results[ticker] = get_ticker_news(ticker, start_date=start_date, limit=limit)
    return results


def extract_sentiment_summary(articles: List[Dict]) -> Dict:
    """
    Extract a summary of news sentiment from a list of articles.
    Uses article metadata (tags, tickers mentioned, source diversity).

    Note: Tiingo's IEX news endpoint provides articles; for deep NLP
    sentiment you'd use their premium endpoints. This function provides
    basic metadata-based analysis.

    Args:
        articles: List of article dicts from get_news()

    Returns:
        Dict with:
        - article_count: Number of articles
        - unique_sources: Set of sources
        - tickers_mentioned: Counter of ticker mentions
        - tags_found: Counter of topic tags
        - date_range: (earliest, latest) dates
        - source_diversity: Number of unique sources
    """
    if not articles or (len(articles) == 1 and "error" in articles[0]):
        return {"error": "No valid articles to analyze", "article_count": 0}

    sources = set()
    ticker_counts = {}
    tag_counts = {}
    dates = []

    for article in articles:
        if "error" in article:
            continue

        src = article.get("source", "unknown")
        sources.add(src)

        for t in article.get("tickers", []):
            ticker_counts[t] = ticker_counts.get(t, 0) + 1

        for tag in article.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        pub_date = article.get("publishedDate", "")
        if pub_date:
            dates.append(pub_date)

    dates.sort()

    return {
        "article_count": len([a for a in articles if "error" not in a]),
        "unique_sources": list(sources),
        "source_diversity": len(sources),
        "tickers_mentioned": dict(sorted(ticker_counts.items(), key=lambda x: -x[1])[:20]),
        "tags_found": dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:20]),
        "date_range": {
            "earliest": dates[0] if dates else None,
            "latest": dates[-1] if dates else None,
        }
    }


def get_news_summary(ticker: str, days_back: int = 7, limit: int = 50) -> Dict:
    """
    One-call convenience: fetch news for a ticker and return summary + articles.

    Args:
        ticker: Stock/crypto ticker
        days_back: Days to look back (default: 7)
        limit: Max articles

    Returns:
        Dict with 'summary' and 'articles' keys
    """
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    articles = get_ticker_news(ticker, start_date=start_date, limit=limit)
    summary = extract_sentiment_summary(articles)
    return {
        "ticker": ticker,
        "summary": summary,
        "articles": articles[:10]  # Return top 10 in summary view
    }


# Module metadata
MODULE_INFO = {
    "name": "tiingo_news_api",
    "version": "1.0.0",
    "category": "News & NLP",
    "source": "https://api.tiingo.com/docs/general/news",
    "free_tier": True,
    "rate_limit": "500 calls/day, 50k/month",
    "requires_key": True,
    "key_env_var": "TIINGO_API_KEY",
    "key_signup": "https://api.tiingo.com/account/api/token",
    "functions": [
        "get_news",
        "get_ticker_news",
        "get_crypto_news",
        "get_bulk_news",
        "search_news",
        "extract_sentiment_summary",
        "get_news_summary",
    ]
}


if __name__ == "__main__":
    print(json.dumps(MODULE_INFO, indent=2))

    # Quick test
    if TIINGO_API_KEY:
        print("\n--- Testing get_news(tickers='AAPL', limit=3) ---")
        news = get_news(tickers="AAPL", limit=3)
        for article in news[:3]:
            if "error" not in article:
                print(f"  {article.get('publishedDate', 'N/A')[:10]}: {article.get('title', 'N/A')[:80]}")
            else:
                print(f"  Error: {article.get('error')}")
    else:
        print("\nNo TIINGO_API_KEY set — set it to test live data")
