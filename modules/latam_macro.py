#!/usr/bin/env python3
"""
latam_macro.py - LatAm macro (Brazil SELIC, Mexico rates) from FRED/BCB.

Brazil SELIC from BCB API, Mexico rate from FRED, Brazil CPI FRED.

Returns DF: date, brazil_selic, mexico_rate, brazil_cpi_yoy.

Cache.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import requests
import pandas_datareader.data as web

CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'latam_macro.json'
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRY_HOURS):
        return None
    with open(CACHE_FILE, 'r') as f:
        data = json.load(f)
    df = pd.read_json(data['df_json'], orient='split')
    df['date'] = pd.to_datetime(df['date'])
    return df

def fetch_brazil_selic():
    url = 'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&amp;dataInicial=01/01/2010'
    resp = requests.get(url)
    data = resp.json()
    df = pd.DataFrame(data)
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
    df['selic_pct'] = pd.to_numeric(df['valor'], errors='coerce')
    return df.set_index('data')[['selic_pct']].tail(500)

def fetch_mexico_rate():
    try:
        df = web.DataReader('INTGSTMXM193N', 'fred')
        return df.rename(columns={'INTGSTMXM193N': 'mexico_rate'})
    except:
        return pd.DataFrame()

def fetch_brazil_cpi():
    try:
        df = web.DataReader('BRACPIALLMINMEI', 'fred')
        df['cpi_yoy'] = df['BRACPIALLMINMEI'].pct_change(12) * 100
        return df[['cpi_yoy']]
    except:
        return pd.DataFrame()

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    try:
        selic = fetch_brazil_selic()
        mexico = fetch_mexico_rate()
        cpi = fetch_brazil_cpi()
        df = selic.join([mexico, cpi], how='outer').ffill()
        df.reset_index(names='date', inplace=True)
        # Save
        with open(CACHE_FILE, 'w') as f:
            json.dump({'df_json': df.to_json(orient='split')}, f)
        return df.tail(100)
    except Exception as e:
        print(e)
        return pd.DataFrame({'brazil_selic': [10.5]})

if __name__ == '__main__':
    print(get_data())
