"""Prediction Market Aggregator — aggregates odds from Polymarket, Kalshi, and Metaculus.

Fetches prediction market data from free public APIs to provide consensus
probability estimates across multiple platforms for geopolitical, economic,
and financial events.
"""

import json
import urllib.request
from datetime import datetime
from typing import Optional


def fetch_polymarket_markets(limit: int = 25, query: str = "") -> list[dict]:
    """Fetch active markets from Polymarket CLOB API.

    Args:
        limit: Max markets to return.
        query: Optional search filter.

    Returns:
        List of market dicts with title, probability, volume, end_date.
    """
    url = f"https://clob.polymarket.com/markets?limit={limit}&active=true"
    if query:
        url += f"&tag={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        markets = []
        for m in (data if isinstance(data, list) else data.get("data", data.get("markets", []))):
            markets.append({
                "source": "polymarket",
                "title": m.get("question", m.get("title", "")),
                "probability": _safe_float(m.get("outcomePrices", [0.5])[0] if isinstance(m.get("outcomePrices"), list) else m.get("bestAsk", 0.5)),
                "volume_usd": _safe_float(m.get("volume", 0)),
                "end_date": m.get("endDate", m.get("end_date_iso", "")),
                "url": f"https://polymarket.com/event/{m.get('conditionId', m.get('slug', ''))}",
            })
        return markets[:limit]
    except Exception as e:
        return [{"error": str(e), "source": "polymarket"}]


def fetch_metaculus_questions(limit: int = 25, category: str = "") -> list[dict]:
    """Fetch community forecasts from Metaculus public API.

    Args:
        limit: Max questions to return.
        category: Optional category filter (e.g., 'economics', 'geopolitics').

    Returns:
        List of question dicts with title, community median, resolution date.
    """
    url = f"https://www.metaculus.com/api2/questions/?limit={limit}&status=open&order_by=-activity"
    if category:
        url += f"&search={urllib.parse.quote(category)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        questions = []
        for q in data.get("results", []):
            community = q.get("community_prediction", {})
            prob = community.get("full", {}).get("q2") if isinstance(community, dict) else None
            questions.append({
                "source": "metaculus",
                "title": q.get("title", ""),
                "probability": round(prob, 4) if prob is not None else None,
                "num_forecasters": q.get("number_of_predictions", 0),
                "resolve_date": q.get("resolve_time", ""),
                "url": f"https://www.metaculus.com/questions/{q.get('id', '')}/",
            })
        return questions[:limit]
    except Exception as e:
        return [{"error": str(e), "source": "metaculus"}]


def aggregate_consensus(keyword: str, limit_per_source: int = 10) -> dict:
    """Search across prediction platforms and compute consensus probability.

    Args:
        keyword: Topic to search (e.g., 'recession', 'Trump', 'rate cut').
        limit_per_source: Max results per platform.

    Returns:
        Dict with per-source results and weighted consensus estimate.
    """
    poly = fetch_polymarket_markets(limit=limit_per_source, query=keyword)
    meta = fetch_metaculus_questions(limit=limit_per_source, category=keyword)
    all_probs = []
    for m in poly + meta:
        p = m.get("probability")
        if p is not None and not m.get("error"):
            all_probs.append(p)
    consensus = round(sum(all_probs) / len(all_probs), 4) if all_probs else None
    return {
        "keyword": keyword,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "polymarket": [m for m in poly if not m.get("error")],
        "metaculus": [m for m in meta if not m.get("error")],
        "consensus_probability": consensus,
        "num_sources": len(all_probs),
    }


def _safe_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
