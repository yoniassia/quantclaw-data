#!/usr/bin/env python3
"""EIA Natural Gas Storage (Weekly).
EIA API v2 natural-gas/stor/wkly with DEMO_KEY.
Working gas in storage.
~250 lines.
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
CACHE_FILE = CACHE_DIR / 'eia_natural_gas_storage.json'
CACHE_AGE_HOURS = 168  # Weekly
USER_AGENT = 'Mozilla/5.0 ...'
API_KEY = 'DEMO_KEY'
BASE_URL = 'https://api.eia.gov/v2/natural-gas/stor/wkly'
PARAMS = {'api_key': API_KEY, 'frequency': 'weekly', 'data[0]': 'value', 'facets[series][]': ['NG_STO_WK']}
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
    logger.info('Fetching EIA NG storage')
    resp = requests.get(BASE_URL, params=PARAMS, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f'Fetched {{len(data["response"]["data"])}} weeks')
    return data

def process_data(raw: Dict) -> pd.DataFrame:
    data_list = raw['response']['data']
    df = pd.DataFrame(data_list)
    df['period'] = pd.to_datetime(df['period'])
    df.set_index('period', inplace=True)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.rename(columns={'value': 'storage_bcf'}, inplace=True)

    df['change_wow'] = df['storage_bcf'].diff()
    df['ma_5w'] = df['storage_bcf'].rolling(5).mean()

    logger.info('EIA NG storage processed')
    return df

def save_cache(raw_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(raw_data, f, indent=2)

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
        print('Natural Gas Storage (Bcf):')
        print(result.tail())
