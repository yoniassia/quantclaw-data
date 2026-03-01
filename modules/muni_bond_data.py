#!/usr/bin/env python3
"""Municipal Bond Yields (FRED WSLB20).
Downloads 20-Year High Grade Muni Bond yields CSV from FRED.
Returns time series DataFrame.
~250 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
import io
from datetime import datetime
from typing import Union, Dict
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'muni_bond_data.json'
CACHE_AGE_HOURS = 24  # Daily
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
CSV_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=WSLB20'
TIMEOUT = 30

def ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    age_h = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if age_h < CACHE_AGE_HOURS:
        logger.info(f'Cache fresh ({{age_h:.1f}}h)')
        try:
            df_cached = pd.read_json(CACHE_FILE)
            return df_cached
        except Exception:
            pass
    return None

def fetch_csv():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching FRED CSV: {{CSV_URL}}')
    resp = requests.get(CSV_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    csv_data = resp.text
    return csv_data

def process_csv(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
    df.rename(columns={'WSLB20': 'yield_pct'}, inplace=True)
    df['yield_pct'] = pd.to_numeric(df['yield_pct'], errors='coerce')

    # Derived metrics
    df['yield_change_1d'] = df['yield_pct'].diff()
    df['ma_30d'] = df['yield_pct'].rolling(30).mean()
    df['ma_90d'] = df['yield_pct'].rolling(90).mean()
    df['vol_30d'] = df['yield_pct'].rolling(30).std()

    # Recent data
    recent = df.tail(252)  # ~1 year monthly?

    logger.info(f'Muni yields: Latest {{recent["yield_pct"].iloc[-1]:.2f}}%, range {{recent["yield_pct"].min():.2f}} - {{recent["yield_pct"].max():.2f}}%')
    return df

def save_cache(df):
    df.to_json(CACHE_FILE, orient='records', date_format='iso')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        logger.info('Using cached muni yields')
        return cached

    try:
        csv_text = fetch_csv()
        df = process_csv(csv_text)
        save_cache(df)
        return df
    except Exception as e:
        logger.error(str(e))
        return {'error': str(e)}

if __name__ == '__main__':
    pd.set_option('display.max_rows', 10)
    result = get_data()
    if isinstance(result, dict):
        print(f'ERROR: {{result["error"]}}')
    else:
        print('Muni Bond Yields (20Y High Grade):')
        print(result.tail())
        print(result.describe())
