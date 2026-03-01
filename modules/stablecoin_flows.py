#!/usr/bin/env python3
"""Stablecoin Supplies and Flows Tracker.
Fetches stablecoin data from DefiLlama (stablecoins.llama.fi).
Includes USDT, USDC, DAI, etc. - circulating supply, price deviation.
Processes to DataFrame sorted by supply.
~240 lines.
"""

import pandas as pd
import requests
import json
import os
import time
import logging
from datetime import datetime
from typing import Union, Dict, Any, List
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'stablecoin_flows.json'
CACHE_AGE_HOURS = 1.0
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
API_URL = 'https://stablecoins.llama.fi/stablecoins'
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
                return data
        except Exception:
            pass
    return None

def fetch_data():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching {{API_URL}}')
    resp = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    logger.info(f'Fetched {{len(data.get(\"peggedAssets\", []))}} stablecoins')
    return data

def process_data(raw: Dict[str, Any]) -> pd.DataFrame:
    assets = raw.get('peggedAssets', [])
    if not assets:
        raise ValueError('No assets data')

    df = pd.DataFrame(assets)

    cols = ['name', 'symbol', 'price', 'circulating', 'circulatingPegged', 'peggedUSD']
    available = [c for c in cols if c in df.columns]
    df = df[available]

    df = df.rename(columns={
        'circulating': 'circulating_supply',
        'circulatingPegged': 'circulating_pegged',
        'peggedUSD': 'pegged_usd'
    })

    numeric_cols = ['price', 'circulating_supply', 'circulating_pegged', 'pegged_usd']
    for col in numeric_cols:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['price_deviation_pct'] = ((df['price'] - 1.0) * 100).round(2)
    df['market_cap_usd'] = df['pegged_usd']
    df['rank'] = df['pegged_usd'].rank(ascending=False).astype(int)

    df = df[df['pegged_usd'] > 1e8].sort_values('pegged_usd', ascending=False).reset_index(drop=True)

    df['fetch_time'] = datetime.utcnow().isoformat()

    logger.info('Top stablecoins processed')
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
        print('Stablecoins (majors >00M):')
        print(result[['symbol', 'pegged_usd', 'price_deviation_pct']])
