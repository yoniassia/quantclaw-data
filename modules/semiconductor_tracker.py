#!/usr/bin/env python3
"""Semiconductor Sales Tracker (FRED NAICS334413).
Manufacturers' shipments for semiconductors (MANDEFNAICS334413).
Monthly sales data.
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
CACHE_FILE = CACHE_DIR / 'semiconductor_tracker.json'
CACHE_AGE_HOURS = 168
USER_AGENT = 'Mozilla/5.0 ...'
CSV_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=MANDEFNAICS334413'
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
    logger.info(f'Fetching semi sales CSV')
    resp = requests.get(CSV_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text

def process_csv(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    df['DATE'] = pd.to_datetime(df['DATE'])
    df.set_index('DATE', inplace=True)
    df.rename(columns={'MANDEFNAICS334413': 'semi_shipments_mil'}, inplace=True)
    df['semi_shipments_mil'] = pd.to_numeric(df['semi_shipments_mil'], errors='coerce')

    df['yoy_change_pct'] = df['semi_shipments_mil'].pct_change(12) * 100
    df['ma_3m'] = df['semi_shipments_mil'].rolling(3).mean()

    logger.info('Semiconductor sales processed')
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
        print('Semiconductor Shipments (Mil $):')
        print(result.tail())
