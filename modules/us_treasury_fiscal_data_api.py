#!/usr/bin/env python3
"""
U.S. Treasury Fiscal Data API — Government Securities & Debt Data Module

Core Treasury integration for fiscal and debt data including:
- Average interest rates on government securities
- Daily treasury yield curves
- Debt to the Penny (daily national debt)
- Treasury statements and fiscal reports
- Dataset search and discovery

Source: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/
Category: Fixed Income & Credit
Free tier: True (no API key required)
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

# Treasury Fiscal Data API Configuration
TREASURY_BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"


def get_interest_rates(security_type: Optional[str] = None, days: int = 30) -> Dict:
    """
    Get average interest rates on government securities.
    
    Args:
        security_type: Filter by security type description (optional)
        days: Number of days of historical data (default: 30)
    
    Returns:
        Dict with 'data' key containing list of interest rate records
    
    Example:
        >>> rates = get_interest_rates(days=7)
        >>> print(f"Latest rate: {rates['data'][0]['avg_interest_rate_amt']}%")
    """
    try:
        # Use avg_interest_rates endpoint (confirmed working)
        url = f"{TREASURY_BASE_URL}/v2/accounting/od/avg_interest_rates"
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Build filter
        filters = [f"record_date:gte:{start_date}"]
        if security_type:
            filters.append(f"security_type_desc:eq:{security_type}")
        
        params = {
            'fields': 'record_date,security_type_desc,security_desc,avg_interest_rate_amt',
            'filter': ','.join(filters),
            'sort': '-record_date',
            'page[size]': 100
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        result = {
            'data': data.get('data', []),
            'meta': data.get('meta', {}),
            'security_type': security_type,
            'days': days,
            'total_records': len(data.get('data', []))
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'security_type': security_type}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'security_type': security_type}


def get_debt_to_penny(days: int = 30) -> Dict:
    """
    Get daily national debt data (Debt to the Penny).
    
    Args:
        days: Number of days of historical data (default: 30)
    
    Returns:
        Dict with 'data' key containing daily debt records
    
    Example:
        >>> debt = get_debt_to_penny(days=7)
        >>> latest = debt['data'][0]
        >>> print(f"Total debt: ${float(latest['tot_pub_debt_out_amt']):,.0f}")
    """
    try:
        url = f"{TREASURY_BASE_URL}/v2/accounting/od/debt_to_penny"
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'fields': 'record_date,tot_pub_debt_out_amt,debt_held_public_amt,intragov_hold_amt',
            'filter': f'record_date:gte:{start_date}',
            'sort': '-record_date',
            'page[size]': 100
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata and calculations
        records = data.get('data', [])
        if len(records) >= 2:
            latest = float(records[0].get('tot_pub_debt_out_amt', 0))
            previous = float(records[1].get('tot_pub_debt_out_amt', 0))
            change = latest - previous
            pct_change = (change / previous * 100) if previous != 0 else 0
        else:
            change = 0
            pct_change = 0
        
        result = {
            'data': records,
            'meta': data.get('meta', {}),
            'days': days,
            'total_records': len(records),
            'daily_change': change,
            'daily_change_pct': round(pct_change, 4)
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'days': days}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'days': days}


def get_treasury_yields(start_date: Optional[str] = None, days: int = 30) -> Dict:
    """
    Get treasury yield curve data (average interest rates).
    Same as get_interest_rates but with explicit yield curve focus.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        days: Number of days if start_date not provided (default: 30)
    
    Returns:
        Dict with 'data' key containing yield curve records
    
    Example:
        >>> yields = get_treasury_yields(days=7)
        >>> for record in yields['data'][:5]:
        ...     print(f"{record['record_date']}: {record['avg_interest_rate_amt']}%")
    """
    try:
        url = f"{TREASURY_BASE_URL}/v2/accounting/od/avg_interest_rates"
        
        # Calculate start date if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'fields': 'record_date,security_type_desc,security_desc,avg_interest_rate_amt,src_line_nbr',
            'filter': f'record_date:gte:{start_date}',
            'sort': '-record_date',
            'page[size]': 100
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        result = {
            'data': data.get('data', []),
            'meta': data.get('meta', {}),
            'start_date': start_date,
            'total_records': len(data.get('data', []))
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'start_date': start_date}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'start_date': start_date}


def get_treasury_statement(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get Treasury statement of net cost data.
    
    Args:
        fiscal_year: Fiscal year (e.g., 2024). If None, gets current/recent data.
    
    Returns:
        Dict with 'data' key containing treasury statement records
    
    Example:
        >>> stmt = get_treasury_statement(fiscal_year=2024)
        >>> print(f"Records: {stmt['total_records']}")
    """
    try:
        url = f"{TREASURY_BASE_URL}/v2/accounting/od/statement_net_cost"
        
        params = {
            'sort': '-record_date',
            'page[size]': 100
        }
        
        # Add fiscal year filter if provided
        if fiscal_year:
            params['filter'] = f'record_fiscal_year:eq:{fiscal_year}'
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Add metadata
        result = {
            'data': data.get('data', []),
            'meta': data.get('meta', {}),
            'fiscal_year': fiscal_year,
            'total_records': len(data.get('data', []))
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'fiscal_year': fiscal_year}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'fiscal_year': fiscal_year}


def search_datasets(keyword: str) -> List[Dict]:
    """
    Search available Treasury datasets by keyword.
    
    Args:
        keyword: Search term (e.g., 'debt', 'interest', 'yield')
    
    Returns:
        List of matching dataset info (manually curated common endpoints)
    
    Example:
        >>> datasets = search_datasets('debt')
        >>> for ds in datasets:
        ...     print(f"{ds['name']}: {ds['description']}")
    """
    # Curated list of major Treasury datasets
    all_datasets = [
        {
            'name': 'Debt to the Penny',
            'endpoint': '/v2/accounting/od/debt_to_penny',
            'description': 'Daily total public debt outstanding',
            'keywords': ['debt', 'national', 'public', 'penny']
        },
        {
            'name': 'Average Interest Rates',
            'endpoint': '/v2/accounting/od/avg_interest_rates',
            'description': 'Average interest rates on government securities by type',
            'keywords': ['interest', 'rates', 'yield', 'curve', 'treasury']
        },
        {
            'name': 'Statement of Net Cost',
            'endpoint': '/v2/accounting/od/statement_net_cost',
            'description': 'Treasury statement of net cost by fiscal year',
            'keywords': ['statement', 'cost', 'fiscal', 'treasury']
        },
        {
            'name': 'Treasury Offset Program',
            'endpoint': '/v2/debt/top',
            'description': 'Treasury Offset Program data',
            'keywords': ['offset', 'program', 'debt', 'collection']
        }
    ]
    
    # Filter by keyword (case-insensitive)
    keyword_lower = keyword.lower()
    matching = [
        ds for ds in all_datasets
        if keyword_lower in ds['name'].lower() 
        or keyword_lower in ds['description'].lower()
        or any(keyword_lower in kw for kw in ds['keywords'])
    ]
    
    return matching


# Helper function for raw API queries
def query_endpoint(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make a raw query to any Treasury Fiscal Data API endpoint.
    
    Args:
        endpoint: API endpoint path (e.g., '/v2/accounting/od/debt_to_penny')
        params: Query parameters dict (optional)
    
    Returns:
        Dict with response data
    
    Example:
        >>> data = query_endpoint('/v2/accounting/od/debt_to_penny', 
        ...                       {'page[size]': 5, 'sort': '-record_date'})
    """
    try:
        url = f"{TREASURY_BASE_URL}{endpoint}"
        
        response = requests.get(url, params=params or {}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'endpoint': endpoint}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'endpoint': endpoint}


if __name__ == "__main__":
    # Quick test
    print("Testing US Treasury Fiscal Data API module...")
    
    # Test 1: Get debt data
    debt = get_debt_to_penny(days=5)
    if 'error' not in debt:
        print(f"✓ Debt to Penny: {debt['total_records']} records")
        if debt['data']:
            latest = debt['data'][0]
            print(f"  Latest ({latest['record_date']}): ${float(latest['tot_pub_debt_out_amt']):,.0f}")
    else:
        print(f"✗ Debt to Penny error: {debt['error']}")
    
    # Test 2: Search datasets
    datasets = search_datasets('debt')
    print(f"✓ Dataset search: {len(datasets)} matches for 'debt'")
    
    print("\nModule ready for import.")
