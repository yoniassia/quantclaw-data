"""
Geopolitical Risk Real-Time Scorer — Quantifies geopolitical risk using news sentiment,
GDELT event data, conflict databases, and economic policy uncertainty indices.

Data sources: GDELT API (free), Economic Policy Uncertainty Index (free),
ACLED conflict data (free tier), FRED (free).
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any


_EPU_SERIES = {
    "US": "USEPUINDXD",
    "EU": "EUEPUINDXM",
    "CN": "CHIEPUINDXM",
    "UK": "UKEPUINDXM",
    "global": "GEPUCURRENT",
}


def fetch_gdelt_events(query: str = "conflict OR war OR sanctions", days: int = 7, limit: int = 50) -> list[dict]:
    """Fetch recent geopolitical events from GDELT's GKG API."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y%m%d%H%M%S")
    end_str = end.strftime("%Y%m%d%H%M%S")
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc?query={urllib.request.quote(query)}"
        f"&mode=ArtList&maxrecords={limit}&startdatetime={start_str}&enddatetime={end_str}"
        f"&format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "source": a.get("domain", ""),
                "tone": a.get("tone", 0),
                "date": a.get("seendate", ""),
                "url": a.get("url", ""),
            }
            for a in articles[:limit]
        ]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_policy_uncertainty(country: str = "US") -> dict[str, Any]:
    """Fetch Economic Policy Uncertainty index from FRED."""
    series_id = _EPU_SERIES.get(country.upper(), _EPU_SERIES["US"])
    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        f"&cosd={(datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            lines = resp.read().decode().strip().split("\n")
        if len(lines) < 2:
            return {"country": country, "error": "No data returned"}
        latest_line = [l for l in lines[1:] if "." not in l.split(",")[-1] or l.split(",")[-1].replace(".", "").replace("-", "").isdigit()]
        valid = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) == 2:
                try:
                    float(parts[1])
                    valid.append(parts)
                except ValueError:
                    continue
        if not valid:
            return {"country": country, "error": "No valid data points"}
        latest = valid[-1]
        values = [float(v[1]) for v in valid[-12:]]
        return {
            "country": country,
            "series": series_id,
            "latest_date": latest[0],
            "latest_value": float(latest[1]),
            "avg_12m": round(sum(values) / len(values), 2),
            "max_12m": max(values),
            "min_12m": min(values),
            "trend": "rising" if len(values) > 1 and values[-1] > sum(values[:-1]) / len(values[:-1]) else "falling",
        }
    except Exception as e:
        return {"country": country, "error": str(e)}


def compute_geopolitical_risk_score(countries: list[str] | None = None) -> dict[str, Any]:
    """
    Compute a composite geopolitical risk score (0-100) combining:
    - Economic Policy Uncertainty Index levels
    - GDELT news tone (negative sentiment)
    - Conflict event density
    """
    if countries is None:
        countries = ["US", "EU", "CN"]

    epu_scores = {}
    for c in countries:
        epu = fetch_policy_uncertainty(c)
        if not epu.get("error"):
            # Normalize EPU to 0-100 (historical range ~50-600)
            raw = epu.get("latest_value", 100)
            normalized = min(100, max(0, (raw - 50) / 5.5))
            epu_scores[c] = {"raw": raw, "normalized": round(normalized, 1), "trend": epu.get("trend")}

    events = fetch_gdelt_events(days=3, limit=30)
    valid_events = [e for e in events if not e.get("error")]
    tones = [e.get("tone", 0) for e in valid_events if isinstance(e.get("tone"), (int, float))]
    avg_tone = sum(tones) / len(tones) if tones else 0
    # Tone is typically -10 to +10; more negative = higher risk
    tone_score = min(100, max(0, 50 - avg_tone * 5))

    epu_avg = sum(s["normalized"] for s in epu_scores.values()) / len(epu_scores) if epu_scores else 50
    composite = round(0.6 * epu_avg + 0.3 * tone_score + 0.1 * min(100, len(valid_events) * 3.3), 1)

    return {
        "composite_score": composite,
        "risk_level": "extreme" if composite > 80 else "high" if composite > 60 else "elevated" if composite > 40 else "moderate" if composite > 20 else "low",
        "components": {
            "policy_uncertainty": epu_scores,
            "news_sentiment_score": round(tone_score, 1),
            "event_density": len(valid_events),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_risk_hotspots(limit: int = 10) -> list[dict]:
    """Identify current geopolitical risk hotspots from GDELT event data."""
    events = fetch_gdelt_events(query="conflict OR military OR sanctions OR crisis", days=3, limit=100)
    valid = [e for e in events if not e.get("error") and isinstance(e.get("tone"), (int, float))]
    # Sort by most negative tone (highest risk)
    valid.sort(key=lambda x: x.get("tone", 0))
    return valid[:limit]
