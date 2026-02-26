"""
Breaking News NLP Classifier — Real-time news categorization and impact scoring.

Classifies financial news into categories (earnings, M&A, regulatory, macro, etc.)
and estimates market impact using keyword-based NLP and sentiment analysis.
Uses free RSS feeds and public news APIs.
"""

import re
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree

# News categories with weighted keyword patterns
CATEGORIES = {
    "earnings": {
        "keywords": ["earnings", "revenue", "profit", "loss", "EPS", "guidance", "beat", "miss", "quarterly results", "annual report"],
        "impact_weight": 0.8
    },
    "mergers_acquisitions": {
        "keywords": ["merger", "acquisition", "acquire", "buyout", "takeover", "deal", "bid", "offer", "combine"],
        "impact_weight": 0.9
    },
    "regulatory": {
        "keywords": ["SEC", "regulation", "fine", "penalty", "compliance", "lawsuit", "investigation", "subpoena", "antitrust"],
        "impact_weight": 0.7
    },
    "macro": {
        "keywords": ["Fed", "interest rate", "inflation", "GDP", "unemployment", "CPI", "FOMC", "central bank", "recession"],
        "impact_weight": 0.85
    },
    "geopolitical": {
        "keywords": ["war", "sanctions", "tariff", "trade war", "embargo", "conflict", "military", "geopolitical"],
        "impact_weight": 0.75
    },
    "leadership": {
        "keywords": ["CEO", "CFO", "resign", "fired", "appointed", "executive", "board", "management change"],
        "impact_weight": 0.6
    },
    "product": {
        "keywords": ["launch", "product", "release", "recall", "FDA approval", "patent", "innovation"],
        "impact_weight": 0.5
    },
    "crypto": {
        "keywords": ["bitcoin", "ethereum", "crypto", "blockchain", "DeFi", "stablecoin", "token", "NFT"],
        "impact_weight": 0.65
    }
}

SENTIMENT_POSITIVE = ["surge", "soar", "rally", "gain", "beat", "upgrade", "bullish", "record high", "outperform", "boom"]
SENTIMENT_NEGATIVE = ["crash", "plunge", "drop", "fall", "miss", "downgrade", "bearish", "record low", "underperform", "bust"]
URGENCY_MARKERS = ["breaking", "alert", "just in", "flash", "urgent", "developing", "exclusive"]


def classify_headline(headline: str) -> Dict:
    """
    Classify a single news headline into category, sentiment, urgency, and impact score.

    Args:
        headline: News headline text

    Returns:
        Dict with category, confidence, sentiment, urgency, impact_score
    """
    text_lower = headline.lower()

    # Category classification
    category_scores = {}
    for cat, config in CATEGORIES.items():
        score = sum(1 for kw in config["keywords"] if kw.lower() in text_lower)
        if score > 0:
            category_scores[cat] = score * config["impact_weight"]

    if category_scores:
        best_cat = max(category_scores, key=category_scores.get)
        confidence = min(category_scores[best_cat] / 3.0, 1.0)
    else:
        best_cat = "general"
        confidence = 0.1

    # Sentiment
    pos_count = sum(1 for w in SENTIMENT_POSITIVE if w in text_lower)
    neg_count = sum(1 for w in SENTIMENT_NEGATIVE if w in text_lower)
    if pos_count > neg_count:
        sentiment = "positive"
        sentiment_score = min(pos_count * 0.3, 1.0)
    elif neg_count > pos_count:
        sentiment = "negative"
        sentiment_score = -min(neg_count * 0.3, 1.0)
    else:
        sentiment = "neutral"
        sentiment_score = 0.0

    # Urgency
    urgency = any(m in text_lower for m in URGENCY_MARKERS)

    # Impact score (0-100)
    impact = int(confidence * 50 + abs(sentiment_score) * 30 + (20 if urgency else 0))
    impact = min(impact, 100)

    return {
        "headline": headline,
        "category": best_cat,
        "confidence": round(confidence, 3),
        "sentiment": sentiment,
        "sentiment_score": round(sentiment_score, 3),
        "urgency": urgency,
        "impact_score": impact,
        "all_categories": {k: round(v, 3) for k, v in sorted(category_scores.items(), key=lambda x: -x[1])}
    }


def classify_batch(headlines: List[str]) -> List[Dict]:
    """
    Classify multiple headlines and sort by impact score.

    Args:
        headlines: List of news headline strings

    Returns:
        List of classification results sorted by impact (highest first)
    """
    results = [classify_headline(h) for h in headlines]
    results.sort(key=lambda x: x["impact_score"], reverse=True)
    return results


def fetch_rss_headlines(feed_url: str = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US") -> List[Dict]:
    """
    Fetch and classify headlines from an RSS feed.

    Args:
        feed_url: RSS feed URL (defaults to Yahoo Finance S&P 500)

    Returns:
        List of classified headline dicts with timestamps
    """
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ElementTree.fromstring(resp.read())

        results = []
        for item in tree.findall(".//item"):
            title = item.findtext("title", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            if title:
                classified = classify_headline(title)
                classified["published"] = pub_date
                classified["url"] = link
                results.append(classified)

        results.sort(key=lambda x: x["impact_score"], reverse=True)
        return results
    except Exception as e:
        return [{"error": str(e)}]


def get_category_summary(headlines: List[str]) -> Dict:
    """
    Get distribution summary of categories across headlines.

    Args:
        headlines: List of headline strings

    Returns:
        Dict with category counts, avg impact, sentiment breakdown
    """
    classified = classify_batch(headlines)
    cats = {}
    sentiments = {"positive": 0, "negative": 0, "neutral": 0}
    total_impact = 0

    for item in classified:
        cat = item["category"]
        cats[cat] = cats.get(cat, 0) + 1
        sentiments[item["sentiment"]] += 1
        total_impact += item["impact_score"]

    return {
        "total_headlines": len(classified),
        "category_distribution": dict(sorted(cats.items(), key=lambda x: -x[1])),
        "sentiment_distribution": sentiments,
        "average_impact": round(total_impact / max(len(classified), 1), 1),
        "high_impact_count": sum(1 for x in classified if x["impact_score"] >= 70),
        "urgent_count": sum(1 for x in classified if x["urgency"])
    }


def filter_by_category(headlines: List[str], category: str) -> List[Dict]:
    """
    Classify headlines and filter to a specific category.

    Args:
        headlines: List of headline strings
        category: Category name to filter by

    Returns:
        Filtered classified results
    """
    classified = classify_batch(headlines)
    return [x for x in classified if x["category"] == category]
