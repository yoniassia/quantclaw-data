#!/usr/bin/env python3
"""
Treasury FiscalData API Module — NightBuilder

U.S. Treasury Department's official fiscal data API providing:
- Public debt levels and components
- Treasury auction results and yields
- Federal government revenues and outlays
- Interest rate statistics
- Exchange rates for international transactions

Data Source: api.fiscaldata.treasury.gov
Refresh: Daily for most datasets, real-time for auctions
Coverage: Complete U.S. federal fiscal and debt data
Free Tier: Fully free, no API key required

Built by: NightBuilder (DevClaw)
Date: 2026-03-05
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

def get_public_debt() -> Dict:
    """
    Get current total public debt outstanding
    
    Returns:
        dict: {'total_debt': float, 'debt_held_by_public': float, 'intragovernmental': float, 'date': str}
    """
    try:
        endpoint = f"{BASE_URL}/v2/accounting/od/debt_outstanding"
        params = {
            'fields': 'record_date,debt_outstanding_amt,src_line_nbr',
            'sort': '-record_date',
            'page[size]': 10
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return {'error': 'No data available'}
        
        # Latest record
        latest = data['data'][0]
        
        # Parse components
        total_debt = 0.0
        held_by_public = 0.0
        intragovernmental = 0.0
        
        for record in data['data'][:10]:
            if record['record_date'] == latest['record_date']:
                amt = float(record.get('debt_outstanding_amt', 0))
                line = record.get('src_line_nbr', '')
                
                if 'Total Public Debt' in str(line) or line == '1':
                    total_debt = amt
                elif 'Debt Held by the Public' in str(line) or line == '2':
                    held_by_public = amt
                elif 'Intragovernmental' in str(line) or line == '3':
                    intragovernmental = amt
        
        return {
            'total_debt': total_debt if total_debt > 0 else held_by_public + intragovernmental,
            'debt_held_by_public': held_by_public,
            'intragovernmental_holdings': intragovernmental,
            'date': latest['record_date'],
            'units': 'millions_usd'
        }
    except Exception as e:
        return {'error': str(e)}


def get_avg_interest_rates(months: int = 12) -> List[Dict]:
    """
    Get average interest rates on US Treasury securities
    
    Args:
        months: Number of months of historical data (default 12)
    
    Returns:
        list: [{'date': str, 'security_type': str, 'rate': float}, ...]
    """
    try:
        start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
        endpoint = f"{BASE_URL}/v2/accounting/od/avg_interest_rates"
        params = {
            'fields': 'record_date,security_type_desc,avg_interest_rate_amt',
            'filter': f'record_date:gte:{start_date}',
            'sort': '-record_date',
            'page[size]': 1000
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rates = []
        for record in data.get('data', []):
            rates.append({
                'date': record['record_date'],
                'security_type': record['security_type_desc'],
                'rate': float(record['avg_interest_rate_amt'])
            })
        
        return rates
    except Exception as e:
        return [{'error': str(e)}]


def get_exchange_rates(date: Optional[str] = None) -> List[Dict]:
    """
    Get Treasury reporting rates of exchange for foreign currencies
    
    Args:
        date: Date in YYYY-MM-DD format (default: latest available)
    
    Returns:
        list: [{'country': str, 'currency': str, 'rate': float, 'date': str}, ...]
    """
    try:
        endpoint = f"{BASE_URL}/v1/accounting/od/rates_of_exchange"
        params = {
            'fields': 'country_currency_desc,exchange_rate,record_date',
            'sort': '-record_date',
            'page[size]': 200
        }
        
        if date:
            params['filter'] = f'record_date:eq:{date}'
        
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rates = []
        for record in data.get('data', []):
            rates.append({
                'country_currency': record['country_currency_desc'],
                'rate': float(record['exchange_rate']),
                'date': record['record_date']
            })
        
        return rates
    except Exception as e:
        return [{'error': str(e)}]


def get_federal_revenue(fiscal_year: Optional[int] = None) -> Dict:
    """
    Get monthly federal government receipts (revenue)
    
    Args:
        fiscal_year: Fiscal year (default: current FY)
    
    Returns:
        dict: {'fiscal_year': int, 'total_receipts': float, 'monthly': [...]}
    """
    try:
        if not fiscal_year:
            # Current fiscal year (Oct 1 - Sep 30)
            now = datetime.now()
            fiscal_year = now.year if now.month >= 10 else now.year - 1
        
        endpoint = f"{BASE_URL}/v1/accounting/mts/mts_table_5"
        params = {
            'fields': 'record_date,classification_desc,current_fytd_net_rcpt_amt',
            'filter': f'record_fiscal_year:eq:{fiscal_year},sequence_number:eq:1',
            'sort': '-record_date',
            'page[size]': 100
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        monthly = []
        total = 0.0
        for record in data.get('data', []):
            amt = float(record.get('current_fytd_net_rcpt_amt', 0))
            monthly.append({
                'date': record['record_date'],
                'category': record.get('classification_desc', 'Total'),
                'receipts': amt
            })
            if 'Total' in record.get('classification_desc', ''):
                total = amt
        
        return {
            'fiscal_year': fiscal_year,
            'total_receipts_fytd': total,
            'monthly_detail': monthly[:12],
            'units': 'millions_usd'
        }
    except Exception as e:
        return {'error': str(e)}


def get_treasury_auctions(days: int = 30) -> List[Dict]:
    """
    Get recent Treasury security auction results
    
    Args:
        days: Number of days to look back (default 30)
    
    Returns:
        list: [{'security_type': str, 'issue_date': str, 'high_yield': float, ...}, ...]
    """
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        endpoint = f"{BASE_URL}/v1/debt/tror/auction_query"
        params = {
            'fields': 'security_type,issue_date,maturity_date,high_yield,high_price,total_accepted',
            'filter': f'issue_date:gte:{start_date}',
            'sort': '-issue_date',
            'page[size]': 100
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        auctions = []
        for record in data.get('data', []):
            auctions.append({
                'security_type': record.get('security_type', ''),
                'issue_date': record.get('issue_date', ''),
                'maturity_date': record.get('maturity_date', ''),
                'high_yield': float(record.get('high_yield', 0)) if record.get('high_yield') else None,
                'high_price': float(record.get('high_price', 0)) if record.get('high_price') else None,
                'total_accepted': float(record.get('total_accepted', 0)) if record.get('total_accepted') else None
            })
        
        return auctions
    except Exception as e:
        return [{'error': str(e)}]


def get_debt_to_penny() -> Dict:
    """
    Get debt to the penny (most precise daily public debt figure)
    
    Returns:
        dict: {'date': str, 'total_debt': float, 'debt_subject_to_limit': float}
    """
    try:
        endpoint = f"{BASE_URL}/v2/accounting/od/debt_to_penny"
        params = {
            'fields': 'record_date,tot_pub_debt_out_amt,debt_subject_to_limit_amt',
            'sort': '-record_date',
            'page[size]': 1
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('data'):
            return {'error': 'No data available'}
        
        latest = data['data'][0]
        return {
            'date': latest['record_date'],
            'total_public_debt': float(latest['tot_pub_debt_out_amt']),
            'debt_subject_to_limit': float(latest.get('debt_subject_to_limit_amt', 0)),
            'units': 'dollars'
        }
    except Exception as e:
        return {'error': str(e)}


# === CONVENIENCE FUNCTIONS ===

def get_latest_debt_summary() -> Dict:
    """Get comprehensive latest debt statistics"""
    return {
        'debt_outstanding': get_public_debt(),
        'debt_to_penny': get_debt_to_penny(),
        'avg_interest_rates': get_avg_interest_rates(months=1)
    }


def get_fiscal_snapshot() -> Dict:
    """Get current fiscal year snapshot"""
    return {
        'revenue': get_federal_revenue(),
        'debt': get_public_debt(),
        'recent_auctions': get_treasury_auctions(days=7)
    }


if __name__ == "__main__":
    # Test the module
    print("=== Treasury FiscalData API Module Test ===\n")
    
    print("1. Public Debt:")
    print(json.dumps(get_public_debt(), indent=2))
    
    print("\n2. Latest Debt to Penny:")
    print(json.dumps(get_debt_to_penny(), indent=2))
    
    print("\n3. Recent Treasury Auctions:")
    auctions = get_treasury_auctions(days=7)
    print(json.dumps(auctions[:3], indent=2))
    
    print("\n4. Exchange Rates (sample):")
    rates = get_exchange_rates()
    print(json.dumps(rates[:5], indent=2))
    
    print("\nModule: treasury_fiscaldata_api — READY ✓")
