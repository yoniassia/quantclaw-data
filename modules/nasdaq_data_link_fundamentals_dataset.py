#!/usr/bin/env python3
"""
Nasdaq Data Link Fundamentals Dataset (SHARADAR SF1)

Provides access to Sharadar Core US Fundamentals dataset via Nasdaq Data Link API.
Free tier provides sample data for testing and development. Covers:
- Quarterly and annual financial statements
- Key financial ratios and metrics
- Revenue, earnings, and cash flow data
- Balance sheet, income statement, cash flow statement items

Source: https://data.nasdaq.com/databases/SF1/documentation
API Docs: https://docs.data.nasdaq.com/docs/tables-1
Category: Earnings & Fundamentals
Free tier: True (demo key provides sample data, limited to 10,000 rows per query)
Update frequency: Quarterly
Author: QuantClaw Data NightBuilder
Phase: 106
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Nasdaq Data Link API Configuration
NASDAQ_BASE_URL = "https://data.nasdaq.com/api/v3"
NASDAQ_API_KEY = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "")

# Dimension codes for SF1 table
DIMENSIONS = {
    'MRY': 'Most Recent Year (annual, most recent fiscal year)',
    'MRQ': 'Most Recent Quarter (quarterly, most recent fiscal quarter)',
    'ARY': 'Annual Report Year (annual, as reported)',
    'ARQ': 'Annual Report Quarter (quarterly, as reported)',
    'MRT': 'Most Recent Trailing Twelve Months',
    'ART': 'Annual Report Trailing Twelve Months'
}

# Common fundamental metrics available in SF1
FUNDAMENTAL_METRICS = [
    'revenue', 'netinc', 'eps', 'ebit', 'ebitda', 'equity', 'assets', 'liabilities',
    'debt', 'fcf', 'price', 'marketcap', 'pe', 'pb', 'ps', 'roe', 'roa', 'de',
    'currentratio', 'grossmargin', 'netmargin', 'revenuegrowth', 'netincgrowth'
]


def _make_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make authenticated request to Nasdaq Data Link API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        dict: JSON response from API
        
    Raises:
        Exception: If API request fails
    """
    if NASDAQ_API_KEY:
        params['api_key'] = NASDAQ_API_KEY
    
    url = f"{NASDAQ_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'error': str(e),
            'status': 'failed',
            'endpoint': endpoint,
            'params': {k: v for k, v in params.items() if k != 'api_key'}
        }


def get_fundamentals(ticker: str, dimension: str = 'MRY', limit: int = 10) -> Dict[str, Any]:
    """
    Get fundamental data for a specific ticker and dimension.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        dimension: Time dimension (MRY, MRQ, ARY, ARQ, MRT, ART) - default MRY
        limit: Maximum number of records to return (default 10)
        
    Returns:
        dict: Fundamental data with columns and data array
        
    Example:
        >>> data = get_fundamentals('AAPL', 'MRY')
        >>> print(data['datatable']['data'][0])  # Most recent annual data
    """
    params = {
        'ticker': ticker.upper(),
        'dimension': dimension.upper(),
        'qopts.per_page': limit
    }
    
    result = _make_request('datatables/SHARADAR/SF1', params)
    
    if 'error' in result:
        return result
    
    return {
        'ticker': ticker.upper(),
        'dimension': dimension.upper(),
        'dimension_description': DIMENSIONS.get(dimension.upper(), 'Unknown'),
        'data': result.get('datatable', {}),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def get_quarterly_financials(ticker: str, limit: int = 8) -> Dict[str, Any]:
    """
    Get quarterly financial statements (most recent quarters as reported).
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of quarters to retrieve (default 8 = 2 years)
        
    Returns:
        dict: Quarterly financial data
    """
    return get_fundamentals(ticker, dimension='ARQ', limit=limit)


def get_annual_financials(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """
    Get annual financial statements (most recent years as reported).
    
    Args:
        ticker: Stock ticker symbol
        limit: Number of years to retrieve (default 5)
        
    Returns:
        dict: Annual financial data
    """
    return get_fundamentals(ticker, dimension='ARY', limit=limit)


def get_key_ratios(ticker: str, dimension: str = 'MRY') -> Dict[str, Any]:
    """
    Get key financial ratios for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        dimension: Time dimension (default MRY for most recent year)
        
    Returns:
        dict: Financial ratios including PE, PB, ROE, ROA, debt/equity, margins
    """
    data = get_fundamentals(ticker, dimension=dimension, limit=1)
    
    if 'error' in data:
        return data
    
    # Extract ratios from the data
    try:
        columns = data['data'].get('columns', [])
        values = data['data'].get('data', [[]])[0] if data['data'].get('data') else []
        
        if not values:
            return {'error': 'No data available', 'ticker': ticker}
        
        # Create dict mapping column names to values
        ratios_data = dict(zip(columns, values))
        
        # Extract common ratios
        ratios = {
            'ticker': ticker,
            'dimension': dimension,
            'pe_ratio': ratios_data.get('pe'),
            'pb_ratio': ratios_data.get('pb'),
            'ps_ratio': ratios_data.get('ps'),
            'roe': ratios_data.get('roe'),
            'roa': ratios_data.get('roa'),
            'debt_equity': ratios_data.get('de'),
            'current_ratio': ratios_data.get('currentratio'),
            'gross_margin': ratios_data.get('grossmargin'),
            'net_margin': ratios_data.get('netmargin'),
            'ebitda_margin': ratios_data.get('ebitdamargin'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return ratios
    except (IndexError, KeyError) as e:
        return {'error': f'Data parsing failed: {str(e)}', 'ticker': ticker}


def get_revenue_earnings(ticker: str, dimension: str = 'MRQ', limit: int = 8) -> Dict[str, Any]:
    """
    Get revenue and earnings data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        dimension: Time dimension (default MRQ for quarterly data)
        limit: Number of periods to retrieve
        
    Returns:
        dict: Revenue and earnings time series
    """
    data = get_fundamentals(ticker, dimension=dimension, limit=limit)
    
    if 'error' in data:
        return data
    
    try:
        columns = data['data'].get('columns', [])
        rows = data['data'].get('data', [])
        
        # Find relevant column indices
        date_idx = columns.index('datekey') if 'datekey' in columns else None
        revenue_idx = columns.index('revenue') if 'revenue' in columns else None
        netinc_idx = columns.index('netinc') if 'netinc' in columns else None
        eps_idx = columns.index('eps') if 'eps' in columns else None
        
        results = []
        for row in rows:
            item = {}
            if date_idx is not None:
                item['date'] = row[date_idx]
            if revenue_idx is not None:
                item['revenue'] = row[revenue_idx]
            if netinc_idx is not None:
                item['net_income'] = row[netinc_idx]
            if eps_idx is not None:
                item['eps'] = row[eps_idx]
            results.append(item)
        
        return {
            'ticker': ticker,
            'dimension': dimension,
            'periods': results,
            'count': len(results),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except (ValueError, IndexError, KeyError) as e:
        return {'error': f'Data parsing failed: {str(e)}', 'ticker': ticker}


def search_tickers(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for tickers in the SHARADAR/TICKERS metadata table.
    
    Args:
        query: Search query (company name or ticker)
        limit: Maximum number of results (default 10)
        
    Returns:
        dict: List of matching tickers with company info
    """
    params = {
        'qopts.per_page': limit
    }
    
    result = _make_request('datatables/SHARADAR/TICKERS', params)
    
    if 'error' in result:
        return result
    
    # Filter results by query if we have data
    data = result.get('datatable', {})
    columns = data.get('columns', [])
    rows = data.get('data', [])
    
    try:
        ticker_idx = columns.index('ticker') if 'ticker' in columns else 0
        name_idx = columns.index('name') if 'name' in columns else 1
        
        filtered = []
        query_lower = query.lower()
        
        for row in rows:
            ticker = str(row[ticker_idx]) if ticker_idx < len(row) else ''
            name = str(row[name_idx]) if name_idx < len(row) else ''
            
            if query_lower in ticker.lower() or query_lower in name.lower():
                filtered.append({
                    'ticker': ticker,
                    'name': name,
                    'full_data': dict(zip(columns, row))
                })
                if len(filtered) >= limit:
                    break
        
        return {
            'query': query,
            'results': filtered,
            'count': len(filtered),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except (ValueError, IndexError) as e:
        return {'error': f'Search failed: {str(e)}', 'query': query}


def list_available_tables() -> Dict[str, Any]:
    """
    List available Nasdaq Data Link tables and their metadata.
    
    Returns:
        dict: Information about available tables
    """
    return {
        'tables': [
            {
                'code': 'SHARADAR/SF1',
                'name': 'Sharadar Core US Fundamentals',
                'description': 'Standardized fundamental indicators for US stocks',
                'dimensions': DIMENSIONS,
                'metrics': FUNDAMENTAL_METRICS[:10],  # First 10 for preview
                'url': 'https://data.nasdaq.com/databases/SF1/documentation'
            },
            {
                'code': 'SHARADAR/TICKERS',
                'name': 'Sharadar Ticker Metadata',
                'description': 'Company information and ticker metadata',
                'url': 'https://data.nasdaq.com/databases/SF1/documentation'
            },
            {
                'code': 'SHARADAR/SEP',
                'name': 'Sharadar Equity Prices',
                'description': 'Daily stock prices with splits and dividends',
                'url': 'https://data.nasdaq.com/databases/SEP/documentation'
            }
        ],
        'api_key_status': 'configured' if NASDAQ_API_KEY else 'using_demo',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


# Module metadata
__version__ = '1.0.0'
__author__ = 'QuantClaw Data NightBuilder'
__all__ = [
    'get_fundamentals',
    'get_quarterly_financials',
    'get_annual_financials',
    'get_key_ratios',
    'get_revenue_earnings',
    'search_tickers',
    'list_available_tables',
    'DIMENSIONS',
    'FUNDAMENTAL_METRICS'
]


if __name__ == "__main__":
    # Test basic functionality
    print(json.dumps(list_available_tables(), indent=2))
