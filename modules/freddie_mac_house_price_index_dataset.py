#!/usr/bin/env python3
"""
Freddie Mac House Price Index Dataset

The Freddie Mac House Price Index provides monthly indices tracking home price 
appreciation across US metros and states using repeat-sales methodology for 
accurate trend analysis. Ideal for backtesting real estate-linked trading strategies.

Source: https://www.freddiemac.com/research/indices/house-price-index
Category: Real Estate & Housing
Free tier: True - Unlimited CSV downloads, no API key required
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from io import StringIO

# Master CSV file contains all geographic breakdowns
FREDDIE_MAC_URL = 'https://www.freddiemac.com/fmac-resources/research/docs/fmhpi_master_file.csv'

# Cache for downloaded data (in-memory for session duration)
_CACHE = {}


def _fetch_data() -> pd.DataFrame:
    """
    Internal helper to fetch and cache CSV data from Freddie Mac.
    
    Returns:
        pandas DataFrame with the master CSV data
    
    Raises:
        requests.RequestException: If download fails
        pd.errors.ParserError: If CSV parsing fails
    """
    if 'master' in _CACHE:
        return _CACHE['master']
    
    try:
        response = requests.get(FREDDIE_MAC_URL, timeout=30)
        response.raise_for_status()
        
        # Parse CSV with dtype specification to avoid warnings
        df = pd.read_csv(StringIO(response.text), low_memory=False)
        
        # Cache result
        _CACHE['master'] = df
        
        return df
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch Freddie Mac data: {str(e)}")
    except pd.errors.ParserError as e:
        raise pd.errors.ParserError(f"Failed to parse CSV: {str(e)}")


def get_national_index(start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
    """
    Get national-level house price index data.
    
    Args:
        start_year: Optional start year filter (e.g., 2020)
        end_year: Optional end year filter (e.g., 2024)
    
    Returns:
        List of dicts with Year, Month, Index_SA, Index_NSA
    
    Example:
        >>> data = get_national_index(start_year=2023)
        >>> print(data[0])
        {'Year': 2023, 'Month': 1, 'Index_SA': 345.6, 'Index_NSA': 344.2, ...}
    """
    try:
        df = _fetch_data()
        
        # Filter for USA national data
        df = df[df['GEO_Type'] == 'US'].copy()
        
        # Apply year filters
        if start_year:
            df = df[df['Year'] >= start_year]
        if end_year:
            df = df[df['Year'] <= end_year]
        
        # Sort by year and month
        df = df.sort_values(['Year', 'Month'])
        
        # Convert to list of dicts
        return df.to_dict('records')
    
    except Exception as e:
        return [{'error': str(e), 'source': 'get_national_index'}]


def get_state_index(state: str, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
    """
    Get state-level house price index data.
    
    Args:
        state: State code (e.g., 'CA', 'NY', 'TX')
        start_year: Optional start year filter
        end_year: Optional end year filter
    
    Returns:
        List of dicts with Year, Month, State, Index_SA, Index_NSA
    
    Example:
        >>> data = get_state_index('CA', start_year=2023)
        >>> print(data[0])
        {'Year': 2023, 'Month': 1, 'GEO_Name': 'CA', 'Index_SA': 412.3, ...}
    """
    try:
        df = _fetch_data()
        
        # Filter for state data
        df = df[df['GEO_Type'] == 'State'].copy()
        
        # Filter for specific state (case-insensitive)
        df = df[df['GEO_Name'].str.upper() == state.upper()]
        
        if len(df) == 0:
            return [{'error': f'State "{state}" not found', 'available_states': get_available_states()}]
        
        # Apply year filters
        if start_year:
            df = df[df['Year'] >= start_year]
        if end_year:
            df = df[df['Year'] <= end_year]
        
        # Sort by year and month
        df = df.sort_values(['Year', 'Month'])
        
        return df.to_dict('records')
    
    except Exception as e:
        return [{'error': str(e), 'source': 'get_state_index', 'state': state}]


def get_metro_index(metro: str, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
    """
    Get metro-level house price index data (CBSA = Core Based Statistical Area).
    
    Args:
        metro: Metro area name (e.g., 'San Francisco', 'New York')
        start_year: Optional start year filter
        end_year: Optional end year filter
    
    Returns:
        List of dicts with Year, Month, Metro, Index_SA, Index_NSA
    
    Example:
        >>> data = get_metro_index('San Francisco', start_year=2023)
        >>> print(len(data))
        36
    """
    try:
        df = _fetch_data()
        
        # Filter for CBSA (metro) data
        df = df[df['GEO_Type'] == 'CBSA'].copy()
        
        # Fuzzy match metro name (case-insensitive substring)
        df = df[df['GEO_Name'].str.contains(metro, case=False, na=False)]
        
        if len(df) == 0:
            return [{'error': f'Metro area matching "{metro}" not found', 
                    'hint': 'Try broader search like "San Francisco" or "New York"'}]
        
        # Apply year filters
        if start_year:
            df = df[df['Year'] >= start_year]
        if end_year:
            df = df[df['Year'] <= end_year]
        
        # Sort by year and month
        df = df.sort_values(['Year', 'Month'])
        
        return df.to_dict('records')
    
    except Exception as e:
        return [{'error': str(e), 'source': 'get_metro_index', 'metro': metro}]


def get_latest_national() -> Dict:
    """
    Get the most recent national house price index value.
    
    Returns:
        Dict with latest Year, Month, Index_SA, Index_NSA
    
    Example:
        >>> latest = get_latest_national()
        >>> print(f"Latest HPI: {latest['Index_SA']} ({latest['Year']}-{latest['Month']})")
        Latest HPI: 297.85 (2026-1)
    """
    try:
        df = _fetch_data()
        
        # Filter for national data
        df = df[df['GEO_Type'] == 'US'].copy()
        
        # Get most recent entry
        df = df.sort_values(['Year', 'Month'], ascending=False)
        
        return df.iloc[0].to_dict() if len(df) > 0 else {'error': 'No data found'}
    
    except Exception as e:
        return {'error': str(e), 'source': 'get_latest_national'}


def get_latest_state(state: str) -> Dict:
    """
    Get the most recent house price index for a specific state.
    
    Args:
        state: State code (e.g., 'CA', 'NY', 'TX')
    
    Returns:
        Dict with latest Year, Month, Index_SA, Index_NSA for that state
    
    Example:
        >>> latest = get_latest_state('CA')
        >>> print(f"California HPI: {latest['Index_SA']} ({latest['Year']}-{latest['Month']})")
    """
    try:
        df = _fetch_data()
        
        # Filter for state data
        df = df[(df['GEO_Type'] == 'State') & (df['GEO_Name'].str.upper() == state.upper())].copy()
        
        if len(df) == 0:
            return {'error': f'State "{state}" not found'}
        
        # Get most recent entry
        df = df.sort_values(['Year', 'Month'], ascending=False)
        
        return df.iloc[0].to_dict()
    
    except Exception as e:
        return {'error': str(e), 'source': 'get_latest_state', 'state': state}


def get_available_states() -> List[str]:
    """
    Get list of all available states in the dataset.
    
    Returns:
        List of state codes
    
    Example:
        >>> states = get_available_states()
        >>> print(states[:5])
        ['AK', 'AL', 'AR', 'AZ', 'CA']
    """
    try:
        df = _fetch_data()
        
        # Filter for state data
        states = df[df['GEO_Type'] == 'State']['GEO_Name'].unique().tolist()
        
        return sorted(states)
    
    except Exception as e:
        return [{'error': str(e), 'source': 'get_available_states'}]


def get_available_metros() -> List[str]:
    """
    Get list of all available metro areas (CBSAs) in the dataset.
    
    Returns:
        List of metro area names
    
    Example:
        >>> metros = get_available_metros()
        >>> print(metros[:3])
        ['Abilene TX', 'Akron OH', 'Albany GA']
    """
    try:
        df = _fetch_data()
        
        # Filter for CBSA (metro) data
        metros = df[df['GEO_Type'] == 'CBSA']['GEO_Name'].unique().tolist()
        
        return sorted(metros)
    
    except Exception as e:
        return [{'error': str(e), 'source': 'get_available_metros'}]


def compare_states(states: List[str], year: int, month: int) -> Dict:
    """
    Compare house price indices across multiple states for a specific month.
    
    Args:
        states: List of state codes (e.g., ['CA', 'NY', 'TX'])
        year: Year to compare
        month: Month to compare (1-12)
    
    Returns:
        Dict mapping state codes to their index values
    
    Example:
        >>> comparison = compare_states(['CA', 'TX', 'NY'], 2025, 12)
        >>> print(comparison)
        {'CA': {'Index_SA': 412.3, ...}, 'TX': {'Index_SA': 285.1, ...}, ...}
    """
    try:
        df = _fetch_data()
        
        # Filter for states, year, and month
        df = df[(df['GEO_Type'] == 'State') & 
                (df['Year'] == year) & 
                (df['Month'] == month)].copy()
        
        # Filter for requested states
        states_upper = [s.upper() for s in states]
        df = df[df['GEO_Name'].str.upper().isin(states_upper)]
        
        # Build comparison dict
        result = {}
        for _, row in df.iterrows():
            result[row['GEO_Name']] = row.to_dict()
        
        return result
    
    except Exception as e:
        return {'error': str(e), 'source': 'compare_states'}


def clear_cache():
    """Clear in-memory cache of downloaded CSV files."""
    global _CACHE
    _CACHE = {}
    return {'status': 'cache_cleared'}


if __name__ == "__main__":
    # Test run
    result = {
        "module": "freddie_mac_house_price_index_dataset",
        "status": "ready",
        "source": "https://www.freddiemac.com/research/indices/house-price-index",
        "data_url": FREDDIE_MAC_URL,
        "functions": [
            "get_national_index",
            "get_state_index",
            "get_metro_index",
            "get_latest_national",
            "get_latest_state",
            "get_available_states",
            "get_available_metros",
            "compare_states",
            "clear_cache"
        ]
    }
    print(json.dumps(result, indent=2))
