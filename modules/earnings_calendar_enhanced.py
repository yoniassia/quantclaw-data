#!/usr/bin/env python3
"""earnings_calendar_enhanced — Yahoo earnings calendar. Requires yfinance. Free."""
import os
import time
from datetime import datetime
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_data(ticker="AAPL", **kwargs):
    """
    Fetch earnings dates and estimates.
    Returns df with Earnings Date, EPS Estimate, Reported EPS, Surprise %.
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{ticker}.json")
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:
            with open(cache_file, 'r') as f:
                return pd.DataFrame(json.load(f))
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates.tail(8)  # recent + future
        calendar = stock.calendar
        if earnings is not None and not earnings.empty:
            df = earnings.reset_index()
            df['fetch_time'] = datetime.now().isoformat()
        else:
            df = pd.DataFrame(calendar).T if calendar is not None else pd.DataFrame({"error": ["No data"]})
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            import json
            json.dump(cache_data, f, default=str)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

if __name__ == "__main__":
    import sys
    import json
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
