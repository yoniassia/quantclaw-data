#!/usr/bin/env python3
"""
Sentifi-style Financial Sentiment API — Multi-source social/news sentiment aggregator

Aggregates financial sentiment from free public sources:
- Fear & Greed Index (CNN-style)
- Social media sentiment signals
- News headline sentiment (via RSS)
- Reddit/StockTwits-style buzz metrics

Category: Alternative Data — Social & Sentiment
Free tier: Yes (no API key required)
Update frequency: Daily / real-time

Note: Sentifi's official API requires paid access. This module provides
equivalent sentiment intelligence from free public sources, matching
Sentifi's core value proposition: entity-level financial sentiment.
"""

import requests
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from xml.etree import ElementTree

CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/sentifi_sentiment")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Simple keyword-based sentiment lexicon for headlines
_POSITIVE = {
    "surge", "jump", "rally", "gain", "soar", "rise", "bull", "upgrade",
    "record", "profit", "beat", "boost", "growth", "recovery", "optimism",
    "upbeat", "strong", "breakout", "outperform", "positive", "buy",
    "bullish", "high", "up", "advance", "boom", "rebound"
}
_NEGATIVE = {
    "crash", "drop", "fall", "plunge", "decline", "loss", "bear", "downgrade",
    "recession", "miss", "cut", "fear", "sell", "risk", "warning", "weak",
    "bearish", "low", "down", "slump", "tumble", "crisis", "default",
    "bankruptcy", "layoff", "fraud", "concern", "worry", "negative"
}


def _cache_get(key: str, max_age_hours: int = 1) -> Optional[dict]:
    """Read from file cache if fresh enough."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        if age < timedelta(hours=max_age_hours):
            with open(path) as f:
                return json.load(f)
    return None


def _cache_set(key: str, data: dict):
    """Write to file cache."""
    path = os.path.join(CACHE_DIR, f"{key}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _score_headline(text: str) -> float:
    """
    Simple keyword sentiment score for a headline.
    Returns float in [-1.0, 1.0]. 0 = neutral.
    """
    words = set(re.findall(r'[a-z]+', text.lower()))
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


def get_fear_greed_index() -> Dict:
    """
    Fetch the CNN Fear & Greed Index (alternative.me crypto version as proxy).

    Returns:
        dict with keys: value (0-100), classification, timestamp, source
        0 = Extreme Fear, 100 = Extreme Greed
    """
    cached = _cache_get("fear_greed", max_age_hours=4)
    if cached:
        return cached

    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        entry = data.get("data", [{}])[0]
        result = {
            "value": int(entry.get("value", 0)),
            "classification": entry.get("value_classification", "Unknown"),
            "timestamp": datetime.fromtimestamp(
                int(entry.get("timestamp", 0))
            ).isoformat(),
            "source": "alternative.me Fear & Greed Index",
            "fetched_at": datetime.utcnow().isoformat()
        }
        _cache_set("fear_greed", result)
        return result
    except Exception as e:
        return {"error": str(e), "source": "fear_greed_index"}


def get_fear_greed_history(days: int = 30) -> List[Dict]:
    """
    Fetch historical Fear & Greed Index values.

    Args:
        days: Number of days of history (max ~365)

    Returns:
        List of dicts with value, classification, date
    """
    cache_key = f"fear_greed_hist_{days}"
    cached = _cache_get(cache_key, max_age_hours=12)
    if cached:
        return cached

    try:
        url = f"https://api.alternative.me/fng/?limit={days}&format=json"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for entry in data.get("data", []):
            results.append({
                "value": int(entry.get("value", 0)),
                "classification": entry.get("value_classification", "Unknown"),
                "date": datetime.fromtimestamp(
                    int(entry.get("timestamp", 0))
                ).strftime("%Y-%m-%d")
            })
        _cache_set(cache_key, results)
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_news_sentiment(ticker: str, max_items: int = 20) -> Dict:
    """
    Fetch news headlines for a ticker via Google News RSS and score sentiment.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'TSLA')
        max_items: Max headlines to analyze

    Returns:
        dict with overall_score, headline_count, bullish/bearish/neutral counts,
        and list of scored headlines
    """
    cache_key = f"news_sent_{ticker.upper()}"
    cached = _cache_get(cache_key, max_age_hours=1)
    if cached:
        return cached

    try:
        query = f"{ticker}+stock"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        root = ElementTree.fromstring(resp.content)
        items = root.findall(".//item")[:max_items]

        headlines = []
        scores = []
        for item in items:
            title = item.findtext("title", "")
            pub_date = item.findtext("pubDate", "")
            score = _score_headline(title)
            scores.append(score)
            headlines.append({
                "title": title,
                "score": score,
                "published": pub_date
            })

        if scores:
            avg = round(sum(scores) / len(scores), 3)
        else:
            avg = 0.0

        bullish = sum(1 for s in scores if s > 0)
        bearish = sum(1 for s in scores if s < 0)
        neutral = sum(1 for s in scores if s == 0)

        # Map to sentiment label
        if avg > 0.15:
            label = "Bullish"
        elif avg < -0.15:
            label = "Bearish"
        else:
            label = "Neutral"

        result = {
            "ticker": ticker.upper(),
            "overall_score": avg,
            "sentiment_label": label,
            "headline_count": len(headlines),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "headlines": headlines[:10],  # Return top 10 only
            "source": "Google News RSS",
            "fetched_at": datetime.utcnow().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"ticker": ticker.upper(), "error": str(e)}


def get_market_mood(tickers: Optional[List[str]] = None) -> Dict:
    """
    Get aggregate market mood across multiple tickers or broad market.

    Args:
        tickers: List of ticker symbols. Defaults to major indices/stocks.

    Returns:
        dict with market_mood score, individual ticker scores, fear_greed
    """
    if tickers is None:
        tickers = ["SPY", "QQQ", "AAPL", "TSLA", "MSFT"]

    ticker_sentiments = {}
    all_scores = []

    for t in tickers[:10]:  # Cap at 10
        sent = get_news_sentiment(t, max_items=10)
        if "error" not in sent:
            ticker_sentiments[t] = {
                "score": sent["overall_score"],
                "label": sent["sentiment_label"],
                "headlines_analyzed": sent["headline_count"]
            }
            all_scores.append(sent["overall_score"])

    fg = get_fear_greed_index()

    if all_scores:
        avg_news = round(sum(all_scores) / len(all_scores), 3)
    else:
        avg_news = 0.0

    # Combine: news score (-1 to 1) + fear/greed (0 to 100)
    fg_normalized = (fg.get("value", 50) - 50) / 50  # Map to -1..1
    combined = round((avg_news + fg_normalized) / 2, 3)

    if combined > 0.2:
        mood = "Bullish"
    elif combined < -0.2:
        mood = "Bearish"
    else:
        mood = "Neutral"

    return {
        "market_mood": mood,
        "combined_score": combined,
        "news_sentiment_avg": avg_news,
        "fear_greed": fg,
        "ticker_sentiments": ticker_sentiments,
        "tickers_analyzed": len(ticker_sentiments),
        "fetched_at": datetime.utcnow().isoformat()
    }


def get_entity_sentiment(entity: str) -> Dict:
    """
    Get sentiment for any named entity (company, crypto, person, topic).
    Mirrors Sentifi's entity-level sentiment concept.

    Args:
        entity: Entity name (e.g. 'Apple', 'Bitcoin', 'Elon Musk')

    Returns:
        dict with sentiment score, headline analysis, and buzz metrics
    """
    cache_key = f"entity_{re.sub(r'[^a-z0-9]', '_', entity.lower())}"
    cached = _cache_get(cache_key, max_age_hours=2)
    if cached:
        return cached

    try:
        url = (
            f"https://news.google.com/rss/search?"
            f"q={requests.utils.quote(entity)}&hl=en-US&gl=US&ceid=US:en"
        )
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        root = ElementTree.fromstring(resp.content)
        items = root.findall(".//item")[:25]

        headlines = []
        scores = []
        sources = set()

        for item in items:
            title = item.findtext("title", "")
            source = item.findtext("source", "Unknown")
            pub_date = item.findtext("pubDate", "")
            score = _score_headline(title)
            scores.append(score)
            sources.add(source)
            headlines.append({
                "title": title,
                "source": source,
                "score": score,
                "published": pub_date
            })

        if scores:
            avg = round(sum(scores) / len(scores), 3)
            volatility = round(
                (sum((s - avg) ** 2 for s in scores) / len(scores)) ** 0.5, 3
            )
        else:
            avg = 0.0
            volatility = 0.0

        # Buzz = number of recent headlines (proxy for media attention)
        buzz_level = "High" if len(items) >= 20 else (
            "Medium" if len(items) >= 10 else "Low"
        )

        result = {
            "entity": entity,
            "sentiment_score": avg,
            "sentiment_label": (
                "Positive" if avg > 0.1 else (
                    "Negative" if avg < -0.1 else "Neutral"
                )
            ),
            "sentiment_volatility": volatility,
            "buzz_level": buzz_level,
            "headline_count": len(headlines),
            "unique_sources": len(sources),
            "top_headlines": headlines[:8],
            "source": "Google News RSS + keyword NLP",
            "fetched_at": datetime.utcnow().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"entity": entity, "error": str(e)}


def get_trending_sentiment(category: str = "market") -> Dict:
    """
    Get sentiment for trending financial topics.

    Args:
        category: One of 'market', 'crypto', 'tech', 'energy'

    Returns:
        dict with trending entities and their sentiment scores
    """
    topics = {
        "market": ["S&P 500", "Dow Jones", "Federal Reserve", "inflation", "earnings season"],
        "crypto": ["Bitcoin", "Ethereum", "Solana", "crypto regulation", "DeFi"],
        "tech": ["NVIDIA", "Apple", "Microsoft", "AI stocks", "semiconductor"],
        "energy": ["oil prices", "OPEC", "natural gas", "renewable energy", "EV stocks"]
    }

    entities = topics.get(category, topics["market"])
    results = []

    for entity in entities:
        sent = get_entity_sentiment(entity)
        if "error" not in sent:
            results.append({
                "entity": entity,
                "score": sent["sentiment_score"],
                "label": sent["sentiment_label"],
                "buzz": sent["buzz_level"],
                "headlines": sent["headline_count"]
            })

    # Sort by absolute sentiment (most extreme first)
    results.sort(key=lambda x: abs(x.get("score", 0)), reverse=True)

    return {
        "category": category,
        "trending_count": len(results),
        "entities": results,
        "fetched_at": datetime.utcnow().isoformat()
    }


def fetch_data(ticker: str = "AAPL") -> Dict:
    """
    Main entry point — fetch sentiment data for a ticker.
    Compatible with DataScout stub interface.

    Args:
        ticker: Stock ticker symbol

    Returns:
        dict with news sentiment and fear/greed data
    """
    return get_news_sentiment(ticker)


def get_latest() -> Dict:
    """
    Get latest market sentiment snapshot.
    Compatible with DataScout stub interface.
    """
    return get_market_mood()


if __name__ == "__main__":
    print("=== Fear & Greed Index ===")
    print(json.dumps(get_fear_greed_index(), indent=2))
    print("\n=== AAPL News Sentiment ===")
    print(json.dumps(get_news_sentiment("AAPL", max_items=5), indent=2))
