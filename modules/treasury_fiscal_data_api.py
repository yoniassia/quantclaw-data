#!/usr/bin/env python3
"""
Treasury Fiscal Data API — US Government Financial Data

Official API from the U.S. Department of the Treasury's Bureau of the Fiscal Service.
Provides authoritative data on:
- National debt (debt to the penny)
- Average interest rates on government securities
- Monthly Treasury statements
- Federal spending and revenue
- Debt held by public vs intragovernmental

Source: https://fiscaldata.treasury.gov/api-documentation/
Category: Government & Regulatory
Free tier: True - No API key required, unlimited access
Update frequency: Daily
Author: QuantClaw Data NightBuilder
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

# Treasury Fiscal Data API Configuration
TREASURY_BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TIMEOUT = 30  # seconds

# ========== DATASET ENDPOINTS ==========

TREASURY_DATASETS = {
    'debt_to_penny': 'v2/accounting/od/debt_to_penny',
    'avg_interest_rates': 'v2/accounting/od/avg_interest_rates',
    'monthly_treasury_statement': 'v1/accounting/mts/mts_table_1',
    'debt_outstanding': 'v1/debt/mspd/mspd_table_1',
    'federal_revenue': 'v1/accounting/od/receipt_mts',
    'federal_spending': 'v1/accounting/od/statement_net_cost',
}


def _make_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Internal helper to make API requests to Treasury Fiscal Data API.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        requests.RequestException: On API errors
    """
    url = f"{TREASURY_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {
            "error": str(e),
            "endpoint": endpoint,
            "params": params
        }


def get_debt_to_penny(days: int = 30) -> Dict[str, Any]:
    """
    Get national debt data (debt to the penny).
    
    This is the most accurate, up-to-date measure of the U.S. national debt,
    updated daily by the Treasury. Shows total public debt outstanding.
    
    Args:
        days: Number of days of historical data (default: 30)
        
    Returns:
        Dictionary with debt data including:
        - record_date: Date of record
        - debt_held_public_amt: Debt held by the public
        - intragov_hold_amt: Intragovernmental holdings
        - tot_pub_debt_out_amt: Total public debt outstanding
        
    Example:
        >>> data = get_debt_to_penny(days=7)
        >>> print(f"Current debt: ${data['data'][0]['tot_pub_debt_out_amt']:,.0f}")
    """
    # Calculate date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        'fields': 'record_date,debt_held_public_amt,intragov_hold_amt,tot_pub_debt_out_amt',
        'filter': f'record_date:gte:{start_date.strftime("%Y-%m-%d")}',
        'sort': '-record_date',
        'page[size]': days
    }
    
    result = _make_request(TREASURY_DATASETS['debt_to_penny'], params)
    
    # Add metadata
    if 'data' in result:
        result['metadata'] = {
            'source': 'US Treasury Bureau of Fiscal Service',
            'dataset': 'Debt to the Penny',
            'days_requested': days,
            'records_returned': len(result.get('data', [])),
            'retrieved_at': datetime.now().isoformat()
        }
    
    return result


def get_avg_interest_rates(security_type: Optional[str] = None, months: int = 12) -> Dict[str, Any]:
    """
    Get average interest rates on U.S. government securities.
    
    Shows the average interest rates the government pays on its debt,
    broken down by security type (bills, notes, bonds, etc.).
    
    Args:
        security_type: Filter by security type (e.g., 'Treasury Bills', 'Treasury Bonds')
                      If None, returns all types
        months: Number of months of historical data (default: 12)
        
    Returns:
        Dictionary with interest rate data including:
        - record_date: Date of record
        - security_type_desc: Type of security
        - avg_interest_rate_amt: Average interest rate
        - security_desc: Detailed security description
        
    Example:
        >>> data = get_avg_interest_rates(security_type='Treasury Bills', months=6)
        >>> latest = data['data'][0]
        >>> print(f"T-Bill rate: {latest['avg_interest_rate_amt']}%")
    """
    # Calculate date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    params = {
        'fields': 'record_date,security_type_desc,security_desc,avg_interest_rate_amt',
        'filter': f'record_date:gte:{start_date.strftime("%Y-%m-%d")}',
        'sort': '-record_date',
        'page[size]': 100
    }
    
    # Add security type filter if specified
    if security_type:
        params['filter'] += f',security_type_desc:eq:{security_type}'
    
    result = _make_request(TREASURY_DATASETS['avg_interest_rates'], params)
    
    # Add metadata
    if 'data' in result:
        result['metadata'] = {
            'source': 'US Treasury Bureau of Fiscal Service',
            'dataset': 'Average Interest Rates on U.S. Treasury Securities',
            'security_type': security_type or 'all',
            'months_requested': months,
            'records_returned': len(result.get('data', [])),
            'retrieved_at': datetime.now().isoformat()
        }
    
    return result


def get_treasury_statement(period: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Monthly Treasury Statement (MTS) - Table 1: Summary of Receipts and Outlays.
    
    The MTS provides a comprehensive overview of federal government receipts,
    outlays, and deficit/surplus for each fiscal year.
    
    Args:
        period: Fiscal period in format 'YYYY-MM' (e.g., '2024-09')
                If None, returns recent periods
        
    Returns:
        Dictionary with treasury statement data including:
        - record_date: Statement date
        - record_fiscal_year: Fiscal year
        - record_fiscal_month: Fiscal month
        - current_month_rcpt_amt: Current month receipts
        - current_month_outly_amt: Current month outlays
        - fytd_rcpt_amt: Fiscal year to date receipts
        - fytd_outly_amt: Fiscal year to date outlays
        
    Example:
        >>> data = get_treasury_statement()
        >>> latest = data['data'][0]
        >>> deficit = float(latest['fytd_outly_amt']) - float(latest['fytd_rcpt_amt'])
        >>> print(f"FY deficit: ${deficit/1e9:.1f}B")
    """
    params = {
        'fields': 'record_date,record_fiscal_year,record_fiscal_month,current_month_rcpt_amt,current_month_outly_amt,fytd_rcpt_amt,fytd_outly_amt',
        'sort': '-record_date',
        'page[size]': 24  # 2 years of monthly data
    }
    
    # Add period filter if specified
    if period:
        # Convert period to date filter
        params['filter'] = f'record_date:eq:{period}-01'
    
    result = _make_request(TREASURY_DATASETS['monthly_treasury_statement'], params)
    
    # Add metadata
    if 'data' in result:
        result['metadata'] = {
            'source': 'US Treasury Bureau of Fiscal Service',
            'dataset': 'Monthly Treasury Statement - Table 1',
            'period': period or 'recent',
            'records_returned': len(result.get('data', [])),
            'retrieved_at': datetime.now().isoformat()
        }
    
    return result


def get_debt_held_public(years: int = 5) -> Dict[str, Any]:
    """
    Get debt held by the public vs intragovernmental holdings.
    
    Shows the breakdown of federal debt between:
    - Debt held by the public (external investors, foreign governments, etc.)
    - Intragovernmental holdings (Social Security Trust Fund, etc.)
    
    Args:
        years: Number of years of historical data (default: 5)
        
    Returns:
        Dictionary with debt breakdown data including:
        - record_date: Date of record
        - debt_held_public_amt: Debt held by the public
        - intragov_hold_amt: Intragovernmental holdings
        - tot_pub_debt_out_amt: Total public debt outstanding
        
    Example:
        >>> data = get_debt_held_public(years=1)
        >>> latest = data['data'][0]
        >>> public_pct = (float(latest['debt_held_public_amt']) / 
        ...               float(latest['tot_pub_debt_out_amt'])) * 100
        >>> print(f"Public debt: {public_pct:.1f}% of total")
    """
    # Calculate date filter - sample quarterly to reduce data volume
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    params = {
        'fields': 'record_date,debt_held_public_amt,intragov_hold_amt,tot_pub_debt_out_amt',
        'filter': f'record_date:gte:{start_date.strftime("%Y-%m-%d")}',
        'sort': '-record_date',
        'page[size]': years * 12  # Monthly sampling
    }
    
    result = _make_request(TREASURY_DATASETS['debt_to_penny'], params)
    
    # Add metadata
    if 'data' in result:
        result['metadata'] = {
            'source': 'US Treasury Bureau of Fiscal Service',
            'dataset': 'Debt Held by Public vs Intragovernmental',
            'years_requested': years,
            'records_returned': len(result.get('data', [])),
            'retrieved_at': datetime.now().isoformat()
        }
    
    return result


def search_datasets(keyword: str) -> List[Dict[str, str]]:
    """
    Search available Treasury Fiscal Data datasets by keyword.
    
    Returns information about available datasets matching the search term.
    Useful for discovering what data is available.
    
    Args:
        keyword: Search term (e.g., 'debt', 'interest', 'revenue')
        
    Returns:
        List of dictionaries with dataset information:
        - name: Dataset identifier
        - endpoint: API endpoint path
        - description: What the dataset contains
        
    Example:
        >>> datasets = search_datasets('debt')
        >>> for ds in datasets:
        ...     print(f"{ds['name']}: {ds['description']}")
    """
    keyword_lower = keyword.lower()
    
    # Expanded dataset registry with descriptions
    all_datasets = {
        'debt_to_penny': {
            'endpoint': TREASURY_DATASETS['debt_to_penny'],
            'description': 'Daily national debt totals - most accurate debt measure'
        },
        'avg_interest_rates': {
            'endpoint': TREASURY_DATASETS['avg_interest_rates'],
            'description': 'Average interest rates on U.S. Treasury securities by type'
        },
        'monthly_treasury_statement': {
            'endpoint': TREASURY_DATASETS['monthly_treasury_statement'],
            'description': 'Monthly summary of federal receipts and outlays'
        },
        'debt_outstanding': {
            'endpoint': TREASURY_DATASETS['debt_outstanding'],
            'description': 'Monthly statement of the public debt outstanding'
        },
        'federal_revenue': {
            'endpoint': TREASURY_DATASETS['federal_revenue'],
            'description': 'Federal government revenue by source'
        },
        'federal_spending': {
            'endpoint': TREASURY_DATASETS['federal_spending'],
            'description': 'Federal government spending by category'
        }
    }
    
    # Search in names and descriptions
    matches = []
    for name, info in all_datasets.items():
        if (keyword_lower in name.lower() or 
            keyword_lower in info['description'].lower()):
            matches.append({
                'name': name,
                'endpoint': info['endpoint'],
                'description': info['description']
            })
    
    return matches


# ========== MODULE INFO ==========

def get_module_info() -> Dict[str, Any]:
    """
    Get information about this module.
    
    Returns:
        Dictionary with module metadata
    """
    return {
        'module': 'treasury_fiscal_data_api',
        'version': '1.0.0',
        'source': 'https://fiscaldata.treasury.gov/api-documentation/',
        'base_url': TREASURY_BASE_URL,
        'api_key_required': False,
        'datasets': list(TREASURY_DATASETS.keys()),
        'functions': [
            'get_debt_to_penny',
            'get_avg_interest_rates',
            'get_treasury_statement',
            'get_debt_held_public',
            'search_datasets',
            'get_module_info'
        ]
    }


if __name__ == "__main__":
    # Demo usage
    print(json.dumps(get_module_info(), indent=2))
