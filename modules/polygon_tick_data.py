#!/usr/bin/env python3
"""polygon_tick_data — Polygon.io tick-level market data. Source: https://api.polygon.io/. Free tier: 5 calls/min, delayed. API key required."""
import requests
import os
import json
import time
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
BASE = "https://api.polygon.io"

def _get_api_key():
    key = os.environ.get("POLYGON_API_KEY")
    if key:
        return key
    cred_path = os.path.join(os.path.dirname(__file__), '..', '..', '.openclaw', 'workspace', '.credentials', 'polygon.json')
    if not os.path.exists(cred_path):
        cred_path = os.path.expanduser("~/.openclaw/workspace/.credentials/polygon.json")
    if os.path.exists(cred_path):
        with open(cred_path) as f:
            return json.load(f).get("apiKey", "")
    return ""

def get_trades(ticker, date, limit=100, **kwargs):
    """Fetch tick-level trades for a ticker on a given date. date format: YYYY-MM-DD."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "No Polygon API key found. Set POLYGON_API_KEY env var."}
    try:
        url = f"{BASE}/v3/trades/{ticker.upper()}?timestamp={date}&limit={limit}&apiKey={api_key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return {"ticker": ticker.upper(), "date": date, "trade_count": len(results),
                "trades": results[:limit], "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_quotes(ticker, date, limit=100, **kwargs):
    """Fetch NBBO quotes for a ticker on a given date."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "No Polygon API key found."}
    try:
        url = f"{BASE}/v3/quotes/{ticker.upper()}?timestamp={date}&limit={limit}&apiKey={api_key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return {"ticker": ticker.upper(), "date": date, "quote_count": len(results),
                "quotes": results[:limit], "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_aggregates(ticker, timespan="day", from_date="2024-01-01", to_date="2024-12-31", multiplier=1, **kwargs):
    """Fetch OHLCV aggregates. timespan: minute, hour, day, week, month."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "No Polygon API key found."}
    cache_key = f"polygon_{ticker}_{timespan}_{from_date}_{to_date}"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 3600:
        with open(cache_file) as f:
            return json.load(f)
    try:
        url = f"{BASE}/v2/aggs/ticker/{ticker.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=desc&limit=5000&apiKey={api_key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        output = {"ticker": ticker.upper(), "timespan": timespan, "from": from_date, "to": to_date,
                  "count": len(results), "bars": results, "fetch_time": datetime.now().isoformat()}
        with open(cache_file, "w") as f:
            json.dump(output, f)
        return output
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_data(ticker="AAPL", **kwargs):
    """Default entry point — returns daily aggregates for last year."""
    from_d = kwargs.get("from_date", "2024-01-01")
    to_d = kwargs.get("to_date", "2024-12-31")
    return get_aggregates(ticker, "day", from_d, to_d)

if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_aggregates(t, "day", "2024-12-01", "2024-12-31")
    if "error" not in result:
        print(f"{result['ticker']}: {result['count']} bars")
        if result['bars']:
            b = result['bars'][0]
            print(f"  Latest: O={b.get('o')} H={b.get('h')} L={b.get('l')} C={b.get('c')} V={b.get('v')}")
    else:
        print(f"Error: {result['error']}")
