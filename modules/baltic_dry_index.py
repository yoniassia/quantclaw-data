#!/usr/bin/env python3
"""baltic_dry_index — Baltic Dry Index. Scrape investing.com or FRED alt. Free."""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from datetime import datetime
import re
import json

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="BDI", **kwargs):
    """
    Scrape Baltic Dry Index current and historical.
    Returns df date, value, change.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                return pd.DataFrame(json.load(f))
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        url = "https://www.investing.com/indices/baltic-dry"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Current price
        price_el = soup.find('span', {'id': 'last_last'})
        current = float(re.findall(r'[\d,]+', price_el.text)[0].replace(',', '')) if price_el else 0
        change_el = soup.find('span', {'id': 'last_change'})
        change = change_el.text.strip() if change_el else '0'
        # Historical table
        hist_table = soup.find('table', {'id': 'curr_table'})
        rows = hist_table.find_all('tr')[1:26] if hist_table else []
        data = []
        data.append({'date': datetime.now().strftime('%Y-%m-%d'), 'value': current, 'change': change, 'type': 'current'})
        for row in rows:
            cols = [td.text.strip() for td in row.find_all('td')]
            if len(cols) >= 3:
                data.append({'date': cols[0], 'value': float(cols[1].replace(',', '')), 'change': cols[2]})
        df = pd.DataFrame(data)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['fetch_time'] = datetime.now().isoformat()
        with open(cache_file, 'w') as f:
            json.dump(df.to_dict('records'), f)
        return df.sort_values('date', ascending=False).head(30)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BDI"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
