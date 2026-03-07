"""
SEC EDGAR Full-Text Search API

Source: https://efts.sec.gov/LATEST/search-index
Category: SEC Filings & Corporate Data
Frequency: Real-time
Authentication: None (free, public access)

Search across all SEC filings by keyword, date, form type. Real-time RSS feeds for new filings.
No API key needed. Must set User-Agent header per SEC policy.
"""

import requests
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import quote

# SEC requires User-Agent header
HEADERS = {
    "User-Agent": "QuantClaw/1.0 (quantclaw@moneyclaw.com)",
    "Accept": "application/json"
}

BASE_URL = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE = "https://www.sec.gov"


def search_filings(
    query: str,
    form_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search SEC filings by keyword with optional filters.
    
    Args:
        query: Search query string
        form_type: Filter by form type (e.g., "10-K", "8-K", "10-Q")
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
        limit: Maximum number of results (default 10)
    
    Returns:
        List of filing dictionaries with metadata
    """
    try:
        # Build query parameters
        search_query = query
        if form_type:
            search_query += f' AND form:"{form_type}"'
        if date_from:
            search_query += f' AND file_date:[{date_from} TO '
            if date_to:
                search_query += f'{date_to}]'
            else:
                search_query += '*]'
        
        params = {
            "q": search_query,
            "from": 0,
            "size": limit
        }
        
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            ciks = source.get("ciks", [])
            cik = ciks[0] if ciks else None
            display_names = source.get("display_names", [])
            company_name = display_names[0] if display_names else None
            
            results.append({
                "accession_number": source.get("adsh"),
                "filing_date": source.get("file_date"),
                "form_type": source.get("form"),
                "company_name": company_name,
                "cik": cik,
                "file_number": source.get("file_num", []),
                "file_type": source.get("file_type"),
                "description": source.get("file_description"),
                "sic": source.get("sics", []),
                "period_ending": source.get("period_ending"),
                "url": f"{EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={source.get('form')}&dateb=&owner=exclude&count=40" if cik else None
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request failed: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]


def get_filing_text(accession_number: str) -> Dict[str, Any]:
    """
    Get full filing text by accession number.
    
    Args:
        accession_number: SEC accession number (e.g., "0001193125-21-123456")
    
    Returns:
        Dictionary with filing text and metadata
    """
    try:
        # Format accession number for URL (remove dashes)
        acc_no = accession_number.replace("-", "")
        
        # Build filing URL
        filing_url = f"{EDGAR_BASE}/cgi-bin/viewer?action=view&cik={acc_no[:10]}&accession_number={accession_number}&xbrl_type=v"
        
        response = requests.get(filing_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        return {
            "accession_number": accession_number,
            "text": response.text[:50000],  # Truncate to first 50k chars
            "full_length": len(response.text),
            "url": filing_url,
            "retrieved_at": datetime.now().isoformat()
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "accession_number": accession_number}
    except Exception as e:
        return {"error": f"Failed to get filing text: {str(e)}", "accession_number": accession_number}


def search_by_company(
    company_name: str,
    form_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search filings by company name.
    
    Args:
        company_name: Company name to search
        form_type: Optional form type filter (e.g., "10-K", "8-K")
        limit: Maximum number of results (default 10)
    
    Returns:
        List of filing dictionaries for the company
    """
    try:
        search_query = f'"{company_name}"'
        if form_type:
            search_query += f' AND form:"{form_type}"'
        
        params = {
            "q": search_query,
            "from": 0,
            "size": limit,
            "sort": [{"file_date": {"order": "desc"}}]
        }
        
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            ciks = source.get("ciks", [])
            cik = ciks[0] if ciks else None
            display_names = source.get("display_names", [])
            company = display_names[0] if display_names else None
            
            results.append({
                "accession_number": source.get("adsh"),
                "filing_date": source.get("file_date"),
                "form_type": source.get("form"),
                "company_name": company,
                "cik": cik,
                "file_type": source.get("file_type"),
                "description": source.get("file_description"),
                "period_ending": source.get("period_ending")
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request failed: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Company search failed: {str(e)}"}]


def search_insider_filings(
    ticker: str,
    date_from: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search insider trading filings (Form 4) by ticker.
    
    Args:
        ticker: Stock ticker symbol
        date_from: Optional start date in YYYY-MM-DD format
        limit: Maximum number of results (default 20)
    
    Returns:
        List of Form 4 insider filing dictionaries
    """
    try:
        search_query = f'{ticker} AND form:"4"'
        if date_from:
            search_query += f' AND file_date:[{date_from} TO *]'
        
        params = {
            "q": search_query,
            "from": 0,
            "size": limit,
            "sort": [{"file_date": {"order": "desc"}}]
        }
        
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            ciks = source.get("ciks", [])
            cik = ciks[0] if ciks else None
            display_names = source.get("display_names", [])
            company = display_names[0] if display_names else None
            
            results.append({
                "accession_number": source.get("adsh"),
                "filing_date": source.get("file_date"),
                "form_type": source.get("form"),
                "company_name": company,
                "cik": cik,
                "period_ending": source.get("period_ending"),
                "url": f"{EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&dateb=&owner=include&count=40" if cik else None
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request failed: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Insider search failed: {str(e)}"}]


def get_recent_filings(
    form_type: str = "10-K",
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get most recent filings by form type.
    
    Args:
        form_type: Form type to search (default "10-K")
        limit: Maximum number of results (default 20)
    
    Returns:
        List of recent filing dictionaries
    """
    try:
        params = {
            "q": f'form:"{form_type}"',
            "from": 0,
            "size": limit,
            "sort": [{"file_date": {"order": "desc"}}]
        }
        
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            ciks = source.get("ciks", [])
            cik = ciks[0] if ciks else None
            display_names = source.get("display_names", [])
            company = display_names[0] if display_names else None
            
            results.append({
                "accession_number": source.get("adsh"),
                "filing_date": source.get("file_date"),
                "form_type": source.get("form"),
                "company_name": company,
                "cik": cik,
                "file_type": source.get("file_type"),
                "description": source.get("file_description"),
                "period_ending": source.get("period_ending"),
                "url": f"{EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=exclude&count=40" if cik else None
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        return [{"error": f"Request failed: {str(e)}"}]
    except Exception as e:
        return [{"error": f"Recent filings search failed: {str(e)}"}]
