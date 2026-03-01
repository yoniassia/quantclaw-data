#!/usr/bin/env python3
"""US Auto Sales Tracker (FRED TOTALSA, LAUTOSA).
Total and light vehicle sales monthly SAAR.
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

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'auto_sales_tracker.json'
CACHE_AGE_HOURS = 24
USER_AGENT = 'Mozilla/5.0 ...'
URLS = {
    'total_sales': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=TOTALSA',
    'light_auto': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=LAUTOSA'
}
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

def fetch_all():
    data = {}
    for name, url in URLS.items():
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        csv_text = resp.text
        data[name] = csv_text
    return data

def process_data(csv_data: Dict[str, str]) -> pd.DataFrame:
    dfs = []
    for name, csv_text in csv_data.items():
        df_temp = pd.read_csv(io.StringIO(csv_text))
        df_temp['DATE'] = pd.to_datetime(df_temp['DATE'])
        col = df_temp.columns[1]
        df_temp.rename(columns={col: name}, inplace=True)
        dfs.append(df_temp[['DATE', name]])

    df = dfs[0].merge(dfs[1], on='DATE', how='outer')
    df.set_index('DATE', inplace=True)
    for col in ['total_sales', 'light_auto']:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['total_sales_yoy'] = df['total_sales'].pct_change(12) * 100
    logger.info('Auto sales processed')
    return df

def save_cache(df):
    df.reset_index().to_json(CACHE_FILE, orient='records')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        return cached

    try:
        csvs = fetch_all()
        df = process_data(csvs)
        save_cache(df)
        return df
    except Exception as e:
        logger.error(str(e))
        return {'error': str(e)}

if __name__ == '__main__':
    result = get_data()
    if isinstance(result, dict):
        print(f'ERROR: {result["error"]}')
    else:
        print('Auto Sales (SAAR Thousands):')
        print(result.tail())
