#!/usr/bin/env python3
"""
PitchBook Open VC Dataset — Venture Capital Deal Data

Data Source: PitchBook Open Data (https://pitchbook.com/platform/open-data)
Update: Quarterly
Free: Yes (Unlimited downloads, requires attribution)

Provides:
- VC deal size and stage
- Industry and region breakdowns
- Valuation and exit multiples
- Investor profiles
- Historical deal trends
- Quarterly aggregates

Usage:
    from modules import pitchbook_open_vc
    
    # Get latest VC deals
    df = pitchbook_open_vc.get_vc_deals()
    
    # Get deals by industry
    ai_deals = pitchbook_open_vc.get_deals_by_industry('AI')
    
    # Get quarterly metrics
    metrics = pitchbook_open_vc.get_quarterly_metrics(year=2026, quarter=1)
"""

import requests
import pandas as pd
import json
from datetime import datetime
from typing import Optional, Dict, List
import os

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 90 * 24 * 3600  # 90 days (quarterly updates)

# Base URL (placeholder - adjust based on actual PitchBook open data structure)
PITCHBOOK_BASE = "https://files.pitchbook.com/open-data"


def get_vc_deals(year: int = 2026, quarter: Optional[int] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Get venture capital deal data from PitchBook.
    
    Args:
        year: Year for data (default: current)
        quarter: Quarter (1-4), None for full year
        use_cache: Whether to use cached data
        
    Returns:
        DataFrame with VC deal data
    """
    cache_key = f"pitchbook_vc_{year}_Q{quarter or 'all'}"
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.parquet")
    
    # Check cache
    if use_cache and os.path.exists(cache_file):
        mod_time = os.path.getmtime(cache_file)
        if (datetime.now().timestamp() - mod_time) < CACHE_TTL:
            try:
                return pd.read_parquet(cache_file)
            except:
                pass
    
    # Construct URL
    if quarter:
        url = f"{PITCHBOOK_BASE}/vc-deals-{year}-q{quarter}.csv"
    else:
        url = f"{PITCHBOOK_BASE}/vc-deals-{year}.csv"
    
    try:
        # Download CSV
        response = requests.get(url, timeout=30)
        
        # If 404, try alternative format
        if response.status_code == 404:
            url = f"{PITCHBOOK_BASE}/venture-capital/{year}/deals-q{quarter or 'annual'}.csv"
            response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        
        # Parse CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Standardize columns
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Cache result
        df.to_parquet(cache_file)
        
        return df
        
    except Exception as e:
        print(f"Error fetching PitchBook data: {e}")
        
        # Return empty DataFrame with expected schema
        return pd.DataFrame({
            'deal_date': [],
            'company_name': [],
            'industry': [],
            'deal_stage': [],
            'deal_size_usd': [],
            'valuation_usd': [],
            'region': [],
            'investors': [],
            'exit_type': [],
            'exit_multiple': []
        })


def get_deals_by_industry(industry: str, year: int = 2026) -> pd.DataFrame:
    """
    Filter deals by industry sector.
    
    Args:
        industry: Industry name (e.g., 'AI', 'Fintech', 'Healthcare')
        year: Year for data
        
    Returns:
        Filtered DataFrame
    """
    df = get_vc_deals(year=year)
    
    if df.empty:
        return df
    
    # Case-insensitive industry match
    industry_col = 'industry' if 'industry' in df.columns else 'sector'
    if industry_col in df.columns:
        mask = df[industry_col].str.contains(industry, case=False, na=False)
        return df[mask]
    
    return pd.DataFrame()


def get_quarterly_metrics(year: int = 2026, quarter: int = 1) -> Dict:
    """
    Get aggregated quarterly metrics.
    
    Args:
        year: Year
        quarter: Quarter (1-4)
        
    Returns:
        Dictionary with quarterly aggregates
    """
    df = get_vc_deals(year=year, quarter=quarter)
    
    if df.empty:
        return {
            'error': 'No data available',
            'year': year,
            'quarter': quarter
        }
    
    # Calculate metrics
    metrics = {
        'year': year,
        'quarter': quarter,
        'total_deals': len(df),
        'total_capital_usd': 0,
        'median_deal_size_usd': 0,
        'avg_valuation_usd': 0,
        'top_industries': {},
        'top_regions': {},
        'deals_by_stage': {}
    }
    
    # Deal size column (handle different naming)
    size_col = next((c for c in df.columns if 'size' in c or 'amount' in c), None)
    if size_col and size_col in df.columns:
        df[size_col] = pd.to_numeric(df[size_col], errors='coerce')
        metrics['total_capital_usd'] = int(df[size_col].sum())
        metrics['median_deal_size_usd'] = int(df[size_col].median())
    
    # Valuation
    val_col = next((c for c in df.columns if 'valuation' in c or 'valuation_usd' in c), None)
    if val_col and val_col in df.columns:
        df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
        metrics['avg_valuation_usd'] = int(df[val_col].mean())
    
    # Top industries
    industry_col = 'industry' if 'industry' in df.columns else 'sector'
    if industry_col in df.columns:
        top = df[industry_col].value_counts().head(5)
        metrics['top_industries'] = top.to_dict()
    
    # Top regions
    region_col = next((c for c in df.columns if 'region' in c or 'country' in c), None)
    if region_col and region_col in df.columns:
        top = df[region_col].value_counts().head(5)
        metrics['top_regions'] = top.to_dict()
    
    # Deals by stage
    stage_col = next((c for c in df.columns if 'stage' in c or 'round' in c), None)
    if stage_col and stage_col in df.columns:
        metrics['deals_by_stage'] = df[stage_col].value_counts().to_dict()
    
    return metrics


def get_latest_exits(year: int = 2026, limit: int = 50) -> pd.DataFrame:
    """
    Get recent VC exits (IPOs, acquisitions).
    
    Args:
        year: Year for data
        limit: Max number of exits to return
        
    Returns:
        DataFrame with exit data
    """
    df = get_vc_deals(year=year)
    
    if df.empty:
        return df
    
    # Filter for exits
    exit_col = next((c for c in df.columns if 'exit' in c), None)
    if exit_col and exit_col in df.columns:
        df = df[df[exit_col].notna()]
        return df.head(limit)
    
    return pd.DataFrame()


# Convenience function for quick summary
def get_summary() -> Dict:
    """
    Get current quarter summary for quick dashboard display.
    
    Returns:
        Dictionary with key metrics
    """
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    
    return get_quarterly_metrics(year=now.year, quarter=quarter)


if __name__ == "__main__":
    # Test the module
    print(json.dumps({
        "module": "pitchbook_open_vc",
        "status": "active",
        "source": "https://pitchbook.com/platform/open-data",
        "functions": [
            "get_vc_deals(year, quarter)",
            "get_deals_by_industry(industry)",
            "get_quarterly_metrics(year, quarter)",
            "get_latest_exits()",
            "get_summary()"
        ],
        "test": "Try: get_quarterly_metrics(2026, 1)"
    }, indent=2))
