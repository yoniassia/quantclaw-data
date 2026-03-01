#!/usr/bin/env python3
"""
insider_sentiment_score.py - Aggregate insider buy/sell ratio from OpenInsider data.

Fetches latest insider buying and selling data from OpenInsider.com,
aggregates buy/sell transactions by date, computes sentiment score as
(buy_value - sell_value) / (buy_value + sell_value) clipped to [-1,1].

Returns DataFrame with columns: date, sentiment_score, buy_ratio, net_value.

Cache: JSON, 24h expiry.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import os
import logging
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL_BUY = "http://openinsider.com/latest-insider-buying"
BASE_URL_SELL = "http://openinsider.com/latest-insider-selling"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "insider_sentiment.json"
CACHE_EXPIRY_HOURS = 24
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
NUM_ROWS = 200  # Number of recent trades to fetch

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
        
        df = pd.read_json(cache_data['df_json'], orient='split')
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
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

def parse_table(soup: BeautifulSoup) -> pd.DataFrame:
    """Parse insider trades table from soup."""
    table = soup.find('table')
    if not table:
        raise ValueError("No table found")
    
    rows = table.find_all('tr')
    data = []
    for row in rows[1:NUM_ROWS+1]:  # Skip header, limit rows
        cols = row.find_all(['td', 'th'])
        if len(cols) > 10:
            text_data = [col.get_text(strip=True) for col in cols]
            data.append(text_data)
    
    if not data:
        raise ValueError("No data rows parsed")
    
    # Define columns based on OpenInsider structure (adjust if needed)
    columns = [
        'filing_date', 'trade_date', 'ticker', 'name', 'title',
        'trade_type', 'owner_type', 'shares', 'price', 'value',
        'ratio', 'pct_change', 'insider_cluster'
    ][:len(data[0])]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Clean and parse
    df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
    df = df.dropna(subset=['trade_date'])
    
    df['shares'] = df['shares'].astype(str).str.replace(',', '').str.replace('K', 'e3').str.replace('M', 'e6')
    df['shares'] = pd.to_numeric(df['shares'], errors='coerce')
    
    df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(',', ''), errors='coerce')
    df['value'] = pd.to_numeric(df['value'].astype(str).str.replace(',', '').str.replace('K', 'e3'), errors='coerce')
    
    df['is_buy'] = df['trade_type'].str.contains('Buy', case=False, na=False)
    
    logger.info(f"Parsed {len(df)} trades")
    return df

def fetch_insider_trades(trade_type: str = 'buy') -> pd.DataFrame:
    """Fetch insider trades for buy or sell."""
    url = BASE_URL_BUY if trade_type == 'buy' else BASE_URL_SELL
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            df = parse_table(soup)
            df['trade_type'] = trade_type
            return df
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {trade_type}: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {trade_type} trades after {max_retries} attempts")

def compute_sentiment(df_buy: pd.DataFrame, df_sell: pd.DataFrame) -> pd.DataFrame:
    """Compute daily sentiment score."""
    # Combine
    df_all = pd.concat([df_buy, df_sell], ignore_index=True)
    
    # Daily aggregates
    daily = df_all.groupby('trade_date').agg({
        'value': ['sum', 'count'],
        'shares': ['sum'],
        'ticker': 'nunique'
    }).round(2)
    
    daily.columns = ['total_value', 'num_trades', 'total_shares', 'unique_tickers']
    
    # Separate buy/sell value
    daily_buy = df_buy.groupby('trade_date')['value'].sum().rename('buy_value')
    daily_sell = df_sell.groupby('trade_date')['value'].sum().rename('sell_value')
    
    daily = daily.join([daily_buy, daily_sell], how='left').fillna(0)
    
    # Sentiment score: (buy - sell) / (buy + sell)
    total_value = daily['buy_value'] + daily['sell_value']
    daily['sentiment_score'] = np.where(
        total_value > 0,
        (daily['buy_value'] - daily['sell_value']) / total_value,
        0
    )
    
    # Buy ratio
    daily['buy_ratio'] = daily['buy_value'] / (daily['buy_value'] + daily['sell_value']).replace(0, np.nan)
    
    daily['net_value'] = daily['buy_value'] - daily['sell_value']
    
    # Sort and clip score, last 30 days
    daily = daily.sort_index().tail(30)
    daily['sentiment_score'] = np.clip(daily['sentiment_score'], -1, 1)
    
    logger.info(f"Computed sentiment for {len(daily)} days")
    return daily.reset_index(names='date')

def get_data() -> pd.DataFrame:
    """
    Get insider sentiment score DataFrame.
    
    Columns: date, sentiment_score, buy_ratio, net_value, total_value, num_trades, ...
    Index: None (reset)
    """
    cached_df = load_cache()
    if cached_df is not None and not cached_df.empty:
        return cached_df
    
    try:
        logger.info("Fetching insider buy data...")
        df_buy = fetch_insider_trades('buy')
        
        logger.info("Fetching insider sell data...")
        df_sell = fetch_insider_trades('sell')
        
        df_result = compute_sentiment(df_buy, df_sell)
        
        if df_result.empty:
            raise ValueError("Result DataFrame is empty")
        
        # Validation
        assert 'sentiment_score' in df_result.columns
        assert len(df_result) > 0
        
        save_cache(df_result)
        return df_result
    except Exception as e:
        logger.error(f"Error fetching/processing data: {str(e)}")
        # Fallback: empty DF with columns
        fallback = pd.DataFrame({
            'date': [datetime.now().date()],
            'sentiment_score': [0.0],
            'buy_ratio': [np.nan]
        })
        return fallback

if __name__ == "__main__":
    df = get_data()
    print(df.tail())
    print(f"\nShape: {df.shape}")
    print(df.dtypes)
