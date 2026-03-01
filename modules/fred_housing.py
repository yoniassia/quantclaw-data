#!/usr/bin/env python3
"""fred_housing — FRED housing starts and permits. Source: https://fred.stlouisfed.org/graph/fredgraph.csv?id=HOUST,PERMIT. Free."""
import requests
import io
import os
import time
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="HOUST", **kwargs):
    """
    Fetch FRED housing data.
    ticker: 'HOUST', 'PERMIT'.
    Returns df with DATE, HOUST, PERMIT.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.csv")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 7:
            return pd.read_csv(cache_file, parse_dates=['DATE'], index_col='DATE')
    try:
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=HOUST,PERMITNEW"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df['DATE'] = pd.to_datetime(df['DATE'])
        df.set_index('DATE', inplace=True)
        df.columns = df.columns.str.strip()
        df = df.dropna()
        df.to_csv(cache_file)
        df['fetch_time'] = datetime.now().isoformat()
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "HOUST"
    result = get_data(ticker)
    print(result.reset_index().to_json(orient='records', date_format='iso'))
