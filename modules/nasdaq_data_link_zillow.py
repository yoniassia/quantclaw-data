#!/usr/bin/env python3
"""
Nasdaq Data Link Zillow — Real Estate & Housing Market Data

Provides comprehensive U.S. housing market data from Zillow via Nasdaq Data Link (formerly Quandal).
Includes home values, rental indices, and market indicators for regional housing price tracking.
Falls back to FRED housing series when Nasdaq Data Link requires premium access.

Source: https://data.nasdaq.com/data/ZILLOW
Category: Real Estate & Housing
Free tier: Limited (50 calls/day, 500/month)
Update frequency: Monthly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# API Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3/datasets"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")
FRED_BASE_URL = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "67587f0c539b9b4c15b36c14f543f5f4")

# ========== ZILLOW INDICATOR REGISTRY ==========
ZILLOW_INDICATORS = {
    'ZHVI': 'Zillow Home Value Index',
    'ZSFH': 'Single Family Home Value Index',
    'ZATT': 'All Transactions Home Value Index',
    'ZABT': 'Average Bottom Tier Home Value',
    'ZAMT': 'Average Middle Tier Home Value',
    'ZATT': 'Average Top Tier Home Value',
    'ZRI': 'Zillow Rental Index',
    'ZRIAAH': 'All Homes Rental Index',
}

# FRED Housing Series Fallback
FRED_HOUSING_SERIES = {
    'MSPUS': 'Median Sales Price of Houses Sold for the United States',
    'CSUSHPINSA': 'S&P/Case-Shiller U.S. National Home Price Index',
    'ASPUS': 'Average Sales Price of Houses Sold for the United States',
    'MEDLISPRIPERSQUAM': 'Median Listing Price per Square Meter in the United States',
    'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average in the United States',
}


def _fetch_nasdaq_data(indicator: str, region: str = "United States", limit: int = 100) -> Dict:
    """
    Internal helper to fetch data from Nasdaq Data Link.
    
    Args:
        indicator: Zillow indicator code (ZHVI, ZSFH, etc.)
        region: Geographic region name
        limit: Number of data points to retrieve
        
    Returns:
        Dict with 'data' key on success, 'error' key on failure
    """
    try:
        # Format: ZILLOW/{indicator}_{region}
        # Note: Region codes may need normalization (spaces, capitalization)
        region_code = region.upper().replace(" ", "")
        dataset_code = f"ZILLOW/{indicator}_{region_code}"
        
        url = f"{NASDAQ_BASE_URL}/{dataset_code}.json"
        params = {
            'limit': limit
        }
        
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'data': data.get('dataset', {}),
                'source': 'nasdaq_data_link',
                'dataset_code': dataset_code,
                'retrieved_at': datetime.now().isoformat()
            }
        elif response.status_code == 404:
            return {'error': f'Dataset not found: {dataset_code}'}
        elif response.status_code == 429:
            return {'error': 'Rate limit exceeded. Consider upgrading or using FRED fallback.'}
        else:
            return {'error': f'API error: {response.status_code} - {response.text}'}
            
    except requests.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def _fetch_fred_data(series_id: str, limit: int = 100) -> Dict:
    """
    Internal helper to fetch housing data from FRED as fallback.
    
    Args:
        series_id: FRED series identifier
        limit: Number of observations to retrieve
        
    Returns:
        Dict with 'data' key on success, 'error' key on failure
    """
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': limit,
            'sort_order': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'data': data.get('observations', []),
                'source': 'fred',
                'series_id': series_id,
                'retrieved_at': datetime.now().isoformat()
            }
        else:
            return {'error': f'FRED API error: {response.status_code}'}
            
    except Exception as e:
        return {'error': f'FRED fallback failed: {str(e)}'}


def get_zillow_home_values(region: str = "United States", indicator: str = "ZHVI", limit: int = 100) -> Dict:
    """
    Get Zillow Home Value Index for a specific region.
    
    Args:
        region: Geographic region (default: "United States")
        indicator: Zillow indicator code (default: "ZHVI")
        limit: Number of data points to retrieve
        
    Returns:
        Dict with 'data' key containing home values, or 'error' key on failure
        
    Example:
        >>> result = get_zillow_home_values(region="New York", indicator="ZHVI")
        >>> if 'data' in result:
        >>>     print(result['data'])
    """
    # Try Nasdaq Data Link first
    result = _fetch_nasdaq_data(indicator, region, limit)
    
    # Fallback to FRED if Nasdaq fails
    if 'error' in result and region == "United States":
        fallback_result = _fetch_fred_data('MSPUS', limit)
        if 'data' in fallback_result:
            fallback_result['note'] = 'Using FRED Median Sales Price as fallback'
            return fallback_result
    
    return result


def get_zillow_rental_index(region: str = "United States", limit: int = 100) -> Dict:
    """
    Get Zillow Rental Index for a specific region.
    
    Args:
        region: Geographic region (default: "United States")
        limit: Number of data points to retrieve
        
    Returns:
        Dict with 'data' key containing rental index, or 'error' key on failure
        
    Example:
        >>> result = get_zillow_rental_index(region="Los Angeles")
        >>> if 'data' in result:
        >>>     print(result['data'])
    """
    return _fetch_nasdaq_data('ZRI', region, limit)


def search_zillow_datasets(query: str, per_page: int = 10) -> Dict:
    """
    Search available Zillow datasets on Nasdaq Data Link.
    
    Args:
        query: Search query string
        per_page: Results per page (default: 10)
        
    Returns:
        Dict with 'data' key containing search results, or 'error' key on failure
        
    Example:
        >>> result = search_zillow_datasets("rental")
        >>> if 'data' in result:
        >>>     for dataset in result['data']:
        >>>         print(dataset['name'])
    """
    try:
        url = "https://data.nasdaq.com/api/v3/datasets.json"
        params = {
            'query': f'zillow {query}',
            'per_page': per_page,
            'database_code': 'ZILLOW'
        }
        
        if NASDAQ_API_KEY:
            params['api_key'] = NASDAQ_API_KEY
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'data': data.get('datasets', []),
                'source': 'nasdaq_data_link_search',
                'query': query,
                'retrieved_at': datetime.now().isoformat()
            }
        else:
            return {'error': f'Search failed: {response.status_code}'}
            
    except Exception as e:
        return {'error': f'Search error: {str(e)}'}


def get_zillow_metro_comparison(metros: List[str] = None, indicator: str = "ZHVI", limit: int = 50) -> Dict:
    """
    Compare housing metrics across multiple metro areas.
    
    Args:
        metros: List of metro area names (default: ["New York", "Los Angeles", "Chicago"])
        indicator: Zillow indicator code (default: "ZHVI")
        limit: Number of data points per metro
        
    Returns:
        Dict with 'data' key containing comparison data, or 'error' key on failure
        
    Example:
        >>> metros = ["New York", "San Francisco", "Austin"]
        >>> result = get_zillow_metro_comparison(metros=metros)
        >>> if 'data' in result:
        >>>     for metro, values in result['data'].items():
        >>>         print(f"{metro}: {values}")
    """
    if metros is None:
        metros = ["New York", "Los Angeles", "Chicago"]
        
    try:
        comparison_data = {}
        errors = []
        
        for metro in metros:
            result = _fetch_nasdaq_data(indicator, metro, limit)
            
            if 'data' in result:
                comparison_data[metro] = result['data']
            else:
                errors.append(f"{metro}: {result.get('error', 'Unknown error')}")
        
        if not comparison_data:
            return {
                'error': 'No data retrieved for any metro area',
                'details': errors
            }
        
        return {
            'data': comparison_data,
            'metros_retrieved': len(comparison_data),
            'metros_failed': len(errors),
            'errors': errors if errors else None,
            'indicator': indicator,
            'retrieved_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Metro comparison failed: {str(e)}'}


# ========== MODULE METADATA ==========
def get_module_info() -> Dict:
    """Get module metadata and status."""
    return {
        'module': 'nasdaq_data_link_zillow',
        'version': '1.0.0',
        'source': 'https://data.nasdaq.com/data/ZILLOW',
        'category': 'Real Estate & Housing',
        'free_tier': 'Limited (50 calls/day, 500/month)',
        'functions': [
            'get_zillow_home_values',
            'get_zillow_rental_index',
            'search_zillow_datasets',
            'get_zillow_metro_comparison'
        ],
        'has_api_key': bool(NASDAQ_API_KEY),
        'fred_fallback': bool(FRED_API_KEY)
    }


if __name__ == "__main__":
    print(json.dumps(get_module_info(), indent=2))
