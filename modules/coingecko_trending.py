#!/usr/bin/env python3
"""coingecko_trending — CoinGecko trending. Source: https://api.coingecko.com/api/v3/search/trending. Free, no API key."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="coins", **kwargs):
    """
    Fetch CoinGecko trending coins, nfts, categories.
    ticker: 'coins', 'nfts', 'categories' or ignore.
    Returns pd.DataFrame with trending data.
    """
    module_name = __name__.split('.')[-1]
    cache_key = ticker.lower()
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                df['fetch_time'] = datetime.now().isoformat()
                return df
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        trending = []
        if 'coins' in data:
            for item in data['coins'][:10]:
                coin = item['item']
                trending.append({
                    'type': 'coin',
                    'name': coin['name'],
                    'symbol': coin['symbol'],
                    'thumb': coin['thumb'],
                    'market_cap_rank': coin['market_cap_rank'],
                    'price_btc': coin['price_btc'],
                    'score': item.get('score', 0)
                })
        if 'nfts' in data:
            for item in data['nfts'][:10]:
                nft = item
                trending.append({
                    'type': 'nft',
                    'name': nft['name'],
                    'symbol': nft['symbol'],
                    'thumb': nft['thumb'],
                    'score': item.get('score', 0)
                })
        df = pd.DataFrame(trending)
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "coins"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
