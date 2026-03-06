#!/usr/bin/env python3
"""
india_macro.py - India GDP/CPI from FRED/RBI.

Series: MKTGDPINA646NWDB (GDP), INDCPIALLMINMEI (CPI), INDPRO (Industrial Production).

Returns DF: date, gdp_yoy, cpi_yoy, ipi_yoy.

Cache.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import requests
import io

SERIES = {
    'gdp': 'MKTGDPINA646NWDB',
    'cpi': 'INDCPIALLMINMEI',
    'ipi': 'INDPRO'
}
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_FILE = CACHE_DIR / 'india_macro.json'

CACHE_DIR.mkdir(exist_ok=True)

def load_cache():
    if not CACHE_FILE.exists():
        return None
    import os
    mtime = datetime.fromtimestamp(os.stat(CACHE_FILE).st_mtime)
    if datetime.now() - mtime > timedelta(hours=24):
        return None
    with open(CACHE_FILE, 'r') as f:
        data = json.load(f)
    df = pd.read_json(data['df_json'], orient='split')
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df.set_index('DATE')

def save_cache(df):
    data = {'df_json': df.reset_index().to_json(orient='split')}
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def fetch_data():
    dfs = []
    for name, sid in SERIES.items():
        try:
            url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}'
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            raw_df = pd.read_csv(io.StringIO(resp.text))
            date_col = [c for c in raw_df.columns if 'date' in c.lower()][0]
            raw_df = raw_df.rename(columns={date_col: 'DATE'})
            raw_df['DATE'] = pd.to_datetime(raw_df['DATE'])
            raw_df = raw_df.set_index('DATE')
            raw_df[name] = pd.to_numeric(raw_df[sid], errors='coerce')
            dfs.append(raw_df[[name]])
        except Exception as e:
            print(f"Failed {sid}: {e}")
    if not dfs:
        raise ValueError("No data")
    df = pd.concat(dfs, axis=1).ffill().dropna()
    for name in SERIES:
        df[f'{name}_yoy'] = df[name].pct_change(4) * 100  # Quarterly approx
    return df.dropna()

def get_data():
    cached = load_cache()
    if cached is not None:
        return cached
    result = fetch_data()
    save_cache(result)
    return result.tail(40)

if __name__ == '__main__':
    print(get_data())
