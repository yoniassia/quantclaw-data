#!/usr/bin/env python3
"""eia_petroleum — EIA petroleum summary. Source: https://api.eia.gov/v2/petroleum/summary?api_key=DEMO_KEY. Free demo."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="WCRUSEC1", **kwargs):  # e.g. crude oil
    """
    Fetch EIA petroleum data.
    ticker: series id.
    Returns df with period, value, etc.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    try:
        params = {
            'api_key': 'DEMO_KEY',
            'frequency': 'weekly',
            'data[0]': 'value',
            'facets[series[]]': [ticker],
            'start': '2020-01-01',
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': '0',
            'length': '5000'
        }
        resp = requests.get("https://api.eia.gov/v2/petroleum/summary", params=params, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        api_data = resp.json()['response']['data']
        df = pd.DataFrame(api_data)
        df['period'] = pd.to_datetime(df['period'])
        df = df.sort_values('period').reset_index(drop=True)
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "WCRUSEC1"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
