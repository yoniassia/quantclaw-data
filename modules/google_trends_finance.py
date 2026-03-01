#!/usr/bin/env python3
"""google_trends_finance — Google Trends for finance keywords. Source: pytrends. Free, no API key."""
import os
import time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq
import json
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="AAPL", timeframe='today 3-m', **kwargs):
    """
    Fetch Google Trends data for ticker in finance context.
    ticker: keyword or list.
    timeframe: e.g. 'today 3-m', 'today 12-m', 'today 5-y'.
    Returns interest_over_time df.
    """
    module_name = __name__.split('.')[-1]
    cache_key = ticker.replace(' ', '_').lower()
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                df = pd.read_json(data, orient='split')
                df['fetch_time'] = datetime.now().isoformat()
                return df
    try:
        pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.1)
        kw_list = [ticker] if isinstance(ticker, str) else ticker[:5]
        cat = 0  # worldwide
        gprop = ''  # web search
        pytrends.build_payload(kw_list, cat=cat, timeframe=timeframe, geo='', gprop=gprop)
        df = pytrends.interest_over_time()
        if df.empty:
            df = pytrends.interest_by_region(resolution='COUNTRY', incLowVol=True, incGeoCode=False)
        df = df.reset_index()
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_json(orient='split')
        with open(cache_file, 'w') as f:
            f.write(cache_data)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
