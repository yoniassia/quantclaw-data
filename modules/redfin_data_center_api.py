#!/usr/bin/env python3
"""
Redfin Data Center API — Real-time US housing market statistics
Fetches median sale prices, inventory, days on market, bidding wars by metro/state.
Source: https://www.redfin.com/news/data-center/
Free tier: Unlimited (public S3 data)
Update frequency: Weekly
"""

import requests
import io
import os
import time
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, Any, List

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Public S3 URLs for Redfin data
REDFIN_URLS = {
    "weekly": "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_covid19/weekly_housing_market_data_most_recent.tsv",
    "monthly": "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/monthly_market_data.tsv"
}


def fetch_housing_data(dataset: str = "weekly", force_refresh: bool = False, nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch Redfin housing market data (TSV format from S3).
    
    NOTE: The weekly dataset is ~1.6GB. This function uses chunked reading
    to load only the most recent data by default (last 50k rows).
    
    Args:
        dataset: 'weekly' or 'monthly'
        force_refresh: Skip cache and fetch fresh data
        nrows: Number of rows to load (default: 50000 for performance)
        
    Returns:
        DataFrame with housing market metrics by region
        
    Columns typically include:
        - region_type, region, state_code, property_type
        - period_begin, period_end, period_duration
        - median_sale_price, median_list_price, median_ppsf
        - homes_sold, pending_sales, new_listings, inventory
        - months_of_supply, median_dom, avg_sale_to_list
        - sold_above_list, price_drops, off_market_in_two_weeks
    """
    module_name = __name__.split('.')[-1]
    cache_file = os.path.join(CACHE_DIR, f"{module_name}_{dataset}_recent.tsv")
    
    # Default to 50k rows for performance (file is 1.6GB+)
    if nrows is None:
        nrows = 50000
    
    # Use cache if fresh (within 7 days for weekly, 30 days for monthly)
    cache_ttl = 86400 * 7 if dataset == "weekly" else 86400 * 30
    if not force_refresh and os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < cache_ttl:
            try:
                df = pd.read_csv(cache_file, sep='\t', low_memory=False)
                df['_cached'] = True
                df['_cache_age_hours'] = round(age / 3600, 1)
                return df
            except Exception:
                pass
    
    # Fetch fresh data (chunked to avoid memory issues)
    try:
        url = REDFIN_URLS.get(dataset, REDFIN_URLS["weekly"])
        headers = {"User-Agent": "Mozilla/5.0 (QuantClaw/1.0)"}
        
        # Download to temp file first (streaming)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.tsv') as tmp:
            tmp_path = tmp.name
            
        print(f"Downloading {dataset} data from Redfin (this may take 30-60 seconds)...")
        resp = requests.get(url, timeout=120, headers=headers, stream=True)
        resp.raise_for_status()
        
        with open(tmp_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Parsing {nrows:,} most recent rows...")
        # Read only the header and last N rows (most recent data)
        # First get total line count
        with open(tmp_path, 'r') as f:
            total_lines = sum(1 for _ in f)
        
        skip_rows = max(0, total_lines - nrows - 1)  # -1 for header
        df = pd.read_csv(tmp_path, sep='\t', skiprows=range(1, skip_rows) if skip_rows > 0 else None, low_memory=False)
        
        os.unlink(tmp_path)
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Parse dates if present
        date_cols = [c for c in df.columns if 'period' in c or 'date' in c]
        for col in date_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass
        
        # Cache the result
        df.to_csv(cache_file, sep='\t', index=False)
        
        df['_cached'] = False
        df['_fetch_time'] = datetime.now().isoformat()
        return df
        
    except Exception as e:
        # Try to return stale cache on error
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, sep='\t', low_memory=False)
            df['_cached'] = True
            df['_error'] = str(e)
            return df
        return pd.DataFrame({"error": [str(e)]})


def get_metro_data(region: str, dataset: str = "weekly") -> pd.DataFrame:
    """
    Get housing data for a specific metro area.
    
    Args:
        region: Metro name (e.g., "San Francisco", "New York", "Austin")
        dataset: 'weekly' or 'monthly'
        
    Returns:
        Filtered DataFrame for the specified metro
    """
    df = fetch_housing_data(dataset)
    
    if 'error' in df.columns:
        return df
    
    # Filter by region (case-insensitive partial match)
    region_col = 'region' if 'region' in df.columns else df.columns[0]
    mask = df[region_col].str.contains(region, case=False, na=False)
    result = df[mask].copy()
    
    # Sort by most recent period
    if 'period_end' in result.columns:
        result = result.sort_values('period_end', ascending=False)
    
    return result


def get_state_data(state: str, dataset: str = "weekly") -> pd.DataFrame:
    """
    Get housing data for a specific state.
    
    Args:
        state: State code (e.g., "CA", "NY", "TX") or full name
        dataset: 'weekly' or 'monthly'
        
    Returns:
        Filtered DataFrame for the specified state
    """
    df = fetch_housing_data(dataset)
    
    if 'error' in df.columns:
        return df
    
    # Try both state_code and state columns
    state_cols = [c for c in df.columns if 'state' in c.lower()]
    if not state_cols:
        return pd.DataFrame({"error": ["No state column found in dataset"]})
    
    state_col = state_cols[0]
    mask = df[state_col].str.upper().str.contains(state.upper(), na=False)
    result = df[mask].copy()
    
    # Sort by most recent period
    if 'period_end' in result.columns:
        result = result.sort_values('period_end', ascending=False)
    
    return result


def get_latest(region_type: str = "metro", limit: int = 10, dataset: str = "weekly") -> pd.DataFrame:
    """
    Get latest housing market snapshot for top regions.
    
    Args:
        region_type: 'metro', 'state', 'city', or 'national'
        limit: Number of regions to return
        dataset: 'weekly' or 'monthly'
        
    Returns:
        DataFrame with most recent data for top regions by sales volume
    """
    df = fetch_housing_data(dataset)
    
    if 'error' in df.columns:
        return df
    
    # Filter by region type
    if 'region_type' in df.columns:
        df = df[df['region_type'].str.lower() == region_type.lower()].copy()
    
    # Get most recent period
    if 'period_end' in df.columns:
        latest_date = df['period_end'].max()
        df = df[df['period_end'] == latest_date].copy()
    
    # Sort by homes sold (or inventory if no sales data)
    sort_col = None
    for col in ['homes_sold', 'inventory', 'new_listings']:
        if col in df.columns:
            sort_col = col
            break
    
    if sort_col:
        df = df.sort_values(sort_col, ascending=False)
    
    return df.head(limit)


def get_market_summary(region: str = None, state: str = None, dataset: str = "weekly") -> Dict[str, Any]:
    """
    Get structured summary of housing market metrics for a region or state.
    
    Args:
        region: Metro area name (optional)
        state: State code (optional)
        dataset: 'weekly' or 'monthly'
        
    Returns:
        Dictionary with key metrics: prices, inventory, days on market, etc.
    """
    if region:
        df = get_metro_data(region, dataset)
    elif state:
        df = get_state_data(state, dataset)
    else:
        df = get_latest("national", limit=1, dataset=dataset)
    
    if df.empty or 'error' in df.columns:
        return {"error": "No data available", "region": region, "state": state}
    
    # Get first row (most recent data)
    row = df.iloc[0]
    
    summary = {
        "region": row.get('region', 'Unknown'),
        "region_type": row.get('region_type', 'Unknown'),
        "state": row.get('state_code', row.get('state', 'Unknown')),
        "period_end": str(row.get('period_end', '')),
        "metrics": {}
    }
    
    # Extract key metrics
    metric_mapping = {
        'median_sale_price': 'median_sale_price',
        'median_list_price': 'median_list_price',
        'median_ppsf': 'median_price_per_sqft',
        'homes_sold': 'homes_sold',
        'inventory': 'active_listings',
        'new_listings': 'new_listings',
        'months_of_supply': 'months_of_supply',
        'median_dom': 'median_days_on_market',
        'avg_sale_to_list': 'sale_to_list_ratio',
        'sold_above_list': 'pct_sold_above_list',
        'price_drops': 'pct_price_drops',
        'off_market_in_two_weeks': 'pct_off_market_2wks'
    }
    
    for col, metric_name in metric_mapping.items():
        if col in row and pd.notna(row[col]):
            summary['metrics'][metric_name] = row[col]
    
    summary['timestamp'] = datetime.now().isoformat()
    summary['source'] = 'Redfin Data Center'
    
    return summary


def get_top_markets(metric: str = "median_sale_price", limit: int = 10, dataset: str = "weekly") -> List[Dict[str, Any]]:
    """
    Get top markets ranked by a specific metric.
    
    Args:
        metric: Column name to rank by (e.g., 'median_sale_price', 'homes_sold', 'median_dom')
        limit: Number of markets to return
        dataset: 'weekly' or 'monthly'
        
    Returns:
        List of dictionaries with market data
    """
    df = fetch_housing_data(dataset)
    
    if 'error' in df.columns or df.empty:
        return [{"error": "No data available"}]
    
    # Get most recent period
    if 'period_end' in df.columns:
        latest_date = df['period_end'].max()
        df = df[df['period_end'] == latest_date].copy()
    
    # Filter to metro areas only
    if 'region_type' in df.columns:
        df = df[df['region_type'].str.lower() == 'metro'].copy()
    
    # Check if metric exists
    if metric not in df.columns:
        return [{"error": f"Metric '{metric}' not found in dataset"}]
    
    # Sort and limit
    df = df.sort_values(metric, ascending=False).head(limit)
    
    # Convert to list of dicts
    result = []
    for _, row in df.iterrows():
        result.append({
            'region': row.get('region', 'Unknown'),
            'state': row.get('state_code', row.get('state', 'Unknown')),
            metric: row[metric],
            'period_end': str(row.get('period_end', ''))
        })
    
    return result


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        region = sys.argv[1]
        result = get_market_summary(region=region)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Default: show top 5 markets by median price
        result = get_top_markets("median_sale_price", limit=5)
        print(json.dumps(result, indent=2, default=str))
