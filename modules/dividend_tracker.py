#!/usr/bin/env python3
"""dividend_tracker — Dividend history from Yahoo. Requires yfinance. Free."""
import os
import time
from datetime import datetime
import pandas as pd
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="AAPL", **kwargs):
    """
    Fetch dividend and split history.
    Returns combined df dividends, splits.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 30:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends.dropna()
        dividends.name = 'dividend'
        splits = stock.splits.dropna()
        splits.name = 'split'
        df = pd.concat([dividends, splits])
        df = df.sort_index().tail(50)  # recent
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.reset_index().to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    import json
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_data(ticker)
    print(result.reset_index().to_json(orient='records', date_format='iso'))
