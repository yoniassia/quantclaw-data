#!/usr/bin/env python3
"""defillama_tvl — DeFi Llama TVL data. Source: https://api.llama.fi/protocols. Free, no API key."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="all", limit=100, **kwargs):
    """
    Fetch DeFi protocols TVL data.
    ticker: chain slug e.g. 'ethereum', 'bitcoin' or 'all'.
    limit: max rows to return.
    Returns pd.DataFrame sorted by TVL desc.
    Columns: name, symbol, tvl, change_1h, change_7d, change_1m, category, chains, audit_score, etc.
    """
    module_name = __name__.split('.')[-1]
    cache_key = ticker.lower().replace('/', '_') if ticker and ticker != "all" else "all"
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:  # 24h cache
            with open(cache_file, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                df['fetch_time'] = datetime.now().isoformat()
                return df.head(limit)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        params = {'limit': 1000}
        if ticker != "all":
            params['chain'] = ticker.lower()
        resp = requests.get("https://api.llama.fi/protocols", params=params, timeout=30, headers=headers)
        resp.raise_for_status()
        api_data = resp.json()
        protocols = api_data
        if isinstance(protocols, dict):
            protocols = protocols.get('protocols', [])
        # Data cleaning
        df = pd.DataFrame(protocols)
        if df.empty:
            return pd.DataFrame({"error": ["No data"]})
        numeric_cols = ['tvl', 'tvlPrevDay', 'tvlPrevWeek', 'tvlPrevMonth', 'change_1h', 'change_7d', 'change_1m', 'change_1y', 'auditScore']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['tvl_btc'] = df.get('tvl', 0) / 60000000000  # approx BTC price placeholder
        df['rank_change'] = df.get('change_1d', 0).rank(ascending=False)
        df = df.sort_values('tvl', ascending=False).reset_index(drop=True)
        df['fetch_time'] = datetime.now().isoformat()
        # Cache
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df.head(limit)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
