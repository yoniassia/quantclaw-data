"""
Fed H.15 Selected Interest Rates — Daily Interest Rate Data

Tracks key market interest rates published daily by the Federal Reserve Board.
Data source: https://www.federalreserve.gov/releases/h15/

Use cases:
- Monitor Fed funds rate and policy rate targets
- Track Treasury yield curve (1mo - 30yr)
- Analyze credit spreads and money market rates
- Calculate yield curve steepness and inversions
- Monitor SOFR (Secured Overnight Financing Rate)

All data via FRED API (free tier)
"""

import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import json
import io
import csv

# Load environment variables
load_dotenv()

CACHE_DIR = Path(__file__).parent.parent / "cache" / "fed_h15"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# H.15 Series Mapping (FRED series IDs)
SERIES_MAP = {
    # Federal Funds
    'fed_funds': 'DFF',
    'fed_funds_target_upper': 'DFEDTARU',
    'fed_funds_target_lower': 'DFEDTARL',
    
    # Treasury Yields
    'treasury_1mo': 'DGS1MO',
    'treasury_3mo': 'DGS3MO',
    'treasury_6mo': 'DGS6MO',
    'treasury_1y': 'DGS1',
    'treasury_2y': 'DGS2',
    'treasury_3y': 'DGS3',
    'treasury_5y': 'DGS5',
    'treasury_7y': 'DGS7',
    'treasury_10y': 'DGS10',
    'treasury_20y': 'DGS20',
    'treasury_30y': 'DGS30',
    
    # SOFR
    'sofr': 'SOFR',
    
    # Prime Rate
    'bank_prime': 'DPRIME',
}


def _fetch_fred_series(series_id: str, days: int = 30, use_cache: bool = True) -> Optional[List[Dict]]:
    """Fetch a single FRED series with caching."""
    cache_path = CACHE_DIR / f"{series_id}_latest.json"
    
    # Check cache (valid for 6 hours)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=6):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
    
    # Fetch from FRED
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'sort_order': 'desc'
    }
    
    try:
        response = requests.get(FRED_BASE, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            return None
        
        observations = data['observations']
        
        # Cache the response
        with open(cache_path, 'w') as f:
            json.dump(observations, f, indent=2)
        
        return observations
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        # Try to return stale cache if available
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None


def get_latest_rates() -> Dict[str, Optional[float]]:
    """
    Get latest values for all key interest rates.
    
    Returns:
        dict: Latest rates with keys matching SERIES_MAP names
    """
    result = {}
    
    for name, series_id in SERIES_MAP.items():
        data = _fetch_fred_series(series_id, days=10)
        if data:
            # Find most recent non-null value
            for obs in data:
                if obs['value'] != '.':
                    try:
                        result[name] = float(obs['value'])
                        result[f"{name}_date"] = obs['date']
                        break
                    except ValueError:
                        continue
        
        if name not in result:
            result[name] = None
            result[f"{name}_date"] = None
    
    return result


def get_treasury_yields() -> Dict[str, Optional[float]]:
    """
    Get complete Treasury yield curve (1mo - 30yr).
    
    Returns:
        dict: Yield curve points with maturity as keys
    """
    treasury_keys = [k for k in SERIES_MAP.keys() if k.startswith('treasury_')]
    result = {}
    
    for name in treasury_keys:
        series_id = SERIES_MAP[name]
        data = _fetch_fred_series(series_id, days=10)
        
        if data:
            for obs in data:
                if obs['value'] != '.':
                    try:
                        maturity = name.replace('treasury_', '')
                        result[maturity] = float(obs['value'])
                        result[f"{maturity}_date"] = obs['date']
                        break
                    except ValueError:
                        continue
        
        if name.replace('treasury_', '') not in result:
            result[name.replace('treasury_', '')] = None
    
    return result


def get_rate_history(series: str = 'treasury_10y', days: int = 90) -> List[Dict[str, str]]:
    """
    Get historical data for a specific rate series.
    
    Args:
        series: Series name from SERIES_MAP keys (e.g., 'treasury_10y', 'fed_funds')
        days: Number of days of history to fetch
    
    Returns:
        list: Historical observations with 'date' and 'value' keys, sorted newest first
    """
    if series not in SERIES_MAP:
        return []
    
    series_id = SERIES_MAP[series]
    data = _fetch_fred_series(series_id, days=days, use_cache=False)
    
    if not data:
        return []
    
    # Filter out missing values and format
    history = []
    for obs in data:
        if obs['value'] != '.':
            try:
                history.append({
                    'date': obs['date'],
                    'value': float(obs['value'])
                })
            except ValueError:
                continue
    
    return history


def get_yield_spread(short: str = 'treasury_2y', long: str = 'treasury_10y') -> Optional[float]:
    """
    Calculate yield spread between two Treasury maturities.
    
    Args:
        short: Short-term maturity (e.g., 'treasury_2y')
        long: Long-term maturity (e.g., 'treasury_10y')
    
    Returns:
        float: Spread in basis points (long - short), or None if data unavailable
    """
    if short not in SERIES_MAP or long not in SERIES_MAP:
        return None
    
    rates = get_latest_rates()
    
    short_rate = rates.get(short)
    long_rate = rates.get(long)
    
    if short_rate is None or long_rate is None:
        return None
    
    # Return spread in basis points
    spread = (long_rate - short_rate) * 100
    return round(spread, 2)


def get_yield_curve_shape() -> Dict[str, any]:
    """
    Analyze current yield curve shape and inversions.
    
    Returns:
        dict: Curve analysis with slope, inversions, and key spreads
    """
    yields = get_treasury_yields()
    
    # Calculate key spreads
    spreads = {}
    spread_pairs = [
        ('2y', '10y'),
        ('3mo', '10y'),
        ('2y', '30y'),
        ('5y', '30y')
    ]
    
    for short, long in spread_pairs:
        short_val = yields.get(short)
        long_val = yields.get(long)
        if short_val is not None and long_val is not None:
            spread = (long_val - short_val) * 100
            spreads[f"{short}_{long}"] = round(spread, 2)
    
    # Determine curve shape
    slope_2_10 = spreads.get('2y_10y', 0)
    if slope_2_10 < 0:
        shape = "inverted"
    elif slope_2_10 < 25:
        shape = "flat"
    elif slope_2_10 < 100:
        shape = "normal"
    else:
        shape = "steep"
    
    return {
        'shape': shape,
        'spreads_bps': spreads,
        'yields': yields,
        'as_of': yields.get('10y_date', datetime.now().strftime('%Y-%m-%d'))
    }
