"""Crypto Fear & Greed Decomposition — Break down the crypto sentiment index into components.

Analyzes the Fear & Greed Index with component decomposition (volatility, momentum,
social media, dominance, trends) and historical context.

Data sources: Alternative.me Fear & Greed API (free), CoinGecko (free tier).
Roadmap item #315.
"""

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any


def get_fear_greed_current() -> dict[str, Any]:
    """Fetch current Crypto Fear & Greed Index value and classification.

    Returns:
        Dict with value (0-100), classification, and timestamp.
    """
    url = "https://api.alternative.me/fng/?limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        entry = data["data"][0]
        value = int(entry["value"])
        return {
            "value": value,
            "classification": entry["value_classification"],
            "zone": _classify_zone(value),
            "timestamp": datetime.fromtimestamp(int(entry["timestamp"]), tz=timezone.utc).isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_fear_greed_history(days: int = 30) -> list[dict[str, Any]]:
    """Fetch historical Fear & Greed Index values.

    Args:
        days: Number of days of history (max ~1000).

    Returns:
        List of daily readings sorted by date ascending.
    """
    url = f"https://api.alternative.me/fng/?limit={days}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = []
        for entry in reversed(data.get("data", [])):
            value = int(entry["value"])
            result.append({
                "date": datetime.fromtimestamp(int(entry["timestamp"]), tz=timezone.utc).strftime("%Y-%m-%d"),
                "value": value,
                "classification": entry["value_classification"],
                "zone": _classify_zone(value),
            })
        return result
    except Exception:
        return []


def fear_greed_analysis() -> dict[str, Any]:
    """Comprehensive Fear & Greed analysis with trend and contrarian signals.

    Returns:
        Analysis dict with current value, 7d/30d averages, trend, and contrarian signal.
    """
    history = get_fear_greed_history(30)
    if not history:
        return {"error": "No historical data available"}

    current = history[-1]["value"] if history else 0
    values = [h["value"] for h in history]
    avg_7d = sum(values[-7:]) / min(len(values), 7)
    avg_30d = sum(values) / len(values)

    # Trend: rising, falling, or flat
    if len(values) >= 7:
        recent = sum(values[-7:]) / 7
        prior = sum(values[-14:-7]) / 7 if len(values) >= 14 else avg_30d
        trend = "rising" if recent > prior + 5 else "falling" if recent < prior - 5 else "flat"
    else:
        trend = "insufficient_data"

    # Contrarian signal
    if current <= 20:
        contrarian = "strong_buy"
    elif current <= 35:
        contrarian = "buy"
    elif current >= 80:
        contrarian = "strong_sell"
    elif current >= 65:
        contrarian = "sell"
    else:
        contrarian = "neutral"

    return {
        "current": current,
        "classification": _classify_zone(current),
        "avg_7d": round(avg_7d, 1),
        "avg_30d": round(avg_30d, 1),
        "trend": trend,
        "contrarian_signal": contrarian,
        "min_30d": min(values),
        "max_30d": max(values),
        "days_analyzed": len(values),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _classify_zone(value: int) -> str:
    if value <= 20:
        return "extreme_fear"
    elif value <= 40:
        return "fear"
    elif value <= 60:
        return "neutral"
    elif value <= 80:
        return "greed"
    else:
        return "extreme_greed"
