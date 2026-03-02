#!/usr/bin/env python3
"""iex_deep_book — IEX Cloud L2 deep book data. Source: https://cloud.iexapis.com/. Free sandbox available."""
import requests
import os
import json
from datetime import datetime

BASE = "https://cloud.iexapis.com/stable"
SANDBOX = "https://sandbox.iexapis.com/stable"

def _get_config():
    key = os.environ.get("IEX_API_KEY", "")
    sandbox = os.environ.get("IEX_SANDBOX", "false").lower() == "true"
    if not key:
        cred_path = os.path.expanduser("~/.openclaw/workspace/.credentials/iex.json")
        if os.path.exists(cred_path):
            with open(cred_path) as f:
                cfg = json.load(f)
                key = cfg.get("apiKey", cfg.get("publishableToken", ""))
                sandbox = cfg.get("sandbox", False)
    base = SANDBOX if sandbox else BASE
    return key, base

def get_deep_book(ticker, **kwargs):
    """Fetch L2 deep book (top of book bids/asks) for a ticker."""
    key, base = _get_config()
    if not key:
        return {"error": "No IEX API key. Set IEX_API_KEY or add .credentials/iex.json"}
    try:
        url = f"{base}/deep/book?symbols={ticker.upper()}&token={key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {"ticker": ticker.upper(), "book": data.get(ticker.upper(), {}),
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

def get_tops(tickers=None, **kwargs):
    """Fetch TOPS (last sale + bid/ask) for tickers. tickers: comma-separated or list."""
    key, base = _get_config()
    if not key:
        return {"error": "No IEX API key."}
    if isinstance(tickers, list):
        tickers = ",".join(tickers)
    tickers = tickers or "AAPL"
    try:
        url = f"{base}/tops?symbols={tickers.upper()}&token={key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return {"tickers": tickers.upper(), "data": resp.json(),
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}

def get_last_sale(tickers=None, **kwargs):
    """Fetch last sale price for tickers."""
    key, base = _get_config()
    if not key:
        return {"error": "No IEX API key."}
    if isinstance(tickers, list):
        tickers = ",".join(tickers)
    tickers = tickers or "AAPL"
    try:
        url = f"{base}/tops/last?symbols={tickers.upper()}&token={key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return {"tickers": tickers.upper(), "data": resp.json(),
                "fetch_time": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}

def get_data(ticker="AAPL", **kwargs):
    return get_deep_book(ticker, **kwargs)

if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_deep_book(t)
    print(json.dumps(result, indent=2)[:500])
