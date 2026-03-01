#!/usr/bin/env python3
"""
rail_traffic.py - AAR rail traffic from FRED (RAILFRTINTERMODAL).

Weekly intermodal rail freight traffic index.

Returns DF: date, rail_intermodal, yoy_change, ma4.

Cache.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import pandas_datareader.data as web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERIES_ID = 'RAILFRTINTERMODAL'
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'rail.json'
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
    df = web.DataReader(SERIES_ID, 'fred', '2010-01-01')
    df = df.rename(columns={SERIES_ID: 'rail_intermodal'})
    df['yoy_change'] = df['rail_intermodal'].pct_change(52) * 100
    df['ma4'] = df['rail_intermodal'].rolling(4).mean()
    return df.dropna()

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    try:
        result = fetch_fred()
        save_cache(result)
        return result.tail(104)  # Last 2 years
    except Exception as e:
        logger.error(e)
        return pd.DataFrame({'rail_intermodal': [100]}, index=[datetime.now()])

if __name__ == '__main__':
    print(get_data().tail())
