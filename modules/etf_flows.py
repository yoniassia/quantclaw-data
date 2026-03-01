#!/usr/bin/env python3
"""etf_flows — ETF fund flows from etfdb.com. Scraping. Free."""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from datetime import datetime
import re

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker=None, **kwargs):
    """
    Scrape ETF flows table.
    ticker: filter symbol.
    Returns df top ETF flows.
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
        url = "https://etfdb.com/etfs/flows/"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'etf-flows-table'}) or soup.find('table', class_='table-flows')
        rows = table.find_all('tr')[1:26]  # top 25
        data = []
        for row in rows:
            cols = row.find_all(['td', 'th'])
            symbol = cols[0].text.strip()
            if ticker and ticker not in symbol:
                continue
            flow_1d = re.findall(r'[\d,.-]+', cols[2].text)[0] if len(cols)>2 else '0'
            flow_5d = re.findall(r'[\d,.-]+', cols[3].text)[0] if len(cols)>3 else '0'
            aum = re.findall(r'[\d,.-]+', cols[4].text)[0] if len(cols)>4 else '0'
            data.append({'symbol': symbol, 'flow_1d': flow_1d, 'flow_5d': flow_5d, 'aum': aum})
        df = pd.DataFrame(data)
        df[['flow_1d', 'flow_5d', 'aum']] = df[['flow_1d', 'flow_5d', 'aum']].apply(pd.to_numeric, errors='coerce')
        df['fetch_time'] = datetime.now().isoformat()
        with open(cache_file, 'w') as f:
            json.dump(df.to_dict('records'), f)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else None
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
