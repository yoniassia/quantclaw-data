"""
Prediction Market Aggregator — Aggregates odds from Polymarket, Kalshi, Metaculus and other
prediction markets to provide consensus probability estimates for geopolitical, economic,
and financial events.

Data sources: Polymarket API (free), Metaculus API (free), PredictIt (free).
"""

import json
import urllib.request
from datetime import datetime
from typing import Any


def fetch_polymarket_markets(limit: int = 50, active_only: bool = True) -> list[dict[str, Any]]:
    """Fetch active prediction markets from Polymarket's public CLOB API."""
    url = f"https://clob.polymarket.com/markets?limit={limit}"
    if active_only:
        url += "&active=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
        return [
            {
                "source": "polymarket",
                "question": m.get("question", m.get("title", "")),
                "probability": _extract_poly_prob(m),
                "volume": m.get("volume", m.get("volumeNum", 0)),
                "end_date": m.get("end_date_iso", m.get("endDate", "")),
                "url": f"https://polymarket.com/event/{m.get('condition_id', m.get('id', ''))}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
            for m in markets[:limit]
        ]
    except Exception as e:
        return [{"error": str(e), "source": "polymarket"}]


def _extract_poly_prob(market: dict) -> float | None:
    """Extract probability from various Polymarket response formats."""
    for key in ("outcomePrices", "outcome_prices"):
        prices = market.get(key)
        if prices:
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except json.JSONDecodeError:
                    continue
            if isinstance(prices, list) and len(prices) > 0:
                try:
                    return round(float(prices[0]), 4)
                except (ValueError, TypeError):
                    pass
    return market.get("probability")


def fetch_metaculus_questions(limit: int = 30, category: str = "economics") -> list[dict[str, Any]]:
    """Fetch prediction questions from Metaculus public API."""
    url = f"https://www.metaculus.com/api2/questions/?limit={limit}&status=open&order_by=-activity"
    if category:
        url += f"&search={category}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        return [
            {
                "source": "metaculus",
                "question": q.get("title", ""),
                "probability": q.get("community_prediction", {}).get("full", {}).get("q2")
                if isinstance(q.get("community_prediction"), dict)
                else None,
                "num_predictions": q.get("number_of_predictions", 0),
                "resolve_date": q.get("resolve_time", ""),
                "url": f"https://www.metaculus.com{q.get('page_url', '')}",
                "fetched_at": datetime.utcnow().isoformat(),
            }
            for q in results[:limit]
        ]
    except Exception as e:
        return [{"error": str(e), "source": "metaculus"}]


def aggregate_consensus(topic: str, sources: list[dict] | None = None) -> dict[str, Any]:
    """
    Aggregate prediction market probabilities across sources for a given topic.
    Returns weighted consensus probability and individual source estimates.
    """
    if sources is None:
        poly = fetch_polymarket_markets(limit=20)
        meta = fetch_metaculus_questions(limit=20)
        sources = poly + meta

    topic_lower = topic.lower()
    matches = [
        s for s in sources
        if not s.get("error") and topic_lower in s.get("question", "").lower()
    ]

    if not matches:
        return {
            "topic": topic,
            "consensus_probability": None,
            "matches": 0,
            "message": "No matching markets found across sources",
        }

    probs = [(m["source"], m["probability"]) for m in matches if m.get("probability") is not None]
    if not probs:
        return {"topic": topic, "consensus_probability": None, "matches": len(matches), "sources": matches}

    avg_prob = round(sum(p for _, p in probs) / len(probs), 4)
    return {
        "topic": topic,
        "consensus_probability": avg_prob,
        "matches": len(matches),
        "individual_estimates": [{"source": s, "probability": p} for s, p in probs],
        "spread": round(max(p for _, p in probs) - min(p for _, p in probs), 4) if len(probs) > 1 else 0,
    }


def get_market_summary() -> dict[str, Any]:
    """Get a summary of active prediction markets across all sources."""
    poly = fetch_polymarket_markets(limit=10)
    meta = fetch_metaculus_questions(limit=10)
    return {
        "polymarket": {"count": len([m for m in poly if not m.get("error")]), "markets": poly[:5]},
        "metaculus": {"count": len([m for m in meta if not m.get("error")]), "questions": meta[:5]},
        "total_tracked": len(poly) + len(meta),
        "timestamp": datetime.utcnow().isoformat(),
    }
