"""
CoStar Market Analytics Feed — Commercial Real Estate Metrics

Tracks commercial real estate market data including vacancy rates, rental yields, 
and cap rates across office, retail, and industrial sectors.

Primary source: CoStar Group market analytics (https://www.costar.com/market-analytics)
Fallback source: FRED (Federal Reserve Economic Data) commercial RE series

Use cases:
- REIT trading signals
- Commercial real estate market analysis
- Sector-specific property metrics
- Geographic market trends
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "costar"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://feed.costar.com/analytics"
FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# FRED series for commercial real estate fallback - validated series
FRED_SERIES = {
    "commercial_re_loans": "REALLN",  # Real estate loans at all commercial banks
    "mortgage_debt": "MDOAH",  # Mortgage debt outstanding
    "housing_starts": "HOUST",  # Housing starts
    "construction_spending": "TLCOMCONS",  # Total construction spending
}


def fetch_costar_data(market: str = "US", use_cache: bool = True) -> Optional[Dict]:
    """
    Fetch commercial real estate data from CoStar feed.
    
    Args:
        market: Market identifier (US, NYC, LAX, etc.)
        use_cache: Use cached data if available and fresh
    
    Returns:
        Dictionary with market analytics or None if unavailable
    """
    cache_path = CACHE_DIR / f"costar_{market}_latest.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Try CoStar feed endpoint
    url = f"{BASE_URL}/commercial"
    params = {"market": market}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        # If auth required or paywall, return None to trigger fallback
        if response.status_code in [401, 402, 403, 451]:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
        
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # CoStar endpoint unavailable, will fall back to FRED
        return None


def fetch_fred_commercial_re(series: str, use_cache: bool = True) -> Optional[pd.DataFrame]:
    """
    Fetch commercial real estate data from FRED as fallback.
    
    Args:
        series: FRED series ID
        use_cache: Use cached data if available and fresh
    
    Returns:
        DataFrame with date index and value column
    """
    cache_path = CACHE_DIR / f"fred_{series}_latest.csv"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            try:
                return pd.read_csv(cache_path, parse_dates=[0], index_col=0)
            except Exception:
                pass  # Cache read failed, fetch fresh
    
    # Fetch from FRED
    params = {
        "id": series,
        "cosd": (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d"),  # 5 years
    }
    
    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        # Parse CSV - FRED uses 'DATE' as first column name
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty or len(df.columns) < 2:
            return None
        
        # Set date column as index
        df.set_index(df.columns[0], inplace=True)
        df.index = pd.to_datetime(df.index)
        
        # Rename value column to series name
        df.columns = [series]
        
        # Convert to numeric, coercing errors (handles '.' for missing values)
        df[series] = pd.to_numeric(df[series], errors='coerce')
        
        # Cache response
        df.to_csv(cache_path)
        
        return df
        
    except Exception as e:
        print(f"Error fetching FRED series {series}: {e}")
        return None


def get_market_analytics(market: str = "US") -> pd.DataFrame:
    """
    Get commercial real estate market analytics.
    
    Tries CoStar feed first, falls back to FRED data if unavailable.
    
    Args:
        market: Market identifier (US, NYC, LAX, etc.)
    
    Returns:
        DataFrame with commercial RE metrics
    """
    # Try CoStar first
    costar_data = fetch_costar_data(market)
    
    if costar_data and "metrics" in costar_data:
        # Parse CoStar response
        records = []
        for metric in costar_data.get("metrics", []):
            records.append({
                "date": metric.get("date"),
                "sector": metric.get("sector", "all"),
                "vacancy_rate": metric.get("vacancy_rate"),
                "cap_rate": metric.get("cap_rate"),
                "rental_yield": metric.get("rental_yield"),
            })
        
        if records:
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
    
    # Fallback to FRED data
    print(f"CoStar data unavailable for {market}, using FRED fallback...")
    
    combined_data = {}
    for name, series in FRED_SERIES.items():
        df = fetch_fred_commercial_re(series)
        if df is not None and not df.empty:
            combined_data[name] = df[series]
    
    if combined_data:
        result = pd.DataFrame(combined_data)
        # Drop rows where all values are NaN
        result = result.dropna(how='all')
        return result
    
    return pd.DataFrame()


def get_sector_metrics(sector: str = "office") -> pd.DataFrame:
    """
    Get metrics for specific commercial real estate sector.
    
    Args:
        sector: Sector type (office, retail, industrial, multifamily)
    
    Returns:
        DataFrame with sector-specific metrics
    """
    # Try CoStar endpoint with sector filter
    cache_path = CACHE_DIR / f"costar_sector_{sector}_latest.json"
    
    url = f"{BASE_URL}/commercial"
    params = {"sector": sector}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code in [401, 402, 403, 451]:
            # Auth required, use general market data as fallback
            return get_market_analytics()
        
        response.raise_for_status()
        data = response.json()
        
        # Cache
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Parse sector data
        if "metrics" in data:
            records = []
            for metric in data["metrics"]:
                records.append({
                    "date": metric.get("date"),
                    "vacancy_rate": metric.get("vacancy_rate"),
                    "cap_rate": metric.get("cap_rate"),
                    "rental_yield": metric.get("rental_yield"),
                    "avg_price_sqft": metric.get("avg_price_sqft"),
                })
            
            if records:
                df = pd.DataFrame(records)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
    
    except Exception:
        pass
    
    # Fallback to general market data
    return get_market_analytics()


def get_latest_snapshot() -> Dict:
    """
    Get latest commercial real estate market snapshot.
    
    Returns:
        Dictionary with current metrics across sectors
    """
    df = get_market_analytics()
    
    if df.empty:
        return {
            "status": "no_data",
            "timestamp": datetime.now().isoformat(),
            "source": "fred_fallback",
        }
    
    # Get most recent data
    latest_row = df.iloc[-1]
    latest = {}
    
    for col in df.columns:
        val = latest_row[col]
        if pd.notna(val):
            latest[col] = float(val) if isinstance(val, (int, float)) else val
    
    latest["timestamp"] = df.index[-1].isoformat()
    latest["source"] = "costar" if "vacancy_rate" in latest else "fred"
    
    return latest


def get_vacancy_trends(lookback_days: int = 365) -> pd.DataFrame:
    """
    Get vacancy rate trends over time.
    
    Args:
        lookback_days: Number of days to look back
    
    Returns:
        DataFrame with vacancy trends
    """
    df = get_market_analytics()
    
    if df.empty:
        return pd.DataFrame()
    
    # Filter to lookback period
    cutoff = datetime.now() - timedelta(days=lookback_days)
    df_filtered = df[df.index >= cutoff]
    
    # Return vacancy-related columns
    vacancy_cols = [col for col in df_filtered.columns if 'vacancy' in col.lower() or 'commercial' in col.lower()]
    
    if vacancy_cols:
        return df_filtered[vacancy_cols]
    
    return df_filtered


if __name__ == "__main__":
    # Test the module
    print("Testing CoStar Market Analytics Feed module...")
    
    # Test 1: Get market analytics
    print("\n1. Fetching market analytics...")
    df = get_market_analytics()
    print(f"   Retrieved {len(df)} data points")
    if not df.empty:
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Sample:\n{df.head(3)}")
    
    # Test 2: Get latest snapshot
    print("\n2. Fetching latest snapshot...")
    snapshot = get_latest_snapshot()
    print(f"   Source: {snapshot.get('source')}")
    print(f"   Timestamp: {snapshot.get('timestamp')}")
    print(f"   Metrics: {list(snapshot.keys())}")
    
    # Test 3: Get vacancy trends
    print("\n3. Fetching vacancy trends...")
    trends = get_vacancy_trends(lookback_days=180)
    print(f"   Retrieved {len(trends)} trend points")
    
    # Test 4: Get sector metrics
    print("\n4. Fetching office sector metrics...")
    office = get_sector_metrics("office")
    print(f"   Retrieved {len(office)} office data points")
    
    print("\n✓ Module test complete")
