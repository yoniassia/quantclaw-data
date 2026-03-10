#!/usr/bin/env python3
"""
Global ETF Redemption API — ETF Redemption Activities & Fund Flow Metrics

Data Source: Global ETF Redemption API (https://globaletfredemption.com/api)
Category: ETF & Fund Flows
Free tier: 500 calls/month, basic metrics, rate limited 10/min
Update: Daily
Generated: 2026-03-07

Provides:
- ETF unit creations and redemptions by symbol
- Implied liquidity metrics
- Emerging markets and crypto-linked ETF flows
- Historical redemption trends

Note: API may be unavailable (announced late 2025, endpoint not yet live).
Module gracefully returns error dicts when API is unreachable.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://api.globaletfredemption.com/v2"
CACHE_DIR = os.path.expanduser("~/.quantclaw/cache/global_etf_redemption")
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": "QuantClaw-Data/1.0",
    "Accept": "application/json",
}
REQUEST_TIMEOUT = 10


def _cache_path(key: str) -> str:
    """Return cache file path for a given key."""
    safe = key.replace("/", "_").replace("?", "_").replace("&", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _read_cache(key: str, max_age_hours: int = 24) -> Optional[dict]:
    """Read cached response if fresh enough."""
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    if age > timedelta(hours=max_age_hours):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _write_cache(key: str, data: dict) -> None:
    """Write response to cache."""
    try:
        with open(_cache_path(key), "w") as f:
            json.dump(data, f, indent=2, default=str)
    except IOError:
        pass


def _api_get(endpoint: str, params: Optional[dict] = None) -> Dict:
    """
    Make a GET request to the Global ETF Redemption API.

    Returns:
        dict with 'data' key on success, or 'error' key on failure.
    """
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"

    cached = _read_cache(cache_key)
    if cached:
        cached["_cached"] = True
        return cached

    try:
        resp = requests.get(
            url, headers=DEFAULT_HEADERS, params=params, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        result = {"data": data, "source": url, "timestamp": datetime.utcnow().isoformat()}
        _write_cache(cache_key, result)
        return result
    except requests.exceptions.ConnectionError:
        return {
            "error": "API unreachable — globaletfredemption.com may not be live yet",
            "source": url,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "source": url, "timestamp": datetime.utcnow().isoformat()}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}", "source": url, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"error": str(e), "source": url, "timestamp": datetime.utcnow().isoformat()}


def get_redemptions(symbol: str, period: str = "last_7_days") -> Dict:
    """
    Get ETF redemption data for a symbol.

    Args:
        symbol: ETF ticker (e.g. 'SPY', 'ARKK', 'QQQ')
        period: Time period — 'last_7_days', 'last_30_days', 'last_90_days', 'ytd'

    Returns:
        dict with redemption data or error info.
    """
    return _api_get("redemptions", {"symbol": symbol.upper(), "period": period})


def get_creations(symbol: str, period: str = "last_7_days") -> Dict:
    """
    Get ETF unit creation data for a symbol.

    Args:
        symbol: ETF ticker (e.g. 'SPY', 'ARKK', 'QQQ')
        period: Time period — 'last_7_days', 'last_30_days', 'last_90_days', 'ytd'

    Returns:
        dict with creation data or error info.
    """
    return _api_get("creations", {"symbol": symbol.upper(), "period": period})


def get_flow_summary(symbol: str) -> Dict:
    """
    Get net fund flow summary (creations minus redemptions) for an ETF.

    Args:
        symbol: ETF ticker

    Returns:
        dict with net flow data or error info.
    """
    return _api_get("flows/summary", {"symbol": symbol.upper()})


def get_liquidity_metrics(symbol: str) -> Dict:
    """
    Get implied liquidity metrics for an ETF.

    Args:
        symbol: ETF ticker

    Returns:
        dict with liquidity data (implied liquidity, spread estimates, etc.) or error info.
    """
    return _api_get("liquidity", {"symbol": symbol.upper()})


def get_top_redemptions(market: str = "US", limit: int = 20) -> Dict:
    """
    Get top ETFs by redemption volume.

    Args:
        market: Market filter — 'US', 'EU', 'APAC', 'EM', 'global'
        limit: Number of results (max 100)

    Returns:
        dict with ranked list or error info.
    """
    return _api_get("redemptions/top", {"market": market.upper(), "limit": min(limit, 100)})


def get_crypto_etf_flows(period: str = "last_30_days") -> Dict:
    """
    Get fund flows for crypto-linked ETFs (BTC, ETH spot ETFs, etc.).

    Args:
        period: Time period — 'last_7_days', 'last_30_days', 'last_90_days', 'ytd'

    Returns:
        dict with crypto ETF flow data or error info.
    """
    return _api_get("flows/crypto", {"period": period})


def get_emerging_market_flows(period: str = "last_30_days") -> Dict:
    """
    Get fund flows for emerging market ETFs.

    Args:
        period: Time period — 'last_7_days', 'last_30_days', 'last_90_days', 'ytd'

    Returns:
        dict with EM ETF flow data or error info.
    """
    return _api_get("flows/emerging-markets", {"period": period})


def get_historical_redemptions(symbol: str, start_date: str = None, end_date: str = None) -> Dict:
    """
    Get historical redemption data for an ETF.

    Args:
        symbol: ETF ticker
        start_date: Start date 'YYYY-MM-DD' (default: 90 days ago)
        end_date: End date 'YYYY-MM-DD' (default: today)

    Returns:
        dict with historical redemption time series or error info.
    """
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    return _api_get("redemptions/history", {
        "symbol": symbol.upper(),
        "start": start_date,
        "end": end_date,
    })


def search_etfs(query: str, market: str = "US") -> Dict:
    """
    Search for ETFs by name or keyword.

    Args:
        query: Search term (e.g. 'bitcoin', 'emerging', 'bond')
        market: Market filter — 'US', 'EU', 'APAC', 'global'

    Returns:
        dict with matching ETFs or error info.
    """
    return _api_get("etfs/search", {"q": query, "market": market.upper()})


def get_module_info() -> Dict:
    """Return module metadata."""
    return {
        "module": "global_etf_redemption_api",
        "source": "https://globaletfredemption.com/api",
        "category": "ETF & Fund Flows",
        "free_tier": True,
        "rate_limit": "500 calls/month, 10/min",
        "update_frequency": "daily",
        "functions": [
            "get_redemptions",
            "get_creations",
            "get_flow_summary",
            "get_liquidity_metrics",
            "get_top_redemptions",
            "get_crypto_etf_flows",
            "get_emerging_market_flows",
            "get_historical_redemptions",
            "search_etfs",
            "get_module_info",
        ],
        "status": "API may not be live yet — functions return error dicts gracefully",
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
