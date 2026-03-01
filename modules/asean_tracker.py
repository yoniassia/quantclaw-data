#!/usr/bin/env python3
"""asean_tracker.py — ASEAN-5 economics from World Bank API.

ASEAN-5: Indonesia (IDN), Thailand (THA), Philippines (PHL), Malaysia (MYS), Vietnam (VNM).

Key indicators:
- GDP growth (NY.GDP.MKTP.KD.ZG)
- CPI inflation (FP.CPI.TOTL.ZG)
- Unemployment rate (SL.UEM.TOTL.ZS)
- Manufacturing value added growth (NV.IND.MANF.KD.ZG)
- Exports growth (NE.EXP.GNFS.KD.ZG)

Annual data 2010-current, latest available.
Cache: 30 days JSON (WB updates quarterly).
Error handling: cached or empty DF.
"""

import os
import time
import json
import pandas as pd
import requests
from datetime import datetime
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

ASEAN_COUNTRIES = ['IDN', 'THA', 'PHL', 'MYS', 'VNM']

INDICATORS = {
    'NY.GDP.MKTP.KD.ZG': 'GDP growth %',
    'FP.CPI.TOTL.ZG': 'CPI YoY %',
    'SL.UEM.TOTL.ZS': 'Unemployment %',
    'NV.IND.MANF.KD.ZG': 'Manufacturing growth %',
    'NE.EXP.GNFS.KD.ZG': 'Exports growth %',
}

YEARS = '2010:2023'

def fetch_wb(indicator: str, countries: List[str]) -> pd.DataFrame:
    """Fetch World Bank data for indicator/countries."""
    country_str = ';'.join(countries)
    url = f"http://api.worldbank.org/v2/country/{country_str}/indicator/{indicator}?date={YEARS}&format=json&MRNEV=latest&MRV=14"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        wb_data = resp.json()
        if len(wb_data) < 2:
            return pd.DataFrame()
        data = wb_data[1]
        df_data = []
        for item in data:
            if item['value'] is not None:
                df_data.append({
                    'country_code': item['country']['id'],
                    'country_name': item['country']['value'],
                    'date': item['date'],
                    'value': item['value'],
                    'indicator': indicator,
                    'indicator_name': INDICATORS[indicator],
                })
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'], format='%Y')
        df['value'] = pd.to_numeric(df['value'])
        return df.sort_values('date', ascending=False)
    except Exception as e:
        logger.error(f"WB {indicator}: {e}")
        return pd.DataFrame()

def get_data(cache_days: int = 30) -> pd.DataFrame:
    """Main get_data."""
    cache_file = os.path.join(CACHE_DIR, 'asean_tracker.json')
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < cache_days * 86400:
        try:
            with open(cache_file, 'r') as f:
                cached_df = pd.read_json(f.read(), orient='records')
            logger.info(f"Loaded ASEAN data ({len(cached_df)} rows)")
            return cached_df
        except Exception as e:
            logger.warning(f"Cache read: {e}")
    
    all_df = pd.DataFrame()
    for ind, name in INDICATORS.items():
        df = fetch_wb(ind, ASEAN_COUNTRIES)
        if not df.empty:
            all_df = pd.concat([all_df, df], ignore_index=True)
        time.sleep(0.5)
    
    if not all_df.empty:
        all_df['fetch_time'] = datetime.now().isoformat()
        all_df = all_df.sort_values(['indicator', 'country_code', 'date'], ascending=[False, True, False])
        try:
            all_df.to_json(cache_file, orient='records', date_format='iso')
            logger.info(f"Cached {len(all_df)} rows")
        except Exception as e:
            logger.error(f"Cache write: {e}")
        return all_df
    return pd.DataFrame({'error': ['No ASEAN data']})

def summary_latest() -> pd.DataFrame:
    """Pivot latest per country/indicator."""
    df = get_data()
    if df.empty:
        return df
    latest = df.loc[df.groupby(['country_code', 'indicator']).date.idxmax()]
    pivot = latest.pivot(index='country_code', columns='indicator_name', values='value').round(2)
    return pivot.fillna('-')

if __name__ == '__main__':
    df = get_data()
    print("ASEAN Latest Summary:")
    print(summary_latest())
    print(f"\nShape: {df.shape}")
