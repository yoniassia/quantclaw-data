"""Sentiment-Weighted News Score — aggregate news sentiment with recency and source weighting.

Combines NLP sentiment analysis with source credibility scoring and exponential
time decay to produce a single composite news sentiment score per ticker.
Uses free RSS/API sources (Google News, Finviz, SEC EDGAR).
"""

import math
import time
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

# Simple lexicon-based sentiment (no heavy deps)
POSITIVE_WORDS = frozenset([
    "surge", "soar", "beat", "upgrade", "bullish", "growth", "profit", "gain",
    "record", "strong", "outperform", "rally", "upside", "boost", "expand",
    "exceed", "breakout", "optimistic", "buy", "accumulate", "overweight",
    "positive", "recover", "rebound", "momentum", "innovation", "breakthrough",
])

NEGATIVE_WORDS = frozenset([
    "crash", "plunge", "miss", "downgrade", "bearish", "loss", "decline",
    "weak", "underperform", "selloff", "downside", "cut", "shrink", "fail",
    "breakdown", "pessimistic", "sell", "reduce", "underweight", "negative",
    "default", "bankruptcy", "fraud", "investigation", "lawsuit", "recall",
])

SOURCE_CREDIBILITY = {
    "reuters": 1.0, "bloomberg": 1.0, "wsj": 0.95, "ft": 0.95,
    "cnbc": 0.85, "marketwatch": 0.80, "seekingalpha": 0.65,
    "benzinga": 0.60, "motleyfool": 0.50, "yahoo": 0.70,
    "finviz": 0.65, "default": 0.50,
}


def compute_lexicon_sentiment(text: str) -> float:
    """Score text sentiment from -1.0 to 1.0 using keyword lexicon.

    Args:
        text: Article headline or body text.

    Returns:
        Sentiment score between -1.0 (very negative) and 1.0 (very positive).
    """
    words = set(re.findall(r'[a-z]+', text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def time_decay_weight(article_age_hours: float, half_life_hours: float = 24.0) -> float:
    """Exponential time decay weight for news recency.

    Args:
        article_age_hours: Age of the article in hours.
        half_life_hours: Half-life for decay (default 24h).

    Returns:
        Weight between 0.0 and 1.0.
    """
    if article_age_hours < 0:
        article_age_hours = 0
    return math.exp(-0.693 * article_age_hours / half_life_hours)


def source_weight(source_name: str) -> float:
    """Return credibility weight for a news source.

    Args:
        source_name: Lowercase source identifier.

    Returns:
        Credibility weight between 0.0 and 1.0.
    """
    source_lower = source_name.lower()
    for key, weight in SOURCE_CREDIBILITY.items():
        if key in source_lower:
            return weight
    return SOURCE_CREDIBILITY["default"]


def compute_weighted_sentiment(
    articles: List[Dict],
    half_life_hours: float = 24.0,
    now: Optional[datetime] = None,
) -> Dict:
    """Compute weighted composite sentiment score from a list of articles.

    Args:
        articles: List of dicts with keys: headline (str), source (str),
                  published_at (ISO datetime str or datetime), sentiment (optional float).
        half_life_hours: Time decay half-life in hours.
        now: Reference time (defaults to UTC now).

    Returns:
        Dict with composite_score, article_count, bullish_pct, bearish_pct,
        top_positive, top_negative, avg_source_quality.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    weighted_sum = 0.0
    weight_total = 0.0
    sentiments: List[Tuple[float, str]] = []
    source_qualities: List[float] = []

    for article in articles:
        headline = article.get("headline", "")
        src = article.get("source", "unknown")
        pub = article.get("published_at")

        # Parse published time
        if isinstance(pub, str):
            try:
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pub_dt = now
        elif isinstance(pub, datetime):
            pub_dt = pub
        else:
            pub_dt = now

        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)

        age_hours = (now - pub_dt).total_seconds() / 3600.0

        # Sentiment
        sent = article.get("sentiment")
        if sent is None:
            sent = compute_lexicon_sentiment(headline)

        # Weights
        tw = time_decay_weight(age_hours, half_life_hours)
        sw = source_weight(src)
        w = tw * sw

        weighted_sum += sent * w
        weight_total += w
        sentiments.append((sent, headline))
        source_qualities.append(sw)

    if weight_total == 0:
        return {
            "composite_score": 0.0,
            "article_count": 0,
            "bullish_pct": 0.0,
            "bearish_pct": 0.0,
            "top_positive": None,
            "top_negative": None,
            "avg_source_quality": 0.0,
        }

    composite = weighted_sum / weight_total
    bullish = sum(1 for s, _ in sentiments if s > 0.1) / len(sentiments) * 100
    bearish = sum(1 for s, _ in sentiments if s < -0.1) / len(sentiments) * 100

    sorted_sents = sorted(sentiments, key=lambda x: x[0])
    top_pos = sorted_sents[-1][1] if sorted_sents else None
    top_neg = sorted_sents[0][1] if sorted_sents else None

    return {
        "composite_score": round(composite, 4),
        "article_count": len(articles),
        "bullish_pct": round(bullish, 1),
        "bearish_pct": round(bearish, 1),
        "top_positive": top_pos,
        "top_negative": top_neg,
        "avg_source_quality": round(sum(source_qualities) / len(source_qualities), 3),
    }


def generate_news_signal(composite_score: float, threshold: float = 0.15) -> Dict:
    """Convert composite sentiment score to a trading signal.

    Args:
        composite_score: Weighted sentiment (-1 to 1).
        threshold: Score threshold for signal generation.

    Returns:
        Dict with signal, strength, confidence.
    """
    abs_score = abs(composite_score)
    if abs_score < threshold:
        signal = "NEUTRAL"
        strength = "weak"
    elif abs_score < 0.4:
        signal = "BULLISH" if composite_score > 0 else "BEARISH"
        strength = "moderate"
    else:
        signal = "STRONG_BULLISH" if composite_score > 0 else "STRONG_BEARISH"
        strength = "strong"

    return {
        "signal": signal,
        "strength": strength,
        "confidence": round(min(abs_score * 2, 1.0), 3),
        "raw_score": round(composite_score, 4),
    }
