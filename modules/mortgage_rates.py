#!/usr/bin/env python3
"""mortgage_rates — Freddie Mac PMMS rates via FRED API. Free."""
import requests
import pandas as pd
import os
import time
from datetime import datetime
import json

try:
    from modules.api_config import FRED_API_KEY
except ImportError:
    FRED_API_KEY = os.environ.get('FRED_API_KEY', '')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# FRED series for mortgage rates
SERIES_MAP = {
    "30-Year Fixed": "MORTGAGE30US",
    "15-Year Fixed": "MORTGAGE15US",
    "5/1 ARM": "MORTGAGE5US",
}

def _fetch_fred_series(series_id: str, limit: int = 52) -> list:
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("observations", [])

def get_data(ticker="30-Year Fixed", **kwargs):
    """
    Get current mortgage rates from FRED.
    ticker: '30-Year Fixed', '15-Year Fixed', '5/1 ARM', or 'all'
    Returns df: rate_type, date, rate, prev_rate, change
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                return pd.DataFrame(json.load(f))

    try:
        if ticker == "all":
            series_to_fetch = SERIES_MAP.items()
        else:
            sid = SERIES_MAP.get(ticker, "MORTGAGE30US")
            series_to_fetch = [(ticker, sid)]

        data = []
        for rate_type, series_id in series_to_fetch:
            obs = _fetch_fred_series(series_id, limit=2)
            if len(obs) >= 1 and obs[0]["value"] != ".":
                current = float(obs[0]["value"])
                prev = float(obs[1]["value"]) if len(obs) >= 2 and obs[1]["value"] != "." else None
                change = round(current - prev, 2) if prev else None
                data.append({
                    "rate_type": rate_type,
                    "date": obs[0]["date"],
                    "rate": current,
                    "prev_rate": prev,
                    "change": change,
                })

        df = pd.DataFrame(data)
        df["fetch_time"] = datetime.now().isoformat()
        if not df.empty:
            with open(cache_file, "w") as f:
                json.dump(df.to_dict("records"), f)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = get_data(ticker)
    print(result.to_string())
