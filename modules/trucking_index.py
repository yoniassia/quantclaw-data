#!/usr/bin/env python3
"""
trucking_index.py - ATA trucking tonnage from FRED (ATASTTFRMM).

Monthly trucking tonnage index.

Returns DF: date, tonnage_index, yoy, ma3.

Cache.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas_datareader.data as web

SERIES_ID = 'ATASTTFRMM'
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'trucking.json'
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRY_HOURS):
        return None
    with open(CACHE_FILE, 'r') as f:
        data = json.load(f)
    df = pd.read_json(data['df_json'], orient='split')
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
    return df

def save_cache(df):
    data = {'df_json': df.reset_index().to_json(orient='split', date_format='iso')}
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def fetch_fred():
    df = web.DataReader(SERIES_ID, 'fred')
    df = df.rename(columns={SERIES_ID: 'tonnage_index'})
    df['yoy'] = df['tonnage_index'].pct_change(12) * 100
    df['ma3'] = df['tonnage_index'].rolling(3).mean()
    return df.dropna()

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    try:
        result = fetch_fred()
        save_cache(result)
        return result.tail(36)  # Last 3 years
    except Exception as e:
        print(e)
        return pd.DataFrame({'tonnage_index': [120]}, index=[datetime.now()])

if __name__ == '__main__':
    print(get_data())
