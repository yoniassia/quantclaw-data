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
import requests
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERIES_ID = 'RAILFRTINTERMODAL'
try:
    from modules.api_config import FRED_API_KEY
except ImportError:
    import os
    FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
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
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={SERIES_ID}&api_key={FRED_API_KEY}&file_type=json&observation_start=2010-01-01"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    obs = resp.json().get('observations', [])
    rows = [{'DATE': o['date'], 'rail_intermodal': float(o['value'])} for o in obs if o['value'] != '.']
    df = pd.DataFrame(rows)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
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
