#!/usr/bin/env python3
"""bank_of_canada — Bank of Canada rates & FX data via Valet API. Free, no API key."""
import requests
import json
import os
import time
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_URL = 'https://www.bankofcanada.ca/valet'

SERIES = {
    'fx_rates': 'FX_RATES_DAILY',
    'policy_rate': 'V122530',
}

def get_data(ticker="fx_rates", limit=100, **kwargs):
    """
    Fetch Bank of Canada economic data.
    ticker: series name (fx_rates, policy_rate) or custom series code.
    limit: max rows to return.
    Returns pd.DataFrame with date and rate columns.
    """
    module_name = __name__.split('.')[-1]
    cache_key = ticker.lower().replace('/', '_')[:50]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{cache_key}.json")
    
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < 86400:  # 24h cache
            with open(cache_file, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                df['fetch_time'] = datetime.now().isoformat()
                return df.head(limit)
    
    series_code = SERIES.get(ticker, ticker)
    
    if series_code in ['FX_RATES_DAILY']:
        endpoint = f"{BASE_URL}/observations/group/{series_code}/json"
    else:
        endpoint = f"{BASE_URL}/observations/{series_code}/json"
    
    params = {'recent': min(limit, 365)}
    headers = {"User-Agent": "QuantClaw-Data/1.0"}
    
    try:
        resp = requests.get(endpoint, params=params, timeout=30, headers=headers)
        resp.raise_for_status()
        api_data = resp.json()
        
        observations = api_data.get('observations', [])
        if not observations:
            return pd.DataFrame({"error": ["No observations returned"]})
        
        # Flatten nested {"v": "value"} structure
        flattened = []
        for obs in observations:
            row = {'date': obs.get('d')}
            for key, val in obs.items():
                if key != 'd' and isinstance(val, dict):
                    row[key] = val.get('v')
                elif key != 'd':
                    row[key] = val
            flattened.append(row)
        
        df = pd.DataFrame(flattened)
        
        # Convert date
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Convert rate columns to numeric
        for col in df.columns:
            if col not in ['date', 'fetch_time']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date desc
        if 'date' in df.columns:
            df = df.sort_values('date', ascending=False).reset_index(drop=True)
        
        df['fetch_time'] = datetime.now().isoformat()
        
        # Cache
        cache_data = df.to_dict('records')
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        
        return df.head(limit)
        
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

def get_fx_rates(limit=100):
    """Get daily FX rates (CAD vs major currencies)."""
    return get_data(ticker='fx_rates', limit=limit)

def get_policy_rate(limit=100):
    """Get Bank of Canada overnight policy rate."""
    return get_data(ticker='policy_rate', limit=limit)

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "fx_rates"
    result = get_data(ticker)
    print(result.to_json(orient='records', date_format='iso'))
