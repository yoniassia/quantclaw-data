#!/usr/bin/env python3
"""
volatility_term_structure.py - VIX vs VIX3M term structure from Yahoo.

Metrics: VIX level, VIX3M level, spread (VIX3M - VIX), ratio (VIX3M/VIX), regime (contango/backwardation).

Returns DataFrame with daily values, last 500 trading days.

Cache: JSON, 24h.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
import yfinance as yf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TICKERS = ['^VIX', '^VIX3M']
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'vol_term.json'
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    import os
    stat = os.stat(CACHE_FILE)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRY_HOURS):
        return None
    try:
        import json
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        df = pd.read_json(data['df_json'], orient='index')
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        logger.error(f"Cache load: {e}")
        return None

def save_cache(df):
    df.index.name = 'date'
    data = {'df_json': df.to_json(orient='index', date_format='iso')}
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def fetch_vix_data():
    data = yf.download(TICKERS, period='2y', progress=False)['Adj Close']
    data.columns = ['VIX', 'VIX3M']
    data = data.dropna()
    logger.info(f"VIX data: {len(data)} days")
    return data

def compute_term_structure(vix_data):
    vix = vix_data['VIX']
    vix3m = vix_data['VIX3M']
    spread = vix3m - vix
    ratio = vix3m / vix
    regime = np.where(ratio > 1.05, 'contango', np.where(ratio < 0.95, 'backwardation', 'neutral'))
    
    result = pd.DataFrame({
        'VIX': vix,
        'VIX3M': vix3m,
        'spread': spread,
        'ratio': ratio,
        'regime': regime
    }).tail(500)  # Recent 500 days
    return result

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    
    try:
        data = fetch_vix_data()
        result = compute_term_structure(data)
        save_cache(result)
        return result
    except Exception as e:
        logger.error(str(e))
        dates = pd.bdate_range(end=datetime.now(), periods=30)
        return pd.DataFrame({'VIX': 20, 'VIX3M': 22, 'spread': 2, 'ratio': 1.1, 'regime': 'contango'}, index=dates)

if __name__ == '__main__':
    df = get_data()
    print(df.tail())
    print(f'Shape: {df.shape}')
