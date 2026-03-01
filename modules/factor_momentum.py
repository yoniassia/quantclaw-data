#!/usr/bin/env python3
"""factor_momentum — Fama-French factors. Source: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip. Free."""
import requests
import zipfile
import io
import os
import time
from datetime import datetime
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="daily", **kwargs):
    """
    Fetch Fama-French research data factors.
    ticker: 'daily', 'monthly'.
    Returns df with Mkt-RF, SMB, HML, RF, date.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.csv")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400 * 30:
            return pd.read_csv(cache_file, index_col='date', parse_dates=True)
    try:
        base_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        zip_file = "F-F_Research_Data_Factors_CSV.zip" if ticker == "daily" else "F-F_Research_Data_Factors_daily_CSV.zip"
        url = base_url + zip_file
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = [n for n in z.namelist() if n.endswith('.csv')][0]
        csv_data = z.read(csv_name).decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(csv_data), skiprows=3, skipinitialspace=True)
        df.columns = ['date', 'mkt_rf', 'smb', 'hml', 'rf']
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df.set_index('date', inplace=True)
        numeric_cols = df.columns
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df = df.dropna()
        df.to_csv(cache_file)
        df['fetch_time'] = datetime.now().isoformat()
        return df.tail(252)  # 1y
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "daily"
    result = get_data(ticker)
    print(result.reset_index().to_json(orient='records', date_format='iso'))
