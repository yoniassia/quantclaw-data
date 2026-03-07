#!/usr/bin/env python3
"""
SEC EDGAR EFTS API — Free Full-Text Search for SEC Filings

Free SEC EDGAR full-text search integration providing:
- Full-text search across all SEC filings
- IPO filings (S-1 forms)
- 8-K current reports
- Insider trading filings (Form 4)
- Filing text extraction

Source: https://efts.sec.gov/LATEST/search-index
Category: IPO & Private Markets
Free tier: True (no API key required, rate-limited by SEC)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# SEC EDGAR Configuration
SEC_SEARCH_BASE_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
SEC_FILING_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

# SEC requires User-Agent header per policy
USER_AGENT = "QuantClaw Data NightBuilder ([email protected])"


def search_filings(query: str = 'artificial intelligence', 
                   form_type: Optional[str] = '10-K',
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None,
                   limit: int = 20) -> List[Dict]:
    """
    Search SEC filings using full-text search.
    
    Args:
        query: Search query text (default: 'artificial intelligence')
        form_type: SEC form type filter (e.g., '10-K', '10-Q', 'S-1', '8-K')
        date_from: Start date in YYYY-MM-DD format (optional)
        date_to: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of results (default: 20)
    
    Returns:
        List of dicts with keys: cik, company, form_type, filing_date, 
                                accession_number, description, file_url
    
    Example:
        >>> results = search_filings('blockchain', form_type='10-K')
        >>> print(f"Found {len(results)} 10-K filings mentioning blockchain")
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Build search query
        search_parts = [query]
        if form_type:
            search_parts.append(f'formType:"{form_type}"')
        if date_from and date_to:
            search_parts.append(f'filedAt:[{date_from} TO {date_to}]')
        
        search_query = ' AND '.join(search_parts)
        
        params = {
            'q': search_query,
            'from': 0,
            'size': limit,
            'sort': 'filedAt:desc'
        }
        
        response = requests.get(SEC_SEARCH_BASE_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get('hits', {}).get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'cik': source.get('ciks', [''])[0] if source.get('ciks') else '',
                'company': source.get('display_names', [''])[0] if source.get('display_names') else '',
                'form_type': source.get('form', ''),
                'filing_date': source.get('file_date', ''),
                'accession_number': source.get('adsh', ''),
                'description': source.get('file_description', ''),
                'file_num': source.get('file_num', ''),
                'period_of_report': source.get('period_ending', '')
            })
        
        return results
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_ipo_filings(date_from: Optional[str] = None,
                    date_to: Optional[str] = None,
                    limit: int = 20) -> List[Dict]:
    """
    Get recent IPO filings (S-1 registration statements).
    
    Args:
        date_from: Start date in YYYY-MM-DD format (optional)
        date_to: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of results (default: 20)
    
    Returns:
        List of dicts with IPO filing details
    
    Example:
        >>> ipos = get_ipo_filings(date_from='2024-01-01', limit=10)
        >>> for ipo in ipos[:3]:
        ...     print(f"{ipo['company']} filed S-1 on {ipo['filing_date']}")
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Search for S-1 filings (IPO registration)
        search_query = 'formType:"S-1"'
        if date_from and date_to:
            search_query += f' AND filedAt:[{date_from} TO {date_to}]'
        
        params = {
            'q': search_query,
            'from': 0,
            'size': limit,
            'sort': 'filedAt:desc'
        }
        
        response = requests.get(SEC_SEARCH_BASE_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get('hits', {}).get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'cik': source.get('ciks', [''])[0] if source.get('ciks') else '',
                'company': source.get('display_names', [''])[0] if source.get('display_names') else '',
                'form_type': source.get('form', ''),
                'filing_date': source.get('file_date', ''),
                'accession_number': source.get('adsh', ''),
                'description': source.get('file_description', ''),
                'file_num': source.get('file_num', '')
            })
        
        return results
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_recent_8k(ticker: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get recent 8-K current reports (material events disclosure).
    
    Args:
        ticker: Stock ticker symbol to filter by (optional)
        limit: Maximum number of results (default: 20)
    
    Returns:
        List of dicts with 8-K filing details
    
    Example:
        >>> reports = get_recent_8k(ticker='AAPL', limit=5)
        >>> for report in reports:
        ...     print(f"{report['filing_date']}: {report['description']}")
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Search for 8-K filings
        search_query = 'formType:"8-K"'
        if ticker:
            search_query += f' AND tickers:"{ticker.upper()}"'
        
        params = {
            'q': search_query,
            'from': 0,
            'size': limit,
            'sort': 'filedAt:desc'
        }
        
        response = requests.get(SEC_SEARCH_BASE_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get('hits', {}).get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'cik': source.get('ciks', [''])[0] if source.get('ciks') else '',
                'company': source.get('display_names', [''])[0] if source.get('display_names') else '',
                'tickers': source.get('tickers', []),
                'form_type': source.get('form', ''),
                'filing_date': source.get('file_date', ''),
                'accession_number': source.get('adsh', ''),
                'description': source.get('file_description', ''),
                'items': source.get('items', [])
            })
        
        return results
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_insider_filings(company: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get insider trading filings (Form 4).
    
    Args:
        company: Company name to filter by (optional)
        limit: Maximum number of results (default: 20)
    
    Returns:
        List of dicts with Form 4 insider trading details
    
    Example:
        >>> insiders = get_insider_filings(company='Apple', limit=10)
        >>> for trade in insiders[:3]:
        ...     print(f"{trade['company']}: {trade['filing_date']}")
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Search for Form 4 filings (insider trading)
        search_query = 'formType:"4"'
        if company:
            search_query += f' AND "{company}"'
        
        params = {
            'q': search_query,
            'from': 0,
            'size': limit,
            'sort': 'filedAt:desc'
        }
        
        response = requests.get(SEC_SEARCH_BASE_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get('hits', {}).get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'cik': source.get('ciks', [''])[0] if source.get('ciks') else '',
                'company': source.get('display_names', [''])[0] if source.get('display_names') else '',
                'form_type': source.get('form', ''),
                'filing_date': source.get('file_date', ''),
                'accession_number': source.get('adsh', ''),
                'description': source.get('file_description', '')
            })
        
        return results
        
    except requests.exceptions.RequestException as e:
        return [{'error': f'Request failed: {str(e)}'}]
    except Exception as e:
        return [{'error': f'Unexpected error: {str(e)}'}]


def get_filing_text(accession_number: str) -> str:
    """
    Fetch full text content of a filing by accession number.
    
    Args:
        accession_number: SEC accession number (format: 0001234567-12-123456)
    
    Returns:
        String containing the full filing text
    
    Example:
        >>> text = get_filing_text('0001193125-21-012345')
        >>> print(text[:500])  # First 500 chars
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Parse accession number to build URL
        # Format: 0001234567-12-123456 → CIK: 1234567, File: 0001234567-12-123456.txt
        cik = accession_number.split('-')[0].lstrip('0')
        if not cik:
            return f"Error: Invalid accession number format: {accession_number}"
        
        # Build filing URL
        accession_clean = accession_number.replace('-', '')
        url = f"{SEC_FILING_BASE_URL}/{cik}/{accession_clean}/{accession_number}.txt"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.text
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching filing: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    # Test the module
    print("SEC EDGAR EFTS Module Test")
    print("=" * 50)
    
    # Test search
    print("\n1. Testing search_filings()...")
    results = search_filings('blockchain', form_type='10-K', limit=3)
    print(f"Found {len(results)} results")
    if results and 'error' not in results[0]:
        print(f"Sample: {results[0]['company']} - {results[0]['filing_date']}")
    
    # Test IPO filings
    print("\n2. Testing get_ipo_filings()...")
    ipos = get_ipo_filings(limit=3)
    print(f"Found {len(ipos)} IPO filings")
    if ipos and 'error' not in ipos[0]:
        print(f"Sample: {ipos[0]['company']} - {ipos[0]['filing_date']}")
    
    # Test 8-K
    print("\n3. Testing get_recent_8k()...")
    eightk = get_recent_8k(limit=3)
    print(f"Found {len(eightk)} 8-K filings")
    if eightk and 'error' not in eightk[0]:
        print(f"Sample: {eightk[0]['company']} - {eightk[0]['filing_date']}")
    
    print("\n" + "=" * 50)
    print("Module test complete!")
