#!/usr/bin/env python3
"""Bitcoin Onchain Metrics Tracker.
Fetches key Bitcoin network stats from Blockchain.info API:
- Hashrate, Difficulty, Mempool size
- Market price, transactions, blocks
Free API, no key.
Returns processed DataFrame.
~250 lines.
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'bitcoin_onchain.json'
CACHE_AGE_HOURS = 0.5  # 30 min
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
API_URL = 'https://api.blockchain.info/stats'
TIMEOUT = 30

def ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    age_h = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if age_h < CACHE_AGE_HOURS:
        logger.info(f'Cache OK ({age_h:.1f}h)')
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                data['fetch_time'] = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).isoformat()
                return data
        except Exception as e:
            logger.warning(f'Cache load fail: {e}')
    logger.info('Stale cache')
    return None

def fetch_data():
    headers = {'User-Agent': USER_AGENT}
    logger.info(f'Fetching {API_URL}')
    resp = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    data['fetch_time'] = datetime.utcnow().isoformat()
    logger.info(f'Hashrate: {data["hashrate_10m_rolling_avg"]:.2f} TH/s')
    return data

def process_data(raw: Dict[str, Any]) -> pd.DataFrame:
    key_metrics = [
        'market_price_usd',
        'hashrate_10m_rolling_avg',  # TH/s
        'minutes_between_blocks_10m_rolling_avg',
        'difficulty_10m_rolling_avg',
        'estimated_transaction_volume_usd',
        'mempool_size',
        'n_orphans_total',
        'transaction_rates_10m_rolling_avg',
        'blocks_size_10m_rolling_avg_bytes'
    ]

    df_data = {'timestamp': [raw['fetch_time']]}
    for metric in key_metrics:
        if metric in raw:
            val = raw[metric]
            df_data[metric.replace('_', ' ').title()] = [val]

    df = pd.DataFrame(df_data)

    # Conversions
    numeric = ['Market Price Usd', 'Hashrate 10M Rolling Avg', 'Minutes Between Blocks 10M Rolling Avg',
               'Difficulty 10M Rolling Avg', 'Estimated Transaction Volume Usd', 'Mempool Size',
               'N Orphans Total', 'Transaction Rates 10M Rolling Avg', 'Blocks Size 10M Rolling Avg Bytes']
    for col in numeric:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Derived
    df['hashrate_phs'] = df['Hashrate 10M Rolling Avg'] / 1000 if 'Hashrate 10M Rolling Avg' in df else np.nan  # PH/s
    df['tx_per_sec'] = df['Transaction Rates 10M Rolling Avg'] / 600 if 'Transaction Rates 10M Rolling Avg' in df else np.nan
    df['mempool_congested'] = df['Mempool Size'] > 100 if 'Mempool Size' in df else False

    logger.info('Processed BTC stats')
    return df

def save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info('Cache saved')

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
        logger.error(f'Error: {e}')
        return {'error': str(e)}

if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    result = get_data()
    if isinstance(result, dict) and 'error' in result:
        print(f'ERROR: {result["error"]}')
    else:
        print('Bitcoin Onchain Metrics:')
        print(result.T)  # Transpose for readability
