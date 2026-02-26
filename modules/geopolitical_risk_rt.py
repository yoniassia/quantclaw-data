"""Geopolitical Risk Real-Time Scorer — scores geopolitical risk from news and event data.

Uses free news APIs and NLP heuristics to compute a real-time geopolitical
risk index inspired by the Caldara-Iacoviello GPR methodology.
"""

import json
import re
import urllib.request
from collections import Counter
from datetime import datetime
from typing import Optional

# Risk keywords weighted by severity (Caldara-Iacoviello inspired)
RISK_KEYWORDS = {
    "war": 5, "invasion": 5, "nuclear": 5, "missile": 4, "airstrike": 4,
    "sanctions": 3, "embargo": 3, "military": 3, "troops": 3, "conflict": 3,
    "tension": 2, "escalation": 3, "cyber attack": 3, "coup": 4, "assassination": 4,
    "terrorism": 4, "insurgency": 3, "blockade": 3, "ceasefire": 1, "treaty": -1,
    "peace": -1, "diplomacy": -1, "negotiate": -1, "withdrawal": 1,
    "tariff": 2, "trade war": 3, "retaliation": 3, "threat": 2, "provocation": 2,
}

REGIONS = {
    "middle_east": ["iran", "israel", "gaza", "lebanon", "syria", "iraq", "yemen", "houthi", "hezbollah"],
    "east_asia": ["china", "taiwan", "north korea", "south china sea", "kim jong"],
    "europe": ["ukraine", "russia", "nato", "crimea", "belarus", "baltic"],
    "south_asia": ["india", "pakistan", "kashmir", "afghanistan"],
    "americas": ["venezuela", "cuba", "cartel", "mexico border"],
}


def score_text(text: str) -> dict:
    """Score a single text block for geopolitical risk.

    Args:
        text: News headline or article body.

    Returns:
        Dict with total_score, matched keywords, and detected regions.
    """
    lower = text.lower()
    matches = {}
    total = 0
    for kw, weight in RISK_KEYWORDS.items():
        count = lower.count(kw)
        if count > 0:
            matches[kw] = {"count": count, "weight": weight, "contribution": count * weight}
            total += count * weight

    regions_hit = []
    for region, terms in REGIONS.items():
        if any(t in lower for t in terms):
            regions_hit.append(region)

    return {
        "score": max(total, 0),
        "keywords_matched": matches,
        "regions": regions_hit,
        "text_length": len(text),
    }


def fetch_risk_headlines(query: str = "geopolitical", max_articles: int = 50) -> list[dict]:
    """Fetch recent headlines from free news sources for risk scoring.

    Args:
        query: Search term.
        max_articles: Max articles to fetch.

    Returns:
        List of scored headline dicts.
    """
    # Use Google News RSS as free source
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        # Simple XML parse for RSS items
        items = re.findall(r"<item>.*?</item>", raw, re.DOTALL)
        results = []
        for item in items[:max_articles]:
            title = re.search(r"<title>(.*?)</title>", item)
            pub = re.search(r"<pubDate>(.*?)</pubDate>", item)
            title_text = title.group(1) if title else ""
            title_text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", title_text)
            scored = score_text(title_text)
            scored["headline"] = title_text
            scored["published"] = pub.group(1) if pub else ""
            results.append(scored)
        return sorted(results, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        return [{"error": str(e)}]


def compute_gpr_index(headlines: Optional[list] = None) -> dict:
    """Compute a GPR-style geopolitical risk index from recent headlines.

    Args:
        headlines: Pre-fetched scored headlines, or None to fetch fresh.

    Returns:
        Dict with gpr_index (0-100 scale), regional breakdown, top threats.
    """
    if headlines is None:
        headlines = fetch_risk_headlines()

    valid = [h for h in headlines if not h.get("error") and h.get("score", 0) > 0]
    if not valid:
        return {"gpr_index": 0, "level": "calm", "regional_scores": {}, "top_threats": []}

    raw_scores = [h["score"] for h in valid]
    total_raw = sum(raw_scores)
    # Normalize to 0-100 (empirical cap ~500 raw = 100 index)
    gpr_index = min(round(total_raw / 5.0, 1), 100)

    region_scores = Counter()
    for h in valid:
        for r in h.get("regions", []):
            region_scores[r] += h["score"]

    level = "calm" if gpr_index < 20 else "elevated" if gpr_index < 50 else "high" if gpr_index < 75 else "extreme"

    return {
        "gpr_index": gpr_index,
        "level": level,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "headlines_analyzed": len(headlines),
        "risk_headlines": len(valid),
        "regional_scores": dict(region_scores.most_common()),
        "top_threats": [{"headline": h["headline"], "score": h["score"], "regions": h["regions"]} for h in valid[:5]],
    }
