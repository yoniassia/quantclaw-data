"""
Alpha Vantage News Sentiment API — AI-Powered Market News & Sentiment

Data Source: Alpha Vantage (https://www.alphavantage.co/documentation/#news-sentiment)
Update: Real-time (continuous news feed)
Free: Yes (demo key, 25 requests/day on free tier)

Provides:
- News articles with AI-generated sentiment scores per ticker
- Topic-based news filtering (technology, earnings, finance, etc.)
- Ticker-specific sentiment labels (Bullish/Bearish/Neutral)
- Multi-ticker relevance scoring
- Time-range filtering for historical news sentiment

Sentiment Score Ranges:
- x <= -0.35: Bearish
- -0.35 < x <= -0.15: Somewhat-Bearish
- -0.15 < x < 0.15: Neutral
- 0.15 <= x < 0.35: Somewhat-Bullish
- x >= 0.35: Bullish
"""

import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/alpha_vantage_news")
os.makedirs(CACHE_DIR, exist_ok=True)

API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

SENTIMENT_LABELS = {
    "Bearish": (-1.0, -0.35),
    "Somewhat-Bearish": (-0.35, -0.15),
    "Neutral": (-0.15, 0.15),
    "Somewhat_Bullish": (0.15, 0.35),
    "Bullish": (0.35, 1.0),
}

VALID_TOPICS = [
    "blockchain", "earnings", "ipo", "mergers_and_acquisitions",
    "financial_markets", "economy_fiscal", "economy_monetary",
    "economy_macro", "energy_transportation", "finance",
    "life_sciences", "manufacturing", "real_estate",
    "retail_wholesale", "technology",
]

VALID_SORT = ["LATEST", "EARLIEST", "RELEVANCE"]


def _make_request(params: dict) -> dict:
    """Internal helper to call Alpha Vantage API with error handling."""
    params["apikey"] = API_KEY
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "Error Message" in data:
            return {"error": data["Error Message"]}
        if "Note" in data:
            return {"error": data["Note"]}  # Rate limit
        if "Information" in data:
            return {"error": data["Information"]}
        return data
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (15s)"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}


def get_news_sentiment(
    tickers: Optional[str] = None,
    topics: Optional[str] = None,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    sort: str = "LATEST",
    limit: int = 50,
) -> Dict:
    """
    Fetch news articles with AI-powered sentiment scores.

    Args:
        tickers: Comma-separated ticker symbols (e.g. 'AAPL', 'AAPL,MSFT').
                 Supports CRYPTO: prefix (e.g. 'CRYPTO:BTC') and
                 FOREX: prefix (e.g. 'FOREX:USD').
        topics: Comma-separated topics to filter by.
                Valid: blockchain, earnings, ipo, mergers_and_acquisitions,
                financial_markets, economy_fiscal, economy_monetary,
                economy_macro, energy_transportation, finance,
                life_sciences, manufacturing, real_estate,
                retail_wholesale, technology.
        time_from: Start time in YYYYMMDDTHHMM format (e.g. '20240101T0000').
        time_to: End time in YYYYMMDDTHHMM format.
        sort: Sort order — LATEST, EARLIEST, or RELEVANCE.
        limit: Max articles to return (default 50, max 1000).

    Returns:
        Dict with 'items' count, 'sentiment_score_definition',
        'relevance_score_definition', and 'feed' list of articles.
    """
    params = {"function": "NEWS_SENTIMENT"}

    if tickers:
        params["tickers"] = tickers
    # Demo key only supports function + tickers + apikey; skip extras for demo
    if API_KEY != "demo":
        if topics:
            params["topics"] = topics
        if time_from:
            params["time_from"] = time_from
        if time_to:
            params["time_to"] = time_to
        if sort in VALID_SORT:
            params["sort"] = sort
        if limit:
            params["limit"] = min(limit, 1000)

    return _make_request(params)


def get_ticker_sentiment(ticker: str, limit: int = 50) -> Dict:
    """
    Get news sentiment specifically for one ticker.

    Args:
        ticker: Stock symbol (e.g. 'AAPL', 'TSLA').
        limit: Max articles (default 50).

    Returns:
        Dict with:
          - ticker: The queried ticker
          - article_count: Number of articles found
          - avg_sentiment: Average sentiment score across articles
          - sentiment_label: Overall sentiment label
          - sentiment_distribution: Count per label
          - articles: List of articles with sentiment details
    """
    data = get_news_sentiment(tickers=ticker, limit=limit)
    if "error" in data:
        return data

    feed = data.get("feed", [])
    articles = []
    scores = []
    label_counts = {
        "Bearish": 0, "Somewhat-Bearish": 0, "Neutral": 0,
        "Somewhat-Bullish": 0, "Bullish": 0,
    }

    for article in feed:
        ticker_data = None
        for ts in article.get("ticker_sentiment", []):
            if ts["ticker"].upper() == ticker.upper():
                ticker_data = ts
                break

        if ticker_data:
            score = float(ticker_data["ticker_sentiment_score"])
            label = ticker_data["ticker_sentiment_label"]
            scores.append(score)
            # Normalize: API uses both _ and - inconsistently
            label = label.replace("_", "-")
            if label in label_counts:
                label_counts[label] += 1

            articles.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "published": article.get("time_published", ""),
                "sentiment_score": score,
                "sentiment_label": label,
                "relevance_score": float(ticker_data.get("relevance_score", 0)),
                "overall_sentiment": article.get("overall_sentiment_score", 0),
                "summary": article.get("summary", "")[:300],
            })

    avg_score = sum(scores) / len(scores) if scores else 0.0
    avg_label = _score_to_label(avg_score)

    return {
        "ticker": ticker.upper(),
        "article_count": len(articles),
        "avg_sentiment": round(avg_score, 4),
        "sentiment_label": avg_label,
        "sentiment_distribution": label_counts,
        "articles": articles,
    }


def get_topic_news(topic: str, limit: int = 50) -> Dict:
    """
    Get news filtered by topic.

    Args:
        topic: One of: blockchain, earnings, ipo, mergers_and_acquisitions,
               financial_markets, economy_fiscal, economy_monetary,
               economy_macro, energy_transportation, finance,
               life_sciences, manufacturing, real_estate,
               retail_wholesale, technology.
        limit: Max articles (default 50).

    Returns:
        Dict with topic, article_count, avg_sentiment, and articles list.
    """
    if topic not in VALID_TOPICS:
        return {"error": f"Invalid topic '{topic}'. Valid: {', '.join(VALID_TOPICS)}"}

    data = get_news_sentiment(topics=topic, limit=limit)
    if "error" in data:
        return data

    feed = data.get("feed", [])
    scores = [a.get("overall_sentiment_score", 0) for a in feed]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    articles = []
    for article in feed:
        articles.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published": article.get("time_published", ""),
            "sentiment_score": article.get("overall_sentiment_score", 0),
            "sentiment_label": article.get("overall_sentiment_label", ""),
            "topics": [t["topic"] for t in article.get("topics", [])],
            "tickers_mentioned": [
                t["ticker"] for t in article.get("ticker_sentiment", [])
            ],
        })

    return {
        "topic": topic,
        "article_count": len(articles),
        "avg_sentiment": round(avg_score, 4),
        "sentiment_label": _score_to_label(avg_score),
        "articles": articles,
    }


def get_multi_ticker_sentiment(tickers: List[str], limit: int = 50) -> Dict:
    """
    Compare sentiment across multiple tickers.

    Args:
        tickers: List of ticker symbols (e.g. ['AAPL', 'TSLA', 'MSFT']).
        limit: Max articles per query (default 50).

    Returns:
        Dict with per-ticker sentiment summary and a ranked list.
    """
    tickers_str = ",".join(t.upper() for t in tickers)
    data = get_news_sentiment(tickers=tickers_str, limit=limit)
    if "error" in data:
        return data

    feed = data.get("feed", [])
    ticker_scores = {t.upper(): [] for t in tickers}

    for article in feed:
        for ts in article.get("ticker_sentiment", []):
            sym = ts["ticker"].upper()
            if sym in ticker_scores:
                ticker_scores[sym].append(float(ts["ticker_sentiment_score"]))

    results = {}
    for sym, scores in ticker_scores.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        results[sym] = {
            "avg_sentiment": round(avg, 4),
            "sentiment_label": _score_to_label(avg),
            "article_count": len(scores),
        }

    ranked = sorted(results.items(), key=lambda x: x[1]["avg_sentiment"], reverse=True)

    return {
        "tickers": results,
        "ranked": [{"ticker": t, **v} for t, v in ranked],
    }


def get_sentiment_summary(ticker: str, days: int = 7) -> Dict:
    """
    Get a sentiment summary for a ticker over the last N days.

    Args:
        ticker: Stock symbol (e.g. 'AAPL').
        days: Number of days to look back (default 7).

    Returns:
        Dict with ticker, period, avg_sentiment, label, article_count,
        bullish_pct, bearish_pct, and daily breakdown.
    """
    time_from = (datetime.utcnow() - timedelta(days=days)).strftime("%Y%m%dT0000")
    data = get_news_sentiment(tickers=ticker, time_from=time_from, limit=1000)
    if "error" in data:
        return data

    feed = data.get("feed", [])
    daily = {}
    all_scores = []

    for article in feed:
        for ts in article.get("ticker_sentiment", []):
            if ts["ticker"].upper() != ticker.upper():
                continue
            score = float(ts["ticker_sentiment_score"])
            all_scores.append(score)
            pub = article.get("time_published", "")
            day = pub[:8] if len(pub) >= 8 else "unknown"
            if day not in daily:
                daily[day] = []
            daily[day].append(score)

    avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    bullish = sum(1 for s in all_scores if s >= 0.15)
    bearish = sum(1 for s in all_scores if s <= -0.15)
    total = len(all_scores) or 1

    daily_summary = {}
    for day, scores in sorted(daily.items()):
        d_avg = sum(scores) / len(scores)
        daily_summary[day] = {
            "avg_sentiment": round(d_avg, 4),
            "label": _score_to_label(d_avg),
            "article_count": len(scores),
        }

    return {
        "ticker": ticker.upper(),
        "period_days": days,
        "avg_sentiment": round(avg, 4),
        "sentiment_label": _score_to_label(avg),
        "article_count": len(all_scores),
        "bullish_pct": round(bullish / total * 100, 1),
        "bearish_pct": round(bearish / total * 100, 1),
        "daily": daily_summary,
    }


def _score_to_label(score: float) -> str:
    """Convert numeric sentiment score to label."""
    if score <= -0.35:
        return "Bearish"
    elif score <= -0.15:
        return "Somewhat-Bearish"
    elif score < 0.15:
        return "Neutral"
    elif score < 0.35:
        return "Somewhat-Bullish"
    else:
        return "Bullish"
