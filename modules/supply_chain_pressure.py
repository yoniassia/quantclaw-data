#!/usr/bin/env python3
"""supply_chain_pressure — NY Fed Global Supply Chain Pressure Index. Source: https://www.newyorkfed.org/research/gscpi. Free scrape."""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from datetime import datetime
import io
import json

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="GSCPI", **kwargs):
    """
    Fetch GSCPI index.
    Returns df with date, gscpi.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}.csv")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 7:
            return pd.read_csv(cache_file, parse_dates=['date'], index_col='date')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        url = "https://www.newyorkfed.org/research/gscpi"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find download link or table
        csv_link = soup.find('a', href=lambda h: h and 'csv' in h.lower())
        if csv_link:
            csv_url = 'https://www.newyorkfed.org' + csv_link['href']
            csv_resp = requests.get(csv_url, headers=headers)
            df = pd.read_csv(io.StringIO(csv_resp.text))
        else:
            # Fallback table parse (if available)
            table = soup.find('table')
            if table:
                df = pd.read_html(str(table))[0]
            else:
                df = pd.DataFrame({"error": ["No data found"]})
                return df
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        df['fetch_time'] = datetime.now().isoformat()
        df.to_csv(cache_file)
        return df.tail(60)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "GSCPI"
    result = get_data(ticker)
    print(result.reset_index().to_json(orient='records', date_format='iso'))
