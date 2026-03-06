#!/usr/bin/env python3
"""
FRED API for Fixed Income Series
Fetch treasury yields, corporate bond spreads, mortgage rates, and more from FRED.

Source: https://fred.stlouisfed.org/docs/api/fred.html
Category: Fixed Income & Credit
Free tier: Completely free, no rate limits, API key optional but recommended
Update frequency: daily
Built by: NightBuilder
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://api.stlouisfed.org/fred"
API_KEY = os.environ.get("FRED_API_KEY", "")

# Common fixed income series
TREASURY_SERIES = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

CORPORATE_BOND_SERIES = {
    "AAA": "DAAA",
    "BAA": "DBAA",
    "BAA_SPREAD": "BAA10Y",
    "HIGH_YIELD": "BAMLH0A0HYM2",
}

MORTGAGE_SERIES = {
    "30Y_FIXED": "MORTGAGE30US",
    "15Y_FIXED": "MORTGAGE15US",
}


def get_series(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch a FRED series by ID.
    
    Args:
        series_id: FRED series identifier (e.g., 'DGS10')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional FRED API key (uses env var if not provided)
        
    Returns:
        DataFrame with date index and value column
    """
    url = f"{BASE_URL}/series/observations"
    params = {
        "series_id": series_id,
        "file_type": "json",
        "api_key": api_key or API_KEY or ""
    }
    
    if start_date:
        params["observation_start"] = start_date
    if end_date:
        params["observation_end"] = end_date
        
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "observations" not in data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data["observations"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[["date", "value"]].set_index("date")
        df.columns = [series_id]
        
        return df.dropna()
        
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return pd.DataFrame()


def get_treasury_curve(
    date: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, float]:
    """
    Get current treasury yield curve.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to latest)
        api_key: Optional FRED API key
        
    Returns:
        Dict mapping maturity to yield
    """
    if date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    else:
        start_date = date
        end_date = date
        
    curve = {}
    for maturity, series_id in TREASURY_SERIES.items():
        df = get_series(series_id, start_date, end_date, api_key)
        if not df.empty:
            curve[maturity] = float(df.iloc[-1].values[0])
            
    return curve


def get_corporate_spreads(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Get corporate bond yields and spreads.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional FRED API key
        
    Returns:
        DataFrame with corporate bond series
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
    dfs = []
    for name, series_id in CORPORATE_BOND_SERIES.items():
        df = get_series(series_id, start_date, end_date, api_key)
        if not df.empty:
            df.columns = [name]
            dfs.append(df)
            
    if dfs:
        return pd.concat(dfs, axis=1).sort_index()
    return pd.DataFrame()


def get_mortgage_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Get mortgage rates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional FRED API key
        
    Returns:
        DataFrame with mortgage rate series
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
    dfs = []
    for name, series_id in MORTGAGE_SERIES.items():
        df = get_series(series_id, start_date, end_date, api_key)
        if not df.empty:
            df.columns = [name]
            dfs.append(df)
            
    if dfs:
        return pd.concat(dfs, axis=1).sort_index()
    return pd.DataFrame()


def get_credit_spread(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate BAA-AAA credit spread.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional FRED API key
        
    Returns:
        DataFrame with spread
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
    baa = get_series("DBAA", start_date, end_date, api_key)
    aaa = get_series("DAAA", start_date, end_date, api_key)
    
    if not baa.empty and not aaa.empty:
        df = pd.concat([baa, aaa], axis=1)
        df.columns = ["BAA", "AAA"]
        df["BAA_AAA_SPREAD"] = df["BAA"] - df["AAA"]
        return df.dropna()
        
    return pd.DataFrame()


def get_multiple_series(
    series_ids: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch multiple FRED series at once.
    
    Args:
        series_ids: List of FRED series IDs
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional FRED API key
        
    Returns:
        DataFrame with all series
    """
    dfs = []
    for series_id in series_ids:
        df = get_series(series_id, start_date, end_date, api_key)
        if not df.empty:
            dfs.append(df)
            
    if dfs:
        return pd.concat(dfs, axis=1).sort_index()
    return pd.DataFrame()


if __name__ == "__main__":
    # Test the module
    print("=== Treasury Yield Curve ===")
    curve = get_treasury_curve()
    for maturity, yield_rate in sorted(curve.items(), key=lambda x: ["1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","20Y","30Y"].index(x[0]) if x[0] in ["1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","20Y","30Y"] else 99):
        print(f"{maturity}: {yield_rate:.2f}%")
    
    print(f"\n=== 10Y Treasury (last 7 days) ===")
    dgs10 = get_series("DGS10", start_date=(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"))
    if not dgs10.empty:
        print(dgs10.tail(5))
    
    print("\n=== Credit Spread (BAA-AAA) ===")
    credit = get_credit_spread(start_date=(datetime.now()-timedelta(days=30)).strftime("%Y-%m-%d"))
    if not credit.empty:
        latest = credit.iloc[-1]
        print(f"BAA: {latest['BAA']:.2f}%")
        print(f"AAA: {latest['AAA']:.2f}%")
        print(f"Spread: {latest['BAA_AAA_SPREAD']:.2f}%")
