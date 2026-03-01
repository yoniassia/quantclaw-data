#!/usr/bin/env python3
"""DEX Volume Tracker.
Fetches DEX volumes and TVL from DefiLlama overview/dexs.
Top DEXes by volume, chain breakdown.
~230 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
from datetime import datetime
from typing import Union, Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'dex_volume_tracker.json'
CACHE_AGE_HOURS = 1.0
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
API_URL = 'https://api.llama.fi/overview/dexs'
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
                return json.load(f)
        except Exception:
            pass
    return None

def fetch_data():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching {{API_URL}}')
    resp = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f'Fetched data for {{len(data.get(\"dexs\", []))}} DEXs')
    return data

def process_data(raw: Dict[str, Any]) -> pd.DataFrame:
    dexs = raw.get('dexs', [])
    if not dexs:
        raise ValueError('No DEXs data')

    df = pd.DataFrame(dexs)

    key_cols = ['name', 'dexVolumeUSD24h', 'tvl', 'change_1d', 'chains']
    available = [c for c in key_cols if c in df.columns]
    df = df[available]

    df = df.rename(columns={
        'dexVolumeUSD24h': 'volume_24h_usd',
        'change_1d': 'volume_change_1d_pct'
    })

    numeric = ['volume_24h_usd', 'tvl', 'volume_change_1d_pct']
    for col in numeric:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['volume_tvl_ratio'] = df['volume_24h_usd'] / df['tvl'].replace(0, np.nan)
    df['rank'] = df['volume_24h_usd'].rank(ascending=False).astype(int)

    df = df.sort_values('volume_24h_usd', ascending=False).head(50).reset_index(drop=True)
    df['fetch_time'] = datetime.utcnow().isoformat()

    logger.info('DEX data processed')
    return df

def save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached:
        return process_data(cached)

    try:
        raw = fetch_data()
        df = process_data(raw)
        save_cache(raw)
        return df
    except Exception as e:
        logger.error(str(e))
        return {'error': str(e)}

if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    result = get_data()
    if isinstance(result, dict) and 'error' in result:
        print(f'ERROR: {{result["error"]}}')
    else:
        print('Top DEX Volumes 24h:')
        print(result[['name', 'volume_24h_usd', 'volume_change_1d_pct']].round(0))
