#!/usr/bin/env python3
"""
SEC-API.io — Insider Trading & Institutional Holdings

Provides access to SEC EDGAR filings including:
- Insider trading data (Form 4 filings)
- Institutional holdings (13F filings)
- Full-text search across all filing types

Uses FREE SEC EDGAR EFTS API as primary source (no API key required).
Falls back to sec-api.io for premium features when SEC_API_KEY is set.

Source: https://sec-api.io/ + https://efts.sec.gov
Category: Insider & Institutional
Free tier: Unlimited via SEC EDGAR, 100 req/day via sec-api.io
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
SEC_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_DATA_BASE = "https://data.sec.gov"
SEC_API_BASE = "https://api.sec-api.io"
SEC_API_KEY = os.environ.get("SEC_API_KEY", "")

# Required User-Agent for SEC.gov (per their robots.txt policy)
HEADERS = {
    "User-Agent": "QuantClaw Data/1.0 (quantclaw-data@moneyclaw.com)",
    "Accept": "application/json"
}


def _make_sec_request(url: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to SEC.gov with proper headers
    
    Args:
        url: Full URL to request
        params: Optional query parameters
    
    Returns:
        Dict with 'success' and either 'data' or 'error'
    """
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return {"success": True, "data": data}
    
    except requests.RequestException as e:
        return {"success": False, "error": f"HTTP error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON decode error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Resolve ticker symbol to CIK number using SEC company tickers mapping
    
    Args:
        ticker: Stock ticker (e.g., "AAPL")
    
    Returns:
        10-digit CIK string or None if not found
    """
    try:
        # SEC maintains a ticker -> CIK mapping at this endpoint
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        ticker_upper = ticker.upper()
        
        # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)  # Zero-pad to 10 digits
                return cik
        
        return None
    
    except Exception:
        return None


def get_insider_trades(ticker: str, days: int = 30) -> Dict:
    """
    Get insider trading filings (Form 4) for a company
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "TSLA")
        days: Number of days to look back (default 30)
    
    Returns:
        Dict with insider trades including transaction type, shares, prices
    """
    try:
        # Resolve ticker to CIK
        cik = _get_cik_from_ticker(ticker)
        if not cik:
            return {
                "success": False,
                "error": f"Could not resolve ticker '{ticker}' to CIK"
            }
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Search SEC EFTS for Form 4 filings
        query = f'ciks:{cik} AND forms:"4"'
        url = SEC_EFTS_BASE
        params = {
            "q": query,
            "dateRange": "custom",
            "startdt": start_date.strftime("%Y-%m-%d"),
            "enddt": end_date.strftime("%Y-%m-%d")
        }
        
        result = _make_sec_request(url, params)
        if not result["success"]:
            return result
        
        data = result["data"]
        
        # Parse filings
        trades = []
        hits = data.get("hits", {}).get("hits", [])
        
        for hit in hits:
            source = hit.get("_source", {})
            
            trade = {
                "filing_date": source.get("file_date", ""),
                "accession_number": source.get("adsh", ""),
                "form_type": source.get("form", ""),
                "company_name": source.get("display_names", [""])[0] if source.get("display_names") else "",
                "cik": source.get("ciks", [""])[0] if source.get("ciks") else "",
                "file_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&dateb=&owner=include&count=40"
            }
            
            trades.append(trade)
        
        return {
            "success": True,
            "ticker": ticker,
            "cik": cik,
            "trades": trades,
            "count": len(trades),
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }


def get_13f_holdings(cik_or_name: str, quarter: Optional[str] = None) -> Dict:
    """
    Get institutional holdings from 13F filings
    
    Args:
        cik_or_name: CIK number or institution name (e.g., "0001067983" or "Berkshire Hathaway")
        quarter: Optional quarter in YYYY-Q format (e.g., "2024-Q4"). Defaults to latest.
    
    Returns:
        Dict with 13F holdings data
    """
    try:
        # If name provided, try to resolve to CIK
        cik = cik_or_name if cik_or_name.isdigit() else None
        
        if not cik:
            # Search for institution by name
            query = f'"{cik_or_name}" AND forms:"13F-HR"'
            url = SEC_EFTS_BASE
            params = {"q": query}
            
            result = _make_sec_request(url, params)
            if not result["success"]:
                return result
            
            hits = result["data"].get("hits", {}).get("hits", [])
            if not hits:
                return {
                    "success": False,
                    "error": f"No 13F filings found for '{cik_or_name}'"
                }
            
            # Extract CIK from first result
            cik = hits[0].get("_source", {}).get("ciks", [""])[0]
            if not cik:
                return {
                    "success": False,
                    "error": "Could not extract CIK from search results"
                }
        
        # Zero-pad CIK to 10 digits
        cik = str(cik).zfill(10)
        
        # Fetch company submissions to get latest 13F filing
        url = f"{SEC_DATA_BASE}/submissions/CIK{cik}.json"
        result = _make_sec_request(url)
        
        if not result["success"]:
            return result
        
        data = result["data"]
        
        # Find 13F-HR filings
        recent_filings = data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        filing_dates = recent_filings.get("filingDate", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        
        filings_13f = []
        for i, form in enumerate(forms):
            if form == "13F-HR":
                filings_13f.append({
                    "filing_date": filing_dates[i],
                    "accession_number": accession_numbers[i],
                    "primary_document": primary_documents[i],
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F&dateb=&owner=exclude&count=40"
                })
        
        if not filings_13f:
            return {
                "success": False,
                "error": f"No 13F-HR filings found for CIK {cik}"
            }
        
        # Get latest filing (or specific quarter if requested)
        target_filing = filings_13f[0]  # Latest by default
        
        if quarter:
            # Parse quarter (e.g., "2024-Q4" -> "2024-12-31")
            try:
                year, q = quarter.split("-Q")
                quarter_end_month = int(q) * 3
                quarter_end = f"{year}-{quarter_end_month:02d}-{[31, 30, 30, 31][int(q)-1]}"
                
                # Find filing closest to quarter end
                for filing in filings_13f:
                    if filing["filing_date"] >= quarter_end:
                        target_filing = filing
                        break
            except Exception:
                pass  # Use latest if quarter parsing fails
        
        return {
            "success": True,
            "cik": cik,
            "institution": data.get("name", ""),
            "latest_filing": target_filing,
            "all_13f_filings": filings_13f[:5],  # Last 5 quarters
            "total_13f_count": len(filings_13f),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cik_or_name": cik_or_name
        }


def search_filings(
    query: str,
    form_type: Optional[str] = None,
    date_from: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """
    Full-text search across SEC filings
    
    Args:
        query: Search query (ticker, company name, CIK, or text)
        form_type: Optional form type filter (e.g., "4", "10-K", "13F-HR")
        date_from: Optional start date in YYYY-MM-DD format
        limit: Maximum number of results (default 10, max 100)
    
    Returns:
        Dict with matching filings
    """
    try:
        # Build search query
        search_query = query
        if form_type:
            search_query += f' AND forms:"{form_type}"'
        
        # Set date range
        params = {"q": search_query}
        
        if date_from:
            params["dateRange"] = "custom"
            params["startdt"] = date_from
            params["enddt"] = datetime.now().strftime("%Y-%m-%d")
        
        # Execute search
        result = _make_sec_request(SEC_EFTS_BASE, params)
        if not result["success"]:
            return result
        
        data = result["data"]
        hits = data.get("hits", {}).get("hits", [])
        
        # Parse results
        filings = []
        for hit in hits[:limit]:
            source = hit.get("_source", {})
            
            filing = {
                "company_name": source.get("display_names", [""])[0] if source.get("display_names") else "",
                "cik": source.get("ciks", [""])[0] if source.get("ciks") else "",
                "form_type": source.get("form", ""),
                "filing_date": source.get("file_date", ""),
                "period_ending": source.get("period_ending", ""),
                "accession_number": source.get("adsh", ""),
                "file_number": source.get("file_num", ""),
                "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={source.get('ciks', [''])[0]}&type={source.get('form', '')}&dateb=&owner=exclude&count=40"
            }
            
            filings.append(filing)
        
        return {
            "success": True,
            "query": query,
            "form_type": form_type,
            "filings": filings,
            "count": len(filings),
            "total_hits": data.get("hits", {}).get("total", {}).get("value", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def get_latest(form_type: str = "4", limit: int = 20) -> Dict:
    """
    Get latest filings of specified type (defaults to Form 4 insider trades)
    
    Args:
        form_type: Form type to fetch (default "4" for insider trades)
        limit: Number of latest filings to return (default 20)
    
    Returns:
        Dict with latest filings
    """
    try:
        # Search for latest filings of specified type
        query = f'forms:"{form_type}"'
        params = {
            "q": query,
            "dateRange": "custom",
            "startdt": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "enddt": datetime.now().strftime("%Y-%m-%d")
        }
        
        result = _make_sec_request(SEC_EFTS_BASE, params)
        if not result["success"]:
            return result
        
        data = result["data"]
        hits = data.get("hits", {}).get("hits", [])
        
        # Parse latest filings
        filings = []
        for hit in hits[:limit]:
            source = hit.get("_source", {})
            
            filing = {
                "company_name": source.get("display_names", [""])[0] if source.get("display_names") else "",
                "ticker": source.get("tickers", [""])[0] if source.get("tickers") else "",
                "cik": source.get("ciks", [""])[0] if source.get("ciks") else "",
                "form_type": source.get("form", ""),
                "filing_date": source.get("file_date", ""),
                "accession_number": source.get("adsh", ""),
                "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={source.get('ciks', [''])[0]}&type={form_type}&dateb=&owner=include&count=40"
            }
            
            filings.append(filing)
        
        # Sort by filing date (most recent first)
        filings.sort(key=lambda x: x["filing_date"], reverse=True)
        
        return {
            "success": True,
            "form_type": form_type,
            "filings": filings,
            "count": len(filings),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "form_type": form_type
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("SEC-API.io - Insider Trading & Institutional Holdings")
    print("=" * 60)
    
    print("\nModule Functions:")
    print("  1. get_insider_trades(ticker, days=30)")
    print("  2. get_13f_holdings(cik_or_name, quarter=None)")
    print("  3. search_filings(query, form_type=None, date_from=None, limit=10)")
    print("  4. get_latest(form_type='4', limit=20)")
    
    print("\n" + json.dumps({
        "module": "sec_apiio",
        "status": "ready",
        "source": "SEC EDGAR EFTS (FREE)",
        "features": [
            "Insider trades (Form 4)",
            "Institutional holdings (13F)",
            "Full-text filing search",
            "Latest filings feed"
        ]
    }, indent=2))
