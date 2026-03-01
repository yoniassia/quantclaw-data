#!/usr/bin/env python3
"""zillow_zhvi — Zillow ZHVI home values. Source: https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv. Free."""
import requests
import io
import os
import time
import gzip
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="United States", months=12, **kwargs):
    """
    Fetch Zillow Home Value Index (ZHVI).
    ticker: RegionName filter.
    months: recent months.
    Returns df with RegionName, State, SizeRank, 2024-xx-xx columns.
    """
    module_name = __name__.split('.')[-1]
    cache_key = f"{ticker.replace(' ', '_')}_{months}"
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.parquet")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 7:
            return pd.read_parquet(cache_file)
    try:
        url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
        resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text), low_memory=False)
        df['Date'] = pd.to_datetime(df.iloc[:, 7:].columns, format='%Y-%m-%d')  # assume date cols start col 7
        recent_cols = df.columns[-months*12:]  # approx
        df_recent = df[['RegionName', 'StateName', 'SizeRank'] + list(recent_cols)]
        if ticker:
            df_recent = df_recent[df_recent['RegionName'].str.contains(ticker, case=False, na=False)]
        df_recent = df_recent.sort_values('SizeRank').head(50)
        df_recent['fetch_time'] = datetime.now().isoformat()
        df_recent.to_parquet(cache_file, index=False)
        return df_recent
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "United States"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
