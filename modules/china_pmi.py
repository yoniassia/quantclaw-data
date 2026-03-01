#!/usr/bin/env python3
"""china_pmi — China Caixin/NBS PMI. Scrape tradingeconomics. Free."""
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

def get_data(ticker="Manufacturing", **kwargs):
    """
    Scrape China PMI data.
    ticker: 'Manufacturing', 'Services'.
    Returns df date, actual, previous, consensus.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                return pd.DataFrame(json.load(f))
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        base_url = "https://tradingeconomics.com/china/"
        url = base_url + ticker.lower().replace(' ', '-') + "-pmi"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Current value
        value_el = soup.find('span', class_='float-big')
        current = float(value_el.text.strip()) if value_el else 0
        # Table historical
        table = soup.find('table', class_='table')
        rows = table.find_all('tr')[:10] if table else []
        data = [{'date': datetime.now().strftime('%Y-%m-%d'), 'pmi': current, 'type': ticker}]
        for row in rows:
            cols = [td.text.strip() for td in row.find_all('td')]
            if len(cols) >= 4:
                data.append({'date': cols[0], 'actual': float(cols[1]), 'previous': float(cols[2]), 'consensus': float(cols[3])})
        df = pd.DataFrame(data)
        df['fetch_time'] = datetime.now().isoformat()
        with open(cache_file, 'w') as f:
            json.dump(df.to_dict('records'), f)
        return df.tail(12)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "Manufacturing"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
