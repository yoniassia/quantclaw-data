#!/usr/bin/env python3
"""
Zillow Research API — Real Estate & Housing Market Data

Zillow Research provides free CSV data downloads for housing market analysis.
Key datasets include ZHVI (Home Value Index), ZORI (Rent Index), inventory,
and listings data at metro, state, zip, and county levels.

Source: https://www.zillow.com/research/data/
Category: Real Estate & Housing
Free tier: True (no API key required, public CSV downloads)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
import io
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Zillow Research CSV Base URL
ZILLOW_BASE_URL = "https://files.zillowstatic.com/research/public_csvs"

# Dataset Registry
ZILLOW_DATASETS = {
    'zhvi': {
        'metro': f"{ZILLOW_BASE_URL}/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
        'state': f"{ZILLOW_BASE_URL}/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
        'zip': f"{ZILLOW_BASE_URL}/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
        'county': f"{ZILLOW_BASE_URL}/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    },
    'zori': {
        'metro': f"{ZILLOW_BASE_URL}/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
        'state': f"{ZILLOW_BASE_URL}/zori/State_zori_uc_sfrcondomfr_sm_month.csv",
        'zip': f"{ZILLOW_BASE_URL}/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv",
        'county': f"{ZILLOW_BASE_URL}/zori/County_zori_uc_sfrcondomfr_sm_month.csv",
    },
    'inventory': {
        'metro': f"{ZILLOW_BASE_URL}/invt_fs_uc_sfrcondo_sm_month_mlp/Metro_invt_fs_uc_sfrcondo_sm_month_mlp.csv",
        'state': f"{ZILLOW_BASE_URL}/invt_fs_uc_sfrcondo_sm_month_mlp/State_invt_fs_uc_sfrcondo_sm_month_mlp.csv",
    }
}


def _fetch_csv_data(url: str, timeout: int = 30) -> List[Dict]:
    """
    Internal helper to fetch and parse CSV data from Zillow.
    
    Args:
        url: CSV file URL
        timeout: Request timeout in seconds
        
    Returns:
        List of dictionaries with parsed CSV data
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Parse CSV
        csv_text = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_text))
        data = list(reader)
        
        return data
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Zillow data: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to parse Zillow CSV: {str(e)}")


def _get_latest_value(row: Dict) -> Optional[float]:
    """Extract the most recent value from a Zillow data row."""
    # Find date columns (format: YYYY-MM-DD)
    date_cols = [k for k in row.keys() if k and len(k) == 10 and k[4] == '-' and k[7] == '-']
    date_cols.sort(reverse=True)  # Most recent first
    
    for col in date_cols:
        val = row.get(col, '').strip()
        if val and val != '':
            try:
                return float(val)
            except ValueError:
                continue
    return None


def get_zhvi(region_type: str = "metro", top_n: int = 20) -> List[Dict]:
    """
    Get Zillow Home Value Index (ZHVI) data.
    
    ZHVI measures the typical home value for a given region. Smoothed, seasonally
    adjusted measure of the typical home value and market changes.
    
    Args:
        region_type: Type of region ('metro', 'state', 'zip', 'county')
        top_n: Number of top regions to return (by most recent value)
        
    Returns:
        List of dictionaries with region name and latest ZHVI value
        
    Example:
        >>> data = get_zhvi(region_type="metro", top_n=10)
        >>> print(data[0])
        {'region': 'San Jose, CA', 'zhvi': 1450000, 'date': '2026-02-01'}
    """
    try:
        if region_type not in ZILLOW_DATASETS['zhvi']:
            raise ValueError(f"Invalid region_type. Choose from: {list(ZILLOW_DATASETS['zhvi'].keys())}")
        
        url = ZILLOW_DATASETS['zhvi'][region_type]
        raw_data = _fetch_csv_data(url)
        
        # Process data
        results = []
        for row in raw_data:
            latest_val = _get_latest_value(row)
            if latest_val is not None:
                region_name = row.get('RegionName', 'Unknown')
                if region_type == 'metro':
                    state = row.get('StateName', '')
                    region_name = f"{region_name}, {state}" if state else region_name
                
                results.append({
                    'region': region_name,
                    'zhvi': latest_val,
                    'region_type': region_type
                })
        
        # Sort by value (highest first) and limit
        results.sort(key=lambda x: x['zhvi'], reverse=True)
        return results[:top_n]
        
    except Exception as e:
        return {'error': str(e), 'function': 'get_zhvi'}


def get_zori(region_type: str = "metro", top_n: int = 20) -> List[Dict]:
    """
    Get Zillow Observed Rent Index (ZORI) data.
    
    ZORI measures the typical observed market rate rent across a given region.
    
    Args:
        region_type: Type of region ('metro', 'state', 'zip', 'county')
        top_n: Number of top regions to return (by most recent value)
        
    Returns:
        List of dictionaries with region name and latest ZORI value
        
    Example:
        >>> data = get_zori(region_type="state", top_n=5)
        >>> print(data[0])
        {'region': 'California', 'zori': 2800, 'region_type': 'state'}
    """
    try:
        if region_type not in ZILLOW_DATASETS['zori']:
            raise ValueError(f"Invalid region_type. Choose from: {list(ZILLOW_DATASETS['zori'].keys())}")
        
        url = ZILLOW_DATASETS['zori'][region_type]
        raw_data = _fetch_csv_data(url)
        
        # Process data
        results = []
        for row in raw_data:
            latest_val = _get_latest_value(row)
            if latest_val is not None:
                region_name = row.get('RegionName', 'Unknown')
                if region_type == 'metro':
                    state = row.get('StateName', '')
                    region_name = f"{region_name}, {state}" if state else region_name
                
                results.append({
                    'region': region_name,
                    'zori': latest_val,
                    'region_type': region_type
                })
        
        # Sort by value (highest first) and limit
        results.sort(key=lambda x: x['zori'], reverse=True)
        return results[:top_n]
        
    except Exception as e:
        return {'error': str(e), 'function': 'get_zori'}


def get_market_overview(metro: str = "United States") -> Dict:
    """
    Get housing market overview for a specific metro area.
    
    Combines ZHVI and ZORI data to provide a market snapshot.
    
    Args:
        metro: Metro area name (e.g., "New York, NY", "United States")
        
    Returns:
        Dictionary with home values, rent, and market metrics
        
    Example:
        >>> data = get_market_overview("San Francisco, CA")
        >>> print(data['zhvi'], data['zori'])
    """
    try:
        # Fetch metro ZHVI data
        zhvi_url = ZILLOW_DATASETS['zhvi']['metro']
        zhvi_data = _fetch_csv_data(zhvi_url)
        
        # Fetch metro ZORI data
        zori_url = ZILLOW_DATASETS['zori']['metro']
        zori_data = _fetch_csv_data(zori_url)
        
        # Find matching metro
        zhvi_row = None
        for row in zhvi_data:
            region_name = row.get('RegionName', '')
            state = row.get('StateName', '')
            full_name = f"{region_name}, {state}" if state else region_name
            if metro.lower() in full_name.lower() or full_name.lower() in metro.lower():
                zhvi_row = row
                break
        
        zori_row = None
        for row in zori_data:
            region_name = row.get('RegionName', '')
            state = row.get('StateName', '')
            full_name = f"{region_name}, {state}" if state else region_name
            if metro.lower() in full_name.lower() or full_name.lower() in metro.lower():
                zori_row = row
                break
        
        if not zhvi_row and not zori_row:
            return {'error': f'Metro area "{metro}" not found', 'function': 'get_market_overview'}
        
        # Build overview
        overview = {
            'metro': metro,
            'zhvi': _get_latest_value(zhvi_row) if zhvi_row else None,
            'zori': _get_latest_value(zori_row) if zori_row else None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate price-to-rent ratio if both available
        if overview['zhvi'] and overview['zori']:
            annual_rent = overview['zori'] * 12
            overview['price_to_rent_ratio'] = round(overview['zhvi'] / annual_rent, 2)
        
        return overview
        
    except Exception as e:
        return {'error': str(e), 'function': 'get_market_overview'}


def get_inventory_data(region_type: str = "metro") -> List[Dict]:
    """
    Get for-sale inventory levels by region.
    
    Inventory data shows the number of homes for sale in a given area.
    
    Args:
        region_type: Type of region ('metro', 'state')
        
    Returns:
        List of dictionaries with region and inventory count
        
    Example:
        >>> data = get_inventory_data(region_type="state")
        >>> print(data[0])
        {'region': 'Florida', 'inventory': 45000}
    """
    try:
        if region_type not in ZILLOW_DATASETS['inventory']:
            raise ValueError(f"Invalid region_type. Choose from: {list(ZILLOW_DATASETS['inventory'].keys())}")
        
        url = ZILLOW_DATASETS['inventory'][region_type]
        raw_data = _fetch_csv_data(url)
        
        # Process data
        results = []
        for row in raw_data:
            latest_val = _get_latest_value(row)
            if latest_val is not None:
                region_name = row.get('RegionName', 'Unknown')
                if region_type == 'metro':
                    state = row.get('StateName', '')
                    region_name = f"{region_name}, {state}" if state else region_name
                
                results.append({
                    'region': region_name,
                    'inventory': int(latest_val),
                    'region_type': region_type
                })
        
        # Sort by inventory (highest first)
        results.sort(key=lambda x: x['inventory'], reverse=True)
        return results
        
    except Exception as e:
        return {'error': str(e), 'function': 'get_inventory_data'}


def get_housing_trend(metro: str, months: int = 12) -> Dict:
    """
    Get price trend for a specific metro over the last N months.
    
    Args:
        metro: Metro area name (e.g., "Austin, TX")
        months: Number of months to look back (default 12)
        
    Returns:
        Dictionary with historical ZHVI values and trend analysis
        
    Example:
        >>> data = get_housing_trend("Miami, FL", months=12)
        >>> print(data['trend'], data['change_pct'])
    """
    try:
        # Fetch metro ZHVI data
        url = ZILLOW_DATASETS['zhvi']['metro']
        raw_data = _fetch_csv_data(url)
        
        # Find matching metro
        target_row = None
        for row in raw_data:
            region_name = row.get('RegionName', '')
            state = row.get('StateName', '')
            full_name = f"{region_name}, {state}" if state else region_name
            if metro.lower() in full_name.lower() or full_name.lower() in metro.lower():
                target_row = row
                break
        
        if not target_row:
            return {'error': f'Metro area "{metro}" not found', 'function': 'get_housing_trend'}
        
        # Extract date columns and sort
        date_cols = [k for k in target_row.keys() if k and len(k) == 10 and k[4] == '-' and k[7] == '-']
        date_cols.sort()  # Oldest to newest
        
        # Get last N months
        recent_cols = date_cols[-months:] if len(date_cols) >= months else date_cols
        
        # Build time series
        time_series = []
        for col in recent_cols:
            val = target_row.get(col, '').strip()
            if val and val != '':
                try:
                    time_series.append({
                        'date': col,
                        'zhvi': float(val)
                    })
                except ValueError:
                    continue
        
        if len(time_series) < 2:
            return {'error': 'Insufficient data for trend analysis', 'function': 'get_housing_trend'}
        
        # Calculate trend
        first_val = time_series[0]['zhvi']
        last_val = time_series[-1]['zhvi']
        change = last_val - first_val
        change_pct = (change / first_val) * 100
        
        return {
            'metro': metro,
            'period_months': len(time_series),
            'start_date': time_series[0]['date'],
            'end_date': time_series[-1]['date'],
            'start_zhvi': first_val,
            'end_zhvi': last_val,
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'trend': 'up' if change > 0 else 'down',
            'time_series': time_series
        }
        
    except Exception as e:
        return {'error': str(e), 'function': 'get_housing_trend'}


def list_available_datasets() -> List[Dict]:
    """
    List all available Zillow Research datasets.
    
    Returns:
        List of dictionaries with dataset information
        
    Example:
        >>> datasets = list_available_datasets()
        >>> for ds in datasets:
        ...     print(ds['name'], ds['description'])
    """
    datasets = [
        {
            'name': 'ZHVI',
            'description': 'Zillow Home Value Index - typical home values',
            'region_types': list(ZILLOW_DATASETS['zhvi'].keys()),
            'frequency': 'monthly',
            'free': True
        },
        {
            'name': 'ZORI',
            'description': 'Zillow Observed Rent Index - typical market rents',
            'region_types': list(ZILLOW_DATASETS['zori'].keys()),
            'frequency': 'monthly',
            'free': True
        },
        {
            'name': 'Inventory',
            'description': 'For-sale inventory levels',
            'region_types': list(ZILLOW_DATASETS['inventory'].keys()),
            'frequency': 'monthly',
            'free': True
        }
    ]
    
    return datasets


if __name__ == "__main__":
    # Test the module
    print("🏠 Zillow Research API Module")
    print("=" * 50)
    
    # Test list_available_datasets
    print("\n📋 Available Datasets:")
    datasets = list_available_datasets()
    for ds in datasets:
        print(f"  - {ds['name']}: {ds['description']}")
    
    # Test get_zhvi
    print("\n🏘️  Top 5 Metro ZHVIs:")
    zhvi = get_zhvi(region_type="metro", top_n=5)
    if isinstance(zhvi, list):
        for item in zhvi[:5]:
            print(f"  {item['region']}: ${item['zhvi']:,.0f}")
    else:
        print(f"  Error: {zhvi.get('error')}")
    
    # Test get_market_overview
    print("\n🌉 Market Overview - San Francisco:")
    overview = get_market_overview("San Francisco")
    if 'error' not in overview:
        print(f"  ZHVI: ${overview.get('zhvi', 0):,.0f}")
        print(f"  ZORI: ${overview.get('zori', 0):,.0f}")
        if 'price_to_rent_ratio' in overview:
            print(f"  Price-to-Rent: {overview['price_to_rent_ratio']}")
    else:
        print(f"  Error: {overview.get('error')}")
