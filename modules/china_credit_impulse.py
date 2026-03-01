#!/usr/bin/env python3
"""china_credit_impulse.py — China credit impulse / TSF growth proxies from TradingEconomics & FRED.

Credit impulse = Δ(TSF yoy) — leading indicator for growth slowdowns.
Proxies:
- Loan growth YoY %
- M2 money supply growth YoY %
- Aggregate credit / GDP (FRED proxy if available)
- TSF growth (scrape if available)

Historical since 2010, compute impulse as yoy diff smoothed.
Cache: 7 days.
"""

import os
import time
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import numpy as np
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

INDICATORS = [
    'loan-growth',
    'money-supply-m2',
]

FRED_PROXIES = [
    'MKTGDPCHNAXQ',  # Credit to private sector % GDP China
]

def scrape_te_china(ind: str) -> pd.DataFrame:
    """Scrape TradingEconomics China indicator."""
    url = f"https://tradingeconomics.com/china/{ind}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', class_='table')
        data = []
        if table:
            rows = table.find_all('tr')[:24]  # 2y monthly
            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cols) >= 3:
                    data.append({
                        'date': cols[0],
                        'actual': float(re.sub(r'[^0-9.-]', '', cols[1])),
                        'previous': float(re.sub(r'[^0-9.-]', '', cols[2])) if cols[2] else np.nan,
                    })
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date', ascending=False).dropna(subset=['actual'])
        df['yoy_growth'] = df['actual']  # already yoy
        return df
    except Exception as e:
        logger.error(f"TE {ind}: {e}")
        return pd.DataFrame()

def fetch_fred_proxy(series: str) -> pd.DataFrame:
    """Fetch FRED CSV."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    try:
        df = pd.read_csv(url, parse_dates=['DATE'], index_col='DATE')
        df.columns = ['value']
        df['date'] = df.index
        df = df.reset_index(drop=True).tail(40)
        df['yoy_growth'] = df['value'].pct_change(4) * 100  # quarterly yoy approx
        return df[['date', 'yoy_growth']]
    except Exception as e:
        logger.error(f"FRED {series}: {e}")
        return pd.DataFrame()

def compute_impulse(df: pd.DataFrame) -> pd.DataFrame:
    """Compute credit impulse: smoothed Δ(yoy)."""
    if df.empty:
        return df
    df = df.sort_values('date')
    df['impulse'] = df['yoy_growth'].rolling(3, center=True).diff().fillna(0)
    df['signal'] = np.where(df['impulse'] > 0, 'expansion', 'contraction')
    return df

def get_data(cache_days: int = 7) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, 'china_credit.json')
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < cache_days * 86400:
        try:
            return pd.read_json(cache_file, orient='records')
        except:
            pass
    
    dfs = []
    for ind in INDICATORS:
        df = scrape_te_china(ind)
        if not df.empty:
            df['indicator'] = ind.title()
            dfs.append(df)
        time.sleep(1)
    
    for series in FRED_PROXIES:
        df = fetch_fred_proxy(series)
        if not df.empty:
            df['indicator'] = series
            dfs.append(df)
    
    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        df_all = compute_impulse(df_all)
        df_all['fetch_time'] = datetime.now().isoformat()
        df_all.to_json(cache_file, orient='records', date_format='iso')
        logger.info(f"China credit data: {len(df_all)} rows")
        return df_all.tail(50)
    return pd.DataFrame({'error': ['No data']})

def latest_impulse() -> Dict:
    df = get_data()
    if df.empty:
        return {}
    latest = df.tail(1)
    return {'latest_impulse': latest['impulse'].iloc[0], 'signal': latest['signal'].iloc[0]}

if __name__ == '__main__':
    df = get_data()
    print(latest_impulse())
    print(df.tail())
