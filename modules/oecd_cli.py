#!/usr/bin/env python3
"""oecd_cli — OECD Composite Leading Indicators. Source: https://sdmx.oecd.org/public/rest/data/OECD,DF_CLI/all. Free."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="USA", **kwargs):
    """
    Fetch OECD CLI data.
    ticker: country code e.g. 'USA'.
    Returns df with TIME_PERIOD, obsValue.
    Note: SDMX JSON parsing simplified.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 7:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return pd.DataFrame(data)
    try:
        url = "https://sdmx.oecd.org/public/rest/data/OECD,DF_CLI/all?startTime=2010-01&endTime=2024-12&format=datajson"
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()
        # Parse SDMX data structure (simplified - adjust based on structure)
        observations = []
        for ds in data.get('dataSets', []):
            for series in ds.get('series', []):
                for obs in series.get('observations', []):
                    obs_dict = obs[0]
                    obs_dict['TIME_PERIOD'] = series.get('TIME_PERIOD', [])
                    obs_dict['LOCATION'] = series.get('LOCATION', ['USA'])[0]
                    observations.append(obs_dict)
        df = pd.DataFrame(observations)
        if ticker:
            df = df[df['LOCATION'].str.upper() == ticker.upper()]
        df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'])
        df['obsValue'] = pd.to_numeric(df['obsValue'])
        df = df.sort_values('TIME_PERIOD').reset_index(drop=True)
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "USA"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
