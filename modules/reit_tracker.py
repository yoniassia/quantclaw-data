#!/usr/bin/env python3
"""REIT ETF Tracker (VNQ, IYR, XLRE).
Fetches price, volume, returns using yfinance.
Daily data last 1Y.
~260 lines.
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

logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s')
logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent
CACHE_DIR = MODULE_DIR.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'reit_tracker.json'
CACHE_AGE_HOURS = 6  # Hourly-ish for EOD
TICKERS = ['VNQ', 'IYR', 'XLRE']
PERIOD = '1y'

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

def fetch_reits():
    data = yf.download(TICKERS, period=PERIOD, progress=False)
    logger.info(f'Fetched {{len(data)}} rows for {{len(TICKERS)}} REIT ETFs')
    return data

def process_data(multi_df: pd.DataFrame) -> pd.DataFrame:
    # Flatten multiindex columns
    if isinstance(multi_df.columns, pd.MultiIndex):
        multi_df.columns = ['_'.join(col).strip() for col in multi_df.columns.values]

    # Key columns
    cols = [c for c in multi_df.columns if any(k in c for k in ['Adj Close', 'Volume', 'Close'])]
    df = multi_df[cols].copy()

    # Daily returns
    adj_cols = [c for c in df.columns if 'Adj Close' in c]
    for col in adj_cols:
        df[f'{col}_return_pct'] = df[col].pct_change() * 100

    # Summary stats per ticker
    summary = []
    for ticker in TICKERS:
        adj_col = f'{ticker}_Adj Close'
        if adj_col in df:
            series = df[adj_col]
            summary.append({
                'ticker': ticker,
                'current_price': series.iloc[-1],
                'price_change_1d': series.pct_change().iloc[-1] * 100,
                'vol_20d': series.pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100,
                'total_return_1y': (series.iloc[-1] / series.iloc[0] - 1) * 100,
                'avg_volume': df[f'{ticker}_Volume'].mean()
            })

    summary_df = pd.DataFrame(summary)
    summary_df['fetch_time'] = datetime.now().isoformat()

    logger.info('REIT summary processed')
    return summary_df

def save_cache(df):
    df.to_json(CACHE_FILE, orient='records')

def get_data() -> Union[pd.DataFrame, Dict[str, str]]:
    ensure_cache_dir()
    cached = load_cache()
    if cached is not None:
        return cached

    try:
        raw_data = fetch_reits()
        df = process_data(raw_data)
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
        print('REIT ETFs Summary:')
        print(result.round(2))
