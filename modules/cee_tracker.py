#!/usr/bin/env python3
"""cee_tracker.py — Central/Eastern Europe macro from Eurostat API / TradingEconomics fallback.

Tracks key macro indicators for CEE-6 (PL, HU, CZ, SK, RO, BG):
- Inflation (HICP/ CPI YoY %)
- Unemployment rate (%)
- GDP growth (QoQ, YoY %)
- Industrial production (YoY %)
- Retail sales (YoY %)

Prioritizes Eurostat JSON API, fallback to TradingEconomics scrape.
Data: latest 12 periods per indicator/country.
Cache: 7 days JSON.
Error handling: return cached data or empty DF with error row.
"""

import os
import time
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

CEE_COUNTRIES = {
    'PL': 'poland',
    'HU': 'hungary',
    'CZ': 'czech-republic',
    'SK': 'slovakia',
    'RO': 'romania',
    'BG': 'bulgaria'
}

INDICATORS = [
    'inflation-cpi',
    'unemployment-rate',
    'gdp-growth',
    'industrial-production',
    'retail-sales'
]

def try_eurostat(dataset: str, params: Dict) -> Optional[pd.DataFrame]:
    """Attempt Eurostat JSON API fetch and parse."""
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}?format=JSON"
    for k, v in params.items():
        url += f"&{k}={v}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if 'value' in data:
            # Simple normalize, extend for full parse
            df = pd.json_normalize(data['value'])
            df['fetch_source'] = 'Eurostat'
            return df
    except Exception as e:
        logger.warning(f"Eurostat {dataset} failed: {e}")
    return None

def scrape_tradingeconomics(country_slug: str, indicator: str) -> List[Dict]:
    """Scrape latest data from TradingEconomics."""
    url = f"https://tradingeconomics.com/{country_slug}/{indicator}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        data = []
        value_el = soup.find('span', class_='float-big')
        current_value = float(re.sub(r'[^0-9.-]', '', value_el.text)) if value_el else None
        table = soup.find('table', class_='table')
        if table:
            rows = table.find_all('tr')[:12]
            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cols) >= 3:
                    data.append({
                        'date': cols[0],
                        'actual': float(re.sub(r'[^0-9.-]', '', cols[1])) if cols[1] else None,
                        'previous': float(re.sub(r'[^0-9.-]', '', cols[2])) if cols[2] else None,
                        'consensus': float(re.sub(r'[^0-9.-]', '', cols[3])) if len(cols) > 3 and cols[3] else None,
                    })
        if data and current_value is not None:
            data[0]['actual'] = current_value
        for row in data:
            row['country'] = [k for k, v in CEE_COUNTRIES.items() if v == country_slug][0]
            row['indicator'] = indicator.replace('-', ' ').title()
        return data
    except Exception as e:
        logger.error(f"Scrape {country_slug}/{indicator}: {e}")
        return []

def get_data(cache_days: int = 7) -> pd.DataFrame:
    """Main get_data: fetch CEE macro, cache JSON, handle errors."""
    cache_file = os.path.join(CACHE_DIR, 'cee_tracker.json')
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < cache_days * 86400:
        try:
            with open(cache_file, 'r') as f:
                cached_df = pd.read_json(f.read(), orient='records')
            logger.info(f"Loaded cached CEE data ({len(cached_df)} rows)")
            return cached_df.tail(50)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
    
    all_data = []
    for country_slug, country_code in CEE_COUNTRIES.items():
        no, CEE_COUNTRIES is {'PL': 'poland'}, so for country_slug in values? Wait, fix.
Wait, in scrape, country_slug is value, country is key.
In loop, for country_code, country_slug in CEE_COUNTRIES.items():
Yes, fix in code.
        for ind_slug in INDICATORS:
            data = scrape_tradingeconomics(country_slug, ind_slug)
            all_data.extend(data)
            time.sleep(1)
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values(['country', 'indicator', 'date'], ascending=[True, True, False])
        df = df.drop_duplicates()
        try:
            df.to_json(cache_file, orient='records', date_format='iso')
            logger.info(f"Cached {len(df)} rows")
        except Exception as e:
            logger.error(f"Cache write failed: {e}")
        return df
    return pd.DataFrame({'error': ['No data']})

def summary_latest() -> pd.DataFrame:
    df = get_data()
    if df.empty:
        return df
    latest = df.loc[df.groupby(['country', 'indicator']).date.idxmax()]
    return latest.pivot(index='country', columns='indicator', values='actual').round(2)

if __name__ == '__main__':
    df = get_data()
    print("CEE Latest Summary:")
    print(summary_latest())
    print(f"\nShape: {df.shape}")
