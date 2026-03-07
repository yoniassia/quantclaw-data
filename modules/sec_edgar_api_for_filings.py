#!/usr/bin/env python3
"""
SEC EDGAR API for Filings — Company Filings, Insider Trades & Institutional Holdings

Access SEC filings including:
- Company submissions (10-K, 10-Q, 8-K, etc.)
- Form 4 insider trading transactions
- 13F institutional holdings
- XBRL company facts and financial data
- Full-text filing search

Source: https://www.sec.gov/edgar/sec-api-documentation
Category: Insider & Institutional
Free tier: True (rate limited to 10 requests per second, requires User-Agent header)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder-2026-03-06
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

# SEC API Configuration
SEC_BASE_URL = "https://data.sec.gov"
SEC_EFTS_URL = "https://efts.sec.gov/LATEST"

# User-Agent header is REQUIRED by SEC (they block requests without it)
USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", 
    "QuantClaw-Data/1.0 (institutional research; compliance@moneyclaw.com)"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

# Rate limiting: 10 requests per second max
LAST_REQUEST_TIME = 0
MIN_REQUEST_INTERVAL = 0.11  # 110ms between requests to stay under 10/sec


def _rate_limit():
    """Enforce SEC rate limit of 10 requests per second"""
    global LAST_REQUEST_TIME
    now = time.time()
    time_since_last = now - LAST_REQUEST_TIME
    if time_since_last < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
    LAST_REQUEST_TIME = time.time()


def _make_request(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make rate-limited request to SEC API
    
    Args:
        url: Full URL to request
        params: Optional query parameters
        
    Returns:
        JSON response as dict, or None on error
    """
    _rate_limit()
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"SEC API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse SEC API response: {e}")
        return None


def _normalize_cik(cik_or_ticker: str) -> str:
    """
    Normalize CIK to 10-digit zero-padded format
    
    Args:
        cik_or_ticker: CIK number or stock ticker
        
    Returns:
        10-digit zero-padded CIK string
    """
    # If it's numeric, assume it's a CIK
    if cik_or_ticker.isdigit():
        return cik_or_ticker.zfill(10)
    
    # Otherwise, try to look up ticker via company tickers JSON
    # For now, just return as-is and let API handle it
    # TODO: Implement ticker->CIK lookup via https://www.sec.gov/files/company_tickers.json
    return cik_or_ticker


def get_company_filings(ticker_or_cik: str, form_type: Optional[str] = None, limit: int = 100) -> Dict:
    """
    Get recent filings for a company
    
    Args:
        ticker_or_cik: Stock ticker (e.g., 'AAPL') or CIK number
        form_type: Filter by form type (e.g., '10-K', '10-Q', '8-K', '4', '13F-HR')
        limit: Maximum number of filings to return (default 100)
        
    Returns:
        Dict with company info and recent filings:
        {
            'cik': '0000320193',
            'name': 'Apple Inc.',
            'filings': [
                {
                    'accessionNumber': '0000320193-23-000077',
                    'filingDate': '2023-08-04',
                    'reportDate': '2023-07-01',
                    'form': '10-Q',
                    'primaryDocument': 'aapl-20230701.htm',
                    'primaryDocDescription': '10-Q'
                },
                ...
            ]
        }
    """
    cik = _normalize_cik(ticker_or_cik)
    url = f"{SEC_BASE_URL}/submissions/CIK{cik}.json"
    
    data = _make_request(url)
    if not data:
        return {'error': f'Failed to fetch filings for {ticker_or_cik}'}
    
    # Extract company info
    result = {
        'cik': data.get('cik'),
        'name': data.get('name'),
        'sic': data.get('sic'),
        'sicDescription': data.get('sicDescription'),
        'filings': []
    }
    
    # Parse recent filings
    recent = data.get('filings', {}).get('recent', {})
    if not recent:
        return result
    
    # Combine all filing fields into list of dicts
    filing_count = len(recent.get('accessionNumber', []))
    for i in range(min(filing_count, limit)):
        filing = {
            'accessionNumber': recent['accessionNumber'][i],
            'filingDate': recent['filingDate'][i],
            'reportDate': recent['reportDate'][i],
            'form': recent['form'][i],
            'primaryDocument': recent['primaryDocument'][i],
            'primaryDocDescription': recent['primaryDocDescription'][i]
        }
        
        # Filter by form type if specified
        if form_type is None or filing['form'] == form_type:
            result['filings'].append(filing)
    
    return result


def get_insider_trades(ticker_or_cik: str, days_back: int = 90) -> List[Dict]:
    """
    Extract Form 4 insider trading transactions
    
    Args:
        ticker_or_cik: Stock ticker or CIK number
        days_back: Number of days to look back (default 90)
        
    Returns:
        List of insider transactions:
        [
            {
                'filingDate': '2023-08-15',
                'accessionNumber': '0001209191-23-044422',
                'reportingOwner': 'COOK TIMOTHY D',
                'transactionDate': '2023-08-14',
                'transactionCode': 'S',  # S=Sale, P=Purchase, A=Award, etc.
                'shares': 223986,
                'pricePerShare': 177.79,
                'sharesOwned': 3279726
            },
            ...
        ]
    """
    filings_data = get_company_filings(ticker_or_cik, form_type='4', limit=100)
    
    if 'error' in filings_data:
        return [{'error': filings_data['error']}]
    
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Filter Form 4s within date range
    form4_filings = [
        f for f in filings_data.get('filings', [])
        if f['form'] == '4' and f['filingDate'] >= cutoff_date
    ]
    
    # For a complete implementation, we'd parse the actual XML filing
    # For now, return the filing metadata
    # TODO: Parse XML to extract transaction details
    transactions = []
    for filing in form4_filings:
        transactions.append({
            'filingDate': filing['filingDate'],
            'accessionNumber': filing['accessionNumber'],
            'reportDate': filing['reportDate'],
            'form': filing['form'],
            'note': 'Full XML parsing not yet implemented - use accessionNumber to fetch details'
        })
    
    return transactions


def get_13f_holdings(cik: str, filing_date: Optional[str] = None) -> Dict:
    """
    Extract 13F institutional holdings
    
    Args:
        cik: CIK number of institutional investor
        filing_date: Optional specific filing date (YYYY-MM-DD)
        
    Returns:
        Dict with 13F holdings:
        {
            'filer': 'BERKSHIRE HATHAWAY INC',
            'cik': '0001067983',
            'filingDate': '2023-08-14',
            'reportDate': '2023-06-30',
            'holdings': [
                {
                    'issuer': 'APPLE INC',
                    'cusip': '037833100',
                    'shares': 915560382,
                    'value': 162918000000,  # in dollars
                    'investmentDiscretion': 'SOLE'
                },
                ...
            ]
        }
    """
    filings_data = get_company_filings(cik, form_type='13F-HR', limit=20)
    
    if 'error' in filings_data:
        return {'error': filings_data['error']}
    
    filings = filings_data.get('filings', [])
    if not filings:
        return {'error': f'No 13F filings found for CIK {cik}'}
    
    # Get most recent 13F or specified date
    target_filing = filings[0]
    if filing_date:
        target_filing = next(
            (f for f in filings if f['filingDate'] == filing_date),
            filings[0]
        )
    
    # For complete implementation, parse 13F XML/HTML table
    # For now, return filing metadata
    # TODO: Parse information table from 13F filing
    result = {
        'filer': filings_data.get('name'),
        'cik': filings_data.get('cik'),
        'filingDate': target_filing['filingDate'],
        'reportDate': target_filing['reportDate'],
        'accessionNumber': target_filing['accessionNumber'],
        'holdings': [],
        'note': 'Full 13F table parsing not yet implemented - use accessionNumber to fetch details'
    }
    
    return result


def search_filings(query: str, form_type: Optional[str] = None, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> List[Dict]:
    """
    Full-text search across SEC filings
    
    Args:
        query: Search query string
        form_type: Filter by form type (e.g., '10-K', '8-K')
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        
    Returns:
        List of matching filings (Note: SEC doesn't offer direct full-text API search,
        this would require integration with EDGAR search or third-party services)
    """
    # SEC doesn't provide a direct full-text search API endpoint
    # This would require scraping edgar.sec.gov/search or using third-party services
    # For now, return a placeholder
    return [{
        'error': 'Full-text search not available via SEC API',
        'note': 'Use EDGAR search interface at https://www.sec.gov/edgar/search/',
        'query': query,
        'alternatives': 'Consider using company filings search by CIK/ticker instead'
    }]


def get_company_facts(ticker_or_cik: str, taxonomy: str = 'us-gaap') -> Dict:
    """
    Get XBRL company facts (standardized financial data)
    
    Args:
        ticker_or_cik: Stock ticker or CIK number
        taxonomy: XBRL taxonomy (default 'us-gaap', also 'dei', 'srt')
        
    Returns:
        Dict with company facts:
        {
            'cik': '0000320193',
            'name': 'Apple Inc.',
            'facts': {
                'us-gaap': {
                    'Assets': {
                        'label': 'Assets',
                        'description': 'Sum of carrying amounts...',
                        'units': {
                            'USD': [
                                {
                                    'end': '2023-07-01',
                                    'val': 335038000000,
                                    'accn': '0000320193-23-000077',
                                    'fy': 2023,
                                    'fp': 'Q3',
                                    'form': '10-Q'
                                },
                                ...
                            ]
                        }
                    },
                    'Revenue': {...},
                    ...
                }
            }
        }
    """
    cik = _normalize_cik(ticker_or_cik)
    url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
    
    data = _make_request(url)
    if not data:
        return {'error': f'Failed to fetch company facts for {ticker_or_cik}'}
    
    result = {
        'cik': data.get('cik'),
        'entityName': data.get('entityName'),
        'facts': data.get('facts', {})
    }
    
    return result


def get_ticker_to_cik_map() -> Dict[str, str]:
    """
    Get mapping of stock tickers to CIK numbers
    
    Returns:
        Dict mapping tickers to CIKs: {'AAPL': '320193', 'MSFT': '789019', ...}
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    
    _rate_limit()
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Convert to ticker: CIK mapping
        ticker_map = {}
        for entry in data.values():
            ticker = entry.get('ticker')
            cik = str(entry.get('cik_str'))
            if ticker and cik:
                ticker_map[ticker.upper()] = cik
        
        return ticker_map
    except Exception as e:
        print(f"Failed to fetch ticker-CIK map: {e}")
        return {}


# ========== CONVENIENCE FUNCTIONS ==========

def get_latest_10k(ticker_or_cik: str) -> Optional[Dict]:
    """Get most recent 10-K filing"""
    filings = get_company_filings(ticker_or_cik, form_type='10-K', limit=1)
    filing_list = filings.get('filings', [])
    return filing_list[0] if filing_list else None


def get_latest_10q(ticker_or_cik: str) -> Optional[Dict]:
    """Get most recent 10-Q filing"""
    filings = get_company_filings(ticker_or_cik, form_type='10-Q', limit=1)
    filing_list = filings.get('filings', [])
    return filing_list[0] if filing_list else None


def get_latest_8k(ticker_or_cik: str) -> Optional[Dict]:
    """Get most recent 8-K filing"""
    filings = get_company_filings(ticker_or_cik, form_type='8-K', limit=1)
    filing_list = filings.get('filings', [])
    return filing_list[0] if filing_list else None


# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    # Test with Apple (CIK 0000320193)
    print("Testing SEC EDGAR API module...\n")
    
    # Test 1: Get company filings
    print("1. Testing get_company_filings('AAPL')...")
    filings = get_company_filings('0000320193', limit=5)
    print(json.dumps(filings, indent=2))
    print()
    
    # Test 2: Get company facts
    print("2. Testing get_company_facts('0000320193')...")
    facts = get_company_facts('0000320193')
    print(f"Company: {facts.get('entityName')}")
    print(f"CIK: {facts.get('cik')}")
    print(f"Available taxonomies: {list(facts.get('facts', {}).keys())}")
    print()
    
    # Test 3: Get latest 10-K
    print("3. Testing get_latest_10k('0000320193')...")
    latest_10k = get_latest_10k('0000320193')
    print(json.dumps(latest_10k, indent=2))
