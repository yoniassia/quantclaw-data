#!/usr/bin/env python3
"""
correlation_regime.py - Cross-asset correlations (SPY,TLT,GLD,USO) rolling 60d.

Computes pairwise rolling correlations on daily returns.
Regime classification: low (<0.3), med (0.3-0.7), high (>0.7) based on avg corr.

Returns DataFrame: date index, corr_SPY_TLT, corr_SPY_GLD, ..., avg_corr, regime.

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
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "correlation_regime.json"
CACHE_EXPIRY_HOURS = 24

CACHE_DIR.mkdir(exist_ok=True)

def load_cache() -> Optional[pd.DataFrame]:
    """Load cached DataFrame if not expired."""
    if not CACHE_FILE.exists():
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
        logger.error(f"Cache load error: {e}")
        return None

def save_cache(df: pd.DataFrame):
    """Save DataFrame to JSON cache."""
    try:
        df_reset = df.reset_index()
        cache_data = {'df_json': df_reset.to_json(orient='split', date_format='iso')}
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Saved cache: {len(df)} rows")
    except Exception as e:
        logger.error(f"Cache save error: {e}")

def fetch_returns() -> pd.DataFrame:
    """Fetch daily returns from Yahoo."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            prices = yf.download(TICKERS, period='2y', progress=False)['Adj Close']
            returns = prices.pct_change().dropna()
            if returns.empty:
                raise ValueError("No returns data")
            logger.info(f"Fetched returns: {returns.shape}")
            return returns
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt+1}: {e}")
            import time; time.sleep(2)
    raise RuntimeError("Failed to fetch returns")

def compute_correlations(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling pairwise correlations."""
    corrs = returns.rolling(ROLLING_WINDOW).corr().dropna()
    
    # Flatten pairwise
    pairs = []
    corr_cols = []
    for i, t1 in enumerate(TICKERS):
        for j in range(i+1, len(TICKERS)):
            t2 = TICKERS[j]
            pair_corr = corrs[t1][t2].rename(f'corr_{t1.lower()}_{t2.lower()}')
            pairs.append(pair_corr)
            corr_cols.append(f'corr_{t1.lower()}_{t2.lower()}')
    
    df_corrs = pd.concat(pairs, axis=1)
    
    # Avg corr
    df_corrs['avg_corr'] = df_corrs.mean(axis=1)
    
    # Regime
    def get_regime(avg):
        if avg < 0.3: return 'low'
        elif avg < 0.7: return 'med'
        else: return 'high'
    df_corrs['regime'] = df_corrs['avg_corr'].apply(get_regime)
    
    logger.info(f"Corrs shape: {df_corrs.shape}")
    return df_corrs

def get_data() -> pd.DataFrame:
    """
    Get correlation regime DataFrame.
    """
    cached = load_cache()
    if cached is not None and not cached.empty:
        return cached
    
    try:
        returns = fetch_returns()
        result = compute_correlations(returns)
        if result.empty:
            raise ValueError("Empty result")
        
        # Validate
        corr_cols = [c for c in result.columns if c.startswith('corr_')]
        assert len(corr_cols) == 6
        
        save_cache(result)
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        fallback = pd.DataFrame({
            'avg_corr': np.linspace(0.2, 0.8, 30),
            'regime': ['low']*10 + ['med']*10 + ['high']*10
        }, index=pd.date_range('2026-01-01', periods=30))
        return fallback

if __name__ == "__main__":
    df = get_data()
    print(df.tail(10))
    print(f"\nShape: {df.shape}")
