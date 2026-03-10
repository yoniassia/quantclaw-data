#!/usr/bin/env python3
"""
ETF Flow Insights API — Real-time ETF inflows/outflows, creation/redemption
activities, AUM changes, and sector allocations.

Source: https://etfflowinsights.com/api/docs
Category: ETF & Fund Flows
Free tier: 1000 requests/day, US ETFs only
API Base: https://api.etfflowinsights.com/v1
"""

import requests
import os
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://api.etfflowinsights.com/v1"
API_KEY = os.getenv("ETF_FLOW_INSIGHTS_API_KEY", "")

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "QuantClaw-Data/1.0"
}

MAJOR_ETFS = ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "EEM", "EFA", "GLD", "TLT",
              "HYG", "XLF", "XLK", "XLE", "XLV", "ARKK", "IBIT", "SCHD", "VEA", "BND"]


def _get_headers():
    """Build request headers with optional API key."""
    h = dict(HEADERS)
    key = API_KEY
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _cache_key(name, **params):
    """Generate a cache filename from function name and params."""
    parts = [name] + [f"{k}={v}" for k, v in sorted(params.items()) if v]
    return os.path.join(CACHE_DIR, f"etf_flow_insights_{'_'.join(parts)}.json")


def _read_cache(path, max_age=3600):
    """Read cache file if fresh enough."""
    try:
        if os.path.exists(path):
            age = time.time() - os.path.getmtime(path)
            if age < max_age:
                with open(path, 'r') as f:
                    return json.load(f)
    except Exception:
        pass
    return None


def _write_cache(path, data):
    """Write data to cache file."""
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass


def _request(endpoint, params=None, cache_age=3600):
    """
    Make a GET request to the ETF Flow Insights API.

    Args:
        endpoint: API endpoint path (e.g., '/flows')
        params: Query parameters dict
        cache_age: Cache TTL in seconds (default 1h)

    Returns:
        dict or list: Parsed JSON response, or error dict
    """
    url = f"{BASE_URL}{endpoint}"
    cache_path = _cache_key(endpoint.strip('/'), **(params or {}))

    cached = _read_cache(cache_path, max_age=cache_age)
    if cached is not None:
        return cached

    try:
        resp = requests.get(url, params=params, headers=_get_headers(), timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            _write_cache(cache_path, data)
            return data
        elif resp.status_code == 429:
            return {"error": "Rate limited (1000 req/day free tier)", "status": 429}
        else:
            return {"error": f"HTTP {resp.status_code}", "message": resp.text[:500]}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed — API may be unavailable", "url": url}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "url": url}
    except Exception as e:
        return {"error": str(e)}


def get_etf_flows(ticker, date=None, period=None):
    """
    Get ETF flow data (inflows/outflows) for a specific ticker.

    Args:
        ticker: ETF symbol (e.g., 'SPY', 'QQQ')
        date: Specific date in YYYY-MM-DD format (default: latest)
        period: Time range — '1d', '5d', '1m', '3m', '6m', '1y' (default: '1d')

    Returns:
        dict: Flow data including net_flow, inflow, outflow, volume, aum
    """
    params = {"ticker": ticker.upper()}
    if date:
        params["date"] = date
    if period:
        params["period"] = period
    return _request("/flows", params)


def get_etf_creation_redemption(ticker, start_date=None, end_date=None):
    """
    Get creation/redemption activity for an ETF.

    Args:
        ticker: ETF symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        list: Creation/redemption records with shares_created, shares_redeemed, net_shares
    """
    params = {"ticker": ticker.upper()}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _request("/creation-redemption", params)


def get_etf_aum(ticker, start_date=None, end_date=None):
    """
    Get AUM (Assets Under Management) history for an ETF.

    Args:
        ticker: ETF symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        list: AUM time series with date, aum, aum_change, aum_change_pct
    """
    params = {"ticker": ticker.upper()}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return _request("/aum", params)


def get_sector_allocations(ticker=None):
    """
    Get sector allocation breakdown for an ETF or across all ETFs.

    Args:
        ticker: Optional ETF symbol. If None, returns aggregate sector flows.

    Returns:
        dict: Sector allocations with weights and flow data
    """
    params = {}
    if ticker:
        params["ticker"] = ticker.upper()
    return _request("/sector-allocations", params)


def get_top_flows(direction="net", limit=20, date=None):
    """
    Get top ETFs ranked by flow volume.

    Args:
        direction: 'net', 'inflow', or 'outflow' (default: 'net')
        limit: Number of results (default: 20, max: 100)
        date: Optional date (YYYY-MM-DD)

    Returns:
        list: ETFs ranked by flow volume with ticker, name, flow amounts
    """
    params = {"direction": direction, "limit": min(limit, 100)}
    if date:
        params["date"] = date
    return _request("/top-flows", params)


def get_flow_summary(tickers=None, period="1d"):
    """
    Get flow summary for multiple ETFs or market-wide.

    Args:
        tickers: List of ETF symbols or None for market-wide summary
        period: '1d', '5d', '1m', '3m' (default: '1d')

    Returns:
        dict: Summary with total_inflow, total_outflow, net_flow, top_inflows, top_outflows
    """
    params = {"period": period}
    if tickers:
        if isinstance(tickers, list):
            params["tickers"] = ",".join(t.upper() for t in tickers)
        else:
            params["tickers"] = tickers.upper()
    return _request("/flow-summary", params)


def get_historical_flows(ticker, start_date, end_date=None, frequency="daily"):
    """
    Get historical flow time series for an ETF.

    Args:
        ticker: ETF symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), defaults to today
        frequency: 'daily', 'weekly', 'monthly' (default: 'daily')

    Returns:
        list: Time series of flow data points
    """
    params = {
        "ticker": ticker.upper(),
        "start_date": start_date,
        "frequency": frequency
    }
    if end_date:
        params["end_date"] = end_date
    return _request("/flows/historical", params, cache_age=7200)


def get_data(ticker=None, **kwargs):
    """
    Unified data getter (QuantClaw standard interface).

    Args:
        ticker: ETF symbol (default: returns top flows)
        **kwargs: Additional params (date, period, etc.)

    Returns:
        dict or list: Flow data for ticker, or top flows if no ticker
    """
    if ticker:
        return get_etf_flows(ticker, **kwargs)
    return get_top_flows(**kwargs)


def get_latest(ticker="SPY"):
    """
    Get latest flow data for a ticker (QuantClaw standard interface).

    Args:
        ticker: ETF symbol (default: 'SPY')

    Returns:
        dict: Latest flow data
    """
    return get_etf_flows(ticker, period="1d")


# Module info for registry
MODULE_INFO = {
    "name": "etf_flow_insights_api",
    "category": "ETF & Fund Flows",
    "source": "https://etfflowinsights.com/api/docs",
    "free_tier": True,
    "rate_limit": "1000 req/day",
    "api_key_required": False,
    "api_key_env": "ETF_FLOW_INSIGHTS_API_KEY",
    "functions": [
        "get_etf_flows", "get_etf_creation_redemption", "get_etf_aum",
        "get_sector_allocations", "get_top_flows", "get_flow_summary",
        "get_historical_flows", "get_data", "get_latest"
    ]
}

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    print(f"Testing ETF Flow Insights API for {ticker}...")
    result = get_etf_flows(ticker)
    print(json.dumps(result, indent=2, default=str))
