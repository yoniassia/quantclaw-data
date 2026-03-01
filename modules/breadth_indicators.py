#!/usr/bin/env python3
"""breadth_indicators — Market breadth from Yahoo (^ADV, ^DEC, ^NH, ^NL). Requires yfinance. Free."""
import os
import time
from datetime import datetime
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="^ADV", period="3mo", **kwargs):
    """
    Fetch market breadth indicators.
    tickers: ^ADV advancing, ^DEC declining, ^NH new highs, ^NL new lows.
    Returns multiindex df Adj Close, plus net_advancers = ADV-DEC, mcad = NH-NL.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{period}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            df = pd.read_json(cache_file, orient='split')
            df.index = pd.to_datetime(df.index)
            df['fetch_time'] = datetime.now().isoformat()
            return df
    try:
        tickers = ['^ADV', '^DEC', '^NYHGH', '^NYLOW']  # NYSE: ^NYHGH ^NYLOW or ^NH ^NL NASDAQ
        if ticker in tickers:
            tickers = [ticker]
        data = yf.download(tickers, period=period, progress=False)['Adj Close']
        data.columns = [c.replace('Adj Close', '').strip() for c in data.columns]
        data['net_advancers'] = data['^ADV'] - data['^DEC']
        data['net_new_highs'] = data['^NYHGH'] - data['^NYLOW']
        data['adv_dec_ratio'] = data['^ADV'] / (data['^DEC'] + 1)
        data.dropna(inplace=True)
        data['fetch_time'] = datetime.now().isoformat()
        cache_data = data.reset_index().to_json(orient='split')
        with open(cache_file, 'w') as f:
            f.write(cache_data)
        return data
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "^ADV"
    result = get_data(ticker)
    print(result.to_json())
