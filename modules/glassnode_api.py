#!/usr/bin/env python3
"""
Glassnode API — On-Chain Metrics for Bitcoin & Ethereum

On-chain analytics including:
- Market metrics (price, market cap, realized cap)
- SOPR (Spent Output Profit Ratio)
- MVRV ratio (Market Value to Realized Value)
- NVT ratio (Network Value to Transactions)
- Exchange balances and flows
- Active addresses and entity counts
- Hash rate and mining metrics
- Supply distribution

Source: https://docs.glassnode.com/
Category: Crypto & DeFi On-Chain
Free tier: True (10 metrics, 1 call/sec, daily resolution, requires free API key)
Update frequency: daily
Author: QuantClaw Data NightBuilder
"""

import requests
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

# Glassnode API Configuration
GLASSNODE_BASE_URL = "https://api.glassnode.com/v1"
DEFAULT_TIMEOUT = 15
RATE_LIMIT_DELAY = 1.1  # free tier: 1 call/sec

# Asset mapping
ASSET_MAP = {
    "BTC": "BTC",
    "ETH": "ETH",
    "bitcoin": "BTC",
    "ethereum": "ETH",
}

# Free tier metrics (T1 - available without paid plan)
FREE_METRICS = [
    "market/price_usd_close",
    "market/marketcap_usd",
    "addresses/active_count",
    "addresses/new_non_zero_count",
    "transactions/count",
    "transactions/rate",
    "mining/hash_rate_mean",
    "mining/difficulty_latest",
    "supply/current",
    "indicators/sopr",
]

_last_call_time = 0.0


def _get_api_key() -> str:
    """
    Get Glassnode API key from environment.

    Set GLASSNODE_API_KEY env var or add to .env file.
    Free tier key available at https://studio.glassnode.com/settings/api

    Returns:
        API key string

    Raises:
        ValueError: If no API key found
    """
    key = os.environ.get("GLASSNODE_API_KEY", "")
    if not key:
        # Try loading from .env in quantclaw-data
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GLASSNODE_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not key:
        raise ValueError(
            "GLASSNODE_API_KEY not set. Get a free key at https://studio.glassnode.com/settings/api"
        )
    return key


def _normalize_asset(asset: str) -> str:
    """Normalize asset symbol to Glassnode format."""
    return ASSET_MAP.get(asset.upper(), asset.upper())


def _rate_limit():
    """Enforce rate limit (1 call/sec for free tier)."""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_call_time = time.time()


def _make_request(
    endpoint: str, params: Optional[Dict] = None
) -> Union[Dict, List]:
    """
    Make HTTP GET request to Glassnode API.

    Args:
        endpoint: API endpoint path (e.g., 'metrics/market/price_usd_close')
        params: Query parameters

    Returns:
        JSON response as dict or list

    Raises:
        requests.exceptions.RequestException: On HTTP errors
        ValueError: If API key not configured
    """
    _rate_limit()
    url = f"{GLASSNODE_BASE_URL}/{endpoint}"
    if params is None:
        params = {}
    params["api_key"] = _get_api_key()

    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("Invalid or missing Glassnode API key") from e
        elif response.status_code == 429:
            raise ValueError("Glassnode rate limit exceeded (free: 1 req/sec)") from e
        raise
    except requests.exceptions.RequestException as e:
        print(f"Glassnode API error: {e}")
        raise


# ========== MARKET METRICS ==========


def get_price_usd(asset: str = "BTC", since: Optional[str] = None,
                  until: Optional[str] = None) -> List[Dict]:
    """
    Get daily closing price in USD.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date as 'YYYY-MM-DD' (default: 30 days ago)
        until: End date as 'YYYY-MM-DD' (default: today)

    Returns:
        List of dicts with 't' (unix timestamp) and 'v' (price USD)

    Example:
        >>> data = get_price_usd("BTC")
        >>> data[-1]
        {'t': 1709856000, 'v': 67000.0}
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/market/price_usd_close", params)


def get_market_cap(asset: str = "BTC", since: Optional[str] = None,
                   until: Optional[str] = None) -> List[Dict]:
    """
    Get market capitalization in USD.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (market cap USD)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/market/marketcap_usd", params)


# ========== ON-CHAIN INDICATORS ==========


def get_sopr(asset: str = "BTC", since: Optional[str] = None,
             until: Optional[str] = None) -> List[Dict]:
    """
    Get Spent Output Profit Ratio (SOPR).

    SOPR > 1: coins moved at profit on average
    SOPR < 1: coins moved at loss on average
    SOPR = 1: coins moved at break-even

    Args:
        asset: 'BTC' (SOPR is Bitcoin-specific)
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (SOPR value)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/indicators/sopr", params)


def get_mvrv_ratio(asset: str = "BTC", since: Optional[str] = None,
                   until: Optional[str] = None) -> List[Dict]:
    """
    Get Market Value to Realized Value (MVRV) ratio.

    MVRV > 3.5: historically overvalued / cycle top zone
    MVRV < 1: historically undervalued / cycle bottom zone

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (MVRV ratio)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/indicators/mvrv", params)


def get_nvt_ratio(asset: str = "BTC", since: Optional[str] = None,
                  until: Optional[str] = None) -> List[Dict]:
    """
    Get Network Value to Transactions (NVT) ratio.

    High NVT: network value is high relative to transaction volume (potentially overvalued)
    Low NVT: network value is low relative to transaction volume (potentially undervalued)

    Args:
        asset: 'BTC' (NVT is primarily a Bitcoin metric)
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (NVT ratio)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/indicators/nvt", params)


# ========== ADDRESS METRICS ==========


def get_active_addresses(asset: str = "BTC", since: Optional[str] = None,
                         until: Optional[str] = None) -> List[Dict]:
    """
    Get daily count of unique active addresses.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (active address count)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/addresses/active_count", params)


def get_new_addresses(asset: str = "BTC", since: Optional[str] = None,
                      until: Optional[str] = None) -> List[Dict]:
    """
    Get daily count of new addresses with non-zero balance.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (new address count)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/addresses/new_non_zero_count", params)


# ========== TRANSACTION METRICS ==========


def get_transaction_count(asset: str = "BTC", since: Optional[str] = None,
                          until: Optional[str] = None) -> List[Dict]:
    """
    Get daily transaction count.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (transaction count)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/transactions/count", params)


def get_transaction_rate(asset: str = "BTC", since: Optional[str] = None,
                         until: Optional[str] = None) -> List[Dict]:
    """
    Get transaction rate (transactions per second).

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (tx/sec)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/transactions/rate", params)


# ========== MINING METRICS ==========


def get_hash_rate(asset: str = "BTC", since: Optional[str] = None,
                  until: Optional[str] = None) -> List[Dict]:
    """
    Get mean hash rate (H/s).

    Args:
        asset: 'BTC' (hash rate is primarily for PoW chains)
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (hash rate H/s)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/mining/hash_rate_mean", params)


def get_mining_difficulty(asset: str = "BTC", since: Optional[str] = None,
                          until: Optional[str] = None) -> List[Dict]:
    """
    Get latest mining difficulty.

    Args:
        asset: 'BTC'
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (difficulty)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/mining/difficulty_latest", params)


# ========== SUPPLY METRICS ==========


def get_current_supply(asset: str = "BTC", since: Optional[str] = None,
                       until: Optional[str] = None) -> List[Dict]:
    """
    Get current circulating supply.

    Args:
        asset: Cryptocurrency symbol ('BTC' or 'ETH')
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (supply in native units)
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request("metrics/supply/current", params)


# ========== CONVENIENCE FUNCTIONS ==========


def get_onchain_summary(asset: str = "BTC") -> Dict:
    """
    Get a summary of key on-chain metrics for an asset.

    Fetches latest values for price, active addresses, transaction count,
    and supply in a single call (respects rate limits).

    Args:
        asset: 'BTC' or 'ETH'

    Returns:
        Dict with latest values for key metrics:
        {
            'asset': 'BTC',
            'timestamp': '2024-03-08',
            'price_usd': 67000.0,
            'active_addresses': 850000,
            'transaction_count': 350000,
            'current_supply': 19650000.0
        }
    """
    asset = _normalize_asset(asset)
    yesterday = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    summary = {"asset": asset, "timestamp": today}

    try:
        price_data = get_price_usd(asset, since=yesterday, until=today)
        if price_data:
            summary["price_usd"] = price_data[-1].get("v")
    except Exception as e:
        summary["price_usd"] = f"error: {e}"

    try:
        addr_data = get_active_addresses(asset, since=yesterday, until=today)
        if addr_data:
            summary["active_addresses"] = addr_data[-1].get("v")
    except Exception as e:
        summary["active_addresses"] = f"error: {e}"

    try:
        tx_data = get_transaction_count(asset, since=yesterday, until=today)
        if tx_data:
            summary["transaction_count"] = tx_data[-1].get("v")
    except Exception as e:
        summary["transaction_count"] = f"error: {e}"

    try:
        supply_data = get_current_supply(asset, since=yesterday, until=today)
        if supply_data:
            summary["current_supply"] = supply_data[-1].get("v")
    except Exception as e:
        summary["current_supply"] = f"error: {e}"

    return summary


def list_free_metrics() -> List[str]:
    """
    List metrics available on the free tier.

    Returns:
        List of metric endpoint paths available without a paid plan.
    """
    return FREE_METRICS.copy()


def get_metric(metric_path: str, asset: str = "BTC",
               since: Optional[str] = None, until: Optional[str] = None) -> List[Dict]:
    """
    Generic function to fetch any Glassnode metric by path.

    Args:
        metric_path: Full metric path (e.g., 'market/price_usd_close')
        asset: Cryptocurrency symbol
        since: Start date 'YYYY-MM-DD'
        until: End date 'YYYY-MM-DD'

    Returns:
        List of dicts with 't' (timestamp) and 'v' (value)

    Example:
        >>> get_metric("indicators/sopr", "BTC", "2024-01-01", "2024-01-31")
    """
    asset = _normalize_asset(asset)
    params = {"a": asset, "i": "24h"}
    if since:
        params["s"] = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    else:
        params["s"] = int((datetime.utcnow() - timedelta(days=30)).timestamp())
    if until:
        params["u"] = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    return _make_request(f"metrics/{metric_path}", params)


if __name__ == "__main__":
    import json
    print(json.dumps({
        "module": "glassnode_api",
        "status": "ready",
        "source": "https://docs.glassnode.com/",
        "functions": len([name for name in dir() if not name.startswith("_") and callable(eval(name))]),
        "free_metrics": len(FREE_METRICS),
        "note": "Requires GLASSNODE_API_KEY env var (free key from studio.glassnode.com)"
    }, indent=2))
