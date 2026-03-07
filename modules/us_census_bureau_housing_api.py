"""
US Census Bureau Housing API — Housing Market Data

Tracks housing units, homeownership rates, vacancy rates, and median home values
via US Census Bureau's American Community Survey (ACS) 5-year estimates.

Data: https://api.census.gov/data/
No API key required. Rate limit: 500 calls/hour per IP.

Use cases:
- Regional housing supply analysis
- Homeownership trend tracking
- Vacancy rate monitoring
- Real estate market fundamentals
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "census_housing"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.census.gov/data"


def _fetch_acs_data(year: int, variables: List[str], geography: str = "state:*", use_cache: bool = True) -> Optional[List]:
    """
    Internal helper to fetch ACS 5-year estimates data.
    
    Args:
        year: Data year (e.g., 2023)
        variables: List of variable codes to fetch
        geography: Geography filter (default: all states)
        use_cache: Use cached data if available and fresh
    
    Returns:
        List of data rows or None if error
    """
    cache_key = f"{year}_{'_'.join(variables)}_{geography.replace(':', '_').replace('*', 'all')}"
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache (24-hour TTL for census data)
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Build API request
    vars_str = "NAME," + ",".join(variables)
    url = f"{BASE_URL}/{year}/acs/acs5"
    params = {
        "get": vars_str,
        "for": geography
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching Census data: {e}")
        return None


def get_housing_units_by_state(year: int = 2023) -> pd.DataFrame:
    """
    Get total housing units by state from ACS 5-year estimates.
    
    Args:
        year: Data year (default: 2023)
    
    Returns:
        DataFrame with columns: state_name, state_code, housing_units
    """
    data = _fetch_acs_data(year, ["B25001_001E"])
    if not data or len(data) < 2:
        return pd.DataFrame()
    
    # First row is headers, rest is data
    headers = data[0]
    rows = data[1:]
    
    # Build DataFrame
    records = []
    for row in rows:
        try:
            records.append({
                "state_name": row[0],
                "housing_units": int(row[1]) if row[1] and row[1] != "-666666666" else None,
                "state_code": row[2],
                "year": year
            })
        except (ValueError, IndexError):
            continue
    
    df = pd.DataFrame(records)
    df = df[df['housing_units'].notna()]  # Remove nulls
    df = df.sort_values('housing_units', ascending=False).reset_index(drop=True)
    
    return df


def get_homeownership_rate(year: int = 2023) -> pd.DataFrame:
    """
    Get homeownership rates by state (owner-occupied / total occupied units).
    
    Args:
        year: Data year (default: 2023)
    
    Returns:
        DataFrame with columns: state_name, state_code, homeownership_rate, owner_occupied, total_occupied
    """
    # B25003_002E = owner occupied, B25003_001E = total occupied
    data = _fetch_acs_data(year, ["B25003_001E", "B25003_002E"])
    if not data or len(data) < 2:
        return pd.DataFrame()
    
    headers = data[0]
    rows = data[1:]
    
    records = []
    for row in rows:
        try:
            total_occupied = int(row[1]) if row[1] and row[1] != "-666666666" else 0
            owner_occupied = int(row[2]) if row[2] and row[2] != "-666666666" else 0
            
            if total_occupied > 0:
                rate = (owner_occupied / total_occupied) * 100
                records.append({
                    "state_name": row[0],
                    "homeownership_rate": round(rate, 2),
                    "owner_occupied": owner_occupied,
                    "total_occupied": total_occupied,
                    "state_code": row[3],
                    "year": year
                })
        except (ValueError, IndexError, ZeroDivisionError):
            continue
    
    df = pd.DataFrame(records)
    df = df.sort_values('homeownership_rate', ascending=False).reset_index(drop=True)
    
    return df


def get_vacancy_rates(year: int = 2023) -> pd.DataFrame:
    """
    Get housing vacancy rates by state (vacant / total units).
    
    Args:
        year: Data year (default: 2023)
    
    Returns:
        DataFrame with columns: state_name, state_code, vacancy_rate, vacant_units, total_units
    """
    # B25002_001E = total units, B25002_003E = vacant units
    data = _fetch_acs_data(year, ["B25002_001E", "B25002_003E"])
    if not data or len(data) < 2:
        return pd.DataFrame()
    
    headers = data[0]
    rows = data[1:]
    
    records = []
    for row in rows:
        try:
            total_units = int(row[1]) if row[1] and row[1] != "-666666666" else 0
            vacant_units = int(row[2]) if row[2] and row[2] != "-666666666" else 0
            
            if total_units > 0:
                rate = (vacant_units / total_units) * 100
                records.append({
                    "state_name": row[0],
                    "vacancy_rate": round(rate, 2),
                    "vacant_units": vacant_units,
                    "total_units": total_units,
                    "state_code": row[3],
                    "year": year
                })
        except (ValueError, IndexError, ZeroDivisionError):
            continue
    
    df = pd.DataFrame(records)
    df = df.sort_values('vacancy_rate', ascending=False).reset_index(drop=True)
    
    return df


def get_building_permits(state: Optional[str] = None) -> pd.DataFrame:
    """
    Get building permits data. 
    Note: Building permits are in a separate Census API endpoint (not ACS).
    This function returns a placeholder - full implementation requires Building Permits Survey API.
    
    Args:
        state: Optional state code filter (e.g., "06" for California)
    
    Returns:
        DataFrame with building permits data (placeholder)
    """
    # Building permits require the Building Permits Survey API
    # https://api.census.gov/data/timeseries/eits/bps
    # This is outside ACS scope - returning informational message
    
    return pd.DataFrame({
        "note": ["Building Permits data requires separate Census Building Permits Survey API"],
        "endpoint": ["https://api.census.gov/data/timeseries/eits/bps"],
        "documentation": ["https://www.census.gov/construction/bps/"]
    })


def get_median_home_value(year: int = 2023) -> pd.DataFrame:
    """
    Get median home values by state for owner-occupied units.
    
    Args:
        year: Data year (default: 2023)
    
    Returns:
        DataFrame with columns: state_name, state_code, median_home_value
    """
    # B25077_001E = median home value (owner-occupied)
    data = _fetch_acs_data(year, ["B25077_001E"])
    if not data or len(data) < 2:
        return pd.DataFrame()
    
    headers = data[0]
    rows = data[1:]
    
    records = []
    for row in rows:
        try:
            median_value = int(row[1]) if row[1] and row[1] not in ["-666666666", "null"] else None
            
            if median_value and median_value > 0:
                records.append({
                    "state_name": row[0],
                    "median_home_value": median_value,
                    "state_code": row[2],
                    "year": year
                })
        except (ValueError, IndexError):
            continue
    
    df = pd.DataFrame(records)
    df = df.sort_values('median_home_value', ascending=False).reset_index(drop=True)
    
    return df


# CLI functions for testing
def cli_housing_summary(year: int = 2023):
    """CLI: Display housing market summary."""
    print(f"\n=== US Housing Market Summary ({year}) ===\n")
    
    # Top 5 states by housing units
    units_df = get_housing_units_by_state(year)
    if not units_df.empty:
        print("Top 5 States by Housing Units:")
        print(units_df[['state_name', 'housing_units']].head().to_string(index=False))
    
    # Top 5 homeownership rates
    ownership_df = get_homeownership_rate(year)
    if not ownership_df.empty:
        print("\n\nTop 5 Homeownership Rates:")
        print(ownership_df[['state_name', 'homeownership_rate']].head().to_string(index=False))
    
    # Top 5 vacancy rates
    vacancy_df = get_vacancy_rates(year)
    if not vacancy_df.empty:
        print("\n\nHighest Vacancy Rates:")
        print(vacancy_df[['state_name', 'vacancy_rate']].head().to_string(index=False))
    
    # Top 5 median home values
    value_df = get_median_home_value(year)
    if not value_df.empty:
        print("\n\nTop 5 Median Home Values:")
        top_values = value_df.head()
        for _, row in top_values.iterrows():
            print(f"{row['state_name']:20s} ${row['median_home_value']:,}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    year = 2023
    if args and args[0].isdigit():
        year = int(args[0])
    
    cli_housing_summary(year)
