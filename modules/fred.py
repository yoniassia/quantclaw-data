"""
FRED (Federal Reserve Economic Data) Module

Simple, focused module for accessing Federal Reserve economic data.
Covers the most essential economic indicators including bond yields,
credit spreads, and interest rates.

Data Source: Federal Reserve Bank of St. Louis (FRED)
Update: Daily to monthly depending on series
Free: Yes (API key optional for higher rate limits)
API Docs: https://fred.stlouisfed.org/docs/api/fred.html

Key Series:
- Treasury yields (all maturities)
- Corporate bond spreads
- Fed Funds Rate
- Inflation indicators (CPI, PCE)
- GDP and employment data
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

# FRED API Configuration
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")  # Optional for basic usage

# Cache directory
CACHE_DIR = Path.home() / ".quantclaw" / "cache" / "fred"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Common economic series
COMMON_SERIES = {
    # Treasury Yields
    'DGS1MO': '1-Month Treasury',
    'DGS3MO': '3-Month Treasury',
    'DGS6MO': '6-Month Treasury',
    'DGS1': '1-Year Treasury',
    'DGS2': '2-Year Treasury',
    'DGS5': '5-Year Treasury',
    'DGS10': '10-Year Treasury',
    'DGS30': '30-Year Treasury',
    
    # Key Spreads
    'T10Y2Y': '10Y-2Y Spread',
    'T10Y3M': '10Y-3M Spread',
    'TEDRATE': 'TED Spread',
    
    # Interest Rates
    'FEDFUNDS': 'Federal Funds Rate',
    'DFF': 'Fed Funds Effective Rate',
    'MORTGAGE30US': '30-Year Mortgage Rate',
    
    # Inflation
    'CPIAUCSL': 'CPI (All Items)',
    'CPILFESL': 'Core CPI',
    'PCEPI': 'PCE Price Index',
    'PCEPILFE': 'Core PCE',
    
    # Credit Spreads
    'BAMLC0A0CM': 'Corp Bond Spread (IG)',
    'BAMLH0A0HYM2': 'High Yield Spread',
    
    # Economy
    'GDP': 'Gross Domestic Product',
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'Nonfarm Payrolls',
}


def get_series(series_id: str, 
               start_date: Optional[str] = None,
               end_date: Optional[str] = None,
               limit: int = 100,
               use_cache: bool = True) -> Dict:
    """
    Fetch economic data for a specific FRED series.
    
    Args:
        series_id: FRED series ID (e.g., 'DGS10' for 10-year treasury)
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        limit: Maximum number of observations (default: 100)
        use_cache: Whether to use cached data if available (default: True)
    
    Returns:
        dict: {
            'series_id': str,
            'name': str,
            'units': str,
            'frequency': str,
            'data': [{'date': str, 'value': float}, ...],
            'latest_value': float,
            'latest_date': str,
            'source': 'FRED'
        }
    """
    # Set defaults
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Check cache
    cache_file = CACHE_DIR / f"{series_id}_{start_date}_{end_date}.json"
    if use_cache and cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age < timedelta(hours=6):  # Cache for 6 hours
            with open(cache_file) as f:
                return json.load(f)
    
    try:
        # Build API URL
        params = {
            'series_id': series_id,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'limit': limit,
            'sort_order': 'desc'
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        # Fetch observations
        obs_url = f"{FRED_BASE_URL}/series/observations"
        response = requests.get(obs_url, params=params, timeout=10)
        response.raise_for_status()
        obs_data = response.json()
        
        # Fetch series metadata
        meta_params = {
            'series_id': series_id,
            'file_type': 'json'
        }
        if FRED_API_KEY:
            meta_params['api_key'] = FRED_API_KEY
            
        meta_url = f"{FRED_BASE_URL}/series"
        meta_response = requests.get(meta_url, params=meta_params, timeout=10)
        meta_response.raise_for_status()
        meta_data = meta_response.json()
        
        # Parse observations
        observations = []
        for obs in obs_data.get('observations', []):
            if obs['value'] != '.':  # FRED uses '.' for missing values
                try:
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
                except (ValueError, KeyError):
                    continue
        
        # Sort by date ascending
        observations.sort(key=lambda x: x['date'])
        
        # Build result
        series_info = meta_data.get('seriess', [{}])[0]
        result = {
            'series_id': series_id,
            'name': series_info.get('title', series_id),
            'units': series_info.get('units', 'N/A'),
            'frequency': series_info.get('frequency', 'N/A'),
            'data': observations,
            'latest_value': observations[-1]['value'] if observations else None,
            'latest_date': observations[-1]['date'] if observations else None,
            'source': 'FRED'
        }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f)
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'error': f'API request failed: {str(e)}',
            'series_id': series_id,
            'source': 'FRED'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'series_id': series_id,
            'source': 'FRED'
        }


def get_yield_curve(date: Optional[str] = None) -> Dict:
    """
    Get the full Treasury yield curve for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
    
    Returns:
        dict: {
            'date': str,
            'yields': {'1MO': float, '3MO': float, ..., '30Y': float},
            'spreads': {'10Y-2Y': float, '10Y-3M': float},
            'inverted': bool,
            'source': 'FRED'
        }
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Fetch all treasury maturities
    maturities = {
        '1MO': 'DGS1MO',
        '3MO': 'DGS3MO',
        '6MO': 'DGS6MO',
        '1Y': 'DGS1',
        '2Y': 'DGS2',
        '5Y': 'DGS5',
        '10Y': 'DGS10',
        '30Y': 'DGS30'
    }
    
    yields = {}
    for label, series_id in maturities.items():
        data = get_series(series_id, start_date=date, end_date=date, limit=1)
        if 'latest_value' in data and data['latest_value'] is not None:
            yields[label] = data['latest_value']
    
    # Calculate spreads
    spreads = {}
    if '10Y' in yields and '2Y' in yields:
        spreads['10Y-2Y'] = yields['10Y'] - yields['2Y']
    if '10Y' in yields and '3MO' in yields:
        spreads['10Y-3M'] = yields['10Y'] - yields['3MO']
    
    # Check if inverted
    inverted = any(spread < 0 for spread in spreads.values())
    
    return {
        'date': date,
        'yields': yields,
        'spreads': spreads,
        'inverted': inverted,
        'source': 'FRED'
    }


def get_credit_spreads() -> Dict:
    """
    Get current corporate bond and high-yield credit spreads.
    
    Returns:
        dict: {
            'investment_grade': float (basis points),
            'high_yield': float (basis points),
            'date': str,
            'source': 'FRED'
        }
    """
    ig = get_series('BAMLC0A0CM', limit=1)  # Investment Grade
    hy = get_series('BAMLH0A0HYM2', limit=1)  # High Yield
    
    return {
        'investment_grade': ig.get('latest_value'),
        'high_yield': hy.get('latest_value'),
        'date': ig.get('latest_date'),
        'source': 'FRED'
    }


def get_fed_rates() -> Dict:
    """
    Get current Federal Reserve interest rates.
    
    Returns:
        dict: {
            'fed_funds_rate': float,
            'fed_funds_effective': float,
            'date': str,
            'source': 'FRED'
        }
    """
    fedfunds = get_series('FEDFUNDS', limit=1)
    dff = get_series('DFF', limit=1)
    
    return {
        'fed_funds_rate': fedfunds.get('latest_value'),
        'fed_funds_effective': dff.get('latest_value'),
        'date': fedfunds.get('latest_date'),
        'source': 'FRED'
    }


def get_inflation_indicators() -> Dict:
    """
    Get current inflation indicators (CPI and PCE).
    
    Returns:
        dict: {
            'cpi_all': float (YoY %),
            'cpi_core': float (YoY %),
            'pce': float (YoY %),
            'pce_core': float (YoY %),
            'date': str,
            'source': 'FRED'
        }
    """
    # Get latest 13 months to calculate YoY
    cpi = get_series('CPIAUCSL', limit=13)
    cpi_core = get_series('CPILFESL', limit=13)
    pce = get_series('PCEPI', limit=13)
    pce_core = get_series('PCEPILFE', limit=13)
    
    def calc_yoy(data):
        """Calculate year-over-year percentage change"""
        if 'data' in data and len(data['data']) >= 13:
            latest = data['data'][-1]['value']
            year_ago = data['data'][0]['value']
            return round(((latest / year_ago) - 1) * 100, 2)
        return None
    
    return {
        'cpi_all': calc_yoy(cpi),
        'cpi_core': calc_yoy(cpi_core),
        'pce': calc_yoy(pce),
        'pce_core': calc_yoy(pce_core),
        'date': cpi.get('latest_date'),
        'source': 'FRED'
    }


def search_series(search_text: str, limit: int = 10) -> List[Dict]:
    """
    Search for FRED series by keyword.
    
    Args:
        search_text: Search query (e.g., "unemployment", "inflation")
        limit: Maximum number of results (default: 10)
    
    Returns:
        list: [{
            'id': str,
            'title': str,
            'frequency': str,
            'units': str,
            'popularity': int
        }, ...]
    """
    try:
        params = {
            'search_text': search_text,
            'file_type': 'json',
            'limit': limit,
            'sort_order': 'popularity',
            'order_by': 'popularity'
        }
        
        if FRED_API_KEY:
            params['api_key'] = FRED_API_KEY
        
        url = f"{FRED_BASE_URL}/series/search"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for series in data.get('seriess', []):
            results.append({
                'id': series.get('id'),
                'title': series.get('title'),
                'frequency': series.get('frequency'),
                'units': series.get('units'),
                'popularity': series.get('popularity', 0)
            })
        
        return results
        
    except Exception as e:
        return [{'error': f'Search failed: {str(e)}'}]


def get_latest_value(series_id: str) -> Optional[float]:
    """
    Quick helper to get just the latest value for a series.
    
    Args:
        series_id: FRED series ID
    
    Returns:
        float: Latest value or None if error
    """
    data = get_series(series_id, limit=1)
    return data.get('latest_value')


# Convenience aliases
def get_10y_treasury() -> Optional[float]:
    """Get current 10-year Treasury yield"""
    return get_latest_value('DGS10')


def get_2y_treasury() -> Optional[float]:
    """Get current 2-year Treasury yield"""
    return get_latest_value('DGS2')


def get_unemployment_rate() -> Optional[float]:
    """Get current unemployment rate"""
    return get_latest_value('UNRATE')


if __name__ == '__main__':
    # Test the module
    print("Testing FRED module...")
    
    print("\n1. 10-Year Treasury:")
    print(get_10y_treasury())
    
    print("\n2. Yield Curve:")
    print(json.dumps(get_yield_curve(), indent=2))
    
    print("\n3. Credit Spreads:")
    print(json.dumps(get_credit_spreads(), indent=2))
    
    print("\n4. Fed Rates:")
    print(json.dumps(get_fed_rates(), indent=2))
