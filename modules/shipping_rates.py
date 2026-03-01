#!/usr/bin/env python3
"""Baltic Dry Index (FRED DBDIY).
Shipping rates proxy via Baltic Dry freight index CSV.
Daily index.
~230 lines.
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

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'shipping_rates.json'
CACHE_AGE_HOURS = 24
USER_AGENT = 'Mozilla/5.0 ...'
CSV_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DBDIY'
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
            df = pd.read_json(CACHE_FILE)
            df['DATE'] = pd.to_datetime(df['DATE'])
            return df
        except:
            pass
    return None

def fetch_csv():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching Baltic Dry CSV')
    resp = requests.get(CSV_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text

def process_csv(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
    df.rename(columns={'DBDIY': 'baltic_dry_index'}, inplace=True)
    df['baltic_dry_index'] = pd.to_numeric(df['baltic_dry_index'], errors='coerce')

    df['index_change_1d'] = df['baltic_dry_index'].pct_change() * 100
    df['ma_20d'] = df['baltic_dry_index'].rolling(20).mean()
    df['ma_200d'] = df['baltic_dry_index'].rolling(200).mean()

    logger.info('Baltic Dry processed')
    return df

def save_cache(df):
    df.reset_index().to_json(CACHE_FILE, orient='records')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
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
    result = get_data()
    if isinstance(result, dict):
        print(f'ERROR: {{result["error"]}}')
    else:
        print('Baltic Dry Index:')
        print(result.tail())
