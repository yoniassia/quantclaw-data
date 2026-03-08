"""SentimentInvestor API — Social sentiment aggregation for stocks.

Aggregates sentiment from Reddit, StockTwits, and X (Twitter) for stocks,
providing hype scores, sentiment metrics, and trend analysis.
Useful for gauging retail investor buzz and contrarian signals.

Data source: SentimentInvestor API (https://sentimentinvestor.com/api)
Auth: Token-based (env var SENTIMENTINVESTOR_TOKEN)
Free tier: Yes (rate-limited)
Update frequency: Hourly
"""

import json
import os
import requests
from datetime import datetime, timezone
from typing import Any, Optional


BASE_URL = "https://api.sentimentinvestor.com/v1"
_TOKEN = os.environ.get("SENTIMENTINVESTOR_TOKEN", "")


def _headers() -> dict[str, str]:
    """Build auth headers."""
    return {
        "Authorization": f"Bearer {_TOKEN}",
        "User-Agent": "QuantClaw/1.0",
        "Accept": "application/json",
    }


def _get(endpoint: str, params: Optional[dict] = None, timeout: int = 10) -> dict[str, Any]:
    """Internal GET helper with error handling.

    Args:
        endpoint: API path after base URL.
        params: Query parameters.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response or error dict.
    """
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=timeout)
        if resp.status_code == 401:
            return {"error": "Unauthorized — set SENTIMENTINVESTOR_TOKEN env var"}
        if resp.status_code == 403:
            return {"error": "Forbidden — token may lack required scope"}
        if resp.status_code == 404:
            return {"error": f"Not found: {endpoint}"}
        if resp.status_code == 429:
            return {"error": "Rate limited — retry after cooldown"}
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": "Invalid JSON response", "status": resp.status_code, "body": resp.text[:500]}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed — API may be unavailable"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": str(e)}


def get_ticker_sentiment(ticker: str, metric: str = "sentiment") -> dict[str, Any]:
    """Fetch sentiment data for a specific ticker.

    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL', 'GME').
        metric: Metric type — 'sentiment', 'hype', 'buzz', 'acs' (all).

    Returns:
        Dict with sentiment scores, source breakdown, and timestamp.
    """
    data = _get(f"/ticker/{ticker.upper()}", params={"metric": metric})
    if "error" in data:
        return data
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data


def get_hype_score(ticker: str) -> dict[str, Any]:
    """Get the hype score for a ticker — measures social media buzz intensity.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dict with hype score (0-100), trend direction, and volume metrics.
    """
    data = _get(f"/ticker/{ticker.upper()}", params={"metric": "hype"})
    if "error" in data:
        return data
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data


def get_sentiment_history(ticker: str, days: int = 30) -> list[dict[str, Any]]:
    """Fetch historical sentiment data for a ticker.

    Args:
        ticker: Stock ticker symbol.
        days: Number of days of history (default 30).

    Returns:
        List of daily sentiment readings sorted by date ascending.
    """
    data = _get(f"/ticker/{ticker.upper()}/history", params={"days": days})
    if isinstance(data, dict) and "error" in data:
        return [data]
    if isinstance(data, list):
        return data
    return data.get("data", data.get("history", [data]))


def get_trending_tickers(limit: int = 20) -> list[dict[str, Any]]:
    """Get currently trending tickers by social media activity.

    Args:
        limit: Max number of tickers to return (default 20).

    Returns:
        List of ticker dicts with hype scores, sorted by buzz descending.
    """
    data = _get("/trending", params={"limit": limit})
    if isinstance(data, dict) and "error" in data:
        return [data]
    if isinstance(data, list):
        return data
    return data.get("data", data.get("tickers", [data]))


def get_source_breakdown(ticker: str) -> dict[str, Any]:
    """Get sentiment breakdown by source (Reddit, StockTwits, X).

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dict with per-source sentiment scores and mention counts.
    """
    data = _get(f"/ticker/{ticker.upper()}/sources")
    if "error" in data:
        return data
    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data


def get_bulk_sentiment(tickers: list[str]) -> dict[str, Any]:
    """Fetch sentiment for multiple tickers in one call.

    Args:
        tickers: List of ticker symbols (max ~50).

    Returns:
        Dict mapping ticker -> sentiment data.
    """
    symbols = ",".join(t.upper() for t in tickers)
    data = _get("/bulk", params={"tickers": symbols})
    if isinstance(data, dict) and "error" in data:
        return data
    data_out = data if isinstance(data, dict) else {"results": data}
    data_out["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data_out


def sentiment_analysis(ticker: str) -> dict[str, Any]:
    """Comprehensive sentiment analysis with contrarian signals.

    Fetches current sentiment + history and computes trend, extremes,
    and contrarian trading signal.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Analysis dict with current score, averages, trend, and signal.
    """
    current = get_ticker_sentiment(ticker, metric="sentiment")
    hype = get_hype_score(ticker)
    history = get_sentiment_history(ticker, days=30)

    # Extract numeric sentiment if available
    cur_val = None
    if isinstance(current, dict) and "error" not in current:
        cur_val = current.get("sentiment", current.get("score", current.get("value")))

    hype_val = None
    if isinstance(hype, dict) and "error" not in hype:
        hype_val = hype.get("hype", hype.get("score", hype.get("value")))

    # Process history for trend analysis
    hist_values = []
    if isinstance(history, list):
        for h in history:
            if isinstance(h, dict) and "error" not in h:
                v = h.get("sentiment", h.get("score", h.get("value")))
                if v is not None:
                    try:
                        hist_values.append(float(v))
                    except (TypeError, ValueError):
                        pass

    result = {
        "ticker": ticker.upper(),
        "current_sentiment": current,
        "hype_score": hype,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    if hist_values:
        avg_7d = sum(hist_values[-7:]) / min(len(hist_values), 7)
        avg_30d = sum(hist_values) / len(hist_values)
        result["avg_7d"] = round(avg_7d, 2)
        result["avg_30d"] = round(avg_30d, 2)
        result["min_30d"] = min(hist_values)
        result["max_30d"] = max(hist_values)
        result["days_analyzed"] = len(hist_values)

        # Trend
        if len(hist_values) >= 7:
            recent = sum(hist_values[-7:]) / 7
            prior = sum(hist_values[-14:-7]) / 7 if len(hist_values) >= 14 else avg_30d
            result["trend"] = "rising" if recent > prior + 5 else "falling" if recent < prior - 5 else "flat"

        # Contrarian signal based on current value
        if cur_val is not None:
            try:
                v = float(cur_val)
                if v <= 20:
                    result["contrarian_signal"] = "strong_buy"
                elif v <= 35:
                    result["contrarian_signal"] = "buy"
                elif v >= 80:
                    result["contrarian_signal"] = "strong_sell"
                elif v >= 65:
                    result["contrarian_signal"] = "sell"
                else:
                    result["contrarian_signal"] = "neutral"
            except (TypeError, ValueError):
                pass

    return result


if __name__ == "__main__":
    print(json.dumps({
        "module": "sentimentinvestor_api",
        "status": "ready",
        "source": "https://sentimentinvestor.com/api",
        "functions": [
            "get_ticker_sentiment",
            "get_hype_score",
            "get_sentiment_history",
            "get_trending_tickers",
            "get_source_breakdown",
            "get_bulk_sentiment",
            "sentiment_analysis",
        ],
    }, indent=2))
