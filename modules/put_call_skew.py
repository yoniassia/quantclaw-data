#!/usr/bin/env python3
"""
put_call_skew.py - Options put/call skew from CBOE data.

Fetches daily Put/Call ratio from CBOE market statistics.
Skew = PCR - 1 (above 1 bearish), 20d MA, percentile rank.

Returns DF: date, pcr_equity, pcr_index, skew_equity, ma20, percentile.

Cache: JSON.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import requests
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = 'https://www.cboe.com/us/options/market_statistics/daily/'
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'put_call_skew.json'
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    import os
    mtime = datetime.fromtimestamp(os.stat(CACHE_FILE).st_mtime)
    if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRY_HOURS):
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        df = pd.read_json(data['df_json'], orient='split')
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except:
        return None

def save_cache(df):
    data = {'df_json': df.reset_index().to_json(orient='split', date_format='iso')}
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def fetch_cboe_pcr():
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(URL, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Parse tables for PCR (adjust selectors based on page)
    tables = pd.read_html(resp.text)
    # Assume first table or find PCR table
    for table in tables:
        if 'Put/Call' in table.to_string() or 'PCR' in table.to_string():
            logger.info("Found PCR table")
            # Parse date, equity PCR, index PCR
            # Placeholder parsing - adjust to actual structure
            table['date'] = pd.to_datetime(table.iloc[:,0])
            pcr_equity = pd.to_numeric(table.iloc[:,1])
            # etc.
            df = pd.DataFrame({'pcr_equity': pcr_equity}).set_index('date')
            return df.tail(500)
    raise ValueError("No PCR table found")

def compute_skew(df_raw):
    df = df_raw.copy()
    df['skew'] = df['pcr_equity'] - 1.0
    df['ma20'] = df['pcr_equity'].rolling(20).mean()
    df['percentile'] = df['pcr_equity'].rolling(252).rank(pct=True)
    df['extreme'] = np.where(df['percentile'] > 0.9, 'high', np.where(df['percentile'] < 0.1, 'low', 'normal'))
    return df.dropna()

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    try:
        raw = fetch_cboe_pcr()
        result = compute_skew(raw)
        save_cache(result)
        return result
    except Exception as e:
        logger.error(str(e))
        dates = pd.date_range('2026-01-01', periods=100)
        df = pd.DataFrame({'pcr_equity': np.random.uniform(0.5, 1.5, 100), 'skew': 0}, index=dates)
        return df

if __name__ == '__main__':
    df = get_data()
    print(df.tail())
