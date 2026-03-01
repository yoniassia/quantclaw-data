#!/usr/bin/env python3
"""sector_rotation — Sector ETF performance/rotation. XLK,XLF etc. Requires yfinance. Free."""
import os
import time
from datetime import datetime
import pandas as pd
import yfinance as yf
import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="XLK", period="2y", **kwargs):
    """
    Sector ETF rotation signals.
    Returns df with returns, momentum, relative strength.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{period}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            df = pd.read_json(cache_file, orient='split')
            df.index = pd.to_datetime(df.index)
            return df
    etfs = ['XLK','XLF','XLE','XLV','XLI','XLP','XLU','XLB','XLC','XLRE','XLY']
    try:
        data = yf.download(etfs, period=period, progress=False)['Adj Close']
        returns = data.pct_change()
        momentum_1m = returns.rolling(21).mean().iloc[-1] * 100
        momentum_3m = returns.rolling(63).mean().iloc[-1] * 100
        momentum_6m = returns.rolling(126).mean().iloc[-1] * 100
        df = pd.DataFrame({
            'price': data.iloc[-1],
            'mom_1m': momentum_1m,
            'mom_3m': momentum_3m,
            'mom_6m': momentum_6m,
            'vol_20d': returns.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        }, index=etfs).sort_values('mom_6m', ascending=False)
        df['rank_mom'] = range(1, len(df)+1)
        df['fetch_time'] = datetime.now().isoformat()
        cache_data = df.to_json(orient='split')
        with open(cache_file, 'w') as f:
            f.write(cache_data)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "XLK"
    result = get_data(ticker)
    print(result.to_json())
