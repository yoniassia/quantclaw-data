"""
Eurostat Demographics API — European Labor & Population Data

Tracks demographic and labor market indicators for EU countries via Eurostat JSON API.
Data: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/

Use cases:
- European market demographic analysis
- Migration flow tracking
- Wage growth and unemployment trends
- Fertility rate analysis for consumer sectors
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
from pathlib import Path
import json

CACHE_DIR = Path(__file__).parent.parent / "cache" / "eurostat_demographics"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def _fetch_eurostat_data(dataset_code: str, params: Dict[str, str], use_cache: bool = True) -> Optional[Dict]:
    """Fetch data from Eurostat API with caching."""
    # Create cache key from dataset and params
    cache_key = f"{dataset_code}_{'_'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
    cache_path = CACHE_DIR / f"{cache_key}.json"
    
    # Check cache
    if use_cache and cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime < timedelta(hours=24):
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = f"{BASE_URL}/{dataset_code}"
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Cache response
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    except Exception as e:
        print(f"Error fetching Eurostat data for {dataset_code}: {e}")
        return None


def _parse_eurostat_response(data: Dict) -> pd.DataFrame:
    """Parse Eurostat JSON response into DataFrame."""
    if not data or "value" not in data:
        return pd.DataFrame()
    
    # Extract values and dimensions
    values = data["value"]
    dimensions = data.get("dimension", {})
    
    # Build index mapping
    rows = []
    for idx, value in values.items():
        # Parse multi-dimensional index
        coords = {}
        dim_sizes = []
        for dim_name, dim_data in dimensions.items():
            if dim_name != "id":
                categories = dim_data.get("category", {}).get("index", {})
                dim_sizes.append(len(categories))
        
        # Convert flat index to coordinates
        idx_num = int(idx)
        for dim_name, dim_data in dimensions.items():
            if dim_name != "id":
                categories = dim_data.get("category", {}).get("index", {})
                cat_list = list(categories.keys())
                if dim_sizes:
                    dim_idx = idx_num % len(categories)
                    coords[dim_name] = cat_list[dim_idx]
                    idx_num //= len(categories)
        
        coords["value"] = value
        rows.append(coords)
    
    return pd.DataFrame(rows)


def fetch_population(country: str = "EU27_2020", use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch population data from Eurostat.
    
    Args:
        country: Country code (e.g., "DE", "FR", "EU27_2020")
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        DataFrame with population data by year
    """
    params = {
        "geo": country,
        "sex": "T",  # Total
        "age": "TOTAL"
    }
    
    data = _fetch_eurostat_data("demo_pjan", params, use_cache)
    if not data:
        return pd.DataFrame()
    
    df = _parse_eurostat_response(data)
    return df


def get_migration_flows(country: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch net migration flows from Eurostat.
    
    Args:
        country: Country code (None for all EU countries)
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        DataFrame with migration flow data
    """
    params = {}
    if country:
        params["geo"] = country
    
    data = _fetch_eurostat_data("migr_imm1ctz", params, use_cache)
    if not data:
        return pd.DataFrame()
    
    df = _parse_eurostat_response(data)
    return df


def get_wage_growth(country: Optional[str] = None, sector: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch wage growth data from Eurostat.
    
    Args:
        country: Country code (None for all EU countries)
        sector: Economic sector code (None for all sectors)
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        DataFrame with wage data
    """
    params = {}
    if country:
        params["geo"] = country
    if sector:
        params["nace_r2"] = sector
    
    data = _fetch_eurostat_data("earn_mw_cur", params, use_cache)
    if not data:
        return pd.DataFrame()
    
    df = _parse_eurostat_response(data)
    return df


def get_unemployment_rate(country: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch unemployment rate from Eurostat.
    
    Args:
        country: Country code (None for all EU countries)
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        DataFrame with unemployment rates
    """
    params = {
        "s_adj": "SA",  # Seasonally adjusted
        "age": "TOTAL",
        "sex": "T"
    }
    if country:
        params["geo"] = country
    
    data = _fetch_eurostat_data("une_rt_m", params, use_cache)
    if not data:
        return pd.DataFrame()
    
    df = _parse_eurostat_response(data)
    return df


def get_fertility_rate(country: Optional[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch fertility rate data from Eurostat.
    
    Args:
        country: Country code (None for all EU countries)
        use_cache: Use cached data if available (24h TTL)
    
    Returns:
        DataFrame with fertility rates
    """
    params = {}
    if country:
        params["geo"] = country
    
    data = _fetch_eurostat_data("demo_find", params, use_cache)
    if not data:
        return pd.DataFrame()
    
    df = _parse_eurostat_response(data)
    return df


if __name__ == "__main__":
    # Quick test
    print("Testing Eurostat Demographics API module...")
    pop = fetch_population("DE")
    print(f"Population data shape: {pop.shape}")
    print(pop.head() if not pop.empty else "No data")
