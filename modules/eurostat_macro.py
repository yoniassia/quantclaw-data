#!/usr/bin/env python3
"""Eurostat Macro GDP (namq_10_gdp).
Eurostat SDMX API for quarterly GDP data.
~260 lines.
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
CACHE_FILE = CACHE_DIR / 'eurostat_macro.json'
CACHE_AGE_HOURS = 168
USER_AGENT = 'Mozilla/5.0 ...'
API_URL = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/namq_10_gdp'
PARAMS = {
    'format': 'jsondataonly',
    'lang': 'en'
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
            return pd.DataFrame(data['value'])
        except:
            pass
    return None

def fetch_data():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching Eurostat GDP')
    resp = requests.get(API_URL, params=PARAMS, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f'Eurostat data size: {{len(data.get(\"value\", []))}}')
    return data

def process_data(raw: Dict) -> pd.DataFrame:
    df_list = []
    for idx, val in raw.get('value', {}).items():
        row = {'index': idx, 'value': val}
        df_list.append(row)
    df = pd.DataFrame(df_list)

    # Parse dimensions from index if SDMX
    # Simplified: assume value column
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    # Add parse logic for GDP series if needed
    logger.info('Eurostat GDP processed')
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
        print(f'ERROR: {result["error"]}')
    else:
        print('Eurostat GDP namq_10_gdp:')
        print(result.head())
