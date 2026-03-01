#!/usr/bin/env python3
"""Emerging Markets Flows Proxy (EEM ETF).
Tracks EEM ETF as EM equity flows proxy via yfinance.
Volume and price trends.
~240 lines.
"""

import pandas as pd
import yfinance as yf
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Union, Dict
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'emerging_market_flows.json'
CACHE_AGE_HOURS = 6
TICKER = 'EEM'

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
            return df
        except:
            pass
    return None

def fetch_eem():
    data = yf.download(TICKER, period='1y', progress=False)
    logger.info(f'EEM data: {{len(data)}} days')
    return data

def process_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw[['Adj Close', 'Volume']].copy()
    df.rename(columns={'Adj Close': 'eem_price', 'Volume': 'volume'}, inplace=True)
    df['price_return_pct'] = df['eem_price'].pct_change() * 100
    df['volume_ma_20'] = df['volume'].rolling(20).mean()
    df['volatility_20'] = df['price_return_pct'].rolling(20).std()

    summary = pd.DataFrame({
        'metric': ['current_price', 'ytd_return_pct', 'avg_volume_20d', 'vol_20d'],
        'value': [
            df['eem_price'].iloc[-1],
            (df['eem_price'].iloc[-1] / df['eem_price'].iloc[0] - 1)*100,
            df['volume_ma_20'].iloc[-1],
            df['volatility_20'].iloc[-1]
        ]
    })
    summary['fetch_time'] = datetime.now().isoformat()

    logger.info('EM flows proxy processed')
    return summary

def save_cache(summary_df):
    summary_df.to_json(CACHE_FILE, orient='records')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        return cached

    try:
        raw = fetch_eem()
        df = process_data(raw)
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
        print('EEM Emerging Markets ETF Summary:')
        print(result)
