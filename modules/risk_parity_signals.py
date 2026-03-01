#!/usr/bin/env python3
"""
risk_parity_signals.py - Risk parity weights using volatility inverse from Yahoo Finance.

Assets: SPY (equity), TLT (bonds), GLD (gold), USO (oil).
Computes rolling 60-day annualized volatility, inverse vol weights.
Weights sum to 1.

Returns DataFrame: date index, columns: weight_SPY, weight_TLT, weight_GLD, weight_USO, vol_SPY, etc.

Cache: JSON, 24h expiry.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import os
import logging
from typing import Optional
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TICKERS = ['SPY', 'TLT', 'GLD', 'USO']
ROLLING_WINDOW = 60
ANNUALIZATION = np.sqrt(252)
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "risk_parity.json"
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache() -> Optional[pd.DataFrame]:
    """Load cached DataFrame if not expired."""
    if not CACHE_FILE.exists():
        logger.info("No cache file found.")
        return None
    
    try:
        stat = CACHE_FILE.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRY_HOURS):
            logger.info("Cache expired.")
            return None
        
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        df = pd.read_json(cache_data['df_json'], orient='split', date_format='iso')
        df.index = pd.to_datetime(df.index)
        logger.info(f"Loaded cache: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error loading cache: {e}")
        return None

def save_cache(df: pd.DataFrame):
    """Save DataFrame to JSON cache."""
    try:
        df_reset = df.reset_index()
        cache_data = {
            'df_json': df_reset.to_json(orient='split', date_format='iso'),
            'timestamp': datetime.now().isoformat()
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Saved cache: {len(df)} rows")
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def fetch_prices() -> pd.DataFrame:
    """Fetch adjusted close prices from Yahoo Finance."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = yf.download(TICKERS, period='2y', progress=False)['Adj Close']
            if data.isna().all().all():
                raise ValueError("All data NaN")
            data = data.dropna()
            logger.info(f"Fetched prices: {data.shape}")
            return data
        except Exception as e:
            logger.warning(f"Download attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(5)
    raise RuntimeError("Failed to fetch prices after retries")

def compute_risk_parity_weights(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute inverse volatility weights."""
    returns = prices.pct_change().dropna()
    
    # Rolling volatility
    vols = returns.rolling(window=ROLLING_WINDOW).std() * ANNUALIZATION
    
    # Inverse vols, forward fill
    inv_vols = (1 / vols).fillna(method='ffill').fillna(0)
    
    # Normalize weights
    weights = inv_vols.div(inv_vols.sum(axis=1), axis=0)
    
    # Combine vols and weights
    result = pd.concat([vols, weights], axis=1, keys=['vol', 'weight'])
    result.columns = [f"{col[1]}_{col[0]}" for col in result.columns]
    result = result.dropna()
    
    # Add sum check
    result['weight_sum'] = weights.sum(axis=1)
    
    logger.info(f"Computed weights: {len(result)} rows")
    return result

def get_data() -> pd.DataFrame:
    """
    Get risk parity signals DataFrame.
    
    Columns: vol_SPY, vol_TLT, ..., weight_SPY, weight_TLT, ..., weight_sum
    """
    cached_df = load_cache()
    if cached_df is not None and not cached_df.empty:
        return cached_df
    
    try:
        prices = fetch_prices()
        df_result = compute_risk_parity_weights(prices)
        
        if df_result.empty:
            raise ValueError("Result DataFrame is empty")
        
        # Validation
        weight_cols = [col for col in df_result.columns if col.startswith('weight_')]
        assert len(weight_cols) == len(TICKERS)
        assert (df_result['weight_sum'] - 1).abs().max() < 0.01
        
        save_cache(df_result)
        return df_result
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}")
        # Fallback
        fallback = pd.DataFrame(index=pd.date_range('2023-01-01', periods=5, freq='D'),
                                columns=[f'weight_{t}' for t in TICKERS] + ['weight_sum'])
        fallback.iloc[:] = 0.25
        fallback['weight_sum'] = 1.0
        return fallback

if __name__ == "__main__":
    df = get_data()
    print(df.tail())
    print(f"\nShape: {df.shape}")
    print(df.describe())
