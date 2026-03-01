#!/usr/bin/env python3
"""Nuclear Capacity Tracker.
Uses EIA API for monthly nuclear electricity generation/capacity.
Proxy for global nuclear capacity trends.
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

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'nuclear_capacity.json'
CACHE_AGE_HOURS = 168
USER_AGENT = 'Mozilla/5.0 ...'
API_KEY = 'DEMO_KEY'
BASE_URL = 'https://api.eia.gov/v2/electricity/rto/fuel-type-data/data'
PARAMS = {
    'api_key': API_KEY,
    'frequency': 'monthly',
    'data[0]': 'value,generation',
    'facets[fuel_type][]': ['nuclear'],
    'facets[respondent][]': ['ALL'],
    'sort[0][column]': 'period',
    'sort[0][direction]': 'desc',
    'offset': 0,
    'length': 5000
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
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data['response']['data'])
            return df
        except:
            pass
    return None

def fetch_data():
    headers = {'User-Agent': USER_AGENT}
    logger.info('Fetching EIA nuclear data')
    resp = requests.get(BASE_URL, params=PARAMS, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f'Fetched {{len(data["response"]["data"])}} records')
    return data

def process_data(raw: Dict) -> pd.DataFrame:
    data_list = raw['response']['data']
    df = pd.DataFrame(data_list)
    df['period'] = pd.to_datetime(df['period'])
    df['respondent'] = df['respondent']
    df['value'] = pd.to_numeric(df['value'], errors='coerce')  # Capacity?
    df['generation'] = pd.to_numeric(df['generation'], errors='coerce')

    # Pivot or aggregate
    df_pivot = df.pivot(index='period', columns='respondent', values='value').fillna(0)
    df_gen = df.pivot(index='period', columns='respondent', values='generation').fillna(0)

    # Total
    df['total_capacity'] = df_pivot.sum(axis=1)
    df['total_gen'] = df_gen.sum(axis=1)

    df = df[['period', 'total_capacity', 'total_gen']].drop_duplicates()
    df.set_index('period', inplace=True)
    df.sort_index(inplace=True)

    logger.info('Nuclear capacity processed')
    return df

def save_cache(raw):
    with open(CACHE_FILE, 'w') as f:
        json.dump(raw, f, indent=2)

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        return cached

    try:
        raw = fetch_data()
        df = process_data(raw)
        save_cache(raw)
        return df
    except Exception as e:
        logger.error(str(e))
        return {'error': str(e)}

if __name__ == '__main__':
    result = get_data()
    if isinstance(result, dict):
        print(f'ERROR: {{result["error"]}}')
    else:
        print('Nuclear Capacity/Gen US EIA:')
        print(result.tail())
