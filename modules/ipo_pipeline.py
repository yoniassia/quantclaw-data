#!/usr/bin/env python3
"""ipo_pipeline — IPO calendar from SEC EDGAR S-1 filings. Free RSS."""
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
import time
from datetime import datetime
import json

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker=None, **kwargs):
    """
    Recent S-1 IPO filings.
    Returns df company, filing_date, link.
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
        url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=S-1&company=&dateb=&owner=include&start=0&count=40&output=atom"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        entries = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            company = title.split(' - ')[0] if ' - ' in title else title
            updated = entry.find('{http://www.w3.org/2005/Atom}updated').text[:10]
            link = entry.find('{http://www.w3.org/2005/Atom}link')['href']
            entries.append({'company': company, 'filing_date': updated, 'link': link})
        df = pd.DataFrame(entries)
        if ticker:
            df = df[df['company'].str.contains(ticker, case=False)]
        df['filing_date'] = pd.to_datetime(df['filing_date'])
        df = df.sort_values('filing_date', ascending=False).head(20)
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else None
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
