#!/usr/bin/env python3
"""Bank of England Base Rate.
Scrapes BoE interest rate history table.
~240 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
from datetime import datetime
from typing import Union, Dict
from pathlib import Path
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'bank_of_england.json'
CACHE_AGE_HOURS = 24
USER_AGENT = 'Mozilla/5.0 ...'
HTML_URL = 'https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate'
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
            df['date'] = pd.to_datetime(df['date'])
            return df
        except:
            pass
    return None

def fetch_html():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching BoE rate page')
    resp = requests.get(HTML_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text

def process_html(html_text: str) -> pd.DataFrame:
    dfs = pd.read_html(StringIO(html_text))
    # Assume first table is the rate history
    df = dfs[0]  # Adjust index if needed
    df.columns = df.columns.str.strip()
    df['date'] = pd.to_datetime(df.iloc[:,0])
    df['base_rate_pct'] = pd.to_numeric(df.iloc[:,1], errors='coerce')
    df = df[['date', 'base_rate_pct']].dropna()
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)

    df['change_bp'] = df['base_rate_pct'].diff() * 100

    logger.info(f'BoE rates: {{len(df)}} changes, current {{df["base_rate_pct"].iloc[-1]:.2f}}%')
    return df

def save_cache(df):
    df.reset_index().to_json(CACHE_FILE, orient='records')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        return cached

    try:
        html = fetch_html()
        df = process_html(html)
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
        print('BoE Base Rate History:')
        print(result.tail())
