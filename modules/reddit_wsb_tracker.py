#!/usr/bin/env python3
"""reddit_wsb_tracker — Reddit r/wallstreetbets hot posts. Source: https://www.reddit.com/r/wallstreetbets/hot.json. Free."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd
import re

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker=None, limit=25, **kwargs):
    """
    Fetch hot posts from r/wallstreetbets.
    ticker: filter titles containing ticker.
    Returns df with title, score, num_comments, url, created_utc, etc.
    """
    module_name = __name__.split('.')[-1]
    cache_key = f"{ticker or 'hot'}_{limit}"
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 3600:  # 1h cache for reddit
            with open(cache_file, 'r') as f:
                return pd.DataFrame(json.load(f))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        url = f"https://www.reddit.com/r/wallstreetbets/hot.json?limit={limit}"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()['data']['children']
        posts = []
        for post in data:
            p = post['data']
            title = p['title']
            if ticker and re.search(rf'\b{ticker.upper()}\b', title, re.I):
                posts.append(p)
            elif not ticker:
                posts.append(p)
        df = pd.DataFrame(posts)
        if not df.empty:
            df['sentiment_score'] = df['title'].apply(lambda x: len(re.findall(r'\${2,}', x)))  # DD count proxy
            df['created'] = pd.to_datetime(df['created_utc'], unit='s')
            df = df[['title', 'score', 'num_comments', 'url', 'created', 'sentiment_score']].sort_values('score', ascending=False)
        df['fetch_time'] = datetime.now().isoformat()
        with open(cache_file, 'w') as f:
            json.dump(df.to_dict('records'), f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else None
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
