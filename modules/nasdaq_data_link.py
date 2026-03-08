#!/usr/bin/env python3
"""
Nasdaq Data Link Module (formerly Quandl)

Access free financial and economic datasets via Nasdaq Data Link API.
- Time-series data for commodities, economics, and markets
- Free datasets: FRED, Yale/Shiller, Multpl, Bitcoin, etc.
- Metadata search and dataset discovery

Data Sources:
- Nasdaq Data Link API v3: https://data.nasdaq.com/docs
- Free tier: 50 API calls/day (300 with free API key)
- No API key required for many free datasets
Refresh: Daily (varies by dataset)
Coverage: Thousands of free datasets across economics, finance, commodities

Author: QUANTCLAW DATA NightBuilder
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Nasdaq Data Link API Configuration
# Free API key from: https://data.nasdaq.com/sign-up
# Optional - many free datasets work without key (lower rate limit)
API_KEY = os.getenv('NASDAQ_DATA_LINK_API_KEY', os.getenv('QUANDL_API_KEY', ''))
BASE_URL = "https://data.nasdaq.com/api/v3"

# Popular free datasets (no premium subscription needed)
FREE_DATASETS = {
    'FRED': {
        'database': 'FRED',
        'description': 'Federal Reserve Economic Data',
        'examples': ['GDP', 'UNRATE', 'DFF', 'CPIAUCSL', 'T10Y2Y', 'M2SL', 'FEDFUNDS']
    },
    'MULTPL': {
        'database': 'MULTPL',
        'description': 'S&P 500 Ratios and Statistics',
        'examples': ['SP500_PE_RATIO_MONTH', 'SP500_DIV_YIELD_MONTH', 'SHILLER_PE_RATIO_MONTH',
                     'SP500_EARNINGS_YIELD_MONTH', 'SP500_REAL_PRICE_MONTH']
    },
    'USTREASURY': {
        'database': 'USTREASURY',
        'description': 'US Treasury Rates',
        'examples': ['YIELD', 'REALYIELD', 'BILLRATES']
    },
    'BITFINEX': {
        'database': 'BITFINEX',
        'description': 'Bitfinex Crypto Exchange Data',
        'examples': ['BTCUSD', 'ETHUSD', 'LTCUSD']
    },
    'LBMA': {
        'database': 'LBMA',
        'description': 'London Bullion Market Association',
        'examples': ['GOLD', 'SILVER']
    },
    'ODA': {
        'database': 'ODA',
        'description': 'IMF Cross Country Macroeconomic Statistics',
        'examples': ['USA_NGDP', 'USA_PCPIPCH', 'CHN_NGDP']
    },
}


def _make_request(endpoint: str, params: Optional[Dict] = None, timeout: int = 15) -> Dict:
    """Make authenticated request to Nasdaq Data Link API.

    Args:
        endpoint: API endpoint path (appended to BASE_URL)
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response as dict

    Raises:
        requests.RequestException: On network/API errors
    """
    if params is None:
        params = {}
    if API_KEY:
        params['api_key'] = API_KEY

    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_dataset(database_code: str, dataset_code: str, start_date: Optional[str] = None,
                end_date: Optional[str] = None, limit: int = 100,
                order: str = 'desc', column_index: Optional[int] = None) -> Dict:
    """Fetch time-series dataset from Nasdaq Data Link.

    Args:
        database_code: Database code (e.g. 'FRED', 'MULTPL', 'USTREASURY')
        dataset_code: Dataset code within database (e.g. 'GDP', 'SP500_PE_RATIO_MONTH')
        start_date: Start date filter 'YYYY-MM-DD' (optional)
        end_date: End date filter 'YYYY-MM-DD' (optional)
        limit: Max rows to return (default 100)
        order: Sort order - 'desc' (newest first) or 'asc' (oldest first)
        column_index: Return only specific column by index (optional)

    Returns:
        Dict with dataset metadata and data rows

    Example:
        >>> get_dataset('FRED', 'GDP', limit=5)
        {'name': 'Gross Domestic Product', 'data': [['2024-01-01', 28269.527], ...]}
    """
    params = {'limit': limit, 'order': order}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if column_index is not None:
        params['column_index'] = column_index

    try:
        raw = _make_request(f"datasets/{database_code}/{dataset_code}.json", params)
        ds = raw.get('dataset', {})
        return {
            'name': ds.get('name', ''),
            'database_code': ds.get('database_code', database_code),
            'dataset_code': ds.get('dataset_code', dataset_code),
            'description': ds.get('description', '')[:300],
            'frequency': ds.get('frequency', ''),
            'newest_available_date': ds.get('newest_available_date', ''),
            'oldest_available_date': ds.get('oldest_available_date', ''),
            'column_names': ds.get('column_names', []),
            'data': ds.get('data', []),
            'refreshed_at': ds.get('refreshed_at', ''),
            'source': f"https://data.nasdaq.com/{database_code}/{dataset_code}",
            'fetched_at': datetime.utcnow().isoformat()
        }
    except requests.RequestException as e:
        return {'error': str(e), 'database_code': database_code, 'dataset_code': dataset_code}


def get_fred_series(series_id: str, limit: int = 100, start_date: Optional[str] = None) -> Dict:
    """Fetch a FRED economic data series via Nasdaq Data Link.

    Args:
        series_id: FRED series code (e.g. 'GDP', 'UNRATE', 'DFF', 'CPIAUCSL', 'T10Y2Y')
        limit: Max data points to return
        start_date: Optional start date 'YYYY-MM-DD'

    Returns:
        Dict with series name, data points, and metadata

    Example:
        >>> get_fred_series('GDP', limit=4)
    """
    return get_dataset('FRED', series_id, limit=limit, start_date=start_date)


def get_sp500_ratios() -> Dict:
    """Fetch key S&P 500 valuation ratios from MULTPL database.

    Returns:
        Dict with PE ratio, dividend yield, Shiller PE, earnings yield (latest values)
    """
    ratios = {}
    ratio_map = {
        'pe_ratio': 'SP500_PE_RATIO_MONTH',
        'div_yield': 'SP500_DIV_YIELD_MONTH',
        'shiller_pe': 'SHILLER_PE_RATIO_MONTH',
        'earnings_yield': 'SP500_EARNINGS_YIELD_MONTH',
    }
    for key, code in ratio_map.items():
        try:
            result = get_dataset('MULTPL', code, limit=1)
            if result.get('data'):
                row = result['data'][0]
                ratios[key] = {'date': row[0], 'value': row[1]}
            else:
                ratios[key] = {'error': 'no data'}
        except Exception as e:
            ratios[key] = {'error': str(e)}

    ratios['fetched_at'] = datetime.utcnow().isoformat()
    ratios['source'] = 'Nasdaq Data Link / MULTPL'
    return ratios


def get_treasury_yields() -> Dict:
    """Fetch latest US Treasury yield curve data.

    Returns:
        Dict with yield curve data across maturities
    """
    try:
        result = get_dataset('USTREASURY', 'YIELD', limit=5)
        if result.get('error'):
            return result

        columns = result.get('column_names', [])
        rows = result.get('data', [])
        yields = []
        for row in rows:
            entry = {}
            for i, col in enumerate(columns):
                entry[col] = row[i] if i < len(row) else None
            yields.append(entry)

        return {
            'yields': yields,
            'latest_date': rows[0][0] if rows else None,
            'column_names': columns,
            'source': 'US Treasury via Nasdaq Data Link',
            'fetched_at': datetime.utcnow().isoformat()
        }
    except requests.RequestException as e:
        return {'error': str(e)}


def get_precious_metals(metal: str = 'GOLD', limit: int = 30) -> Dict:
    """Fetch precious metal prices from London Bullion Market (LBMA).

    Args:
        metal: 'GOLD' or 'SILVER'
        limit: Number of data points

    Returns:
        Dict with price history and metadata
    """
    metal = metal.upper()
    if metal not in ('GOLD', 'SILVER'):
        return {'error': f'Unsupported metal: {metal}. Use GOLD or SILVER'}
    return get_dataset('LBMA', metal, limit=limit)


def search_datasets(query: str, database_code: Optional[str] = None,
                    per_page: int = 10, page: int = 1) -> List[Dict]:
    """Search for datasets on Nasdaq Data Link.

    Args:
        query: Search query string
        database_code: Optionally restrict to a specific database
        per_page: Results per page (max 100)
        page: Page number

    Returns:
        List of matching dataset summaries

    Example:
        >>> search_datasets('oil price', per_page=3)
    """
    params = {'query': query, 'per_page': per_page, 'page': page}
    if database_code:
        params['database_code'] = database_code

    try:
        raw = _make_request('datasets.json', params)
        datasets = raw.get('datasets', [])
        return [{
            'database_code': ds.get('database_code', ''),
            'dataset_code': ds.get('dataset_code', ''),
            'name': ds.get('name', ''),
            'description': (ds.get('description', '') or '')[:200],
            'frequency': ds.get('frequency', ''),
            'newest_available_date': ds.get('newest_available_date', ''),
            'type': ds.get('type', ''),
        } for ds in datasets]
    except requests.RequestException as e:
        return [{'error': str(e)}]


def get_database_metadata(database_code: str) -> Dict:
    """Fetch metadata about a Nasdaq Data Link database.

    Args:
        database_code: Database code (e.g. 'FRED', 'MULTPL')

    Returns:
        Dict with database name, description, dataset count, etc.
    """
    try:
        raw = _make_request(f"databases/{database_code}.json")
        db = raw.get('database', {})
        return {
            'code': db.get('database_code', database_code),
            'name': db.get('name', ''),
            'description': (db.get('description', '') or '')[:500],
            'datasets_count': db.get('datasets_count', 0),
            'image': db.get('image', ''),
            'premium': db.get('premium', False),
            'fetched_at': datetime.utcnow().isoformat()
        }
    except requests.RequestException as e:
        return {'error': str(e), 'database_code': database_code}


def list_free_databases() -> List[Dict]:
    """List curated free databases available on Nasdaq Data Link.

    Returns:
        List of free database summaries with example dataset codes
    """
    result = []
    for key, info in FREE_DATASETS.items():
        result.append({
            'code': info['database'],
            'description': info['description'],
            'example_datasets': info['examples']
        })
    return result


def get_dataset_latest(database_code: str, dataset_code: str) -> Dict:
    """Get the single most recent data point from a dataset.

    Args:
        database_code: Database code
        dataset_code: Dataset code

    Returns:
        Dict with latest date, value(s), and metadata
    """
    result = get_dataset(database_code, dataset_code, limit=1)
    if result.get('error'):
        return result

    data = result.get('data', [])
    columns = result.get('column_names', [])
    if not data:
        return {'error': 'no data available', 'dataset': f'{database_code}/{dataset_code}'}

    latest = {}
    for i, col in enumerate(columns):
        latest[col] = data[0][i] if i < len(data[0]) else None

    return {
        'dataset': f'{database_code}/{dataset_code}',
        'name': result.get('name', ''),
        'latest': latest,
        'newest_available_date': result.get('newest_available_date', ''),
        'fetched_at': datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    print(json.dumps({
        "module": "nasdaq_data_link",
        "status": "active",
        "functions": [
            "get_dataset", "get_fred_series", "get_sp500_ratios",
            "get_treasury_yields", "get_precious_metals", "search_datasets",
            "get_database_metadata", "list_free_databases", "get_dataset_latest"
        ],
        "source": "https://data.nasdaq.com/docs"
    }, indent=2))
