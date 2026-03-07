#!/usr/bin/env python3
"""
Nasdaq Data Link (Emerging Markets Datasets) — QuantClaw Data Module

Access free emerging market equity data from Nasdaq Data Link (formerly Quandl).
Covers India NSE/BSE, Hong Kong HKEX, and other emerging market datasets.
Provides historical prices and fundamentals for quantitative backtesting.

Source: https://data.nasdaq.com/
Category: Emerging Markets
Free tier: True - 50 API calls per day without key, unlimited with free registration
Update frequency: Daily
Author: QuantClaw Data NightBuilder
Phase: NightBuilder

API Endpoints:
- Dataset: https://data.nasdaq.com/api/v3/datasets/{database}/{dataset}.json
- Search: https://data.nasdaq.com/api/v3/datasets.json?query={query}
- Metadata: https://data.nasdaq.com/api/v3/datasets/{database}/{dataset}/metadata.json
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Nasdaq Data Link API Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY") or os.environ.get("QUANDL_API_KEY", "")

# ========== EMERGING MARKETS DATABASE CODES ==========

EM_DATABASES = {
    'NSE': 'National Stock Exchange of India',
    'BSE': 'Bombay Stock Exchange (India)',
    'HKEX': 'Hong Kong Stock Exchange',
    'WIKI': 'Wiki EOD Stock Prices (Legacy Free - includes US stocks)',
    'SSE': 'Shanghai Stock Exchange',
    'SZSE': 'Shenzhen Stock Exchange',
}

# Common EM index datasets
EM_INDICES = {
    'india_nifty50': ('NSE', 'NIFTY_50'),
    'india_sensex': ('BSE', 'SENSEX'),
    'hong_kong_hsi': ('HKEX', 'HSI'),
}


# ========== CORE API FUNCTIONS ==========

def _make_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Internal helper to make API requests to Nasdaq Data Link.
    
    Args:
        endpoint: API endpoint path (e.g., 'datasets/NSE/TATAMOTORS')
        params: Optional query parameters
        
    Returns:
        Dict containing parsed JSON response
        
    Raises:
        Exception: If API request fails
    """
    url = f"{NASDAQ_BASE_URL}/{endpoint}"
    
    # Add API key if available (optional for free tier)
    if params is None:
        params = {}
    if NASDAQ_API_KEY:
        params['api_key'] = NASDAQ_API_KEY
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'endpoint': endpoint,
            'status': 'failed',
            'message': f'Nasdaq Data Link API request failed: {e}'
        }


def get_dataset(database: str, dataset: str, start_date: Optional[str] = None, 
                end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch a dataset from Nasdaq Data Link.
    
    Args:
        database: Database code (e.g., 'NSE', 'BSE', 'WIKI')
        dataset: Dataset code (e.g., 'TATAMOTORS', 'AAPL')
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dict containing dataset metadata and data points
        
    Example:
        >>> data = get_dataset('WIKI', 'AAPL', limit=10)
        >>> print(data['dataset']['name'])
    """
    endpoint = f"datasets/{database}/{dataset}.json"
    
    params = {'limit': limit}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    result = _make_request(endpoint, params)
    
    if 'error' in result:
        return result
    
    # Add convenience metadata
    if 'dataset' in result:
        result['dataset']['_fetched_at'] = datetime.utcnow().isoformat()
        result['dataset']['_database'] = database
        result['dataset']['_dataset_code'] = dataset
    
    return result


def get_nse_stock(symbol: str, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch stock data from India's National Stock Exchange (NSE).
    
    Args:
        symbol: NSE stock symbol (e.g., 'TATAMOTORS', 'RELIANCE', 'INFY')
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dict containing NSE stock data
        
    Example:
        >>> data = get_nse_stock('TATAMOTORS', limit=5)
        >>> if 'dataset' in data:
        >>>     print(f"Latest close: {data['dataset']['data'][0]}")
    """
    return get_dataset('NSE', symbol.upper(), start_date, end_date, limit)


def get_bse_stock(symbol: str, start_date: Optional[str] = None,
                  end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch stock data from Bombay Stock Exchange (BSE).
    
    Args:
        symbol: BSE stock symbol (e.g., 'BOM500112' for State Bank of India)
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dict containing BSE stock data
        
    Example:
        >>> data = get_bse_stock('BOM500112', limit=5)
    """
    return get_dataset('BSE', symbol.upper(), start_date, end_date, limit)


def get_hkex_stock(symbol: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch stock data from Hong Kong Stock Exchange (HKEX).
    
    Args:
        symbol: HKEX stock symbol (e.g., '00700' for Tencent)
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dict containing HKEX stock data
        
    Example:
        >>> data = get_hkex_stock('00700', limit=5)  # Tencent
    """
    return get_dataset('HKEX', symbol, start_date, end_date, limit)


def search_datasets(query: str, per_page: int = 10, page: int = 1) -> Dict[str, Any]:
    """
    Search for datasets across all Nasdaq Data Link databases.
    
    Args:
        query: Search query string (e.g., 'emerging markets', 'india stock')
        per_page: Results per page (default 10, max 100)
        page: Page number (default 1)
        
    Returns:
        Dict containing search results with dataset metadata
        
    Example:
        >>> results = search_datasets('india nse', per_page=5)
        >>> for ds in results.get('datasets', []):
        >>>     print(f"{ds['database_code']}/{ds['dataset_code']}: {ds['name']}")
    """
    endpoint = "datasets.json"
    
    params = {
        'query': query,
        'per_page': min(per_page, 100),
        'page': page
    }
    
    result = _make_request(endpoint, params)
    
    if 'error' in result:
        return result
    
    # Add convenience metadata
    result['_search_query'] = query
    result['_fetched_at'] = datetime.utcnow().isoformat()
    
    return result


def get_emerging_market_index(market: str, start_date: Optional[str] = None,
                               end_date: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch major emerging market index data.
    
    Args:
        market: Market identifier - 'india_nifty50', 'india_sensex', 'hong_kong_hsi'
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Maximum number of rows to return (default 100)
        
    Returns:
        Dict containing index data
        
    Example:
        >>> data = get_emerging_market_index('india_nifty50', limit=10)
        >>> if 'dataset' in data:
        >>>     print(f"Index: {data['dataset']['name']}")
    """
    market_lower = market.lower()
    
    if market_lower not in EM_INDICES:
        return {
            'error': 'Invalid market identifier',
            'valid_markets': list(EM_INDICES.keys()),
            'requested': market,
            'status': 'failed'
        }
    
    database, dataset_code = EM_INDICES[market_lower]
    return get_dataset(database, dataset_code, start_date, end_date, limit)


def get_dataset_metadata(database: str, dataset: str) -> Dict[str, Any]:
    """
    Fetch metadata for a specific dataset without pulling data.
    
    Args:
        database: Database code (e.g., 'NSE', 'BSE')
        dataset: Dataset code (e.g., 'TATAMOTORS')
        
    Returns:
        Dict containing dataset metadata (description, column names, frequency, etc.)
        
    Example:
        >>> meta = get_dataset_metadata('NSE', 'TATAMOTORS')
        >>> print(meta['dataset']['column_names'])
    """
    endpoint = f"datasets/{database}/{dataset}/metadata.json"
    
    result = _make_request(endpoint)
    
    if 'error' in result:
        return result
    
    if 'dataset' in result:
        result['dataset']['_fetched_at'] = datetime.utcnow().isoformat()
    
    return result


def list_available_databases() -> Dict[str, str]:
    """
    List all known emerging market databases supported by this module.
    
    Returns:
        Dict mapping database codes to descriptions
        
    Example:
        >>> dbs = list_available_databases()
        >>> for code, name in dbs.items():
        >>>     print(f"{code}: {name}")
    """
    return EM_DATABASES.copy()


# ========== CONVENIENCE FUNCTIONS ==========

def get_latest_price(database: str, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent price data for a stock.
    
    Args:
        database: Database code ('NSE', 'BSE', 'HKEX', etc.)
        symbol: Stock symbol
        
    Returns:
        Dict with latest price data or None if unavailable
        
    Example:
        >>> latest = get_latest_price('NSE', 'TATAMOTORS')
        >>> if latest:
        >>>     print(f"Close: {latest['close']}, Date: {latest['date']}")
    """
    result = get_dataset(database, symbol, limit=1)
    
    if 'error' in result or 'dataset' not in result:
        return None
    
    dataset = result['dataset']
    if not dataset.get('data'):
        return None
    
    # Map column names to values
    columns = dataset.get('column_names', [])
    values = dataset['data'][0]
    
    latest = dict(zip(columns, values))
    latest['_symbol'] = symbol
    latest['_database'] = database
    
    return latest


# ========== MODULE INFO ==========

def get_module_info() -> Dict[str, Any]:
    """
    Get information about this module.
    
    Returns:
        Dict containing module metadata
    """
    return {
        'module': 'nasdaq_data_link_emerging_markets_datasets',
        'version': '1.0.0',
        'source': 'https://data.nasdaq.com/',
        'category': 'Emerging Markets',
        'free_tier': True,
        'api_key_required': False,
        'api_key_configured': bool(NASDAQ_API_KEY),
        'rate_limit': '50 calls/day without key, unlimited with free registration',
        'supported_databases': list(EM_DATABASES.keys()),
        'supported_indices': list(EM_INDICES.keys()),
        'functions': [
            'get_dataset',
            'get_nse_stock',
            'get_bse_stock',
            'get_hkex_stock',
            'search_datasets',
            'get_emerging_market_index',
            'get_dataset_metadata',
            'get_latest_price',
            'list_available_databases',
        ]
    }


if __name__ == "__main__":
    # Module self-test
    info = get_module_info()
    print(json.dumps(info, indent=2))
    
    print("\n--- Testing search_datasets ---")
    search_result = search_datasets('india nse', per_page=3)
    if 'datasets' in search_result:
        print(f"Found {len(search_result['datasets'])} datasets")
        for ds in search_result['datasets'][:3]:
            print(f"  - {ds['database_code']}/{ds['dataset_code']}: {ds['name']}")
    else:
        print(f"Search error: {search_result.get('error', 'Unknown')}")
    
    print("\n--- Testing get_dataset (WIKI/AAPL) ---")
    wiki_result = get_dataset('WIKI', 'AAPL', limit=3)
    if 'dataset' in wiki_result:
        print(f"Dataset: {wiki_result['dataset']['name']}")
        print(f"Latest {len(wiki_result['dataset']['data'])} rows:")
        for row in wiki_result['dataset']['data'][:3]:
            print(f"  {row[0]}: Close {row[4] if len(row) > 4 else 'N/A'}")
    else:
        print(f"Dataset error: {wiki_result.get('error', 'Unknown')}")
