#!/usr/bin/env python3
"""
FRED Bond Series API — Corporate, Credit, and Municipal Bond Data

Specialized FRED module focused on bond market time series:
- Corporate bond yields (BAA, AAA corporate spreads)
- High-yield credit spreads (ICE BofA indices)
- Municipal bond yields
- Mortgage-backed securities rates
- Investment grade vs high yield spread dynamics
- Credit default swap proxies

Source: https://fred.stlouisfed.org/docs/api/fred.html
Category: Fixed Income & Credit
Update frequency: Daily

Use cases:
- Credit risk analysis
- Fixed income portfolio management
- Corporate bond spread monitoring
- Municipal bond market analysis
- High-yield market sentiment tracking

Author: QuantClaw Data — NightBuilder
"""

import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json

# Load environment variables
load_dotenv()

# Configuration
CACHE_DIR = Path(__file__).parent.parent / "cache" / "fred_bond_series"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Bond series registry
BOND_SERIES = {
    # Corporate Bond Yields
    'AAA': 'Moody\'s Seasoned AAA Corporate Bond Yield',
    'BAA': 'Moody\'s Seasoned BAA Corporate Bond Yield',
    'BAA10Y': 'BAA Corporate Bond Yield Relative to 10-Year Treasury',
    
    # High-Yield Credit Spreads (ICE BofA indices)
    'BAMLH0A0HYM2': 'ICE BofA US High Yield Index Option-Adjusted Spread',
    'BAMLC0A0CM': 'ICE BofA US Corporate Index Option-Adjusted Spread',
    'BAMLC0A4CBBB': 'ICE BofA BBB US Corporate Index Option-Adjusted Spread',
    
    # Municipal Bonds
    'MMUAA10Y': 'Muni AAA 10-Year Yield',
    'MMUBB10Y': 'Muni BBB 10-Year Yield',
    
    # Mortgage-Backed Securities
    'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average',
    'MORTGAGE15US': '15-Year Fixed Rate Mortgage Average',
    'MORTGAGE5US': '5/1-Year Adjustable Rate Mortgage Average',
    
    # Treasury Benchmarks (for spread calculation)
    'DGS10': '10-Year Treasury Constant Maturity Rate',
    'DGS2': '2-Year Treasury Constant Maturity Rate',
}


def _fetch_fred_series(series_id: str, use_cache: bool = True, days_back: int = 365) -> Optional[pd.DataFrame]:
    """
    Internal function to fetch a FRED series with caching.
    
    Args:
        series_id: FRED series identifier
        use_cache: Whether to use cached data (24hr TTL)
        days_back: Number of days of historical data to fetch
    
    Returns:
        DataFrame with date index and value column, or None on error
    """
    if not FRED_API_KEY:
        print("Warning: FRED_API_KEY not set in environment")
        return None
    
    cache_path = CACHE_DIR / f"{series_id}_latest.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    df = pd.DataFrame(data)
                    if not df.empty:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                        return df
            except Exception as e:
                print(f"Cache read error for {series_id}: {e}")
    
    # Fetch from FRED API
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    url = f"{BASE_URL}/series/observations"
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'observation_start': start_date.strftime('%Y-%m-%d'),
        'observation_end': end_date.strftime('%Y-%m-%d')
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' not in data:
            return None
        
        observations = data['observations']
        if not observations:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(observations)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df = df[['date', 'value']].dropna()
        
        # Cache the data
        cache_data = df.to_dict('records')
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2, default=str)
        
        df = df.set_index('date')
        return df
        
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}")
        return None


def get_corporate_bond_yields(use_cache: bool = True) -> Dict[str, any]:
    """
    Get corporate bond yields (AAA, BAA) and spread over Treasuries.
    
    Returns:
        Dict with latest_date, aaa_yield, baa_yield, baa_spread, quality_spread (BAA-AAA)
    """
    aaa_df = _fetch_fred_series('AAA', use_cache=use_cache)
    baa_df = _fetch_fred_series('BAA', use_cache=use_cache)
    spread_df = _fetch_fred_series('BAA10Y', use_cache=use_cache)
    
    result = {
        'latest_date': None,
        'aaa_yield': None,
        'baa_yield': None,
        'baa_spread': None,
        'quality_spread': None,
        'data_available': False
    }
    
    try:
        if aaa_df is not None and not aaa_df.empty:
            result['aaa_yield'] = float(aaa_df['value'].iloc[-1])
            result['latest_date'] = str(aaa_df.index[-1].date())
        
        if baa_df is not None and not baa_df.empty:
            result['baa_yield'] = float(baa_df['value'].iloc[-1])
            if not result['latest_date']:
                result['latest_date'] = str(baa_df.index[-1].date())
        
        if spread_df is not None and not spread_df.empty:
            result['baa_spread'] = float(spread_df['value'].iloc[-1])
        
        # Calculate quality spread (BAA - AAA)
        if result['aaa_yield'] is not None and result['baa_yield'] is not None:
            result['quality_spread'] = round(result['baa_yield'] - result['aaa_yield'], 2)
        
        result['data_available'] = result['latest_date'] is not None
        
    except Exception as e:
        print(f"Error processing corporate bond yields: {e}")
    
    return result


def get_credit_spreads(use_cache: bool = True) -> Dict[str, any]:
    """
    Get high-yield and investment-grade credit spreads from ICE BofA indices.
    
    Returns:
        Dict with latest_date, high_yield_spread, investment_grade_spread, bbb_spread
    """
    hy_df = _fetch_fred_series('BAMLH0A0HYM2', use_cache=use_cache)  # High Yield OAS
    ig_df = _fetch_fred_series('BAMLC0A0CM', use_cache=use_cache)    # IG Corporate OAS
    bbb_df = _fetch_fred_series('BAMLC0A4CBBB', use_cache=use_cache) # BBB OAS
    
    result = {
        'latest_date': None,
        'high_yield_spread': None,
        'investment_grade_spread': None,
        'bbb_spread': None,
        'data_available': False
    }
    
    try:
        if hy_df is not None and not hy_df.empty:
            result['high_yield_spread'] = float(hy_df['value'].iloc[-1])
            result['latest_date'] = str(hy_df.index[-1].date())
        
        if ig_df is not None and not ig_df.empty:
            result['investment_grade_spread'] = float(ig_df['value'].iloc[-1])
            if not result['latest_date']:
                result['latest_date'] = str(ig_df.index[-1].date())
        
        if bbb_df is not None and not bbb_df.empty:
            result['bbb_spread'] = float(bbb_df['value'].iloc[-1])
        
        result['data_available'] = result['latest_date'] is not None
        
    except Exception as e:
        print(f"Error processing credit spreads: {e}")
    
    return result


def get_muni_yields(use_cache: bool = True) -> Dict[str, any]:
    """
    Get municipal bond yields for AAA and BBB rated bonds (10-year maturity).
    
    Returns:
        Dict with latest_date, muni_aaa_10y, muni_bbb_10y, muni_quality_spread
    """
    aaa_df = _fetch_fred_series('MMUAA10Y', use_cache=use_cache)
    bbb_df = _fetch_fred_series('MMUBB10Y', use_cache=use_cache)
    
    result = {
        'latest_date': None,
        'muni_aaa_10y': None,
        'muni_bbb_10y': None,
        'muni_quality_spread': None,
        'data_available': False
    }
    
    try:
        if aaa_df is not None and not aaa_df.empty:
            result['muni_aaa_10y'] = float(aaa_df['value'].iloc[-1])
            result['latest_date'] = str(aaa_df.index[-1].date())
        
        if bbb_df is not None and not bbb_df.empty:
            result['muni_bbb_10y'] = float(bbb_df['value'].iloc[-1])
            if not result['latest_date']:
                result['latest_date'] = str(bbb_df.index[-1].date())
        
        # Calculate quality spread
        if result['muni_aaa_10y'] is not None and result['muni_bbb_10y'] is not None:
            result['muni_quality_spread'] = round(result['muni_bbb_10y'] - result['muni_aaa_10y'], 2)
        
        result['data_available'] = result['latest_date'] is not None
        
    except Exception as e:
        print(f"Error processing municipal yields: {e}")
    
    return result


def get_mbs_rates(use_cache: bool = True) -> Dict[str, any]:
    """
    Get mortgage-backed securities rates (30-year, 15-year, 5/1 ARM).
    
    Returns:
        Dict with latest_date, mortgage_30y, mortgage_15y, mortgage_5y_arm
    """
    m30_df = _fetch_fred_series('MORTGAGE30US', use_cache=use_cache)
    m15_df = _fetch_fred_series('MORTGAGE15US', use_cache=use_cache)
    m5_df = _fetch_fred_series('MORTGAGE5US', use_cache=use_cache)
    
    result = {
        'latest_date': None,
        'mortgage_30y': None,
        'mortgage_15y': None,
        'mortgage_5y_arm': None,
        'data_available': False
    }
    
    try:
        if m30_df is not None and not m30_df.empty:
            result['mortgage_30y'] = float(m30_df['value'].iloc[-1])
            result['latest_date'] = str(m30_df.index[-1].date())
        
        if m15_df is not None and not m15_df.empty:
            result['mortgage_15y'] = float(m15_df['value'].iloc[-1])
            if not result['latest_date']:
                result['latest_date'] = str(m15_df.index[-1].date())
        
        if m5_df is not None and not m5_df.empty:
            result['mortgage_5y_arm'] = float(m5_df['value'].iloc[-1])
        
        result['data_available'] = result['latest_date'] is not None
        
    except Exception as e:
        print(f"Error processing MBS rates: {e}")
    
    return result


def get_hy_ig_spread_history(days_back: int = 365, use_cache: bool = True) -> pd.DataFrame:
    """
    Get historical high-yield vs investment-grade spread dynamics.
    
    Args:
        days_back: Number of days of history to fetch
        use_cache: Whether to use cached data
    
    Returns:
        DataFrame with date index and columns: hy_spread, ig_spread, hy_ig_differential
    """
    hy_df = _fetch_fred_series('BAMLH0A0HYM2', use_cache=use_cache, days_back=days_back)
    ig_df = _fetch_fred_series('BAMLC0A0CM', use_cache=use_cache, days_back=days_back)
    
    if hy_df is None or ig_df is None or hy_df.empty or ig_df.empty:
        return pd.DataFrame()
    
    try:
        # Merge on date
        merged = pd.merge(
            hy_df.rename(columns={'value': 'hy_spread'}),
            ig_df.rename(columns={'value': 'ig_spread'}),
            left_index=True,
            right_index=True,
            how='inner'
        )
        
        # Calculate differential
        merged['hy_ig_differential'] = merged['hy_spread'] - merged['ig_spread']
        
        return merged
        
    except Exception as e:
        print(f"Error processing HY/IG spread history: {e}")
        return pd.DataFrame()


def get_bond_market_dashboard(use_cache: bool = True) -> Dict[str, any]:
    """
    Comprehensive bond market dashboard with all key metrics.
    
    Returns:
        Dict containing corporate yields, credit spreads, muni yields, and MBS rates
    """
    dashboard = {
        'timestamp': datetime.now().isoformat(),
        'corporate_bonds': get_corporate_bond_yields(use_cache=use_cache),
        'credit_spreads': get_credit_spreads(use_cache=use_cache),
        'municipal_bonds': get_muni_yields(use_cache=use_cache),
        'mortgage_rates': get_mbs_rates(use_cache=use_cache)
    }
    
    # Add market stress indicator
    credit = dashboard['credit_spreads']
    if credit['high_yield_spread'] is not None:
        hy_spread = credit['high_yield_spread']
        if hy_spread > 800:
            stress_level = "SEVERE"
        elif hy_spread > 600:
            stress_level = "ELEVATED"
        elif hy_spread > 400:
            stress_level = "MODERATE"
        else:
            stress_level = "LOW"
        
        dashboard['market_stress_indicator'] = {
            'level': stress_level,
            'hy_spread_bps': hy_spread
        }
    
    return dashboard


if __name__ == "__main__":
    print("FRED Bond Series API Module")
    print("=" * 50)
    
    # Test all functions
    print("\n1. Corporate Bond Yields:")
    corp = get_corporate_bond_yields()
    print(json.dumps(corp, indent=2))
    
    print("\n2. Credit Spreads:")
    credit = get_credit_spreads()
    print(json.dumps(credit, indent=2))
    
    print("\n3. Municipal Yields:")
    muni = get_muni_yields()
    print(json.dumps(muni, indent=2))
    
    print("\n4. MBS Rates:")
    mbs = get_mbs_rates()
    print(json.dumps(mbs, indent=2))
    
    print("\n5. Bond Market Dashboard:")
    dashboard = get_bond_market_dashboard()
    print(json.dumps(dashboard, indent=2, default=str))
